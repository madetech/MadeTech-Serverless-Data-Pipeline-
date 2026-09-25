import pandas as pd
from duckdb import InvalidInputException
from sqlalchemy.types import JSON
from src.data_transformation.data_connector import DataConnector
from src.data_transformation.data_ingestor import DataIngestor
from src.data_transformation.historical_data import HistoricalDataProcessor
from src.data_transformation.schema_mapping import SchemaMapping

# TODO: Look into replacing print statements with logging statements

### GLOBAL VARIABLES CLASS INSTANTIATION
con = DataConnector()
ingestor = DataIngestor("fakestore_api", "0.1")
schema_mapping = SchemaMapping()
history = HistoricalDataProcessor()
schema = schema_mapping.load_yaml_schema("table_metadata/table_schema.yaml")
dtype_mapping = schema_mapping.build_dtype_dict(schema)

credentials = con.read_database_credentials("credentials/db_creds_local.yaml")

con_string = con.create_connection_string(
    credentials, connect_to_database=True, new_db_name="api_data"
)

db_engine = con.initialise_database_connection(con_string)
print(db_engine)


def load_bronze_table():
    ### BRONZE LAYER ####

    try:
        bronze_df = pd.read_parquet("sample_data/sample_api.parquet")
        bronze_layer_table = ingestor.create_duck_db_relation(bronze_df)
    except InvalidInputException:
        raise InvalidInputException(
            "Invalid format. Please create one of the following objects first "
            "pandas.DataFrame "
            "duckdb.DuckDBPyRelation "
            "pyarrow Table, Dataset "
            "RecordBatchReader "
            "Scanner "
            "or NumPy ndarrays with supported format "
        )
    bronze_layer_table_with_metadata = ingestor.add_metadata_columns(
        rel=bronze_layer_table
    )

    print(bronze_layer_table_with_metadata.columns)

    con.load_to_db(
        bronze_layer_table_with_metadata.to_df(),
        db_engine,
        "bronze_fake_ecommerce_api_data",
        "replace",
        "bronze_layer",
        dtypes={"rating": JSON},
    )


def database_table_name_check(table_name: str):
    # List all tables within the database and add them to a list.
    list_of_database_tables = con.list_db_tables(db_engine, schema=True)
    # Scan through the list to verify if the table_name exists.
    if table_name in list_of_database_tables:
        print(
            f"table_name {table_name} exists. Applying Historical Transformations"
        )
        return True
    else:
        print("Table does not exist")
        return False


def load_silver_table(table_name: str):
    ### SILVER LAYER ###
    table_name_check = database_table_name_check(f"silver_{table_name}")

    if table_name_check == True:
        # Read in the bronze and silver tables
        bronze_table = ingestor.extract_from_database(
            f"bronze_{table_name}", db_engine, "bronze_layer"
        )
        current_silver_table = ingestor.extract_from_database(
            f"silver_{table_name}", db_engine, "silver_layer"
        )
        # Convert the pandas dataframes to duckdb relations
        bronze_table_duckdb = ingestor.create_duck_db_relation(bronze_table)
        silver_table_duckdb = ingestor.create_duck_db_relation(
            current_silver_table
        )

        combined_table = history.compare_records(
            bronze_table_duckdb, silver_table_duckdb, "id"
        )
        altered_records = history.filter_unchanged_records(
            combined_table=combined_table
        )
        if len(altered_records) == 0:
            print("Empty Table. Skipping table upload")
        else:
            # Update the timestamp(s) within the silver_table

            appended_silver_table = ingestor.update_timestamp(
                altered_records, "ingestion_timestamp"
            )
            # TODO: Add in some slowly changing dimension logic here (SCD 1 or 2?)

            con.load_to_db(
                appended_silver_table.to_df(),
                db_engine,
                f"silver_{table_name}",
                "append",
                "silver_layer",
                dtypes=dtype_mapping,
            )

    else:
        extracted_bronze_table = ingestor.extract_from_database(
            "bronze_fake_ecommerce_api_data", db_engine, "bronze_layer"
        )

        duckdb_bronze_table = ingestor.create_duck_db_relation(
            extracted_bronze_table
        )

        silver_table = ingestor.update_timestamp(
            duckdb_bronze_table, "ingestion_timestamp"
        )

        con.load_to_db(
            silver_table.to_df(),
            db_engine,
            "silver_fake_ecommerce_api_data",
            "replace",
            "silver_layer",
            dtypes=dtype_mapping,
        )


def load_gold_table():
    ### GOLD LAYER ###
    extracted_silver_table = ingestor.extract_from_database(
        "silver_fake_ecommerce_api_data", db_engine, "silver_layer"
    )

    duckdb_silver_table = ingestor.create_duck_db_relation(
        extracted_silver_table
    )

    gold_table = ingestor.update_timestamp(
        duckdb_silver_table, "ingestion_timestamp"
    )

    con.load_to_db(
        gold_table.to_df(),
        db_engine,
        "gold_fake_ecommerce_api_data",
        "replace",
        "gold_layer",
        dtypes=dtype_mapping,
    )


def main():
    load_bronze_table()
    load_silver_table("fake_ecommerce_api_data")
    load_gold_table()


# Commented functions for testing purposes
# load_bronze_table()
# load_silver_table("fake_ecommerce_api_data")
# load_gold_table()
main()

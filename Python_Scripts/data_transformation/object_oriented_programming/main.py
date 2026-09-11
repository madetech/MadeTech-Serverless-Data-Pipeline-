from data_transformation.data_connector import DataConnector
from data_transformation.data_ingestor import DataIngestor
from data_transformation.schema_mapping import SchemaMapping
from data_transformation.historical_data import HistoricalDataProcessor
from sqlalchemy.types import JSON
import pandas as pd 


### GLOBAL VARIABLES CLASS INSTANTIATION 
con = DataConnector()
ingestor = DataIngestor('fakestore_api', "0.1")
schema_mapping = SchemaMapping()
history = HistoricalDataProcessor()
schema = schema_mapping.load_yaml_schema("table_metadata/table_schema.yaml")
dtype_mapping = schema_mapping.build_dtype_dict(schema)

credentials = con.read_database_credentials('credentials/db_creds_local.yaml')
print(credentials)
con_string = con.create_connection_string(credentials, connect_to_database=True, new_db_name='api_data')
print(con_string)
db_engine = con.initialise_database_connection(con_string)
print(db_engine)


def load_bronze_table():
### BRONZE LAYER #### 
    df = pd.read_parquet('sample_data/sample_api.parquet')

    bronze_layer_table = ingestor.add_metadata_columns(df)

    print(bronze_layer_table.columns)

    con.load_to_db(bronze_layer_table, db_engine, 'bronze_fake_ecommerce_api_data', 'replace', 'bronze_layer', dtypes={"rating": JSON})

def database_table_name_check(table_name : str):
    # List all tables within the database and add them to a list. 
    list_of_database_tables = con.list_db_tables(db_engine, schema=True)
    # Scan through the list to verify if the table_name exists.
    if table_name in list_of_database_tables:
        print(f"table_name {table_name} exists. Applying Historical Transformations")
        return True
    else:
        print('Table does not exist')
        return False 
    
def load_silver_table(table_name : str):
    ### SILVER LAYER ###
    table_name_check = database_table_name_check(table_name)

    if table_name_check == True:
        # Read in the bronze and silver tables 
        bronze_table = ingestor.extract_from_database(f"bronze_{table_name}", db_engine, "bronze_layer")
        current_silver_table = ingestor.extract_from_database(f"silver_{table_name}", db_engine, "silver_layer")

        # Add Hash Columns to both tables 
        bronze_table_hash = history.create_hash_column(bronze_table)
        silver_table_hash = history.create_hash_column(current_silver_table)

        # Compare both hash columns 
        comparison_df = history.compare_hashes(silver_table_hash, bronze_table_hash, 'id')
        # Filter out unchanged records 
        altered_records_df = comparison_df[comparison_df['status'] != 'unchanged']
        if len(altered_records_df) == 0:
            print('Empty DataFrame. Skipping table upload')
        else:
            # Drop the hash columns from the table 
            no_hashes_df = altered_records_df.drop(columns=['hash_column_current', 'hash_column_new'])
            #TODO: Add in some slowly changing dimension logic here (SCD 1 or 2?)
            # Add the metadata columns to the no_hashes_df then upload to the db, appending to the table 
            appended_silver_table = ingestor.add_metadata_columns(no_hashes_df)
            con.load_to_db(appended_silver_table, db_engine, f'silver_{table_name}', 'append', 'silver_layer', dtypes=dtype_mapping)
        
    else:
        extracted_bronze_table = ingestor.extract_from_database('bronze_fake_ecommerce_api_data', db_engine, 'bronze_layer')
        
        silver_table = ingestor.add_metadata_columns(extracted_bronze_table)

        con.load_to_db(silver_table, db_engine, 'silver_fake_ecommerce_api_data', 'replace', 'silver_layer', dtypes=dtype_mapping)


def load_gold_table(): 
    ### GOLD LAYER ###
    extracted_silver_table = ingestor.extract_from_database('silver_fake_ecommerce_api_data', db_engine, 'silver_layer')

    gold_table = ingestor.add_metadata_columns(extracted_silver_table)

    con.load_to_db(gold_table, db_engine, 'gold_fake_ecommerce_api_data', 'replace', 'gold_layer', dtypes=dtype_mapping)



def main(): 
    load_bronze_table()
    load_silver_table("fake_ecommerce_api_data")
    load_gold_table()

main()


from data_transformation.data_connector import DataConnector
from data_transformation.data_ingestor import DataIngestor
from data_transformation.schema_mapping import SchemaMapping
from sqlalchemy.types import JSON
import pandas as pd 


### GLOBAL VARIABLES CLASS INSTANTIATION 
con = DataConnector()
ingestor = DataIngestor('fakestore_api', "0.1")
schema_mapping = SchemaMapping()
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

def load_silver_table():
    ### SILVER LAYER ###
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
    load_silver_table()
    load_gold_table()



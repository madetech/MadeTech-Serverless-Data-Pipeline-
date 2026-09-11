from botocore.exceptions import ClientError
from datetime import datetime
from io import BytesIO
from pandas import DataFrame
from sqlalchemy.engine import Engine 
from sqlalchemy.exc import OperationalError
import boto3 
import io 
import pandas as pd 

class DataIngestor: 

    def __init__(self, source_name="unknown", version="1.0"):
        self.source_name = source_name
        self.version = version
        self.s3_client = boto3.client('s3')

    def extract_from_database(self, table_name : str, engine : Engine, schema_name : str):

        try: 
            df = pd.read_sql_table(table_name, engine, schema=schema_name)
            return df 
        except OperationalError as e:
                    # Handles connection query errors
                    raise ValueError(f"Failed to read table '{table_name}': {e}")

        except Exception as e:
            # Handles other exceptions
            raise Exception(f"Error occured while reading table '{table_name}' : {e}")


    def extract_from_s3(self, bucket_name, object_file_path):

        try:
            # Get the API response from boto3 
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_file_path)
            # For debugging purposes 
            # print(response) 
            # Read in raw file in bytes 
            raw_bytes = response['Body'].read()

            buffer = io.BytesIO(raw_bytes)
            return buffer 
        except ClientError as e:
            print(f"Failed to extract {object_file_path} from bucket {bucket_name}: {e}")
            raise e

    def add_metadata_columns(self, df: DataFrame):

        df = df.copy() 
        df["source"] = self.source_name
        df["version"] = self.version
        df["ingestion_timestamp"] = datetime.now()

        return df 


        
    def _load_pandas(self, buffer : BytesIO , file_type : str ):
        
        if file_type == 'csv':
            return pd.read_csv(buffer)
        elif file_type == 'json':
            return pd.read_json(buffer)
        elif file_type == 'parquet':
            return pd.read_parquet(buffer)
        else:
            raise ValueError(f"Unsupported file_type '{file_type}' for pandas engine")


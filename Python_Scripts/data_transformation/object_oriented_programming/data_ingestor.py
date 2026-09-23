import io
from datetime import datetime
from io import BytesIO
from typing import Any

import boto3
import duckdb
import pandas as pd
from botocore.exceptions import ClientError
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError


class DataIngestor:
    def __init__(self, source_name: str = "unknown", version: str = "1.0"):
        self.source_name = source_name
        self.version = version
        self.s3_client = boto3.client("s3")

    def extract_from_database(
        self, table_name: str, engine: Engine, schema_name: str
    ):

        try:
            df = pd.read_sql_table(table_name, engine, schema=schema_name)
            return df
        except OperationalError as e:
            # Handles connection query errors
            raise ValueError(f"Failed to read table '{table_name}': {e}")

    def extract_from_s3(self, bucket_name, object_file_path):

        try:
            # Get the API response from boto3
            response = self.s3_client.get_object(
                Bucket=bucket_name, Key=object_file_path
            )
            # For debugging purposes
            # print(response)
            # Read in raw file in bytes
            raw_bytes = response["Body"].read()

            buffer = io.BytesIO(raw_bytes)
            return buffer
        except ClientError as e:
            print(
                f"Failed to extract {object_file_path} from bucket {bucket_name}: {e}"
            )
            raise e

    def create_duck_db_relation(
        self, data_object: Any
    ) -> duckdb.DuckDBPyRelation:
        """
        Wrap an existing pandas.DataFrame, pyarrow Table/Dataset,
        RecordBatchReader, Scanner, or NumPy ndarray into a DuckDBPyRelation.
        """
        try:
            return (
                duckdb.sql(
                    "SELECT * FROM data_object",
                    params={"data_object": data_object},
                )
                if False
                else duckdb.from_df(data_object)
                if isinstance(data_object, pd.DataFrame)
                else duckdb.sql("SELECT * FROM data_object")
            )
        except duckdb.InvalidInputException as e:
            raise duckdb.InvalidInputException(
                "Invalid format. Please create one of the following objects first "
                "pandas.DataFrame, duckdb.DuckDBPyRelation, pyarrow Table, Dataset, "
                "RecordBatchReader, Scanner, or NumPy ndarrays with supported format"
            ) from e

    def add_metadata_columns(
        self, rel: duckdb.DuckDBPyRelation, **kwargs: dict[str, Any]
    ) -> duckdb.DuckDBPyRelation:
        """
        Add one or more constant metadata columns to a DuckDBPyRelation
        by cross-joining it with a one-row relation of metadata values.

        This avoids relying on DuckDB's automatic scope lookup for `rel`,
        since the relation is passed in and joined explicitly.
        """
        defaults = {
            "source_name": self.source_name,
            "version": self.version,
            "ingestion_timestamp": datetime.now(),
        }

        metadata = {**defaults, **kwargs}

        select_expr = ", ".join(f"${k} AS {k}" for k in metadata)
        meta_rel = duckdb.sql(f"SELECT {select_expr}", params=metadata)
        meta_rel.show()

        return rel.join(meta_rel, condition="1=1", how="inner")

    def _load_pandas(self, buffer: BytesIO, file_type: str):

        if file_type == "csv":
            return pd.read_csv(buffer)
        elif file_type == "json":
            return pd.read_json(buffer)
        elif file_type == "parquet":
            return pd.read_parquet(buffer)
        else:
            raise ValueError(
                f"Unsupported file_type '{file_type}' for pandas engine"
            )

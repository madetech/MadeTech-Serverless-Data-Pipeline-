import csv
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, ClassVar

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import requests
import tenacity
from log_config.logger import setup_logger

# requests.Session
# http.client
logger = setup_logger(__name__)

s3_client = boto3.client("s3")

BASE_URL = "https://fakestoreapi.com"


class APIClientError(Exception):
    """
    Custom base exception to prevent leaking `requests` internals.
    """


@dataclass
class SchemaBuilder:
    fields: dict[str, Any]

    _TYPE_MAP: ClassVar[dict[str, pa.DataType]] = {
        # Null
        "null": pa.null(),
        # Boolean
        "boolean": pa.bool_(),
        # Signed integers
        "integer8": pa.int8(),
        "integer16": pa.int16(),
        "integer32": pa.int32(),
        "integer64": pa.int64(),
        # Unsigned integers
        "unsigned_integer8": pa.uint8(),
        "unsigned_integer16": pa.uint16(),
        "unsigned_integer32": pa.uint32(),
        "unsigned_integer64": pa.uint64(),
        # Floating point
        "float16": pa.float16(),
        "float32": pa.float32(),
        "float64": pa.float64(),
        # Date (no time component)
        "date32": pa.date32(),
        "date64": pa.date64(),
        # String / text
        "string": pa.string(),  # alias: pa.utf8()
        "large_string": pa.large_string(),  # alias: pa.large_utf8()
        "string_view": pa.string_view(),
        # Binary
        "binary": pa.binary(),  # variable-length by default (length=-1)
        "large_binary": pa.large_binary(),
        "binary_view": pa.binary_view(),
    }

    @classmethod
    def _resolve_leaf_type(cls, type_name: str) -> pa.DataType:
        try:
            return cls._TYPE_MAP[type_name]
        except KeyError:
            raise ValueError(f"Unsupported type: {type_name!r}")

    def _resolve_type(self, type_spec: str | dict) -> pa.DataType:
        if isinstance(type_spec, dict):
            return pa.struct(self._build_tuples(type_spec))
        return self._resolve_leaf_type(type_spec)

    def _build_tuples(
        self, fields: dict[str, Any]
    ) -> list[tuple[str, pa.DataType]]:
        return [
            (name, self._resolve_type(spec)) for name, spec in fields.items()
        ]

    def to_tuples(self) -> list[tuple[str, pa.DataType]]:
        return self._build_tuples(self.fields)

    def __call__(self) -> pa.Schema:
        return pa.schema(self.to_tuples())


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        )
    ),
    stop=(tenacity.stop_after_attempt(3)),
    wait=tenacity.wait_random_exponential(multiplier=1, max=30),
    reraise=True,
)
def make_request(
    method: str,
    url: str,
    headers: dict[str, Any],
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    stream: bool = False,
    timeout: tuple[int, int] = (3, 10),
) -> dict[str, Any] | list[dict[str, Any]] | Iterator[bytes]:
    """
    TODO:

    data
    What is being sent inside the request

    """
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=data,
            params=params,
            timeout=timeout,
            stream=stream,
        )
        # Checks the response
        response.raise_for_status()
        # Raise our own custom exception
    except requests.exceptions.HTTPError as err:
        # Check to see if the response is not blank
        assert err.response is not None

        if err.response.status_code == 404:
            # Raise the custom exception from the err exception
            raise APIClientError(str(err)) from err

        elif err.response.status_code == 401:
            raise APIClientError(
                f"{method} request to {url} failed! "
                f"{err.response.status_code} "
                "Authentication Error. Please check your credentials"
            ) from err
        else:
            # Fallback for other error messages.
            raise APIClientError(
                f"{method} request to {url} failed! "
                f"{err.response.status_code} {err.response.reason}"
            ) from err

    try:
        if stream == True:
            return response.iter_lines()
        else:
            return response.json()
    except requests.exceptions.JSONDecodeError:
        # check if the repsonse is not a blank string
        # breakpoint()
        if not response.text.strip():
            logger.warning(
                f"Request to {response.url} succeeded, but response is empty. "
                "Returning empty dictionary"
            )

            return {}
        raise APIClientError(
            f"Request to {response.url} succeeded, but returned invalid JSON."
        )


def get_product(product_id: int) -> dict[str, Any]:
    """
    Set up a basic stdout logging configuration.

    Usage: `logger = setup_logger(__name__)`.

    Args:
        name (str): Module `__name__` to ensure logs are traceable to their
            source code location.
        level (int): Root logger logging level. Ranges from 0 to 50.
            (DEBUG | INFO | WARNING | ERROR | CRITICAL).

    Returns:
        Logger (logging.Logger): An instance of the configured logging class.
    """
    try:
        clean_product_id = int(product_id)
    except (ValueError, TypeError):
        raise TypeError(
            f"product_id must be an integer, got {type(product_id)}!"
        )
    endpoint = f"/products/{clean_product_id}"
    url = BASE_URL + endpoint

    logger.info(f"Getting single product from {url}")

    data = make_request(method="get", url=url, headers={})

    if not isinstance(data, dict):
        raise TypeError(
            f"API response should be of type dict, got {type(data)} !"
        )

    # If a dictionary contains any items, it is Falsely object
    if not data:
        logger.warning(
            f"API returned an empty response "
            f"because there was no data for {product_id=}"
        )

    return data


# Write a function called get_all_products, where the function returns a generator of products


def get_all_products(stream: bool) -> Iterator[dict[str, Any]]:
    """
    Get all products as an iterator where each item is a dictionary.

    Raises:
        TypeError: When API response is not a raw list.

    Yields:
        Iterator[dict[str, Any]]: Iterator of product dictionaries.
    """

    endpoint = "/products"
    url = BASE_URL + endpoint

    logger.info(f"Getting all products from {url=}")

    data = make_request(method="get", url=url, headers={}, stream=stream)

    # check to see if the data is empty

    if not data:
        logger.warning(
            "API returned an empty response because there were no products"
        )
        return

    if not isinstance(data, list):
        raise TypeError(
            f"API response should be of type list, got {type(data)} !"
        )
    yield from data


def extract_field_names(data_list: list[dict[str, Any]]) -> list[str]:

    try:
        logger.debug(f"Extracting from {data_list}")
        logger.info(f"Number of records: {len(data_list)}")
        first_element = data_list[0]
        logger.info(f"Getting first element of list {first_element}")
        logger.debug(f"Type of the first element : {type(first_element)}")
        field_names = list(first_element.keys())
        logger.info(f"Generated field names : {field_names}")
        return field_names

    except TypeError:
        logger.critical(
            f"Output data should be a list got {type(data_list)} !"
        )
        raise TypeError(
            f"Output data should be a list got {type(data_list)} !"
        )


def save_to_csv(
    file_name: str, data: dict[str, Any], field_names: list[str]
) -> None:
    with open(f"{file_name}.csv", "w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=field_names, delimiter=","
        )
        writer.writeheader()
        for line in data:
            writer.writerow(line)


def save_to_parquet(
    file_name: str, data: list[dict[str, Any]], schema: pa.Schema
):
    with open(f"{file_name}.parquet", "w") as parquet_file:
        target_table = pa.Table.from_pylist(data, schema=schema)
        pq.write_table(table=target_table, where=f"{file_name}.parquet")


def file_transfer_to_s3(file_name: str, object_name: str, bucket_name: str):
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        print(
            f"Uploaded {file_name} to S3 bucket {bucket_name} to {object_name}"
        )
    except:
        raise Exception(f"Failed to upload {file_name} to S3 {e}")


if __name__ == "__main__":
    data_generator = get_all_products(stream=False)
    print(data_generator)
    # TODO: What if the field names change? Extract the field names from the API response
    generated_list = list(data_generator)
    field_names = extract_field_names(generated_list)
    field_definitions = {
        "id": "integer32",
        "title": "string",
        "price": "float64",
        "description": "string",
        "category": "string",
        "image": "string",
        "rating": {
            "rate": "float64",
            "count": "integer32",
        },
    }

    new_fields = {}

    builder = SchemaBuilder(field_definitions)
    schema_from_builder = builder()  # calling the instance returns pa.Schema

    save_to_csv("sample_data", data=generated_list, field_names=field_names)
    save_to_parquet(
        "sample_data_parquet", generated_list, schema=schema_from_builder
    )

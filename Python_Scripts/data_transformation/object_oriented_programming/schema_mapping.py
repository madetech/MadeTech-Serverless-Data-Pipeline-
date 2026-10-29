import yaml
from sqlalchemy import (
    Integer, String, Float, Text, JSON, Numeric,
    Boolean, DateTime, BigInteger, SmallInteger
)

class SchemaMapping:
# ---------------------------------------------------------
# Map string type names from YAML to actual SQLAlchemy classes
# ---------------------------------------------------------
    TYPE_MAP = {
        "Integer": Integer,
        "BigInteger": BigInteger,
        "SmallInteger": SmallInteger,
        "String": String,
        "Text": Text,
        "Float": Float,
        "Numeric": Numeric,
        "Boolean": Boolean,
        "DateTime": DateTime,
        "JSON": JSON,
    }
    def __init__(self): 
        pass 

    def load_yaml_schema(self, yaml_path: str) -> dict:
        """Load the YAML schema file."""
        with open(yaml_path, "r") as f:
            schema = yaml.safe_load(f)
        return schema


    def build_sqlalchemy_type(self, col_def: dict):
        """
        Given a column definition dict from YAML,
        instantiate the correct SQLAlchemy type with parameters.
        """
        type_name = col_def.get("type")
        sqla_type = self.TYPE_MAP.get(type_name)

        if sqla_type is None:
            raise ValueError(f"Unsupported type '{type_name}' in schema.")

        # Handle parameterized types
        if type_name == "String" and "length" in col_def:
            return sqla_type(length=col_def["length"])

        if type_name == "Numeric":
            precision = col_def.get("precision", 10)
            scale = col_def.get("scale", 2)
            return sqla_type(precision=precision, scale=scale)

        # Types without extra params (Integer, Float, Text, JSON, Boolean, etc.)
        return sqla_type()


    def build_dtype_dict(self, schema: dict) -> dict:
        """
        Build a dict of {column_name: SQLAlchemy type instance}
        suitable for pandas df.to_sql(dtype=...).
        """
        dtype_dict = {}
        columns = schema.get("columns", {})

        for col_name, col_def in columns.items():
            dtype_dict[col_name] = self.build_sqlalchemy_type(col_def)

        return dtype_dict


if __name__ == "__main__":
    # Example usage
    schema_mapping = SchemaMapping()
    schema = schema_mapping.load_yaml_schema("table_metadata/table_schema.yaml")
    dtype_mapping = schema_mapping.build_dtype_dict(schema)

    print("Generated dtype mapping for df.to_sql():\n")
    for col, sqla_type in dtype_mapping.items():
        print(f"  {col}: {sqla_type}")
import hashlib

import duckdb
import pandas as pd
from pandas import DataFrame


class HistoricalDataProcessor:
    # Default metadata columns to exclude from hashing
    DEFAULT_EXCLUDE_COLUMNS = [
        "ingestion_timestamp",
        "source",
        "version",
        "hash_column",
    ]

    def __init__(self, exclude_columns: list = None):
        self.exclude_columns = (
            exclude_columns
            if exclude_columns is not None
            else self.DEFAULT_EXCLUDE_COLUMNS
        )

    def create_hash_column(
        self,
        df: DataFrame,
        column_list: list = None,
        hash_column_name: str = "hash_column",
    ):
        df = df.copy()

        if column_list is None:
            column_list = [
                col for col in df.columns if col not in self.exclude_columns
            ]
        else:
            # Validate columns exist
            missing = [col for col in column_list if col not in df.columns]
            if missing:
                raise KeyError(f"Columns not found in DataFrame: {missing}")

        # Replace nulls with a consistent placeholder, then cast to string
        hash_input = df[column_list].fillna("NULL").astype(str)

        # Combine column values row-wise (order-sensitive) and hash
        df[hash_column_name] = hash_input.agg("|".join, axis=1).apply(
            lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()
        )
        return df

    def compare_hashes(
        self,
        current_df: DataFrame,
        new_df: DataFrame,
        business_key: str | list[str] | None = None,
        hash_column_name: str = "hash_column",
    ):
        for name, df in [("current_df", current_df), ("new_df", new_df)]:
            if hash_column_name not in df.columns:
                raise KeyError(f"'{hash_column_name}' not found in {name}")

        if business_key is not None:
            return self._compare_with_key(
                current_df, new_df, business_key, hash_column_name
            )
        else:
            return self._compare_without_key(
                current_df, new_df, hash_column_name
            )

    def _compare_without_key(
        self, current_df: DataFrame, new_df: DataFrame, hash_column_name
    ):
        current_subset = current_df[[hash_column_name]].drop_duplicates()

        merged = pd.merge(
            current_subset,
            new_df,
            on=hash_column_name,
            how="outer",
            indicator=True,
        )

        def determine_status(indicator):
            if indicator == "right_only":
                return "new"
            elif indicator == "left_only":
                return "removed_or_changed"  # No business key means records cannot be validated for changes
            else:
                return "unchanged"

        merged["status"] = merged["_merge"].apply(determine_status)
        merged = merged.drop(columns=["_merge"])

        return merged

    def _compare_with_key(
        self,
        current_df: DataFrame,
        new_df: DataFrame,
        business_key,
        hash_column_name,
    ):
        keys = (
            [business_key]
            if isinstance(business_key, str)
            else list(business_key)
        )

        missing_current = [k for k in keys if k not in current_df.columns]
        missing_new = [k for k in keys if k not in new_df.columns]
        if missing_current or missing_new:
            raise KeyError(
                f"Business key columns missing — current_df: {missing_current}, new_df: {missing_new}"
            )

        # Warn on duplicate keys, since they'd cause a fan-out join
        if current_df.duplicated(subset=keys).any():
            raise ValueError(
                f"Duplicate business key(s) found in current_df: {keys}"
            )
        if new_df.duplicated(subset=keys).any():
            raise ValueError(
                f"Duplicate business key(s) found in new_df: {keys}"
            )

        current_subset = current_df[keys + [hash_column_name]]

        merged = pd.merge(
            current_subset,
            new_df,
            on=keys,
            how="outer",
            suffixes=("_current", "_new"),
            indicator=True,
        )

        current_hash_col = f"{hash_column_name}_current"
        new_hash_col = f"{hash_column_name}_new"

        def determine_status(row):
            if row["_merge"] == "right_only":
                return "new"
            elif row["_merge"] == "left_only":
                return "deleted"
            else:
                return (
                    "unchanged"
                    if row[current_hash_col] == row[new_hash_col]
                    else "changed"
                )

        merged["status"] = merged.apply(determine_status, axis=1)
        merged = merged.drop(columns=["_merge"])

        return merged

    def compare_records(
        self,
        current_rel: duckdb.DuckDBPyRelation,
        new_rel: duckdb.DuckDBPyRelation,
        business_key: str | list[str],
        exclude_columns: list[str] = None,
    ) -> duckdb.DuckDBPyRelation:
        keys = (
            [business_key]
            if isinstance(business_key, str)
            else list(business_key)
        )
        exclude_columns = exclude_columns or self.exclude_columns

        # Validate keys exist on both sides
        for name, rel in [("current_rel", current_rel), ("new_rel", new_rel)]:
            missing_keys = [k for k in keys if k not in rel.columns]
            if missing_keys:
                raise KeyError(
                    f"Business key columns missing in {name}: {missing_keys}"
                )

        self._validate_no_duplicate_keys(current_rel, keys, "current_rel")
        self._validate_no_duplicate_keys(new_rel, keys, "new_rel")

        # Columns to compare: exclude keys and metadata columns
        compare_columns = [
            c
            for c in new_rel.columns
            if c not in keys and c not in exclude_columns
        ]

        if not compare_columns:
            raise ValueError(
                "No columns available to compare after excluding keys/metadata"
            )

        # Build the join condition across (possibly composite) business keys
        key_join = " AND ".join(f"c.{k} = n.{k}" for k in keys)

        # Build the diff condition: true if ANY compared column differs
        diff_condition = " OR ".join(
            f"c.{col} IS DISTINCT FROM n.{col}" for col in compare_columns
        )

        new_records = duckdb.sql(f"""
            SELECT *, 'new' AS status
            FROM new_rel n
            ANTI JOIN current_rel c ON {key_join}
        """)

        deleted_records = duckdb.sql(f"""
            SELECT *, 'deleted' AS status
            FROM current_rel c
            ANTI JOIN new_rel n ON {key_join}
        """)

        matched_records = duckdb.sql(f"""
            SELECT
                n.*,
                CASE WHEN {diff_condition} THEN 'changed' ELSE 'unchanged' END AS status
            FROM new_rel n
            INNER JOIN current_rel c ON {key_join}
        """)

        combined_table = duckdb.sql("""
            SELECT * FROM new_records
            UNION ALL
            SELECT * FROM deleted_records
            UNION ALL
            SELECT * FROM matched_records
        """)
        return combined_table

    def filter_unchanged_records(
        self, combined_table: duckdb.DuckDBPyRelation
    ):
        new_changed_deleted_records = duckdb.sql(
            "SELECT * FROM combined_table WHERE status != 'unchanged'"
        )

        return new_changed_deleted_records

    def _validate_no_duplicate_keys(
        self,
        rel: duckdb.DuckDBPyRelation,
        keys: list[str],
        name: str,
    ) -> None:
        key_cols = ", ".join(keys)
        dupes = duckdb.sql(f"""
            SELECT {key_cols}
            FROM rel
            GROUP BY {key_cols}
            HAVING COUNT(*) > 1
        """)
        if dupes.fetchone() is not None:
            raise ValueError(
                f"Duplicate business key(s) found in {name}: {keys}"
            )

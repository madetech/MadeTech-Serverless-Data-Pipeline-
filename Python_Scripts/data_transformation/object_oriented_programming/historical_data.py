from pandas import DataFrame
from typing import Union, List 
import pandas as pd 
import hashlib 

class HistoricalDataProcessor:
    # Default metadata columns to exclude from hashing
    DEFAULT_EXCLUDE_COLUMNS = [
        "ingestion_timestamp",
        "source",
        "version",
        "hash_column"
    ]
    def __init__(self, exclude_columns : list = None):
        self.exclude_columns = exclude_columns if exclude_columns is not None else self.DEFAULT_EXCLUDE_COLUMNS
        pass 

    def create_hash_column(self, df : DataFrame, column_list : list=None, hash_column_name : str="hash_column"):
        df = df.copy()

        if column_list is None:
            column_list = [col for col in df.columns if col not in self.exclude_columns]
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

        # Combine specified columns into a single string per row, then hash
        # df[hash_column_name] = df[column_list].astype(str).agg('|'.join, axis=1).apply(
        #     lambda x: hashlib.sha256(x.encode('utf-8')).hexdigest()
        # )
        return df 

    def compare_hashes(self, current_df : DataFrame, new_df : DataFrame, business_key : Union[str, List[str], None] = None, hash_column_name : str="hash_column"):
        for name, df in [("current_df", current_df), ("new_df", new_df)]:
            if hash_column_name not in df.columns:
                raise KeyError(f"'{hash_column_name}' not found in {name}")
            
     
        if business_key is not None:
            return self._compare_with_key(current_df, new_df, business_key, hash_column_name)
        else:
             return self._compare_without_key(current_df, new_df, hash_column_name)

            
    
    def _compare_without_key(self, current_df : DataFrame, new_df : DataFrame, hash_column_name):
        current_subset = current_df[[hash_column_name]].drop_duplicates()

        merged = pd.merge(
            current_subset,
            new_df,
            on=hash_column_name,
            how="outer",
            indicator=True
        )

        def determine_status(indicator):
            if indicator == "right_only":
                return "new"
            elif indicator == "left_only":
                return "removed_or_changed" # No business key means records cannot be validated for changes 
            else:
                return "unchanged"

        merged["status"] = merged["_merge"].apply(determine_status)
        merged = merged.drop(columns=["_merge"]) 

        return merged  

    def _compare_with_key(self, current_df : DataFrame, new_df : DataFrame, business_key, hash_column_name):
        keys = [business_key] if isinstance(business_key, str) else list(business_key)

        missing_current = [k for k in keys if k not in current_df.columns]
        missing_new = [k for k in keys if k not in new_df.columns]
        if missing_current or missing_new:
            raise KeyError(
                f"Business key columns missing — current_df: {missing_current}, new_df: {missing_new}"
            )

        # Warn on duplicate keys, since they'd cause a fan-out join
        if current_df.duplicated(subset=keys).any():
            raise ValueError(f"Duplicate business key(s) found in current_df: {keys}")
        if new_df.duplicated(subset=keys).any():
            raise ValueError(f"Duplicate business key(s) found in new_df: {keys}")

        current_subset = current_df[keys + [hash_column_name]]

        merged = pd.merge(
            current_subset,
            new_df,
            on=keys,
            how="outer",
            suffixes=("_current", "_new"),
            indicator=True
        )

        current_hash_col = f"{hash_column_name}_current"
        new_hash_col = f"{hash_column_name}_new"

        def determine_status(row):
            if row["_merge"] == "right_only":
                return "new"
            elif row["_merge"] == "left_only":
                return "deleted"
            else:
                return "unchanged" if row[current_hash_col] == row[new_hash_col] else "changed"

        merged["status"] = merged.apply(determine_status, axis=1)
        merged = merged.drop(columns=["_merge"])

        return merged 
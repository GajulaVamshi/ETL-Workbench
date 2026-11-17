import pandas as pd

def validate_dataframe(df):
    if not isinstance(df, pd.DataFrame): raise ValueError("Input is not a DataFrame.")
    if df.empty: raise ValueError("Dataset contains no rows.")
    if len(df.columns) == 0: raise ValueError("Dataset contains no columns.")
    if df.columns.duplicated().any(): raise ValueError("Duplicate column names found.")
    if all(df[c].isna().all() for c in df.columns): raise ValueError("All columns are empty.")

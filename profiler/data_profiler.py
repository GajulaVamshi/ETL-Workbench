import pandas as pd

def profile_dataframe(df):
    columns = pd.DataFrame({
        "column": [str(c) for c in df.columns],
        "dtype": [str(df[c].dtype) for c in df.columns],
        "non_null": [int(df[c].notna().sum()) for c in df.columns],
        "missing": [int(df[c].isna().sum()) for c in df.columns],
        "missing_%": [round(float(df[c].isna().mean()*100),2) for c in df.columns],
        "unique": [int(df[c].nunique(dropna=True)) for c in df.columns]
    })
    return {"columns": columns, "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum())}

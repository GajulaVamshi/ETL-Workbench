import ast, operator
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

_BIN = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv, ast.Pow:operator.pow, ast.Mod:operator.mod}
_UN = {ast.UAdd:operator.pos, ast.USub:operator.neg}

def _expression(expr, df):
    tree = ast.parse(expr, mode="eval")
    def visit(n):
        if isinstance(n, ast.Expression): return visit(n.body)
        if isinstance(n, ast.Name):
            if n.id not in df.columns: raise ValueError(f"Unknown column: {n.id}")
            return df[n.id]
        if isinstance(n, ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _BIN: return _BIN[type(n.op)](visit(n.left),visit(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _UN: return _UN[type(n.op)](visit(n.operand))
        raise ValueError("Expression supports column names, numbers and arithmetic operators only.")
    return visit(tree)

def apply_transformations(source, cfg):
    df = source.copy(deep=True)
    drop = cfg.get("drop_cols", [])
    unknown = set(drop)-set(df.columns)
    if unknown: raise ValueError(f"Unknown columns: {sorted(unknown)}")
    if drop: df = df.drop(columns=drop)
    strategy = cfg.get("missing_strategy","Leave unchanged")
    if strategy == "Drop rows": df = df.dropna()
    elif strategy == "Fill with zero": df = df.fillna(0)
    elif strategy == "Fill with custom value": df = df.fillna(cfg.get("custom_value",""))
    elif strategy in ("Fill with mean","Fill with median","Fill with mode"):
        for col in df.columns:
            if not df[col].isna().any(): continue
            if strategy == "Fill with mean" and pd.api.types.is_numeric_dtype(df[col]): df[col] = df[col].fillna(df[col].mean())
            elif strategy == "Fill with median" and pd.api.types.is_numeric_dtype(df[col]): df[col] = df[col].fillna(df[col].median())
            elif strategy == "Fill with mode":
                modes = df[col].mode()
                if not modes.empty: df[col] = df[col].fillna(modes.iloc[0])
    elif strategy != "Leave unchanged": raise ValueError("Unknown missing-value strategy.")
    if cfg.get("remove_duplicates"): df = df.drop_duplicates(keep=cfg.get("duplicate_keep","first"))
    name, expr = cfg.get("derived_name",""), cfg.get("derived_expression","")
    if name or expr:
        if not name or not expr: raise ValueError("Provide both derived column name and expression.")
        if name in df.columns: raise ValueError("Derived column already exists.")
        df[name] = _expression(expr, df)
    cols, method = cfg.get("scale_cols",[]), cfg.get("scaling","None")
    for col in cols:
        if col not in df: raise ValueError(f"Unknown scaling column: {col}")
        if not pd.api.types.is_numeric_dtype(df[col]): raise ValueError(f"Scaling requires numeric column: {col}")
        mask = df[col].notna()
        if method != "None" and mask.any():
            scaler = MinMaxScaler() if method.startswith("Min-Max") else StandardScaler()
            df.loc[mask,col] = scaler.fit_transform(df.loc[mask,[col]]).ravel()
    return df.reset_index(drop=True)

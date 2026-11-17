import re
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL

def _engine(cfg):
    url = URL.create("mysql+pymysql", username=cfg["username"], password=cfg["password"], host=cfg["host"], port=int(cfg.get("port",3306)), database=cfg["database"])
    return create_engine(url, pool_pre_ping=True)

def get_mysql_tables(host, port, database, username, password):
    cfg = locals(); engine = _engine(cfg)
    try: return inspect(engine).get_table_names()
    finally: engine.dispose()

def load_mysql_table(host, port, database, username, password, table):
    if not re.fullmatch(r"[A-Za-z0-9_]+", table): raise ValueError("Invalid table name.")
    cfg = locals(); engine = _engine(cfg)
    try: return pd.read_sql_table(table, engine)
    finally: engine.dispose()

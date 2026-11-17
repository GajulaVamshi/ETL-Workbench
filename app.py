import streamlit as st
from extractors.file_loader import load_uploaded_file
from extractors.database import get_mysql_tables, load_mysql_table
from validators.file_validator import validate_dataframe
from profiler.data_profiler import profile_dataframe
from transformations.engine import apply_transformations
from exporters.exporter import export_dataframe, write_mysql_table

st.set_page_config(page_title="ETL Workbench", page_icon="⚙️", layout="wide")
st.title("⚙️ ETL Workbench")
st.caption("Extract • Validate • Profile • Transform • Export")
for key, default in [("source_df", None), ("result_df", None), ("source_name", None)]:
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("Data source")
    mode = st.radio("Source", ["Upload file", "MySQL database"])
    if mode == "Upload file":
        f = st.file_uploader("Upload CSV, JSON, Excel, Parquet or PDF", type=["csv","json","xlsx","xls","parquet","pdf"])
        if st.button("Load file", disabled=f is None, type="primary"):
            try:
                df = load_uploaded_file(f); validate_dataframe(df)
                st.session_state.source_df, st.session_state.result_df = df.copy(), None
                st.session_state.source_name = f.name
                st.success("Loaded and validated.")
            except Exception as e: st.error(str(e))
    else:
        host = st.text_input("Host", "localhost"); port = st.number_input("Port", 1, 65535, 3306)
        database = st.text_input("Database"); username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        cfg = dict(host=host, port=int(port), database=database, username=username, password=password)
        if st.button("Connect / list tables"):
            try:
                st.session_state.mysql_cfg = cfg
                st.session_state.mysql_tables = get_mysql_tables(**cfg)
            except Exception as e: st.error(str(e))
        tables = st.session_state.get("mysql_tables", [])
        if tables:
            table = st.selectbox("Table", tables)
            if st.button("Load table", type="primary"):
                try:
                    df = load_mysql_table(**st.session_state.mysql_cfg, table=table); validate_dataframe(df)
                    st.session_state.source_df, st.session_state.result_df = df.copy(), None
                    st.session_state.source_name = "MySQL: " + table
                except Exception as e: st.error(str(e))

df = st.session_state.source_df
if df is None:
    st.info("Choose a source from the sidebar to begin."); st.stop()

st.subheader("Source: " + str(st.session_state.source_name))
a,b,c = st.columns(3); a.metric("Rows", len(df)); b.metric("Columns", len(df.columns)); c.metric("Missing cells", int(df.isna().sum().sum()))
t1,t2,t3 = st.tabs(["Preview & profile","Preprocessing","Export"])
with t1:
    st.dataframe(df.head(100), use_container_width=True)
    p = profile_dataframe(df)
    x,y = st.columns(2); x.metric("Duplicate rows", p["duplicate_rows"]); y.metric("Missing cells", p["missing_cells"])
    st.dataframe(p["columns"], use_container_width=True)
with t2:
    with st.form("transform"):
        drop = st.multiselect("Remove columns", list(df.columns))
        missing = st.selectbox("Missing values", ["Leave unchanged","Drop rows","Fill with zero","Fill with mean","Fill with median","Fill with mode","Fill with custom value"])
        custom = st.text_input("Custom value")
        dedupe = st.checkbox("Remove duplicate rows")
        keep = st.selectbox("Keep duplicate", ["first","last"])
        numeric = df.select_dtypes(include="number").columns.tolist()
        scale_cols = st.multiselect("Numeric columns to scale", numeric)
        scaling = st.selectbox("Scaling", ["None","Min-Max (0 to 1)","Standardize (z-score)"])
        st.markdown("**Optional derived column**")
        new_name = st.text_input("New column name")
        expr = st.text_input("Arithmetic expression, e.g. price * quantity")
        run = st.form_submit_button("Apply transformations", type="primary")
    if run:
        try:
            st.session_state.result_df = apply_transformations(df, dict(drop_cols=drop, missing_strategy=missing, custom_value=custom, remove_duplicates=dedupe, duplicate_keep=keep, scale_cols=scale_cols, scaling=scaling, derived_name=new_name.strip(), derived_expression=expr.strip()))
            st.success("Transformations applied.")
        except Exception as e: st.error(str(e))
    if st.session_state.result_df is not None:
        out = st.session_state.result_df
        st.write("Transformed preview"); st.dataframe(out.head(100), use_container_width=True)
        st.write(f"Before: {df.shape[0]} rows × {df.shape[1]} columns | After: {out.shape[0]} rows × {out.shape[1]} columns")
        st.dataframe(profile_dataframe(out)["columns"], use_container_width=True)
with t3:
    out = st.session_state.result_df if st.session_state.result_df is not None else df
    fmt = st.selectbox("Export format", ["CSV","JSON","Excel","Parquet","PDF report","MySQL table"])
    if fmt != "MySQL table":
        try:
            payload, name, mime = export_dataframe(out, fmt)
            st.download_button("Download " + name, payload, file_name=name, mime=mime, type="primary")
        except Exception as e: st.error(str(e))
    else:
        cfg = st.session_state.get("mysql_cfg")
        if not cfg: st.info("Connect to MySQL in the sidebar first.")
        else:
            table = st.text_input("Destination table")
            mode = st.selectbox("If table exists", ["fail","append","replace"])
            confirm = st.checkbox("Confirm overwrite") if mode == "replace" else True
            if st.button("Write to MySQL", disabled=not table or not confirm):
                try: write_mysql_table(out, cfg, table, mode); st.success("Write completed.")
                except Exception as e: st.error(str(e))

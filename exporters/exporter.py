import io, re
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

def export_dataframe(df, fmt):
    fmt = fmt.lower(); b = io.BytesIO()
    if fmt == "csv": return df.to_csv(index=False).encode(), "etl_export.csv", "text/csv"
    if fmt == "json": return df.to_json(orient="records",indent=2).encode(), "etl_export.json", "application/json"
    if fmt == "excel":
        with pd.ExcelWriter(b,engine="openpyxl") as w: df.to_excel(w,index=False,sheet_name="Data")
        return b.getvalue(),"etl_export.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if fmt == "parquet":
        df.to_parquet(b,index=False); return b.getvalue(),"etl_export.parquet","application/octet-stream"
    if fmt == "pdf report": return _pdf(df),"etl_report.pdf","application/pdf"
    raise ValueError("Unsupported export format.")

def _pdf(df):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape,A4
    from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    b=io.BytesIO(); doc=SimpleDocTemplate(b,pagesize=landscape(A4))
    data=[list(map(str,df.columns))]
    data += [["" if pd.isna(v) else str(v)[:80] for v in row] for row in df.head(500).itertuples(index=False,name=None)]
    t=Table(data,repeatRows=1); t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#263B53")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.3,colors.grey),("FONTSIZE",(0,0),(-1,-1),7)]))
    doc.build([Paragraph("ETL Workbench - Data Report",getSampleStyleSheet()["Title"]),Spacer(1,10),t]); return b.getvalue()

def write_mysql_table(df,cfg,table,mode):
    if not re.fullmatch(r"[A-Za-z0-9_]+",table): raise ValueError("Invalid destination table name.")
    url=URL.create("mysql+pymysql",username=cfg["username"],password=cfg["password"],host=cfg["host"],port=int(cfg.get("port",3306)),database=cfg["database"])
    engine=create_engine(url,pool_pre_ping=True)
    try: df.to_sql(table,engine,if_exists=mode,index=False,chunksize=1000)
    finally: engine.dispose()

# ETL Workbench

## Setup (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Tests
```powershell
pytest -q
```

## Features
- CSV, JSON, Excel, Parquet, text-based PDF table and MySQL input.
- Data validation and profiling.
- Remove columns, handle missing values, remove duplicates, arithmetic derived columns, numeric scaling.
- CSV, JSON, Excel, Parquet, PDF report and MySQL output.
- Each transformation run starts from the original loaded DataFrame.

## Limitations
Scanned PDFs/OCR are not supported. PDF export creates a table report (up to 500 rows), not a copy of the original PDF layout. JSON expects an object or array of objects. Add authentication, upload limits, audit logging and secrets management before public production deployment.

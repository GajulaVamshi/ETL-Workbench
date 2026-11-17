from pathlib import Path
import io, json
import pandas as pd

def load_uploaded_file(uploaded):
    ext = Path(uploaded.name).suffix.lower()
    raw = uploaded.getvalue()
    if not raw: raise ValueError("Uploaded file is empty.")
    stream = io.BytesIO(raw)
    try:
        if ext == ".csv": df = pd.read_csv(stream)
        elif ext == ".json":
            obj = json.loads(raw.decode("utf-8-sig"))
            if not isinstance(obj, (dict, list)): raise ValueError("JSON must be an object or array.")
            df = pd.json_normalize(obj)
        elif ext in (".xlsx", ".xls"): df = pd.read_excel(stream)
        elif ext == ".parquet": df = pd.read_parquet(stream)
        elif ext == ".pdf": df = _pdf_tables(stream)
        else: raise ValueError("Unsupported file type.")
    except Exception as e:
        if isinstance(e, ValueError): raise
        raise ValueError(f"Could not parse {uploaded.name}: {e}") from e
    if not isinstance(df, pd.DataFrame): raise ValueError("File did not contain tabular data.")
    return df

def _pdf_tables(stream):
    import pdfplumber
    frames = []
    with pdfplumber.open(stream) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables() or []:
                if table and len(table) > 1:
                    headers = [str(v) if v is not None else f"column_{i}" for i,v in enumerate(table[0])]
                    part = pd.DataFrame(table[1:], columns=headers)
                    part["source_page"] = page_no
                    frames.append(part)
    if not frames: raise ValueError("No text-based tables found. Scanned PDF OCR is not supported.")
    return pd.concat(frames, ignore_index=True)

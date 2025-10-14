# Medical ETL API - Postman Testing Guide

## 1. Start the API server

```powershell
# Activate your venv if you use one
. .\.venv\Scripts\Activate.ps1

# Install dependencies (once)
pip install -r requirements.txt

# Start the API
python .\medical_etl_system\start_api.py
```

By default the server listens on http://127.0.0.1:8000

## 2. Import the Postman collection
- Open Postman
- Import `medical_etl_system/Medical_ETL_API.postman_collection.json`

## 3. Run ETL via Postman
Use the "Run ETL" request in the collection. Example body:

```json
{
  "source": "C:\\Users\\kulka\\Downloads\\Dataset1_ClassicExcelMap",
  "dest": "D:\\ETL_Output\\Dataset1_ClassicExcelMap",
  "mapping": "C:\\Users\\kulka\\Downloads\\Dataset1_ClassicExcelMap\\demographics.xlsx",
  "dry_run": false
}
```

Notes:
- The destination path must be OUTSIDE this repo folder; the API will reject repo-internal paths.
- Mapping is optional; if omitted, the pipeline will parse filenames and use OCR as configured.

## 4. Responses
A successful response returns JSON with a summary:
```json
{
  "summary": {
    "total_files_found": 21,
    "total_files_processed": 21,
    "successful_extractions": 21,
    "failed_extractions": 0,
    "mapped_files": 20,
    "unmapped_files": 0,
    "duplicate_files": 0,
    "organized_files": 21,
    "errors": [],
    "warnings": []
  }
}
```

## 5. Troubleshooting
- If you see an error about the destination being inside the repo, change `dest` to a drive outside this project (e.g., `D:\ETL_Output\...`).
- For OCR, set `TESSERACT_CMD` if Tesseract is in a custom path.
- Logs are written under `medical_etl_system/logs/` with timestamps.

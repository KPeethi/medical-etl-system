# Medical ETL System (VS Code friendly)

Organizes medical documents into patient folders. Works with or without a mapping file.

- Target folder naming: `Lastname, Firstname MM-DD-YYYY`
- Copies only; source is never modified
- Duplicates go to `duplicates/`
- Unresolved files go to `unmapped/`
- Detailed JSON + text logs for SSIS automation

## 1) Install (Windows, PowerShell)

```powershell
# Create venv (optional)
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Install Python deps
pip install -r requirements.txt
```

Optional system deps for OCR:
- Tesseract OCR (Windows): `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Poppler (for PDF OCR via pdf2image): optional; only needed for OCRing PDFs

If Tesseract is installed in a non-default path, set an env var before running:
```powershell
$env:TESSERACT_CMD = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
```

## 2) Run

Mapping mode (Excel/CSV/JSON mapping file):
```powershell
python .\medical_etl_system\main.py "C:\path\to\Export" "C:\path\to\Output" --mapping "C:\path\to\demographics.xlsx"
```

No-mapping mode (auto-detect from filenames/OCR):
```powershell
python .\medical_etl_system\main.py "C:\path\to\Export" "C:\path\to\Output"
```

Dry-run (never writes files; logs only):
```powershell
python .\medical_etl_system\main.py "C:\path\to\Export" "C:\path\to\Output" --dry-run
```

## 3) Mapping file field synonyms
The system recognizes common synonyms automatically:
- ID: `id`, `patient_id`, `patientid`, `pno`, `id number`, `mrn`, `chart_id`, etc.
- Last name: `lastname`, `last_name`, `lname`, `surname`, `family_name`
- First name: `firstname`, `first_name`, `fname`, `givenname`, `forename`
- DOB: `dob`, `date_of_birth`, `birth_date`
- Filename: `filename`, `file_name`, `document_name`, `doc_name`

Excel is read with `openpyxl`. CSV/TSV are supported; JSON is supported.

## 4) What gets organized
- Recursively walks directories; nested ZIPs are extracted to a temp folder and processed
- Supported file types: PDF, JPG, JPEG, PNG, TIFF, TIF
- OCR is best-effort: if Tesseract is not available, pipeline continues without OCR
- Duplicates are detected per patient by identical size, except:
  - year-based variants (e.g., 2022 vs 2023) are NOT duplicates
  - series parts like `_1`, `_2`, `(1)` are NOT duplicates

## 5) Logs
- Text log: `medical_etl_system/logs/<dry_run|real_run>_YYYYMMDD_HHMMSS.log`
- JSON log: same name `.json` — includes:
  - session id, run mode, runner, start time
  - per-file entries with source/destination
  - summary counts and warnings/errors

## 6) Folder naming rules
- Folder: `Lastname, Firstname MM-DD-YYYY`
- Middle names/initials are ignored for folder naming
- If DOB is missing, folder is `Lastname, Firstname`
- If names are missing but ID exists: `Patient_<ID>`
- If no info can be derived: file goes to `unmapped/`

## 7) Notes
- Source is never modified; files are copied to destination
- For very large archives or images, you may want to pre-install Tesseract/Poppler for better results

## 8) Batch helper (optional)
You can run the helper script at `medical_etl_system\tools\run_pipeline.bat` and edit it to fit your paths.

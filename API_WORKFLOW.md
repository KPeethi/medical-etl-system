# API Workflow Diagram

## Medical ETL System API - Request/Response Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (Postman, curl, etc)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (api.py)                      │
│                     http://localhost:8000                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  GET /health                                               │ │
│  │  └─> Health Check                                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  POST /api/v1/dataset/inspect                             │ │
│  │  Input: {"file_path": "/path/to/dataset.zip"}             │ │
│  │  ├─> FileExtractor.inspect_archive()                      │ │
│  │  │   ├─> Read ZIP metadata (no extraction)                │ │
│  │  │   ├─> List all files inside                            │ │
│  │  │   └─> Calculate sizes and structure                    │ │
│  │  └─> Output: {files[], total_files, size, structure}      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  POST /api/v1/dataset/upload-and-inspect                  │ │
│  │  Input: multipart/form-data (file upload)                 │ │
│  │  ├─> Save to temp file                                    │ │
│  │  ├─> Inspect using FileExtractor                          │ │
│  │  └─> Clean up temp file                                   │ │
│  │  └─> Output: {files[], total_files, size, structure}      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  POST /api/v1/etl/run                                      │ │
│  │  Input: {                                                  │ │
│  │    source_path: "/source",                                │ │
│  │    destination_path: "/dest",                             │ │
│  │    mapping_file: "/mapping.xlsx",  ← OPTIONAL             │ │
│  │    dry_run: true/false                                    │ │
│  │  }                                                         │ │
│  │  ├─> MedicalETLProcessor.__init__()                       │ │
│  │  │   ├─> FileExtractor                                    │ │
│  │  │   ├─> OCRProcessor                                     │ │
│  │  │   ├─> PatientParser                                    │ │
│  │  │   ├─> MappingProcessor (if mapping file provided)      │ │
│  │  │   ├─> DuplicateDetector                                │ │
│  │  │   └─> FileOrganizer                                    │ │
│  │  ├─> processor.run()                                      │ │
│  │  │   ├─> Validate inputs                                  │ │
│  │  │   ├─> Load mapping (optional)                          │ │
│  │  │   ├─> Extract & discover files                         │ │
│  │  │   ├─> Process each file                                │ │
│  │  │   │   ├─> Try mapping lookup (if available)            │ │
│  │  │   │   ├─> OCR extraction (fallback)                    │ │
│  │  │   │   ├─> Parse patient data                           │ │
│  │  │   │   └─> Detect duplicates                            │ │
│  │  │   ├─> Organize files                                   │ │
│  │  │   │   └─> "Lastname, Firstname DOB" folders            │ │
│  │  │   └─> Generate statistics                              │ │
│  │  └─> Output: {status, session_id, results{...}}           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────┬─┘
                                                                 │
                                                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   File System / Storage                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Source Files (Input)                                            │
│  ├─> Medical records                                             │
│  ├─> ZIP archives                                                │
│  └─> Mapping file (optional)                                     │
│                                                                   │
│  Destination (Output)                                            │
│  ├─> Smith, John 01-15-1980/                                     │
│  │   ├─> 2022_chart.pdf                                          │
│  │   ├─> 2023_xray.jpg                                           │
│  │   └─> lab_results.pdf                                         │
│  ├─> Johnson, Mary 03-22-1975/                                   │
│  │   └─> ...                                                     │
│  ├─> duplicates/                                                 │
│  └─> unmapped/                                                   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Key Features Illustrated

### 1. Dataset Inspection
- **No extraction required** - Reads ZIP metadata only
- **Fast and efficient** - Returns immediately
- **Complete information** - Files, sizes, structure

### 2. Optional Mapping File
- **Two modes:**
  1. **With mapping:** Direct patient lookup
  2. **Without mapping:** OCR + filename parsing
- **No validation errors** for missing optional field
- **Flexible workflow** adapts to available data

### 3. Output Organization
```
destination_path/
├── Smith, John 01-15-1980/
│   ├── 2022_chart.pdf
│   ├── 2023_xray.jpg
│   └── lab_results.pdf
├── Johnson, Mary 03-22-1975/
│   ├── record1.pdf
│   └── xray1.jpg
├── duplicates/
│   └── Smith, John 01-15-1980/
│       └── duplicate_chart.pdf
└── unmapped/
    └── unknown_file.pdf
```

Format: **"Lastname, Firstname DOB"**

### 4. No Hardcoded Values
All paths provided via API:
- ✅ source_path - Request parameter
- ✅ destination_path - Request parameter
- ✅ mapping_file - Request parameter (optional)
- ✅ file_path (inspect) - Request parameter

## Example API Calls

### 1. Inspect Dataset
```bash
curl -X POST http://localhost:8000/api/v1/dataset/inspect \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/medical_records.zip"}'
```

Response:
```json
{
  "status": "success",
  "file_path": "/data/medical_records.zip",
  "total_files": 50,
  "total_size_mb": 25.5,
  "files": [...]
}
```

### 2. Run ETL (No Mapping)
```bash
curl -X POST http://localhost:8000/api/v1/etl/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/data/records",
    "destination_path": "/data/organized"
  }'
```

### 3. Run ETL (With Mapping)
```bash
curl -X POST http://localhost:8000/api/v1/etl/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/data/records",
    "destination_path": "/data/organized",
    "mapping_file": "/data/mapping.xlsx"
  }'
```

## Error Handling

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "source_path"],
      "msg": "Path cannot be empty",
      "type": "value_error"
    }
  ]
}
```

### 404 Not Found
```json
{
  "detail": "Source path does not exist: /invalid/path"
}
```

### 500 Internal Error
```json
{
  "detail": "Error running ETL process: <error details>"
}
```

## Interactive Documentation

Once API is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Try out endpoints directly in the browser!

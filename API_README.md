# Medical ETL System API

REST API for the Medical ETL System that provides endpoints for processing medical records and inspecting datasets.

## Features

- **ETL Processing**: Run the complete ETL pipeline via API
- **Dataset Inspection**: Inspect ZIP file contents without extraction
- **File Upload**: Upload and inspect ZIP files directly
- **Optional Mapping**: Mapping files are optional, system falls back to OCR/filename parsing
- **Flexible Output**: Organizes files as "Lastname, Firstname DOB"

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- **GET** `/health` - Check API health status
- **GET** `/` - API information

### ETL Operations
- **POST** `/api/v1/etl/run` - Run the ETL process

### Dataset Inspection
- **POST** `/api/v1/dataset/inspect` - Inspect a ZIP file by path
- **POST** `/api/v1/dataset/upload-and-inspect` - Upload and inspect a ZIP file

## Usage Examples

### Using curl

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Inspect ZIP File
```bash
curl -X POST http://localhost:8000/api/v1/dataset/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/dataset.zip"
  }'
```

#### Run ETL Process (without mapping file)
```bash
curl -X POST http://localhost:8000/api/v1/etl/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/path/to/source",
    "destination_path": "/path/to/destination",
    "dry_run": false
  }'
```

#### Run ETL Process (with mapping file)
```bash
curl -X POST http://localhost:8000/api/v1/etl/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/path/to/source",
    "destination_path": "/path/to/destination",
    "mapping_file": "/path/to/mapping.xlsx",
    "dry_run": false
  }'
```

#### Upload and Inspect ZIP File
```bash
curl -X POST http://localhost:8000/api/v1/dataset/upload-and-inspect \
  -F "file=@/path/to/dataset.zip"
```

### Using Postman

1. **Import the API**:
   - Open Postman
   - Create a new request
   - Set the base URL to `http://localhost:8000`

2. **Inspect Dataset**:
   - Method: POST
   - URL: `http://localhost:8000/api/v1/dataset/inspect`
   - Body (JSON):
     ```json
     {
       "file_path": "/path/to/dataset.zip"
     }
     ```

3. **Run ETL Process**:
   - Method: POST
   - URL: `http://localhost:8000/api/v1/etl/run`
   - Body (JSON):
     ```json
     {
       "source_path": "/path/to/source",
       "destination_path": "/path/to/destination",
       "mapping_file": "/path/to/mapping.xlsx",
       "dry_run": false
     }
     ```
   - Note: `mapping_file` is optional and can be omitted

4. **Upload and Inspect**:
   - Method: POST
   - URL: `http://localhost:8000/api/v1/dataset/upload-and-inspect`
   - Body: form-data
   - Key: `file` (type: File)
   - Value: Select your ZIP file

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Response Models

### ETL Response
```json
{
  "status": "success",
  "session_id": "abc123",
  "message": "ETL process completed successfully",
  "results": {
    "total_files_found": 100,
    "total_files_processed": 95,
    "successful_extractions": 90,
    "failed_extractions": 5,
    "mapped_files": 80,
    "unmapped_files": 10,
    "duplicate_files": 5,
    "organized_files": 85
  }
}
```

### Inspect Response
```json
{
  "status": "success",
  "file_path": "/path/to/dataset.zip",
  "total_files": 50,
  "total_size_bytes": 52428800,
  "total_size_mb": 50.0,
  "files": [
    {
      "name": "patient_record.pdf",
      "size": 1048576,
      "path": "records/patient_record.pdf",
      "is_archive": false,
      "is_image": false,
      "is_pdf": true
    }
  ],
  "archive_structure": {
    "directories": {
      "records": {
        "files": [
          {
            "name": "patient_record.pdf",
            "size": 1048576,
            "type": ".pdf"
          }
        ]
      }
    }
  }
}
```

## Error Handling

The API uses standard HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found (file/path doesn't exist)
- **422**: Validation Error (missing required fields)
- **500**: Internal Server Error

Example error response:
```json
{
  "detail": "Source path does not exist: /invalid/path"
}
```

## Key Features

### No Hardcoded Values
All paths are provided via API requests - no hardcoded values in the code.

### Optional Mapping File
The mapping file is optional. If not provided, the system will:
1. Parse filenames for patient information
2. Use OCR to extract text from images/PDFs
3. Combine results for best accuracy

### Output Structure
Files are organized as: `Lastname, Firstname DOB`

Example:
```
Destination/
├── Smith, John 01-15-1980/
│   ├── 2022_chart.pdf
│   ├── 2023_xray.jpg
│   └── lab_results.pdf
├── duplicates/
│   └── [duplicate files]
└── unmapped/
    └── [unidentified files]
```

## Configuration

The API uses the same configuration as the main ETL system. See `config/config.py` for settings.

## Troubleshooting

### Port Already in Use
If port 8000 is already in use, specify a different port:
```bash
uvicorn api:app --port 8001
```

### CORS Issues
For development with frontend applications, you may need to enable CORS in `api.py`.

### File Permissions
Ensure the API process has read permissions for source files and write permissions for destination directories.

## Production Deployment

For production deployment, consider:

1. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)
2. Set up proper authentication/authorization
3. Use HTTPS
4. Configure logging
5. Set up monitoring and health checks
6. Use environment variables for configuration

Example production command:
```bash
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

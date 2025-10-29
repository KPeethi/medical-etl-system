# Medical ETL REST API for Postman

## Overview
This API allows you to process medical files from source to destination using HTTP requests. The source files are **never modified** - only copied to the destination with proper organization.

## Base URL
```
http://localhost:5000
```

## Authentication

**⚠️ SECURITY WARNING**: This API should only be run on your local machine for development/testing.

### Optional API Key Authentication

You can enable API key authentication by setting an environment variable:

```bash
# Windows
set API_KEY=your-secret-key-here

# Linux/Mac
export API_KEY=your-secret-key-here
```

When enabled, include the API key in all requests:

```
Headers:
X-API-Key: your-secret-key-here
```

If `API_KEY` is not set, the API runs without authentication (local development only)

---

## POST /api/process

Process files from source to destination with optional mapping configuration.

### Request Body

```json
{
  "source": "/path/to/medical_dataset.zip",
  "dest": "/path/to/organized_output",
  "dry_run": false,
  "mapping": "/path/to/demographics_index.json"
}
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| source | string | Yes | Path to source folder or ZIP file. Source is **never modified**. |
| dest | string | Yes | Path to destination folder where organized files will be copied. |
| dry_run | boolean | No | If `true`, only simulate processing without copying files. Default: `true` |
| mapping | string | No | Path to mapping file (JSON, Excel, or CSV) for custom file organization. |

### Mapping File Formats

#### JSON Format
```json
{
  "module_mappings": {
    "labs": "Laboratory",
    "imaging": "Radiology",
    "notes": "Clinical_Notes"
  }
}
```

#### Excel/CSV Format
Must have two columns: `pattern` and `module`

| pattern | module |
|---------|--------|
| labs | Laboratory |
| imaging | Radiology |
| notes | Clinical_Notes |

### Response (Success - 200 OK)

```json
{
  "status": "success",
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_key": "md5hash1234567890",
  "mode": "REAL_RUN",
  "source": "/path/to/medical_dataset.zip",
  "destination": "/path/to/organized_output",
  "stats": {
    "processed": 150,
    "copied": 142,
    "skipped": 3,
    "unmapped": 4,
    "errors": 1
  },
  "log_file": "./logs/etl_run_a1b2c3d4.csv",
  "message": "Processing completed successfully"
}
```

### Response (Error - 400 Bad Request)

```json
{
  "error": "Source path does not exist: C:/path/to/source"
}
```

### Response (Error - 500 Internal Server Error)

```json
{
  "status": "error",
  "error": "Failed to extract ZIP: corrupted file",
  "message": "Processing failed"
}
```

---

## GET /health

Health check endpoint to verify the API is running.

### Response (200 OK)

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Additional API Endpoints

### GET /api/stats
Get overall processing statistics.

### GET /api/unmapped
Get list of unmapped files.

### GET /api/bad-dob
Get files with invalid date of birth.

### GET /api/duplicates
Get duplicate files detected.

### GET /api/audit
Get audit trail of all file operations.

---

## Example Usage in Postman

### 1. Dry Run Test (No Changes)

**Request:**
```
POST http://localhost:5000/api/process
Content-Type: application/json

{
  "source": "/path/to/sample_data.zip",
  "dest": "/path/to/output",
  "dry_run": true
}
```

This will **simulate** processing without actually copying files.

### 2. Real Run with Mapping

**Request:**
```
POST http://localhost:5000/api/process
Content-Type: application/json

{
  "source": "/path/to/medical_dataset.zip",
  "dest": "/path/to/organized_output",
  "dry_run": false,
  "mapping": "/path/to/demographics_index.json"
}
```

This will:
1. Extract the ZIP file (if source is ZIP)
2. Read the mapping file
3. Process all files according to the mapping
4. Copy organized files to destination
5. **Leave source untouched**

### 3. Simple Folder Processing

**Request:**
```
POST http://localhost:5000/api/process
Content-Type: application/json

{
  "source": "/path/to/medical_files",
  "dest": "/path/to/organized",
  "dry_run": false
}
```

Uses default configuration to organize files.

---

## Important Notes

1. **Source is Read-Only**: The source files and folders are **never modified or deleted**.
2. **ZIP Extraction**: ZIP files are safely extracted with security protections:
   - Path traversal attacks blocked (e.g., `../../etc/passwd`)
   - Symlink-based escapes prevented  
   - Each file validated before AND after extraction
   - Malicious archives rejected with clear error messages
3. **Logging**: All operations are logged to CSV files and database for audit trail.
4. **Dry Run First**: Always test with `"dry_run": true` first to see what would happen.
5. **Path Format**: Use forward slashes `/` or escaped backslashes `\\` in JSON.
6. **Local Use Only**: This API defaults to localhost-only (127.0.0.1) binding for security. Set `FLASK_HOST=0.0.0.0` to expose on network (not recommended).
7. **Authentication**: Optional API key authentication can be enabled via `API_KEY` environment variable.
8. **Security**: Production-grade path traversal protection, symlink attack prevention, and safe file extraction.

---

## Troubleshooting

**Error: "Source path does not exist"**
- Check the path is correct
- Use absolute paths
- Ensure proper path separators (`/` or `\\\\` in JSON)

**Error: "No module named pandas"**
- Restart the Flask server to pick up dependencies

**Error: "Failed to extract ZIP"**
- Ensure the ZIP file is not corrupted
- Check you have read permissions

**Error: "Failed to parse mapping file"**
- Verify JSON syntax is valid
- For Excel/CSV, ensure columns are named `pattern` and `module`
- Check file encoding is UTF-8

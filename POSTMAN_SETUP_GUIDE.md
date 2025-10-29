# 🏥 Medical File Processing - Postman Ready Setup

## ✅ Complete Workflow Implementation
**Mapping → Folder → Filename → OCR → Unmapped**

## 🚀 Quick Start

### 1. Start the API Server
```bash
python postman_api_server.py
```

### 2. Import Postman Collection
1. Open Postman
2. Click "Import" 
3. Select `Medical_File_Processing_API.postman_collection.json`
4. Collection will be imported with all endpoints ready

### 3. Set Your Variables
1. In Postman, go to the collection variables tab
2. Set these variables with your actual paths:
   - `source_path`: Your source files or ZIP location
   - `dest_path`: Where you want organized output
   - `roster_path`: (Optional) Your roster CSV file
   - `mapping_path`: (Optional) Your mapping CSV file

### 4. Test the Health Check
```
GET http://localhost:5001/health
```

## 📋 Available Endpoints

### Health Check
- **GET** `/health`
- Verify API server is running

### Process Files
- **POST** `/api/process`
- Main processing endpoint with complete workflow

### Get Status
- **GET** `/api/status/<run_id>`
- Check processing status

### Download Logs
- **GET** `/api/logs/<run_id>`
- Download detailed processing logs

## 🔄 Workflow Order (Implemented)

1. **MAPPING** - Check roster/mapping files first
2. **FOLDER** - Extract patient info from folder structure  
3. **FILENAME** - Parse filename patterns
4. **OCR** - Extract from PDF/image content (if available)
5. **UNMAPPED** - Files that couldn't be processed

## 📝 Example Postman Requests

### Basic Processing (Dry Run)
```json
POST /api/process
{
    "source": "{{source_path}}",
    "dest": "{{dest_path}}",
    "dry_run": true
}
```

### With Roster File
```json
POST /api/process
{
    "source": "{{source_path}}", 
    "dest": "{{dest_path}}",
    "roster": "{{roster_path}}",
    "dry_run": true
}
```

### With Mapping File
```json
POST /api/process
{
    "source": "{{source_path}}",
    "dest": "{{dest_path}}", 
    "mapping": "{{mapping_path}}",
    "dry_run": true
}
```

### Complete Workflow
```json
POST /api/process
{
    "source": "{{source_path}}",
    "dest": "{{dest_path}}",
    "roster": "{{roster_path}}",
    "mapping": "{{mapping_path}}", 
    "dry_run": true
}
```

### Live Run (Actually Move Files)
```json
POST /api/process  
{
    "source": "{{source_path}}",
    "dest": "{{dest_path}}",
    "dry_run": false
}
```

## 📊 Response Format

```json
{
    "status": "success",
    "run_id": "generated_id", 
    "mode": "DRY_RUN",
    "workflow": "Mapping → Folder → Filename → OCR → Unmapped",
    "source": "{{source_path}}",
    "destination": "{{dest_path}}",
    "stats": {
        "mapping_matched": 0,
        "folder_matched": 0, 
        "filename_matched": 0,
        "ocr_matched": 0,
        "unmapped": 0,
        "total_processed": 0
    },
    "message": "Processing completed successfully",
    "timestamp": "current_timestamp"
}
```

## 🔧 Files Created

1. **`postman_api_server.py`** - Production-ready Flask API server
2. **`working_universal_processor.py`** - Updated with complete workflow  
3. **`Medical_File_Processing_API.postman_collection.json`** - Complete Postman collection
4. **`POSTMAN_SETUP_GUIDE.md`** - This setup guide

## ✅ Features Implemented

- ✅ Complete workflow: Mapping → Folder → Filename → OCR → Unmapped
- ✅ Optional roster and mapping file support
- ✅ Dry run and live processing modes
- ✅ Detailed statistics tracking by detection method
- ✅ API logging and status checking
- ✅ Error handling and validation
- ✅ Postman collection with tests
- ✅ Health check endpoint

## 🎯 Ready for Production

The system is now fully organized and ready for Postman testing with the exact workflow you requested!
# Medical File Processing System - Production Ready

## Core System

### `working_universal_processor.py`
- **Workflow:** Mapping → Folder → Filename → OCR → Unmapped
- **Parameters:** `--source`, `--dest`, `--roster`, `--mapping`, `--live`
- **Generic:** No hardcoded paths, works with any medical dataset

### `postman_api_server.py` 
- **Port:** 5001
- **Endpoints:** `/health`, `/api/process`, `/api/status/<id>`, `/api/logs/<id>`
- **Generic:** Uses variables for all paths

### `Medical_File_Processing_API.postman_collection.json`
- **Variables:** `{{source_path}}`, `{{dest_path}}`, `{{roster_path}}`, `{{mapping_path}}`
- **Generic:** No hardcoded examples, all parameterized

## Usage

1. **Start API:** `python postman_api_server.py`
2. **Import Collection:** Load the JSON file into Postman
3. **Set Variables:** Configure your actual paths in Postman variables
4. **Execute:** Run any endpoint with your data

## Workflow Verification

✅ **Mapping** - Checks roster/mapping files first  
✅ **Folder** - Extracts from folder structure  
✅ **Filename** - Parses filename patterns  
✅ **OCR** - Processes PDF/image content  
✅ **Unmapped** - Handles unprocessable files  

## Clean Features

- No sample data included
- No hardcoded paths
- No demo content
- Fully parameterized
- Production ready
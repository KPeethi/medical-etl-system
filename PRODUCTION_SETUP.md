# Medical ETL System - Production Setup Guide

## Overview
The Medical ETL System is now completely free of hardcoded values and ready for production deployment. All paths, configurations, and settings can be customized through environment variables and command-line parameters.

## Quick Start

### 1. Environment Setup

Copy the example environment file and customize it:
```bash
cp config/environment_example.env config/.env
# Edit config/.env with your specific paths and settings
```

### 2. Tesseract OCR Setup

The system automatically detects Tesseract installation. If auto-detection fails:
```bash
# Set environment variable
export TESSERACT_CMD="/path/to/tesseract"

# Or in .env file
TESSERACT_CMD="/usr/bin/tesseract"
```

### 3. Basic Usage

Process a dataset with custom paths:
```bash
python main.py --source "/path/to/dataset" --destination "/path/to/output"
```

Process with Excel mapping:
```bash
python main.py --source "/path/to/dataset" --destination "/path/to/output" --mapping "/path/to/mapping.xlsx"
```

### 4. Dataset1_ClassicExcelMap Processing

For the specific Dataset1_ClassicExcelMap:
```bash
python process_dataset1.py --dataset-path "/path/to/Dataset1_ClassicExcelMap" --output-path "/path/to/output"
```

Run in demo mode (no actual dataset required):
```bash
python process_dataset1.py --demo
```

## Configuration Options

### Environment Variables (.env file)

| Variable | Default | Description |
|----------|---------|-------------|
| `TESSERACT_CMD` | Auto-detected | Path to Tesseract executable |
| `DATA_DIR` | data | Data directory (relative to project) |
| `LOGS_DIR` | logs | Logs directory (relative to project) |
| `TEMP_DIR` | temp | Temporary files directory |
| `LOG_LEVEL` | INFO | Logging level |
| `MAX_LOG_SIZE_MB` | 100 | Max log file size before rotation |
| `WORKER_THREADS` | 4 | Number of processing threads |
| `MAX_FILE_SIZE_MB` | 100 | Maximum file size for processing |
| `OCR_LANGUAGES` | eng | OCR languages (comma-separated) |
| `DUPLICATE_SIZE_THRESHOLD` | 100 | File size difference for duplicates |
| `DUPLICATE_FOLDER_NAME` | duplicates | Folder name for duplicate files |
| `UNMAPPED_FOLDER_NAME` | unmapped | Folder name for unmapped files |

### Command Line Arguments

#### main.py
- `--source` / `-s`: Source directory path
- `--destination` / `-d`: Destination directory path  
- `--mapping` / `-m`: Excel mapping file path
- `--dry-run`: Preview mode (no actual file operations)
- `--verbose` / `-v`: Verbose logging

#### process_dataset1.py
- `--dataset-path`: Path to Dataset1_ClassicExcelMap
- `--output-path`: Output directory for processed files
- `--mapping-file`: Excel mapping file
- `--demo`: Run in demo mode

## Directory Structure

The system creates the following structure (configurable):
```
project_root/
├── config/
│   ├── .env                    # Your environment configuration
│   └── environment_example.env # Template with all options
├── data/                       # Data files (configurable)
├── logs/                       # Log files (configurable)
├── temp/                       # Temporary files (configurable)
└── processed_datasets/         # Output location example
```

## Auto-Detection Features

### Tesseract OCR
The system automatically searches for Tesseract in:
1. Environment variable `TESSERACT_CMD`
2. System PATH
3. Common installation paths:
   - Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`
   - Linux: `/usr/bin/tesseract`
   - macOS: `/opt/homebrew/bin/tesseract`

### Dataset Paths
When using `process_dataset1.py` without `--dataset-path`, it searches:
1. Current directory + Dataset1_ClassicExcelMap
2. User Downloads + Dataset1_ClassicExcelMap
3. Relative path Dataset1_ClassicExcelMap

## Deployment Examples

### Windows Production
```cmd
# Set environment
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
set DATA_DIR=D:\Medical_ETL\data
set LOGS_DIR=D:\Medical_ETL\logs

# Run processing
python main.py --source "D:\Medical_Records\Dataset1" --destination "D:\Processed_Records"
```

### Linux Production
```bash
# Set environment
export TESSERACT_CMD=/usr/bin/tesseract
export DATA_DIR=/opt/medical_etl/data
export LOGS_DIR=/var/log/medical_etl

# Run processing
python main.py --source "/data/medical_records" --destination "/processed/records"
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

# Set environment
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV DATA_DIR=/app/data
ENV LOGS_DIR=/app/logs

# Copy application
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Run application
CMD ["python", "main.py"]
```

## Migration from Hardcoded Version

If you have an existing installation with hardcoded paths:

1. **Backup your data** and logs
2. **Update to this version**
3. **Create .env file** with your specific paths
4. **Test with --dry-run** first
5. **Run normally** once verified

## Support

For deployment assistance or configuration questions:
- Check the logs in the configured `LOGS_DIR`
- Run with `--verbose` for detailed output
- Use `--demo` mode for testing configuration
- Verify Tesseract installation with auto-detection

## Security Notes

- Store sensitive paths in `.env` file (not in version control)
- Set appropriate file permissions on data directories
- Use dedicated service accounts in production
- Regularly rotate log files based on `MAX_LOG_SIZE_MB` setting
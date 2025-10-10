# Medical ETL System - Directory Structure

## Project Structure

```
medical_etl_system/
├── 📁 config/                    # Configuration management
│   ├── 📄 config.py             # Main configuration
│   ├── 📄 __init__.py           
│   └── 📄 .env                  # Environment variables (create from example)
├── 📁 modules/                   # Core processing modules
│   ├── 📄 __init__.py
│   ├── 📄 duplicate_detector.py # Duplicate file detection
│   ├── 📄 etl_logger.py         # Comprehensive logging
│   ├── 📄 excel_manager.py      # Excel template and export
│   ├── 📄 file_extractor.py     # Archive extraction
│   ├── 📄 file_organizer.py     # File organization
│   ├── 📄 mapping_processor.py  # Excel mapping processing
│   ├── 📄 ocr_processor.py      # OCR text extraction
│   └── 📄 patient_parser.py     # Patient info extraction
├── 📁 data/                      # Data files (configurable location)
├── 📁 logs/                      # Log files (configurable location)  
├── 📁 temp/                      # Temporary files (configurable location)
├── 📄 main.py                   # Main ETL processor
├── 📄 requirements.txt          # Python dependencies
└── 📄 setup.py                  # Package installation
```

## Usage Patterns

### Basic Processing
```bash
# Process medical files from source to organized destination
python main.py --source "/path/to/medical/files" --destination "/path/to/organized/output"
```

### With Excel Mapping
```bash
# Use Excel mapping file to identify patients
python main.py --source "/path/to/medical/files" --destination "/path/to/organized/output" --mapping "/path/to/patient_list.xlsx"
```

### Preview Mode
```bash
# See what would happen without making changes
python main.py --source "/path/to/medical/files" --destination "/path/to/organized/output" --dry-run
```

## Output Structure

After processing, your destination directory will have:

```
destination/
├── 📁 Smith, John 01-15-1990/
│   ├── 📄 2022_chest_xray.pdf
│   ├── 📄 2023_blood_work.pdf
│   └── 📄 2024_consultation.pdf
├── 📁 Johnson, Mary 03-22-1985/
│   ├── 📄 2023_mammogram.pdf
│   └── 📄 2024_followup.pdf
├── 📁 duplicates/
│   └── 📁 Smith, John 01-15-1990/
│       └── 📄 duplicate_xray.pdf
└── 📁 unmapped/
    └── 📄 unidentified_file.pdf
```

## Log Files

The system creates comprehensive logs in the logs directory:

```
logs/
├── 📄 medical_etl_20241010_1430.log    # Main processing log
├── 📄 session_summary_20241010.json    # Session summary
└── 📄 patient_summary_20241010.xlsx    # Excel report
```

## Configuration

All paths are configurable via environment variables in the `.env` file:

```env
# Directory locations
DATA_DIR=data
LOGS_DIR=logs  
TEMP_DIR=temp

# Processing settings
WORKER_THREADS=4
MAX_FILE_SIZE_MB=100

# OCR configuration
TESSERACT_CMD=/usr/bin/tesseract  # Auto-detected if not set
OCR_LANGUAGES=eng
```

## Key Features

- ✅ **Zero hardcoded paths** - Everything configurable
- ✅ **Cross-platform** - Works on Windows, Linux, macOS  
- ✅ **Auto-detection** - Finds Tesseract automatically
- ✅ **Archive support** - ZIP, RAR, 7Z extraction
- ✅ **OCR processing** - Text extraction from PDFs/images
- ✅ **Excel integration** - Mapping templates and reports
- ✅ **Comprehensive logging** - Full audit trails
- ✅ **Duplicate detection** - Smart file deduplication
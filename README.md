# Medical ETL System

## Overview
This Medical ETL (Extract, Transform, Load) system processes medical records with two main workflows:
1. **Mapping Mode**: Uses Excel/CSV mapping files to identify patients
2. **No-Mapping Mode**: Extracts patient information from filenames and OCR

## 🎉 Production Ready Features
- ✅ **Zero hardcoded paths** - Fully configurable via environment variables
- ✅ **Auto-detection** - Automatically finds Tesseract and common paths
- ✅ **Command-line interface** - Flexible path specification
- ✅ **REST API** - FastAPI-based web API for remote operations
- ✅ **Dataset inspection** - Inspect ZIP files without extraction
- ✅ **Environment configuration** - .env file support for all settings
- ✅ **Cross-platform compatibility** - Windows, Linux, macOS support
- ✅ **Docker ready** - Container deployment support

**Quick Start:**
```bash
# Copy and configure environment
cp config/environment_example.env config/.env

# Process any dataset (CLI)
python main.py --source "/path/to/dataset" --destination "/path/to/output"

# Process with mapping (CLI)
python main.py --source "/path/to/dataset" --destination "/path/to/output" --mapping "/path/to/mapping.xlsx"

# Or use the REST API
python api.py
# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

**Output Structure:**
```
Destination/
├── Lastname, Firstname DOB/
│   ├── 2022_chart1.pdf
│   ├── 2023_chart2.pdf
│   ├── 2024_xray.jpg
│   └── lab_results.pdf
├── duplicates/
│   └── [duplicate files organized by patient]
└── unmapped/
    └── [files that couldn't be identified]
```

## System Requirements

### Python Environment
- Python 3.8 or higher
- Windows 10/11 (primary target platform)
- At least 4GB RAM (8GB recommended for large datasets)
- 10GB free disk space for temporary files

### External Dependencies

#### Tesseract OCR (Required)
1. **Download Tesseract for Windows:**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (tesseract-ocr-w64-setup-v5.3.0.exe or newer)

2. **Install Tesseract:**
   ```
   - Run the installer as Administrator
   - Install to default location: C:\Program Files\Tesseract-OCR\
   - Add additional language packs if needed (English is included by default)
   ```

3. **Add to System PATH (Optional but recommended):**
   ```
   - Open System Properties > Environment Variables
   - Add C:\Program Files\Tesseract-OCR to PATH
   ```

#### Microsoft Visual C++ Redistributable
- Download and install from Microsoft's website
- Required for some Python packages (especially image processing libraries)

## Installation Steps

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd medical_etl_system

# Or download and extract the ZIP file
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter issues, install core packages individually:
pip install pandas numpy Pillow pytesseract pdf2image openpyxl py7zr rarfile
```

### 4. Verify Tesseract Installation
```bash
# Test Tesseract installation
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

### 5. Configure Tesseract Path (if needed)
The system automatically detects Tesseract installation. If needed, you can manually configure the path in `config/config.py`:
```python
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Directory Structure
```
medical_etl_system/
├── main.py                 # Main ETL processor
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── config/
│   └── config.py          # Configuration settings
├── modules/
│   ├── file_extractor.py  # File extraction from archives
│   ├── ocr_processor.py   # OCR text extraction
│   ├── patient_parser.py  # Patient data parsing
│   ├── mapping_processor.py # Mapping file processing
│   ├── duplicate_detector.py # Duplicate detection
│   ├── file_organizer.py  # File organization
│   └── etl_logger.py      # Comprehensive logging
├── logs/                  # Log files (created automatically)
├── temp/                  # Temporary extraction files
└── data/                  # Optional data storage
```

## Usage

### REST API (Recommended for Remote Operations)

The system includes a FastAPI-based REST API for remote operations.

#### Start the API Server
```bash
python api.py
# Or using uvicorn
uvicorn api:app --reload
```

#### API Endpoints
- **GET** `/health` - Health check
- **POST** `/api/v1/dataset/inspect` - Inspect ZIP file contents
- **POST** `/api/v1/dataset/upload-and-inspect` - Upload and inspect ZIP file
- **POST** `/api/v1/etl/run` - Run ETL process

#### API Examples
```bash
# Health check
curl http://localhost:8000/health

# Inspect a dataset
curl -X POST http://localhost:8000/api/v1/dataset/inspect \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/dataset.zip"}'

# Run ETL without mapping file (mapping is optional)
curl -X POST http://localhost:8000/api/v1/etl/run \
  -H "Content-Type: application/json" \
  -d '{
    "source_path": "/path/to/source",
    "destination_path": "/path/to/destination",
    "dry_run": false
  }'
```

**API Documentation:**
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
- See [API_README.md](API_README.md) for complete API documentation

### Basic Command Line Usage

#### Dry Run (No actual file operations)
```bash
python main.py /path/to/source/folder /path/to/destination/folder --dry-run
```

#### Real Run with Mapping File
```bash
python main.py /path/to/source/folder /path/to/destination/folder --mapping mapping.xlsx
```

#### Real Run without Mapping (OCR + Filename parsing)
```bash
python main.py /path/to/source/folder /path/to/destination/folder
```

#### Verbose Output
```bash
python main.py /path/to/source/folder /path/to/destination/folder --verbose --dry-run
```

### Command Line Options
- `source`: Source directory or file path (required)
- `destination`: Destination directory path (required)
- `--mapping, -m`: Path to mapping file (Excel/CSV)
- `--dry-run, -d`: Perform dry run without actual file operations
- `--verbose, -v`: Enable verbose logging

### Example Commands

```bash
# Example 1: Process with mapping file (dry run)
python main.py "C:\Medical_Records\Source" "C:\Medical_Records\Organized" --mapping "C:\mapping.xlsx" --dry-run

# Example 2: Process without mapping (real run)
python main.py "C:\Medical_Records\Source" "C:\Medical_Records\Organized"

# Example 3: Process ZIP files with mapping
python main.py "C:\Records.zip" "C:\Organized" --mapping "patient_mapping.csv" --verbose
```

## Configuration

### Mapping File Format
The mapping file should be Excel (.xlsx) or CSV with columns that match these synonyms:

**Patient ID columns:**
- id, patient_id, patientid, pno, patient_no, mrn, medical_record_number

**Name columns:**
- firstname, first_name, fname, givenname, given_name
- lastname, last_name, lname, surname, family_name

**Filename columns:**
- filename, file_name, document, doc_name

**Date of Birth columns:**
- dob, date_of_birth, birthdate, birth_date

### Sample Mapping File
```csv
Patient_ID,Last_Name,First_Name,DOB,File_Name
12345,Smith,John,01-15-1980,john_smith_chart.pdf
67890,Johnson,Mary,03-22-1975,mary_johnson_xray.jpg
```

## File Processing Workflow

### 1. File Discovery and Extraction
- Scans source directory recursively
- Extracts nested ZIP, RAR, 7Z archives
- Supports unlimited nesting depth
- Handles password-protected archives (logs warnings)

### 2. Patient Data Identification
**With Mapping File:**
- Looks up by filename
- Looks up by extracted patient ID
- Falls back to OCR/filename parsing if not found

**Without Mapping File:**
- Parses filenames for patient information
- Uses OCR to extract text from images/PDFs
- Combines results for best accuracy

### 3. Duplicate Detection
- **Exact duplicates**: Same file content (hash)
- **Potential duplicates**: Same size, different content
- **Patient variations**: Multiple files for same patient
- **Year/Module preservation**: Files with same size but different years/modules are NOT considered duplicates and ALL are preserved with year prefixes (e.g., 2021_chart.pdf, 2022_chart.pdf, 2023_chart.pdf)

### 4. File Organization
Creates folder structure:
```
Destination/
├── Lastname, Firstname DOB/
│   ├── 2022_chart.pdf
│   ├── 2023_xray.jpg
│   └── chart1.tiff
├── duplicates/
│   └── [duplicate files organized by patient]
└── unmapped/
    └── [files that couldn't be identified]
```

## Logging and Monitoring

### Log Files
- **Session logs**: Detailed processing logs with timestamps
- **Summary files**: JSON summaries for each session
- **SSIS integration**: Structured logs for automation

### Log Locations
- `logs/dry_run_YYYYMMDD_HHMMSS.log`
- `logs/real_run_YYYYMMDD_HHMMSS.log`
- `logs/session_summary_YYYYMMDD_HHMMSS.json`

### Monitoring Progress
The system provides real-time console output and detailed logs including:
- Files processed count
- Success/failure rates
- Duplicate detection results
- Patient folder creation
- Error details and warnings

## Troubleshooting

### Common Issues

#### Tesseract Not Found
```
Error: pytesseract.pytesseract.TesseractNotFoundError
Solution: Install Tesseract OCR and verify path in config.py
```

#### Memory Issues with Large Files
```
Error: MemoryError during image processing
Solution: Increase system RAM or process files in smaller batches
```

#### Permission Errors
```
Error: PermissionError accessing files
Solution: Run as Administrator or check file permissions
```

#### Archive Extraction Failures
```
Error: Bad archive file
Solution: Check if archives are corrupted or password-protected
```

### Performance Optimization

#### For Large Datasets (>10,000 files):
1. Use SSD storage for temp directory
2. Increase available RAM
3. Process in smaller batches
4. Use verbose mode to monitor progress

#### For Network Drives:
1. Copy source files locally first
2. Use local destination for initial processing
3. Copy organized files to network location

## Advanced Configuration

### OCR Settings
The system automatically detects optimal OCR settings. You can adjust in `config/config.py`:
- OCR languages: `OCR_LANGUAGES = ['eng', 'spa']`
- Tesseract auto-detection: Automatically finds installation
- Processing optimization: Auto-configures based on system capabilities

### Processing Settings
The system auto-configures optimal settings based on your system:
- `MAX_WORKERS = 4`: Auto-adjusts to CPU cores
- `CHUNK_SIZE = 1000`: Auto-optimizes for dataset size
- `DUPLICATE_SIZE_THRESHOLD = 100`: Configurable duplicate detection sensitivity

### File Type Support
Supported formats:
- **Images**: JPG, PNG, TIFF, BMP, GIF
- **Documents**: PDF
- **Archives**: ZIP, RAR, 7Z, TAR, GZ
- **Mapping**: XLSX, XLS, CSV, TSV

## Integration with SSIS

The system generates structured logs compatible with SQL Server Integration Services:
- JSON session summaries
- CSV export functionality
- Detailed error tracking
- Performance metrics

### SSIS Integration Example
```sql
-- Example SSIS task to read session summary
BULK INSERT ETL_Sessions
FROM 'C:\ETL\logs\session_summary_20231201_143000.json'
WITH (FORMATFILE = 'json_format.xml')
```

## 📚 Documentation

- **[API_README.md](API_README.md)** - Complete REST API documentation
- **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** - Complete production deployment guide
- **[EXCEL_FORMATS.md](EXCEL_FORMATS.md)** - Excel mapping file formats
- **[ENHANCED_PROCESSING.md](ENHANCED_PROCESSING.md)** - Processing pipeline details
- **[LOCATION_MAP.md](LOCATION_MAP.md)** - File organization structure

## Support and Maintenance

### Regular Maintenance
1. Clean temp directory periodically
2. Archive old log files based on `MAX_LOG_SIZE_MB` setting
3. Update Python dependencies
4. Verify Tesseract functionality

### Backup Strategy
- Source files (read-only, no modifications)
- Destination organized files
- Mapping files and environment configuration
- Log files for audit trail

### Performance Monitoring
- Session duration
- Files processed per hour
- Error rates
- Memory usage
- Disk space utilization

For additional support or feature requests, refer to the project documentation or contact the development team.
"""
Configuration settings for Medical ETL System
"""

import os
import shutil
from pathlib import Path


def load_env_file(env_file_path=None):
    """Load environment variables from .env file"""
    if env_file_path is None:
        env_file_path = Path(__file__).parent / '.env'
    
    if not env_file_path.exists():
        return
    
    with open(env_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')


# Load environment variables
load_env_file()


class Config:
    """Main configuration class for the ETL system"""
    
    # Base directories (configurable via environment)
    BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BASE_DIR / os.environ.get('LOGS_DIR', 'logs')
    TEMP_DIR = BASE_DIR / os.environ.get('TEMP_DIR', 'temp')
    DATA_DIR = BASE_DIR / os.environ.get('DATA_DIR', 'data')
    
    # Processing modes
    DRY_RUN_MODE = "dry_run"
    REAL_RUN_MODE = "real_run"
    
    # Processing settings (configurable via environment)
    MAX_WORKERS = int(os.environ.get('WORKER_THREADS', '4'))
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', '100'))
    CHUNK_SIZE = 8192
    
    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif'}
    SUPPORTED_PDF_FORMATS = {'.pdf'}
    SUPPORTED_ARCHIVE_FORMATS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
    SUPPORTED_MAPPING_FORMATS = {'.xlsx', '.xls', '.csv', '.tsv'}
    
    # OCR Settings (configurable via environment)
    TESSERACT_CMD = None  # Auto-detected at runtime
    OCR_LANGUAGES = os.environ.get('OCR_LANGUAGES', 'eng').split(',')
    
    # Date format settings - configurable
    OUTPUT_DATE_FORMAT = "%m-%d-%Y"
    INPUT_DATE_FORMATS = [
        "%m-%d-%Y", "%m/%d/%Y", "%m.%d.%Y",
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", 
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"
    ]
    
    # Processing settings (auto-configurable)
    MAX_WORKERS = 4
    CHUNK_SIZE = 1000
    
    # Field name synonyms for mapping files
    ID_FIELD_SYNONYMS = {
        'id', 'patient_id', 'patientid', 'pno', 'p_no', 'patient_no', 
        'patient_number', 'id_number', 'idnumber', 'entity_id', 
        'entityid', 'medical_id', 'medicalid', 'chart_id', 'chartid',
        'mrn', 'medical_record_number', 'record_id', 'recordid'
    }
    
    LASTNAME_FIELD_SYNONYMS = {
        'lastname', 'last_name', 'lname', 'l_name', 'surname', 
        'family_name', 'familyname', 'last', 'sur_name'
    }
    
    FIRSTNAME_FIELD_SYNONYMS = {
        'firstname', 'first_name', 'fname', 'f_name', 'givenname', 
        'given_name', 'first', 'forename', 'christian_name'
    }
    
    FILENAME_FIELD_SYNONYMS = {
        'filename', 'file_name', 'file', 'document', 'doc', 
        'document_name', 'doc_name', 'name', 'filepath', 'file_path'
    }
    
    DOB_FIELD_SYNONYMS = {
        'dob', 'date_of_birth', 'dateofbirth', 'birth_date', 
        'birthdate', 'birth', 'born', 'birthday'
    }
    
    # Detection thresholds (configurable via environment)
    DUPLICATE_SIZE_THRESHOLD = int(os.environ.get('DUPLICATE_SIZE_THRESHOLD', '100'))
    
    # Folder structure (configurable via environment)
    DUPLICATE_FOLDER_NAME = os.environ.get('DUPLICATE_FOLDER_NAME', 'duplicates')
    UNMAPPED_FOLDER_NAME = os.environ.get('UNMAPPED_FOLDER_NAME', 'unmapped')
    
    # Logging configuration (configurable via environment)
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    MAX_LOG_SIZE_MB = int(os.environ.get('MAX_LOG_SIZE_MB', '100'))

    @classmethod
    def get_log_file_path(cls, run_type: str,
                          timestamp: str | None = None) -> Path:
        """Get the log file path for a specific run type"""
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{run_type}_{timestamp}.log"
        return cls.LOGS_DIR / filename
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        for directory in [cls.LOGS_DIR, cls.TEMP_DIR, cls.DATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_image_file(cls, filepath: Path) -> bool:
        """Check if file is a supported image format"""
        return filepath.suffix.lower() in cls.SUPPORTED_IMAGE_FORMATS
    
    @classmethod
    def is_pdf_file(cls, filepath: Path) -> bool:
        """Check if file is a PDF"""
        return filepath.suffix.lower() in cls.SUPPORTED_PDF_FORMATS
    
    @classmethod
    def is_archive_file(cls, filepath: Path) -> bool:
        """Check if file is a supported archive format"""
        return filepath.suffix.lower() in cls.SUPPORTED_ARCHIVE_FORMATS
    
    @classmethod
    def is_mapping_file(cls, filepath: Path) -> bool:
        """Check if file is a supported mapping format"""
        return filepath.suffix.lower() in cls.SUPPORTED_MAPPING_FORMATS
    
    @classmethod
    def normalize_field_name(cls, field_name: str) -> str:
        """Normalize field name for comparison"""
        return field_name.lower().strip().replace(' ', '_')
    
    @classmethod
    def get_field_type(cls, field_name: str) -> str:
        """Determine the type of field based on synonyms"""
        normalized = cls.normalize_field_name(field_name)
        
        if normalized in cls.ID_FIELD_SYNONYMS:
            return 'id'
        elif normalized in cls.FIRSTNAME_FIELD_SYNONYMS:
            return 'firstname'
        elif normalized in cls.LASTNAME_FIELD_SYNONYMS:
            return 'lastname'
        elif normalized in cls.FILENAME_FIELD_SYNONYMS:
            return 'filename'
        elif normalized in cls.DOB_FIELD_SYNONYMS:
            return 'dob'
        else:
            return 'unknown'


class DatabaseConfig:
    """Database configuration for optional database integration"""
    
    # SQLite database for tracking processed files
    DB_PATH = Config.DATA_DIR / "etl_tracking.db"
    
    # Table schemas
    PROCESSED_FILES_TABLE = """
    CREATE TABLE IF NOT EXISTS processed_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_path TEXT NOT NULL,
        destination_path TEXT,
        file_hash TEXT,
        file_size INTEGER,
        patient_id TEXT,
        patient_name TEXT,
        date_of_birth TEXT,
        processing_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        run_type TEXT,
        status TEXT
    )
    """
    
    DUPLICATE_FILES_TABLE = """
    CREATE TABLE IF NOT EXISTS duplicate_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_file_id INTEGER,
        duplicate_path TEXT,
        detection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (original_file_id) REFERENCES processed_files (id)
    )
    """


# Environment-specific settings
def load_environment_config():
    """Load environment-specific configuration"""
    # Auto-detect Tesseract installation
    tesseract_cmd = _detect_tesseract()
    if tesseract_cmd:
        Config.TESSERACT_CMD = tesseract_cmd
    
    return Config


def _detect_tesseract():
    """Auto-detect Tesseract installation path"""
    # Check environment variable first
    env_path = os.environ.get('TESSERACT_CMD')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check if tesseract is in PATH
    tesseract_cmd = shutil.which('tesseract')
    if tesseract_cmd:
        return tesseract_cmd
    
    # Check common installation paths
    common_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
        '/opt/homebrew/bin/tesseract'
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Return None if not found - will need manual configuration
    return None



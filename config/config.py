from __future__ import annotations

import os
from pathlib import Path
from typing import List


class Config:
    # Run modes
    DRY_RUN_MODE = 'dry-run'
    REAL_RUN_MODE = 'real'

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    MAX_LOG_SIZE_MB = 50

    # Folder names
    DUPLICATE_FOLDER_NAME = 'duplicates'
    UNMAPPED_FOLDER_NAME = 'unmapped'

    # Directories (relative to project root)
    ROOT_DIR = Path(__file__).resolve().parents[1]
    LOG_DIR = ROOT_DIR / 'logs'
    TEMP_DIR = ROOT_DIR / 'temp'
    OUTPUT_DIR = ROOT_DIR / 'temp_output'

    # Supported formats
    IMAGE_EXTENSIONS: List[str] = [
        '.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'
    ]
    PDF_EXTENSIONS: List[str] = ['.pdf']
    TEXT_EXTENSIONS: List[str] = ['.txt']
    ARCHIVE_EXTENSIONS: List[str] = ['.zip']
    MAPPING_EXTENSIONS: List[str] = ['.xlsx', '.xls', '.csv', '.json']

    # Date formats
    INPUT_DATE_FORMATS: List[str] = [
        '%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y'
    ]
    OUTPUT_DATE_FORMAT: str = '%m-%d-%Y'

    # OCR
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD', None)

    @staticmethod
    def ensure_directories() -> None:
        Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_log_file_path(run_type: str, session_id: str) -> Path:
        Config.ensure_directories()
        return Config.LOG_DIR / f'etl_{run_type}_{session_id}.log'

    @staticmethod
    def is_image_file(path: Path) -> bool:
        return path.suffix.lower() in Config.IMAGE_EXTENSIONS

    @staticmethod
    def is_pdf_file(path: Path) -> bool:
        return path.suffix.lower() in Config.PDF_EXTENSIONS

    @staticmethod
    def is_text_file(path: Path) -> bool:
        return path.suffix.lower() in Config.TEXT_EXTENSIONS

    @staticmethod
    def is_archive_file(path: Path) -> bool:
        return path.suffix.lower() in Config.ARCHIVE_EXTENSIONS

    @staticmethod
    def is_mapping_file(path: Path) -> bool:
        return path.suffix.lower() in Config.MAPPING_EXTENSIONS

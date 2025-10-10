"""
Initialize modules package
"""

# Import main classes for easier access
from .file_extractor import FileExtractor
from .ocr_processor import OCRProcessor
from .patient_parser import PatientParser
from .mapping_processor import MappingProcessor
from .duplicate_detector import DuplicateDetector
from .file_organizer import FileOrganizer
from .etl_logger import ETLLogger

__all__ = [
    'FileExtractor',
    'OCRProcessor', 
    'PatientParser',
    'MappingProcessor',
    'DuplicateDetector',
    'FileOrganizer',
    'ETLLogger'
]
"""
File Extraction System for Medical ETL
Handles nested ZIP files and recursive extraction
"""

import zipfile
import shutil
import logging
import hashlib
import re
from pathlib import Path
from typing import List, Tuple, Optional
from medical_etl_system.config.config import Config

logger = logging.getLogger(__name__)


class FileExtractor:
    """Handles extraction of nested archive files"""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.config = Config()
        self.temp_dir = temp_dir or self.config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_files: List[Path] = []
        
    def extract_all_files(
        self, source_path: Path, max_depth: int = 10
    ) -> List[Tuple[Path, Path]]:
        """
        Extract all files from source, handling nested archives
        
        Args:
            source_path: Source directory or file path
            max_depth: Maximum nesting depth to prevent infinite recursion
            
        Returns:
            List of (file_path, original_path) tuples where:
            - file_path: the actual file to process (extracted if from archive)
            - original_path: the original container
              (same path as file for non-archives; archive path for extracted)
        """
        files_to_process = []

        try:
            # Process a single file
            if source_path.is_file():
                if self.config.is_archive_file(source_path):
                    files_to_process.extend(self._extract_archive_recursive(
                        source_path, max_depth
                    ))
                else:
                    files_to_process.append((source_path, source_path))
            
            # Process directory recursively
            elif source_path.is_dir():
                for item in source_path.rglob("*"):
                    if item.is_file():
                        if self.config.is_archive_file(item):
                            files_to_process.extend(
                                self._extract_archive_recursive(
                                    item, max_depth
                                )
                            )
                        elif self._is_supported_file(item):
                            files_to_process.append((item, item))

        except Exception as e:
            logger.error(
                f"Error extracting files from {source_path}: {str(e)}"
            )

        # Sort files for consistent processing order
        files_to_process.sort(key=lambda x: str(x[0]))

        return files_to_process

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported type"""
        return (
            self.config.is_image_file(file_path)
            or self.config.is_pdf_file(file_path)
            or self.config.is_text_file(file_path)
        )
    
    def _extract_archive_recursive(
        self, archive_path: Path, max_depth: int
    ) -> List[Tuple[Path, Path]]:
        """Extract archive and process nested archives"""
        extracted_files: List[Tuple[Path, Path]] = []
        
        if max_depth <= 0:
            logger.warning(
                f"Maximum extraction depth reached for {archive_path}"
            )
            return extracted_files

        try:
            extract_dir = self._create_extraction_dir(archive_path)
            
            if not self._extract_archive(archive_path, extract_dir):
                logger.error(f"Failed to extract {archive_path}")
                return extracted_files
                
            for extracted_item in extract_dir.rglob("*"):
                if extracted_item.is_file():
                    if self.config.is_archive_file(extracted_item):
                        # Recursively extract nested archives
                        nested_files = self._extract_archive_recursive(
                            extracted_item, max_depth - 1
                        )
                        extracted_files.extend(nested_files)
                    elif self._is_supported_file(extracted_item):
                        # Add supported file as (file_path, original_path)
                        extracted_files.append((extracted_item, archive_path))
                        
        except Exception as e:
            logger.error(f"Error extracting archive {archive_path}: {str(e)}")
        
        return extracted_files
    
    def _create_extraction_dir(self, archive_path: Path) -> Path:
        """Create unique extraction directory"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        dir_name = f"{archive_path.stem}_{unique_id}"
        extract_dir = self.temp_dir / dir_name
        extract_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_files.append(extract_dir)
        return extract_dir
    
    def _extract_archive(self, archive_path: Path, extract_dir: Path) -> bool:
        """Extract archive to specified directory"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    # Skip directories
                    if member.filename.endswith('/'):
                        continue
                    
                    # Skip certain file types
                    if self._is_system_file(member.filename):
                        continue
                    
                    try:
                        zip_ref.extract(member, extract_dir)
                    except Exception as e:
                        logger.error(
                            f"Error extracting {member.filename}: {str(e)}"
                        )
                        continue
                
                return True
                
        except zipfile.BadZipFile:
            logger.error(f"Bad ZIP file: {archive_path}")
        except RuntimeError as e:
            if "password required" in str(e).lower():
                logger.warning(f"Password protected ZIP: {archive_path}")
            else:
                logger.error(f"Error extracting ZIP {archive_path}: {str(e)}")
        
        return False
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get comprehensive file information"""
        try:
            stat = file_path.stat()
            
            info = {
                'path': str(file_path),
                'name': file_path.name,
                'stem': file_path.stem,
                'suffix': file_path.suffix,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_archive': self.config.is_archive_file(file_path),
                'is_image': self.config.is_image_file(file_path),
                'is_pdf': self.config.is_pdf_file(file_path),
                'is_mapping': self.config.is_mapping_file(file_path)
            }
            
            # Calculate file hash for duplicate detection
            info['hash'] = self._calculate_file_hash(file_path)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {}
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
                    
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def _is_system_file(self, filename: str) -> bool:
        """Check if file is a system/hidden file"""
        system_patterns = [
            r'__MACOSX',
            r'\.DS_Store$',
            r'Thumbs\.db$',
            r'desktop\.ini$',
            r'\.gitignore$'
        ]
        
        return any(re.match(pattern, filename) for pattern in system_patterns)
    
    def cleanup_temp_files(self):
        """Clean up temporary extraction directories"""
        try:
            for temp_dir in self.extracted_files:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temp directory: {temp_dir}")
            
            self.extracted_files.clear()
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
            return
    
    def get_extraction_statistics(self) -> dict:
        """Get statistics about extraction process"""
        total_temp_dirs = len(self.extracted_files)
        total_size = 0
        
        try:
            for temp_dir in self.extracted_files:
                if temp_dir.exists():
                    for file_path in temp_dir.rglob("*"):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating extraction statistics: {str(e)}")
        
        return {
            'temp_directories_created': total_temp_dirs,
            'total_temp_size_bytes': total_size,
            'total_temp_size_mb': round(total_size / (1024 * 1024), 2)
        }

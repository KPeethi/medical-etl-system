"""
File Extraction System for Medical ETL
Handles nested ZIP files and recursive extraction
"""

import os
import zipfile
import rarfile
import tarfile
import py7zr
import shutil
import logging
from pathlib import Path
from typing import List, Generator, Tuple, Optional
from config.config import Config

logger = logging.getLogger(__name__)


class FileExtractor:
    """Handles extraction of nested archive files"""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        self.config = Config()
        self.temp_dir = temp_dir or self.config.TEMP_DIR
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_files = []
        
    def extract_all_files(self, source_path: Path, 
                         max_depth: int = 10) -> Generator[Tuple[Path, Path], None, None]:
        """
        Extract all files from source, handling nested archives
        
        Args:
            source_path: Source directory or file path
            max_depth: Maximum nesting depth to prevent infinite recursion
            
        Yields:
            Tuple of (original_path, extracted_path)
        """
        try:
            if source_path.is_file():
                if self.config.is_archive_file(source_path):
                    yield from self._extract_archive_recursive(
                        source_path, max_depth
                    )
                else:
                    yield (source_path, source_path)
            elif source_path.is_dir():
                yield from self._process_directory_recursive(
                    source_path, max_depth
                )
        except Exception as e:
            logger.error(f"Error extracting files from {source_path}: {str(e)}")
    
    def _process_directory_recursive(self, directory: Path, 
                                   max_depth: int) -> Generator[Tuple[Path, Path], None, None]:
        """Process directory recursively"""
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    if self.config.is_archive_file(item):
                        yield from self._extract_archive_recursive(
                            item, max_depth
                        )
                    else:
                        yield (item, item)
        except Exception as e:
            logger.error(f"Error processing directory {directory}: {str(e)}")
    
    def _extract_archive_recursive(self, archive_path: Path, 
                                 max_depth: int) -> Generator[Tuple[Path, Path], None, None]:
        """Extract archive and process nested archives"""
        if max_depth <= 0:
            logger.warning(f"Maximum extraction depth reached for {archive_path}")
            return
        
        try:
            # Create unique extraction directory
            extract_dir = self._create_extraction_dir(archive_path)
            
            # Extract based on file type
            success = self._extract_archive(archive_path, extract_dir)
            
            if not success:
                logger.error(f"Failed to extract {archive_path}")
                return
            
            # Process extracted files
            for extracted_item in extract_dir.rglob("*"):
                if extracted_item.is_file():
                    if self.config.is_archive_file(extracted_item):
                        # Recursively extract nested archives
                        yield from self._extract_archive_recursive(
                            extracted_item, max_depth - 1
                        )
                    else:
                        # Yield regular file
                        yield (archive_path, extracted_item)
                        
        except Exception as e:
            logger.error(f"Error extracting archive {archive_path}: {str(e)}")
    
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
            suffix = archive_path.suffix.lower()
            
            if suffix == '.zip':
                return self._extract_zip(archive_path, extract_dir)
            elif suffix == '.rar':
                return self._extract_rar(archive_path, extract_dir)
            elif suffix == '.7z':
                return self._extract_7z(archive_path, extract_dir)
            elif suffix in ['.tar', '.gz', '.tar.gz']:
                return self._extract_tar(archive_path, extract_dir)
            else:
                logger.warning(f"Unsupported archive format: {suffix}")
                return False
                
        except Exception as e:
            logger.error(f"Error extracting {archive_path}: {str(e)}")
            return False
    
    def _extract_zip(self, archive_path: Path, extract_dir: Path) -> bool:
        """Extract ZIP file"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Check for password protection
                if zip_ref.testzip() is not None:
                    logger.warning(f"ZIP file may be corrupted: {archive_path}")
                
                zip_ref.extractall(extract_dir)
                logger.debug(f"Extracted ZIP: {archive_path} to {extract_dir}")
                return True
                
        except zipfile.BadZipFile:
            logger.error(f"Bad ZIP file: {archive_path}")
            return False
        except RuntimeError as e:
            if "password required" in str(e).lower():
                logger.warning(f"Password protected ZIP: {archive_path}")
            else:
                logger.error(f"Error extracting ZIP {archive_path}: {str(e)}")
            return False
    
    def _extract_rar(self, archive_path: Path, extract_dir: Path) -> bool:
        """Extract RAR file"""
        try:
            with rarfile.RarFile(archive_path) as rar_ref:
                rar_ref.extractall(extract_dir)
                logger.debug(f"Extracted RAR: {archive_path} to {extract_dir}")
                return True
                
        except rarfile.BadRarFile:
            logger.error(f"Bad RAR file: {archive_path}")
            return False
        except Exception as e:
            logger.error(f"Error extracting RAR {archive_path}: {str(e)}")
            return False
    
    def _extract_7z(self, archive_path: Path, extract_dir: Path) -> bool:
        """Extract 7Z file"""
        try:
            with py7zr.SevenZipFile(archive_path, mode='r') as sz_ref:
                sz_ref.extractall(extract_dir)
                logger.debug(f"Extracted 7Z: {archive_path} to {extract_dir}")
                return True
                
        except Exception as e:
            logger.error(f"Error extracting 7Z {archive_path}: {str(e)}")
            return False
    
    def _extract_tar(self, archive_path: Path, extract_dir: Path) -> bool:
        """Extract TAR/TAR.GZ file"""
        try:
            mode = 'r:gz' if archive_path.suffix.lower() in ['.gz', '.tar.gz'] else 'r'
            
            with tarfile.open(archive_path, mode) as tar_ref:
                # Security check for path traversal
                def is_safe_path(path: str) -> bool:
                    return not (path.startswith('/') or '..' in path)
                
                safe_members = [m for m in tar_ref.getmembers() 
                              if is_safe_path(m.name)]
                
                for member in safe_members:
                    tar_ref.extract(member, extract_dir)
                
                logger.debug(f"Extracted TAR: {archive_path} to {extract_dir}")
                return True
                
        except Exception as e:
            logger.error(f"Error extracting TAR {archive_path}: {str(e)}")
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
        import hashlib
        
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
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


class ArchiveValidator:
    """Validates archive files before extraction"""
    
    @staticmethod
    def is_valid_zip(zip_path: Path) -> bool:
        """Check if ZIP file is valid"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                return zip_ref.testzip() is None
        except:
            return False
    
    @staticmethod
    def is_valid_rar(rar_path: Path) -> bool:
        """Check if RAR file is valid"""
        try:
            with rarfile.RarFile(rar_path) as rar_ref:
                return rar_ref.testrar() is None
        except:
            return False
    
    @staticmethod
    def is_valid_7z(sz_path: Path) -> bool:
        """Check if 7Z file is valid"""
        try:
            with py7zr.SevenZipFile(sz_path, mode='r') as sz_ref:
                sz_ref.testzip()
                return True
        except:
            return False
    
    @staticmethod
    def get_archive_info(archive_path: Path) -> dict:
        """Get detailed information about archive"""
        info = {
            'path': str(archive_path),
            'size': archive_path.stat().st_size,
            'type': archive_path.suffix.lower(),
            'is_valid': False,
            'file_count': 0,
            'compressed_size': 0,
            'uncompressed_size': 0
        }
        
        try:
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    info['is_valid'] = zip_ref.testzip() is None
                    info['file_count'] = len(zip_ref.infolist())
                    info['compressed_size'] = sum(f.compress_size for f in zip_ref.infolist())
                    info['uncompressed_size'] = sum(f.file_size for f in zip_ref.infolist())
            
            # Add similar logic for other archive types as needed
            
        except Exception as e:
            logger.error(f"Error getting archive info for {archive_path}: {str(e)}")
        
        return info
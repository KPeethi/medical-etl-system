"""
Duplicate Detection System for Medical ETL
Identifies duplicate files based on size, content, and patient information
"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from config.config import Config

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """File information for duplicate detection"""
    path: Path
    size: int
    hash: str
    patient_id: str
    patient_name: str
    date_of_birth: str
    file_type: str
    original_filename: str


class DuplicateDetector:
    """Detects duplicate files using multiple criteria"""
    
    def __init__(self):
        self.config = Config()
        self.processed_files: List[FileInfo] = []
        self.duplicates: List[Tuple[FileInfo, FileInfo]] = []
        self.unique_files: List[FileInfo] = []
        
    def add_file(self, file_path: Path, patient_data: Dict[str, str],
                 original_path: Optional[Path] = None) -> FileInfo:
        """
        Add a file for duplicate detection
        
        Args:
            file_path: Path to the file
            patient_data: Parsed patient information
            original_path: Original file path before extraction
            
        Returns:
            FileInfo object
        """
        try:
            # Calculate file information
            file_info = FileInfo(
                path=file_path,
                size=file_path.stat().st_size,
                hash=self._calculate_file_hash(file_path),
                patient_id=patient_data.get('id', ''),
                patient_name=self._format_patient_name(
                    patient_data.get('firstname', ''),
                    patient_data.get('lastname', '')
                ),
                date_of_birth=patient_data.get('dob', ''),
                file_type=file_path.suffix.lower(),
                original_filename=original_path.name if original_path else file_path.name
            )
            
            self.processed_files.append(file_info)
            return file_info
            
        except Exception as e:
            logger.error(f"Error adding file {file_path} for duplicate detection: {str(e)}")
            raise
    
    def detect_duplicates(self) -> Dict[str, List[FileInfo]]:
        """
        Detect duplicates among all processed files
        
        Returns:
            Dictionary with duplicate groups
        """
        self.duplicates.clear()
        self.unique_files.clear()
        
        try:
            # Group files by different criteria
            hash_groups = self._group_by_hash()
            size_groups = self._group_by_size()
            patient_groups = self._group_by_patient()
            
            # Identify exact duplicates (same hash)
            exact_duplicates = self._find_exact_duplicates(hash_groups)
            
            # Identify potential duplicates (same size, different content)
            potential_duplicates = self._find_potential_duplicates(size_groups)
            
            # Identify patient file variations
            patient_variations = self._find_patient_variations(patient_groups)
            
            # Combine all duplicate categories
            all_duplicates = {
                'exact_duplicates': exact_duplicates,
                'potential_duplicates': potential_duplicates,
                'patient_variations': patient_variations,
                'unique_files': self._get_unique_files()
            }
            
            # Log statistics
            self._log_duplicate_statistics(all_duplicates)
            
            return all_duplicates
            
        except Exception as e:
            logger.error(f"Error detecting duplicates: {str(e)}")
            return {}
    
    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def _format_patient_name(self, firstname: str, lastname: str) -> str:
        """Format patient name consistently"""
        if lastname and firstname:
            return f"{lastname.strip()}, {firstname.strip()}"
        elif lastname:
            return lastname.strip()
        elif firstname:
            return firstname.strip()
        else:
            return ""
    
    def _group_by_hash(self) -> Dict[str, List[FileInfo]]:
        """Group files by hash"""
        hash_groups = {}
        for file_info in self.processed_files:
            if file_info.hash:
                if file_info.hash not in hash_groups:
                    hash_groups[file_info.hash] = []
                hash_groups[file_info.hash].append(file_info)
        return hash_groups
    
    def _group_by_size(self) -> Dict[int, List[FileInfo]]:
        """Group files by size"""
        size_groups = {}
        for file_info in self.processed_files:
            if file_info.size not in size_groups:
                size_groups[file_info.size] = []
            size_groups[file_info.size].append(file_info)
        return size_groups
    
    def _group_by_patient(self) -> Dict[str, List[FileInfo]]:
        """Group files by patient"""
        patient_groups = {}
        for file_info in self.processed_files:
            # Create patient key from available information
            patient_key = self._create_patient_key(file_info)
            if patient_key:
                if patient_key not in patient_groups:
                    patient_groups[patient_key] = []
                patient_groups[patient_key].append(file_info)
        return patient_groups
    
    def _create_patient_key(self, file_info: FileInfo) -> str:
        """Create a consistent patient key for grouping"""
        # Prioritize ID if available
        if file_info.patient_id:
            return f"id:{file_info.patient_id}"
        
        # Use name and DOB combination
        if file_info.patient_name and file_info.date_of_birth:
            return f"name_dob:{file_info.patient_name}:{file_info.date_of_birth}"
        
        # Use name only if DOB not available
        if file_info.patient_name:
            return f"name:{file_info.patient_name}"
        
        return ""
    
    def _find_exact_duplicates(self, hash_groups: Dict[str, List[FileInfo]]) -> List[List[FileInfo]]:
        """Find exact duplicates (same content hash)"""
        exact_duplicates = []
        
        for hash_value, files in hash_groups.items():
            if len(files) > 1:
                # Sort by modification time or name to determine "original"
                sorted_files = sorted(files, key=lambda f: (f.path.stat().st_mtime, f.path.name))
                exact_duplicates.append(sorted_files)
                
                logger.info(f"Found {len(files)} exact duplicates with hash {hash_value[:8]}...")
        
        return exact_duplicates
    
    def _find_potential_duplicates(self, size_groups: Dict[int, List[FileInfo]]) -> List[List[FileInfo]]:
        """Find potential duplicates (same size, different content)"""
        potential_duplicates = []
        
        for size, files in size_groups.items():
            if len(files) > 1:
                # Filter out files that are already exact duplicates
                unique_hashes = set()
                potential_group = []
                
                for file_info in files:
                    if file_info.hash not in unique_hashes:
                        unique_hashes.add(file_info.hash)
                        potential_group.append(file_info)
                
                # Only consider as potential duplicates if size is significant
                # and there are multiple files with different hashes
                if len(potential_group) > 1 and size > 1024:  # > 1KB
                    # Check if these are truly duplicates or just different files from different years/modules
                    if self._are_truly_duplicates(potential_group):
                        potential_duplicates.append(potential_group)
        
        return potential_duplicates
    
    def _are_truly_duplicates(self, files: List[FileInfo]) -> bool:
        """Check if files are truly duplicates (not just different years/modules)"""
        # If files belong to same patient, check for year/module differences
        patient_keys = set()
        for file_info in files:
            patient_key = self._create_patient_key(file_info)
            if patient_key:
                patient_keys.add(patient_key)
        
        # If all files belong to same patient
        if len(patient_keys) == 1:
            # Check if files have different years or modules
            years_found = set()
            modules_found = set()
            
            for file_info in files:
                # Extract year from filename
                year = self._extract_year_from_filename(file_info.original_filename)
                if year:
                    years_found.add(year)
                
                # Extract module information
                module = self._extract_module_from_filename(file_info.original_filename)
                if module:
                    modules_found.add(module)
            
            # If different years or modules found, these are NOT duplicates
            if len(years_found) > 1 or len(modules_found) > 1:
                return False  # Different years/modules = NOT duplicates
        
        # Check file type similarity
        file_types = set(f.file_type for f in files)
        if len(file_types) == 1:  # Same file type
            # Check filename similarity (but exclude year/module differences)
            if self._have_similar_base_filenames(files):
                return True  # Same base name, same type = likely duplicate
        
        return False  # Default to not duplicate
    
    def _extract_year_from_filename(self, filename: str) -> str:
        """Extract year from filename"""
        import re
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        matches = re.findall(year_pattern, filename)
        return matches[0] if matches else ""
    
    def _extract_module_from_filename(self, filename: str) -> str:
        """Extract module/chart information from filename"""
        import re
        filename_lower = filename.lower()
        
        # Look for module patterns
        module_patterns = [
            r'(chart\d+)',
            r'(module\d+)',
            r'(part\d+)',
            r'(section\d+)',
            r'(page\d+)',
            r'(doc\d+)',
            r'(file\d+)'
        ]
        
        for pattern in module_patterns:
            matches = re.findall(pattern, filename_lower)
            if matches:
                return matches[0]
        
        return ""
    
    def _have_similar_base_filenames(self, files: List[FileInfo]) -> bool:
        """Check if files have similar base filenames (excluding year/module)"""
        if len(files) < 2:
            return False
        
        import re
        
        # Extract base names without years, modules, and numbers
        base_names = []
        for file_info in files:
            base_name = file_info.original_filename
            # Remove extension
            base_name = Path(base_name).stem
            # Remove years
            base_name = re.sub(r'\b(20\d{2}|19\d{2})\b', '', base_name)
            # Remove modules
            base_name = re.sub(r'(chart|module|part|section|page|doc|file)\d*', '', base_name, flags=re.IGNORECASE)
            # Remove numbers and common suffixes
            base_name = re.sub(r'[_\-\s]*\d+[_\-\s]*', '', base_name)
            base_name = re.sub(r'[_\-\s]*(copy|final|v\d+)[_\-\s]*', '', base_name, flags=re.IGNORECASE)
            # Clean up
            base_name = re.sub(r'[_\-\s]+', '_', base_name).strip('_').lower()
            base_names.append(base_name)
        
        # Check if base names are similar
        unique_base_names = set(name for name in base_names if name)
        return len(unique_base_names) <= 1  # All have same base name
    
    def _find_patient_variations(self, patient_groups: Dict[str, List[FileInfo]]) -> List[List[FileInfo]]:
        """Find different files for the same patient (not duplicates, but variations)"""
        patient_variations = []
        
        for patient_key, files in patient_groups.items():
            if len(files) > 1:
                # Group by unique content (hash)
                hash_groups = {}
                for file_info in files:
                    if file_info.hash not in hash_groups:
                        hash_groups[file_info.hash] = []
                    hash_groups[file_info.hash].append(file_info)
                
                # If patient has multiple unique files, it's variations
                unique_files = []
                for hash_value, hash_files in hash_groups.items():
                    # Take the first file from each hash group
                    unique_files.append(hash_files[0])
                
                if len(unique_files) > 1:
                    patient_variations.append(unique_files)
        
        return patient_variations
    
    def _get_unique_files(self) -> List[FileInfo]:
        """Get list of unique files (no duplicates)"""
        unique_files = []
        hash_groups = self._group_by_hash()
        
        for hash_value, files in hash_groups.items():
            if files:
                # Take the first file from each hash group as the unique representative
                unique_files.append(files[0])
        
        # Add files without hashes (if any)
        for file_info in self.processed_files:
            if not file_info.hash:
                unique_files.append(file_info)
        
        return unique_files
    
    def _log_duplicate_statistics(self, duplicates: Dict[str, List]):
        """Log duplicate detection statistics"""
        total_files = len(self.processed_files)
        exact_duplicates = len(duplicates.get('exact_duplicates', []))
        potential_duplicates = len(duplicates.get('potential_duplicates', []))
        patient_variations = len(duplicates.get('patient_variations', []))
        unique_files = len(duplicates.get('unique_files', []))
        
        logger.info(f"Duplicate Detection Summary:")
        logger.info(f"  Total files processed: {total_files}")
        logger.info(f"  Exact duplicate groups: {exact_duplicates}")
        logger.info(f"  Potential duplicate groups: {potential_duplicates}")
        logger.info(f"  Patient variation groups: {patient_variations}")
        logger.info(f"  Unique files: {unique_files}")
    
    def get_duplicate_report(self) -> Dict[str, any]:
        """Generate detailed duplicate detection report"""
        duplicates = self.detect_duplicates()
        
        report = {
            'summary': {
                'total_files': len(self.processed_files),
                'exact_duplicate_groups': len(duplicates.get('exact_duplicates', [])),
                'potential_duplicate_groups': len(duplicates.get('potential_duplicates', [])),
                'patient_variation_groups': len(duplicates.get('patient_variations', [])),
                'unique_files': len(duplicates.get('unique_files', [])),
            },
            'details': {
                'exact_duplicates': [],
                'potential_duplicates': [],
                'patient_variations': [],
            },
            'recommendations': []
        }
        
        # Add detailed information for each duplicate group
        for group in duplicates.get('exact_duplicates', []):
            group_info = {
                'type': 'exact_duplicate',
                'file_count': len(group),
                'files': [self._file_info_to_dict(f) for f in group],
                'recommendation': 'Keep first file, move others to duplicates folder'
            }
            report['details']['exact_duplicates'].append(group_info)
        
        for group in duplicates.get('potential_duplicates', []):
            group_info = {
                'type': 'potential_duplicate',
                'file_count': len(group),
                'files': [self._file_info_to_dict(f) for f in group],
                'recommendation': 'Manual review recommended'
            }
            report['details']['potential_duplicates'].append(group_info)
        
        for group in duplicates.get('patient_variations', []):
            group_info = {
                'type': 'patient_variation',
                'file_count': len(group),
                'files': [self._file_info_to_dict(f) for f in group],
                'recommendation': 'Organize in patient folder with descriptive names'
            }
            report['details']['patient_variations'].append(group_info)
        
        # Generate recommendations
        if report['summary']['exact_duplicate_groups'] > 0:
            report['recommendations'].append(
                f"Found {report['summary']['exact_duplicate_groups']} groups of exact duplicates. "
                "Consider moving duplicate files to separate folder."
            )
        
        if report['summary']['potential_duplicate_groups'] > 0:
            report['recommendations'].append(
                f"Found {report['summary']['potential_duplicate_groups']} groups of potential duplicates. "
                "Manual review recommended to determine if files are truly duplicates."
            )
        
        return report
    
    def _file_info_to_dict(self, file_info: FileInfo) -> Dict[str, any]:
        """Convert FileInfo to dictionary"""
        return {
            'path': str(file_info.path),
            'size': file_info.size,
            'hash': file_info.hash[:16] + '...' if file_info.hash else '',
            'patient_id': file_info.patient_id,
            'patient_name': file_info.patient_name,
            'date_of_birth': file_info.date_of_birth,
            'file_type': file_info.file_type,
            'original_filename': file_info.original_filename
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.processed_files.clear()
        self.duplicates.clear()
        self.unique_files.clear()
        logger.debug("Duplicate detector cache cleared")
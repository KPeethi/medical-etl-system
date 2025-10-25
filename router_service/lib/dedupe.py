from typing import Dict, Tuple, Optional
from pathlib import Path

class DuplicateDetector:
    """Detect duplicate files using size and hash-based policies"""
    
    def __init__(self, policy: str = 'same_size_same_module'):
        self.policy = policy
        self.seen_files: Dict[str, Dict[str, str]] = {}
    
    def check_duplicate(
        self,
        file_path: str,
        patient_key: str,
        module: str,
        size_bytes: int,
        quick_hash: str,
        full_hash: str
    ) -> Tuple[bool, str]:
        """
        Check if file is duplicate
        Returns: (is_duplicate, reason)
        """
        key = self._make_key(patient_key, module, size_bytes, quick_hash)
        
        if key in self.seen_files:
            existing = self.seen_files[key]
            
            if self.policy == 'same_size_same_module':
                if existing.get('full_hash') == full_hash:
                    return True, f"Duplicate: same hash as {existing.get('path', 'previous file')}"
                else:
                    return False, "Different hash, keeping both files"
            
            elif self.policy == 'strict_hash':
                return True, f"Duplicate: same hash as {existing.get('path', 'previous file')}"
            
            elif self.policy == 'size_only':
                return True, f"Duplicate: same size as {existing.get('path', 'previous file')}"
        
        self.seen_files[key] = {
            'path': file_path,
            'full_hash': full_hash,
            'module': module
        }
        
        return False, "Unique file"
    
    def _make_key(self, patient_key: str, module: str, size_bytes: int, quick_hash: str) -> str:
        """Create lookup key based on policy"""
        if self.policy == 'same_size_same_module':
            return f"{patient_key}_{module}_{size_bytes}_{quick_hash}"
        elif self.policy == 'strict_hash':
            return f"{patient_key}_{quick_hash}"
        elif self.policy == 'size_only':
            return f"{patient_key}_{size_bytes}"
        else:
            return f"{patient_key}_{module}_{size_bytes}_{quick_hash}"
    
    def reset(self):
        """Clear seen files cache"""
        self.seen_files.clear()

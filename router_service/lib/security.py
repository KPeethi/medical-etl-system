import re
import hashlib
from typing import Any, Optional

class SecurityManager:
    """PHI-safe logging and security utilities"""
    
    PHI_PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN-REDACTED]'),
        (r'\b\d{3}\.\d{2}\.\d{4}\b', '[SSN-REDACTED]'),
        (r'\b[A-Z0-9]{2}\d{6}\b', '[MRN-REDACTED]'),
    ]
    
    PATH_PHI_PATTERNS = [
        (r"(^|[/\\])((?=.*[A-Z])[A-Za-z''.-]{2,}),\s*((?=.*[A-Z])[A-Za-z''.-]{2,})[^/\\]*?(/|\\)", r'\1[PATIENT-REDACTED]\4'),
        (r"(^|[/\\])((?=.*[A-Z])[A-Za-z''.-]{2,})[_ ]((?=.*[A-Z])[A-Za-z''.-]{2,})[^/\\]*?(/|\\)", r'\1[PATIENT-REDACTED]\4'),
        (r"\b((?=.*[A-Z])[A-Za-z''.-]+),\s*((?=.*[A-Z])[A-Za-z''.-]+)(?=\s+\d{2}-\d{2}-\d{4}|/|\\)", '[NAME-REDACTED]'),
        (r'\b\d{4}-\d{2}-\d{2}\b', '[DOB-REDACTED]'),
        (r'\b\d{2}-\d{2}-\d{4}\b', '[DOB-REDACTED]'),
        (r'\b\d{2}/\d{2}/\d{4}\b', '[DOB-REDACTED]'),
    ]
    
    @staticmethod
    def redact(text: str, enable_redaction: bool = True) -> str:
        """Redact PHI from text for safe logging"""
        if not enable_redaction or not text:
            return text
        
        redacted = str(text)
        
        for pattern, replacement in SecurityManager.PHI_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)
        
        return redacted
    
    @staticmethod
    def redact_path(path: str, enable_redaction: bool = True) -> str:
        """Redact patient-identifiable information from file paths"""
        if not enable_redaction or not path:
            return path
        
        redacted = str(path)
        
        for pattern, replacement in SecurityManager.PATH_PHI_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)
        
        for pattern, replacement in SecurityManager.PHI_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)
        
        return redacted
    
    @staticmethod
    def compute_hash(data: Any) -> str:
        """Compute SHA-256 hash of data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = str(data).encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def compute_file_hash(file_path: str, quick_hash_bytes: Optional[int] = None) -> tuple[str, str]:
        """
        Compute file hash
        Returns: (quick_hash, full_hash)
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                full_hash = hashlib.sha256(file_data).hexdigest()
                
                if quick_hash_bytes is not None and quick_hash_bytes > 0 and len(file_data) > quick_hash_bytes:
                    quick_data = file_data[:quick_hash_bytes]
                    quick_hash = hashlib.sha256(quick_data).hexdigest()[:16]
                else:
                    quick_hash = full_hash[:16]
                
                return quick_hash, full_hash
        except Exception as e:
            return '', ''
    
    @staticmethod
    def compute_integrity_chain_hash(previous_hash: str, current_data: str) -> str:
        """Compute tamper-evident chain hash"""
        combined = f"{previous_hash}{current_data}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

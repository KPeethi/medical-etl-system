import re
from pathlib import Path
from typing import Optional, Dict, Any

class ModuleResolver:
    """Resolve file module/category based on folder and filename patterns"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.module_config = self.config.get('module_detection', {})
    
    def resolve_module(self, file_path: str, folder_path: str) -> str:
        """
        Determine file module using folder keywords and filename patterns
        Priority: folder keywords -> filename patterns -> default
        """
        file_path_obj = Path(file_path)
        filename = file_path_obj.name.lower()
        folder_name = Path(folder_path).name.lower() if folder_path else ''
        
        folder_keywords = self.module_config.get('folder_keywords', {})
        for module, keywords in folder_keywords.items():
            if any(keyword.lower() in folder_name for keyword in keywords):
                return module
        
        filename_patterns = self.module_config.get('filename_patterns', {})
        for module, patterns in filename_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return module
        
        ext = file_path_obj.suffix.lower()
        if ext in ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.bmp', '.dcm']:
            return 'imaging'
        elif ext in ['.pdf', '.doc', '.docx', '.rtf', '.txt']:
            return 'documents'
        elif ext in ['.xlsx', '.xls', '.csv']:
            return 'reports'
        
        return 'misc'

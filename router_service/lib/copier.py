import shutil
from pathlib import Path
from typing import Tuple, Optional

class SafeCopier:
    """Safe file copy operations with error handling"""
    
    @staticmethod
    def safe_copy(
        src_path: str,
        dst_dir: str,
        filename: Optional[str] = None,
        dry_run: bool = False
    ) -> Tuple[bool, str, str]:
        """
        Safely copy file to destination
        Returns: (success, destination_path, error_message)
        """
        try:
            src = Path(src_path)
            
            if not src.exists():
                return False, '', f"Source file does not exist: {src_path}"
            
            if not src.is_file():
                return False, '', f"Source is not a file: {src_path}"
            
            dst_dir_path = Path(dst_dir)
            
            if not dry_run:
                dst_dir_path.mkdir(parents=True, exist_ok=True)
            
            final_filename = filename if filename else src.name
            dst_path = dst_dir_path / final_filename
            
            if dry_run:
                return True, str(dst_path), "DRY_RUN: Would copy file"
            
            if dst_path.exists():
                base_name = dst_path.stem
                extension = dst_path.suffix
                counter = 1
                while dst_path.exists():
                    final_filename = f"{base_name}_{counter}{extension}"
                    dst_path = dst_dir_path / final_filename
                    counter += 1
            
            shutil.copy2(src, dst_path)
            
            return True, str(dst_path), "File copied successfully"
            
        except Exception as e:
            return False, '', f"Copy error: {str(e)}"
    
    @staticmethod
    def ensure_directory(path: str, dry_run: bool = False) -> bool:
        """Ensure directory exists"""
        try:
            if dry_run:
                return True
            
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False

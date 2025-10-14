"""
File Organizer for Medical ETL System
Organizes files into patient folders with normalized naming.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

from medical_etl_system.config.config import Config


class FileOrganizer:
    """Organizes medical files into patient-specific folders"""

    def __init__(self, destination_root: Path):
        self.config = Config()
        self.destination_root = Path(destination_root)
        self.duplicates_folder = (
            self.destination_root / self.config.DUPLICATE_FOLDER_NAME
        )
        self.unmapped_folder = (
            self.destination_root / self.config.UNMAPPED_FOLDER_NAME
        )
        self.destination_root.mkdir(parents=True, exist_ok=True)
        self.duplicates_folder.mkdir(parents=True, exist_ok=True)
        self.unmapped_folder.mkdir(parents=True, exist_ok=True)
        self._organized = 0
        self._duplicates = 0
        self._unmapped = 0

    def organize_file(
        self,
        source_path: Path,
        patient_data: Dict[str, Any],
        is_duplicate: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Organize a single file into appropriate patient folder."""
        result: Dict[str, Any] = {
            'source_path': str(source_path),
            'destination_path': '',
            'action': '',
            'success': False,
            'error': None,
            'patient_folder': '',
            'new_filename': ''
        }

        try:
            if is_duplicate:
                # duplicates: keep original filename
                if self._has_sufficient_patient_data(patient_data):
                    folder_name = self._create_patient_folder_name(
                        patient_data
                    )
                    target_dir = self.duplicates_folder / folder_name
                else:
                    target_dir = self.duplicates_folder / 'unidentified'
                destination_path = target_dir / source_path.name
                result['action'] = 'moved_to_duplicates'
            elif not self._has_sufficient_patient_data(patient_data):
                # unmapped grouped by extension
                ext = source_path.suffix.lower().lstrip('.') or 'no_extension'
                target_dir = self.unmapped_folder / ext
                destination_path = target_dir / source_path.name
                result['action'] = 'moved_to_unmapped'
            else:
                # patient folder naming
                folder_name = self._create_patient_folder_name(patient_data)
                target_dir = self.destination_root / folder_name
                destination_path = target_dir / source_path.name
                result['action'] = 'organized_to_patient_folder'

            result['patient_folder'] = str(target_dir)
            result['destination_path'] = str(destination_path)
            result['new_filename'] = destination_path.name

            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                final_destination = self._resolve_filename_conflict(
                    destination_path
                )
                shutil.copy2(source_path, final_destination)
                result['destination_path'] = str(final_destination)
                result['new_filename'] = final_destination.name

            result['success'] = True
            if is_duplicate:
                self._duplicates += 1
            elif not self._has_sufficient_patient_data(patient_data):
                self._unmapped += 1
            else:
                self._organized += 1
            return result

        except Exception as e:
            result['error'] = f"Error organizing file {source_path}: {e}"
            return result

    def _has_sufficient_patient_data(
        self, patient_data: Dict[str, Any]
    ) -> bool:
        if not patient_data:
            return False
        lastname = (
            patient_data.get('lastname')
            or patient_data.get('LastName')
            or patient_data.get('last_name')
            or ''
        ).strip()
        firstname = (
            patient_data.get('firstname')
            or patient_data.get('FirstName')
            or patient_data.get('first_name')
            or ''
        ).strip()
        pid = (
            patient_data.get('id')
            or patient_data.get('patient_id')
            or patient_data.get('PatientID')
            or ''
        ).strip()
        return bool((lastname and firstname) or pid)

    def _create_patient_folder_name(self, patient_data: Dict[str, Any]) -> str:
        # Extract values with synonyms
        lastname = (
            patient_data.get('lastname')
            or patient_data.get('LastName')
            or patient_data.get('last_name')
            or ''
        ).strip().title()
        firstname = (
            patient_data.get('firstname')
            or patient_data.get('FirstName')
            or patient_data.get('first_name')
            or ''
        ).strip().title()
        dob_raw = (
            patient_data.get('dob')
            or patient_data.get('DOB')
            or patient_data.get('date_of_birth')
            or ''
        ).strip()
        pid = (
            patient_data.get('id')
            or patient_data.get('patient_id')
            or patient_data.get('PatientID')
            or ''
        ).strip()

        # Folder base
        if lastname and firstname:
            folder_name = f"{lastname}, {firstname}"
        elif pid:
            folder_name = f"Patient_{pid}"
        else:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = f"Unknown_Patient_{ts}"

        # Append DOB if parseable
        dob = self._normalize_dob(dob_raw)
        if dob:
            folder_name = f"{folder_name} {dob}"

        return self._clean_folder_name(folder_name)

    def _normalize_dob(self, dob: str) -> str:
        if not dob:
            return ''
        # Try Config INPUT_DATE_FORMATS, then safe fallbacks
        fmts = list(self.config.INPUT_DATE_FORMATS)
        fmts += ['%m-%d-%y', '%m/%d/%y', '%Y%m%d']
        for fmt in fmts:
            try:
                dt = datetime.strptime(dob, fmt)
                return dt.strftime(self.config.OUTPUT_DATE_FORMAT)
            except Exception:
                continue
        # Not parseable; return empty to avoid wrong folder naming
        return ''

    def _clean_folder_name(self, name: str) -> str:
        invalid = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for ch in invalid:
            name = name.replace(ch, '_')
        name = ' '.join(name.split())
        return name[:100]

    def _resolve_filename_conflict(self, destination_path: Path) -> Path:
        if not destination_path.exists():
            return destination_path
        base = destination_path.stem
        ext = destination_path.suffix
        parent = destination_path.parent
        idx = 1
        while idx < 1000:
            alt = parent / f"{base}_{idx:03d}{ext}"
            if not alt.exists():
                return alt
            idx += 1
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        return parent / f"{base}_{ts}{ext}"

    def get_organization_statistics(self) -> Dict[str, Any]:
        return {
            'total_organized': self._organized,
            'total_duplicates': self._duplicates,
            'total_unmapped': self._unmapped,
            'destination_root': str(self.destination_root),
            'duplicates_folder': str(self.duplicates_folder),
            'unmapped_folder': str(self.unmapped_folder),
        }

    def clear_statistics(self) -> None:
        self._organized = 0
        self._duplicates = 0
        self._unmapped = 0


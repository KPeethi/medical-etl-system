"""
Mapping Processor
Loads mapping files (Excel/CSV/JSON) and provides smart lookup
for patient information based on filename, id, etc.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

# pyright: reportMissingTypeStubs=false
import pandas as pd  # type: ignore

from medical_etl_system.config.config import Config
from .excel_mapper import ExcelMapper

logger = logging.getLogger(__name__)


class MappingProcessor:
    def __init__(self) -> None:
        self.config = Config()
        # Core dictionaries
        self.demographics: Dict[str, Dict[str, Any]] = {}
        self.documents_by_filename: Dict[str, Dict[str, Any]] = {}

    def load_mapping_files(
        self, single_mapping_file: Optional[Path] = None
    ) -> None:
        """Load mapping file(s).
        If single_mapping_file is provided, load only that; otherwise
        load any mapping files found under project's data/ folder.
        """
        sources = []
        if single_mapping_file and single_mapping_file.exists():
            sources = [single_mapping_file]
        else:
            data_dir = self.config.ROOT_DIR / 'data'
            if data_dir.exists():
                for p in data_dir.rglob('*'):
                    if p.is_file() and self.config.is_mapping_file(p):
                        sources.append(p)

        for p in sources:
            try:
                self._load_single_mapping(p)
                logger.info("Loaded mapping: %s", p)
            except Exception as e:
                logger.error("Failed loading mapping %s: %s", p, e)

    def load_mapping_from_directories(self, directories: list[Path]) -> None:
        """Scan the given directories for mapping files and load them.

        This enables auto-ingestion of JSON/CSV/Excel mapping files that
        were extracted from archives during the discovery step.
        """
        files_to_load: list[Path] = []
        for d in directories:
            try:
                if not d or not d.exists():
                    continue
                for p in d.rglob('*'):
                    if p.is_file() and self.config.is_mapping_file(p):
                        files_to_load.append(p)
            except Exception as e:
                logger.warning("Skipping mapping scan in %s: %s", d, e)
        for p in files_to_load:
            try:
                self._load_single_mapping(p)
                logger.info("Loaded mapping from extracted: %s", p)
            except Exception as e:
                logger.error("Failed loading extracted mapping %s: %s", p, e)

    def _load_single_mapping(self, path: Path) -> None:
        ext = path.suffix.lower()
        if ext in ('.xlsx', '.xls'):
            self.demographics.update(ExcelMapper.load_excel_mapping(path))
        elif ext == '.csv':
            df = pd.read_csv(path)
            self._ingest_dataframe(df)
        elif ext == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
                self._ingest_dataframe(df)
            elif isinstance(data, dict):
                # Expect id -> info mapping
                for k, v in data.items():
                    if isinstance(v, dict):
                        rec = v.copy()
                        rec['id'] = rec.get('id', k)
                        self._ingest_record(rec)
        else:
            logger.warning("Unsupported mapping file: %s", path)

    def _ingest_dataframe(self, df: pd.DataFrame) -> None:
        for _, row in df.iterrows():
            rec = {str(k): row[k] for k in df.columns}
            self._ingest_record(rec)

    def _ingest_record(self, rec: Dict[str, Any]) -> None:
        # Normalize keys
        norm = {
            str(k).strip(): ('' if pd.isna(v) else str(v).strip())
            for k, v in rec.items()
        }
        # If looks like demographics
        pid = norm.get('PatientID') or norm.get('patient_id') or norm.get('id')
        ln = norm.get('LastName') or norm.get('lastname')
        fn = norm.get('FirstName') or norm.get('firstname')
        dob = norm.get('DOB') or norm.get('dob')
        filename = norm.get('Filename') or norm.get('filename')

        if filename and (ln or fn or pid):
            key = Path(filename).name.lower()
            self.documents_by_filename[key] = {
                'id': pid or '',
                'lastname': (ln or '').title(),
                'firstname': (fn or '').title(),
                'dob': dob or '',
                'LastName': (ln or '').title(),
                'FirstName': (fn or '').title(),
                'DOB': dob or '',
            }
        if pid and (ln or fn):
            try:
                pid_str = str(int(float(pid)))
            except Exception:
                pid_str = str(pid)
            self.demographics[pid_str] = {
                'id': pid_str,
                'lastname': (ln or '').title(),
                'firstname': (fn or '').title(),
                'dob': dob or '',
                'LastName': (ln or '').title(),
                'FirstName': (fn or '').title(),
                'DOB': dob or '',
            }

    def smart_patient_lookup(self, file_path: Path) -> Dict[str, Any]:
        """Try filename-based mapping first, then ID in name, then nothing."""
        name = file_path.name.lower()
        # 1. Direct filename mapping
        if name in self.documents_by_filename:
            return {
                'found': True,
                'patient_info': self.documents_by_filename[name],
                'strategy': 'filename'
            }
        # 2. Search for id pattern and map by demographics
        pid = self._extract_id_from_name(name)
        if pid and pid in self.demographics:
            return {
                'found': True,
                'patient_info': self.demographics[pid],
                'strategy': 'id_in_name'
            }
        return {'found': False, 'patient_info': {}, 'strategy': 'none'}

    def _extract_id_from_name(self, name: str) -> Optional[str]:
        m = re.search(r'(?:^|[^\d])(\d{4,})(?:[^\d]|$)', name)
        if m:
            return m.group(1)
        return None


"""
Duplicate detector groups files by patient identity and flags potential
duplicates based on identical sizes for the same patient, except when
filenames indicate year/series.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class DuplicateDetector:
    def __init__(self):
        # map: patient_key -> list of (path, size, name)
        self._by_patient: Dict[str, List[Tuple[Path, int, str]]] = {}

    def _patient_key(self, patient_data: Dict[str, Any]) -> str:
        pid = (
            patient_data.get('id') or patient_data.get('patient_id') or ''
        ).strip()
        ln = (
            patient_data.get('lastname') or patient_data.get('LastName') or ''
        ).strip()
        fn = (
            patient_data.get('firstname')
            or patient_data.get('FirstName')
            or ''
        ).strip()
        dob = (
            patient_data.get('dob') or patient_data.get('DOB') or ''
        ).strip()
        if pid:
            return f"id:{pid}"
        if ln and fn and dob:
            return f"{ln},{fn} {dob}"
        if ln and fn:
            return f"{ln},{fn}"
        return 'unknown'

    def add_file(
        self,
        file_path: Path,
        patient_data: Dict[str, Any],
        original_path: Path,
    ):
        try:
            size = file_path.stat().st_size
            name = file_path.name
            key = self._patient_key(patient_data)
            self._by_patient.setdefault(key, []).append(
                (file_path, size, name)
            )
        except Exception as e:
            logger.error(f"DuplicateDetector add_file error: {e}")

    def detect_duplicates(self) -> Dict[str, Any]:
        exact: List[List[Any]] = []
        potential: List[List[Any]] = []
        for key, items in self._by_patient.items():
            # group by size
            by_size: Dict[int, List[Tuple[Path, int, str]]] = {}
            for (p, s, n) in items:
                by_size.setdefault(s, []).append((p, s, n))
            for size, group in by_size.items():
                if len(group) <= 1:
                    continue
                # If filenames include distinct year or series markers,
                # don't mark as exact
                years = set()
                series = 0
                for p, s, n in group:
                    y = self._extract_year(n)
                    if y:
                        years.add(y)
                    if self._is_series(n):
                        series += 1
                if len(years) > 1 or series > 0:
                    potential.append(group)
                else:
                    exact.append(group)
        return {
            'exact_duplicates': exact,
            'potential_duplicates': potential
        }

    def _extract_year(self, name: str) -> str:
        import re
        m = re.search(r"\b(20\d{2}|19\d{2})\b", name)
        return m.group(1) if m else ''

    def _is_series(self, name: str) -> bool:
        import re
        return bool(re.search(r"(_\d+|\(\d+\)|-\d+)$", name))

    def get_duplicate_report(self) -> Dict[str, Any]:
        return {
            'patients': len(self._by_patient),
        }

    def clear_cache(self):
        self._by_patient.clear()

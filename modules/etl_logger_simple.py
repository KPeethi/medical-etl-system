"""
Simple ETL Logger that captures detailed per-file and session logs.
Writes a rotating text log and a JSON session summary suitable for SSIS.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from medical_etl_system.config.config import Config

class ETLLogger:
    def __init__(self, run_type: str, level: str, source_label: str,
                 max_log_size_mb: int = 50):
        Config.ensure_directories()
        self.run_type = run_type
        self.source_label = source_label
        self.start_ts = datetime.now()
        self.session_id = self.start_ts.strftime("%Y%m%d_%H%M%S")
        self.text_log = Config.get_log_file_path(run_type, self.session_id)
        self.json_log = self.text_log.with_suffix('.json')

        self.logger = logging.getLogger(f"medical_etl.{self.session_id}")
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self.logger.handlers.clear()

        fh = logging.FileHandler(self.text_log, encoding='utf-8')
        fmt = logging.Formatter(Config.LOG_FORMAT, Config.LOG_DATE_FORMAT)
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        self.logger.addHandler(sh)

        import getpass
        self._session: Dict[str, Any] = {
            'session_id': self.session_id,
            'run_type': run_type,
            'source': source_label,
            'start_time': self.start_ts.isoformat(),
            'run_by': getpass.getuser(),
            'files': [],
            'summary': {
                'total_files_processed': 0,
                'successful_extractions': 0,
                'organized_files': 0,
                'errors': [],
                'warnings': []
            }
        }

        self.info(f"Session started. Logs: {self.text_log}")

    def get_current_stats(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'log_file': str(self.text_log)
        }

    # basic logging proxies
    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    # structured logs used by main pipeline
    def log_file_processing_start(
        self,
        source_path: str,
        file_info: Dict[str, Any],
        destination_path: Optional[str] = None,
    ) -> str:
        op_id = f"op_{len(self._session['files'])+1:06d}"
        self._session['files'].append({
            'operation_id': op_id,
            'source_path': source_path,
            'destination_path': destination_path,
            'file_info': file_info,
            'events': [
                {'ts': datetime.now().isoformat(), 'msg': 'start'}
            ]
        })
        return op_id

    def log_file_processing_end(
        self, operation_id: str, payload: Dict[str, Any]
    ):
        rec = self._find_file_record(operation_id)
        if rec is None:
            return
        rec.update({k: v for k, v in payload.items() if k not in ['events']})
        rec['events'].append({'ts': datetime.now().isoformat(), 'msg': 'end'})

    def log_mapping_operation(self, mapping_file: Path, stats: Dict[str, Any]):
        self.info(f"Loaded mapping {mapping_file} :: {stats}")

    def log_patient_parsing(self, file_path: Path, parsed: Dict[str, Any]):
        self.info(
            "Parsed patient from %s: %s, %s %s",
            file_path.name,
            parsed.get('lastname', ''),
            parsed.get('firstname', ''),
            parsed.get('dob', ''),
        )

    def log_ocr_operation(self, file_path: Path, result: Dict[str, Any]):
        self.info(
            "OCR %s: success=%s pages=%d",
            file_path.name,
            result.get('success'),
            len(result.get('pages', [])),
        )

    def log_duplicate_detection(self, duplicate_groups: Dict[str, Any]):
        self.info(f"Duplicate groups: {duplicate_groups.keys()}")

    def log_file_organization(
        self, file_path: Path, organization_result: Dict[str, Any]
    ):
        self.info(
            "Organized %s -> %s",
            file_path.name,
            organization_result.get('destination_path'),
        )

    def log_warning(
        self, where: str, msg: str, extra: Optional[Dict[str, Any]] = None
    ):
        self.warning(f"[{where}] {msg} :: {extra or {}}")
        self._session['summary']['warnings'].append({
            'where': where,
            'msg': msg,
            'extra': extra or {},
        })

    def log_error(
        self, where: str, msg: str, extra: Optional[Dict[str, Any]] = None
    ):
        self.error(f"[{where}] {msg} :: {extra or {}}")
        self._session['summary']['errors'].append({
            'where': where,
            'msg': msg,
            'extra': extra or {},
        })

    def finalize_session(self, session_summary: Dict[str, Any]):
        self._session['summary'].update({
            'total_files_processed': session_summary.get(
                'total_files_processed', 0
            ),
            'successful_extractions': session_summary.get(
                'successful_extractions', 0
            ),
            'organized_files': session_summary.get('organized_files', 0),
        })
        # include patient summaries and raw processing results
        self._session['patient_summaries'] = session_summary.get(
            'patients', {}
        )
        self._session['processing_results'] = session_summary.get(
            'processing_results', {}
        )

        try:
            with open(self.json_log, 'w', encoding='utf-8') as f:
                json.dump(self._session, f, indent=2, default=str)
        except Exception as e:
            self.error(f"Failed to write json log: {e}")

    def _find_file_record(self, op_id: str) -> Optional[Dict[str, Any]]:
        for rec in self._session['files']:
            if rec.get('operation_id') == op_id:
                return rec
        return None

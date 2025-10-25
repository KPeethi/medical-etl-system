import csv
import os
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .security import SecurityManager

class ETLLogger:
    """CSV and SQL logging for ETL events"""
    
    def __init__(
        self,
        csv_dir: str,
        run_id: str,
        session_key: str,
        db_url: Optional[str] = None,
        enable_redaction: bool = True
    ):
        self.csv_dir = csv_dir
        self.run_id = run_id
        self.session_key = session_key
        self.db_url = db_url
        self.enable_redaction = enable_redaction
        self.security = SecurityManager()
        
        self.csv_path = Path(csv_dir) / f"etl_log_{run_id}.csv"
        self.events = []
        
        self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers"""
        Path(self.csv_dir).mkdir(parents=True, exist_ok=True)
        
        headers = [
            'run_id', 'session_key', 'event_time_utc',
            'invoked_by_user', 'host_platform', 'python_version',
            'script_version', 'mode', 'practice_id',
            'src_root', 'dst_root', 'src_path', 'rel_path', 'dst_path',
            'nested_level', 'action', 'reason',
            'patient_key', 'last', 'first', 'dob', 'module',
            'file_ext', 'file_size_bytes', 'size_quick_hash', 'sha256_full',
            'provenance_id', 'config_hash'
        ]
        
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
    
    def log_event(self, event: Dict[str, Any]):
        """Log an ETL event to CSV and optionally to database"""
        event['run_id'] = self.run_id
        event['session_key'] = self.session_key
        event['event_time_utc'] = datetime.utcnow().isoformat()
        
        if self.enable_redaction:
            if 'src_path' in event:
                event['src_path'] = self.security.redact_path(event['src_path'])
            if 'dst_path' in event:
                event['dst_path'] = self.security.redact_path(event['dst_path'])
            if 'rel_path' in event:
                event['rel_path'] = self.security.redact_path(event['rel_path'])
            if 'reason' in event:
                event['reason'] = self.security.redact(event['reason'])
        
        self.events.append(event)
        
        self._append_to_csv(event)
        
        if self.db_url:
            self._log_to_db(event)
    
    def _append_to_csv(self, event: Dict[str, Any]):
        """Append event to CSV file"""
        try:
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=event.keys(), extrasaction='ignore')
                writer.writerow(event)
        except Exception as e:
            print(f"Error writing to CSV: {e}")
    
    def _log_to_db(self, event: Dict[str, Any]):
        """Log event to PostgreSQL database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            query = """
                INSERT INTO FACT_FileProcessing (
                    RunID, SessionKey, EventTimeUTC, SourcePath, DestinationPath,
                    Action, Reason, Module, FileExtension, FileSizeBytes,
                    ProvenanceID, ConfigHash, ContentHash, NestedLevel,
                    InvokedByUser, HostPlatform, PythonVersion, ScriptVersion,
                    Mode, PracticeID
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cur.execute(query, (
                event.get('run_id'),
                event.get('session_key'),
                event.get('event_time_utc'),
                event.get('src_path'),
                event.get('dst_path'),
                event.get('action'),
                event.get('reason'),
                event.get('module'),
                event.get('file_ext'),
                event.get('file_size_bytes'),
                event.get('provenance_id'),
                event.get('config_hash'),
                event.get('sha256_full'),
                event.get('nested_level'),
                event.get('invoked_by_user'),
                event.get('host_platform'),
                event.get('python_version'),
                event.get('script_version'),
                event.get('mode'),
                event.get('practice_id')
            ))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error logging to database: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate run summary"""
        action_counts = {}
        total_bytes = 0
        total_files = len(self.events)
        
        for event in self.events:
            action = event.get('action', 'UNKNOWN')
            action_counts[action] = action_counts.get(action, 0) + 1
            total_bytes += event.get('file_size_bytes', 0)
        
        return {
            'run_id': self.run_id,
            'session_key': self.session_key,
            'total_files': total_files,
            'total_bytes': total_bytes,
            'action_counts': action_counts,
            'csv_path': str(self.csv_path)
        }

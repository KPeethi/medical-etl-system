from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Dict, Any, List

from medical_etl_system.config.config import Config


def _summarize_paths(paths: List[Path]) -> Dict[str, Any]:
    cfg = Config()
    counts: Dict[str, int] = {}
    mapping_files: List[str] = []
    doc_files: List[str] = []

    for p in paths:
        ext = p.suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1
        if cfg.is_mapping_file(p):
            mapping_files.append(p.as_posix())
        if (
            cfg.is_pdf_file(p)
            or cfg.is_image_file(p)
            or cfg.is_text_file(p)
        ):
            doc_files.append(p.as_posix())

    return {
        "total_files": len(paths),
        "by_extension": counts,
        "has_mapping": len(mapping_files) > 0,
        "mapping_files": mapping_files,
        "doc_files_sample": doc_files[:10],
    }


def inspect_dataset(source: str) -> Dict[str, Any]:
    """Classify a dataset at 'source' (zip or directory).

    Returns a dict with keys: kind, summary, notes.
    """
    src = Path(source)
    cfg = Config()
    if not src.exists():
        return {"error": f"Source does not exist: {src}"}

    if src.is_file() and cfg.is_archive_file(src):
        try:
            with zipfile.ZipFile(src, "r") as zf:
                namelist = [n for n in zf.namelist() if not n.endswith("/")]
                # Build pseudo Paths to leverage extension logic
                files = [Path(n) for n in namelist]
                summary = _summarize_paths(files)
                kind = "zip"
                notes = []
                if summary["has_mapping"] and summary["total_files"] == len(
                    summary["mapping_files"]
                ):
                    msg = (
                        "Archive contains mapping only; "
                        "no supported documents found"
                    )
                    notes.append(msg)
                return {"kind": kind, "summary": summary, "notes": notes}
        except zipfile.BadZipFile:
            return {"error": f"Bad ZIP file: {src}"}
    
    # Directory: walk files
    paths: List[Path] = []
    for p in src.rglob("*"):
        if p.is_file():
            paths.append(p)
    summary = _summarize_paths(paths)
    return {"kind": "directory", "summary": summary, "notes": []}

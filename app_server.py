from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from medical_etl_system.main import MedicalETL
from medical_etl_system.modules.dataset_inspector import (
    inspect_dataset as inspect_dataset_util,
)


class RunEtlRequest(BaseModel):
    source: str = Field(
        ..., description="Source folder or file path"
    )
    dest: str = Field(
        ..., description=(
            "Destination folder (must be outside the code repository)"
        ),
    )
    mapping: Optional[str] = Field(
        None, description="Optional mapping file path"
    )
    dry_run: bool = Field(
        False, description="Dry run without copying files"
    )

    @validator("source", "dest", "mapping", pre=True, always=True)
    def normalize_paths(cls, v):  # type: ignore[override]
        if v is None:
            return v
        return str(Path(str(v)).expanduser().resolve())


class RunEtlResponse(BaseModel):
    summary: Dict[str, Any]
    log_file: Optional[str] = None


app = FastAPI(title="Medical ETL API", version="1.0.0")


def _is_inside_repo(path: Path) -> bool:
    """Return True if the given path is inside the repo root."""
    repo_root = Path(__file__).resolve().parents[1]
    try:
        path.resolve().relative_to(repo_root)
        return True
    except Exception:
        return False


@app.post("/run-etl", response_model=RunEtlResponse)
def run_etl(req: RunEtlRequest) -> RunEtlResponse:
    source = Path(req.source)
    dest = Path(req.dest)
    mapping = Path(req.mapping) if req.mapping else None

    if not source.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Source does not exist: {source}",
        )

    # Enforce: do not save output inside the repo
    if _is_inside_repo(dest):
        raise HTTPException(
            status_code=400,
            detail=(
                "Destination cannot be inside the code repository. "
                "Provide an external path."
            ),
        )

    etl = MedicalETL(source, dest, mapping, req.dry_run)
    summary = etl.run()
    return RunEtlResponse(summary=summary)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


class InspectRequest(BaseModel):
    source: str = Field(..., description="Source folder or zip file path")

    @validator("source", pre=True, always=True)
    def normalize_source(cls, v):  # type: ignore[override]
        return str(Path(str(v)).expanduser().resolve())


@app.post("/inspect")
def inspect(req: InspectRequest) -> Dict[str, Any]:
    """Inspect a dataset (directory or zip) and summarize contents."""
    src = Path(req.source)
    if not src.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Source does not exist: {src}",
        )
    report = inspect_dataset_util(str(src))
    return report

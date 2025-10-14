from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from .main import MedicalETL


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

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from .main import MedicalETL


class RunEtlRequest(BaseModel):
	source: str = Field(..., description="Source folder or file path")
	dest: str = Field(
		..., description="Destination folder (must be outside repo)"
	)
	mapping: Optional[str] = Field(
		None, description="Optional mapping file path"
	)
	dry_run: bool = Field(False, description="Dry run without copying files")

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
			status_code=400, detail=f"Source does not exist: {source}"
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

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from .main import MedicalETL


class RunEtlRequest(BaseModel):
	source: str = Field(
		..., description="Source folder or file path"
	)
	dest: str = Field(
		..., description=(
			"Destination folder (must be outside repo)"
		)
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
    # Disallow writing inside the repo (workspace root)
    # Workspace root is two levels up from this file: medical_etl_system/..
    repo_root = Path(__file__).resolve().parents[1]
    try:
        path.resolve().relative_to(repo_root)
        return True
    except Exception:
        return False


@app.post("/run-etl", response_model=RunEtlResponse)
def run_etl(req: RunEtlRequest):
	source = Path(req.source)
	dest = Path(req.dest)
	mapping = Path(req.mapping) if req.mapping else None

	if not source.exists():
		raise HTTPException(
			status_code=400,
			detail=f"Source does not exist: {source}"
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

	# Log path is written by ETLLogger internally; we don't fetch it directly
	return RunEtlResponse(summary=summary)


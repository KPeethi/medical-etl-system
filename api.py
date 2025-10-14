"""
FastAPI Application for Medical ETL System
Provides REST API endpoints for ETL operations and dataset inspection
"""

import os
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from main import MedicalETLProcessor


# API Models
class ETLRequest(BaseModel):
    """Request model for ETL process"""
    source_path: str = Field(..., description="Path to source files or directory")
    destination_path: str = Field(..., description="Path to destination directory")
    mapping_file: Optional[str] = Field(None, description="Path to mapping file (Excel/CSV)")
    dry_run: bool = Field(False, description="Perform dry run without actual file operations")
    
    @validator('source_path', 'destination_path')
    def validate_path(cls, v):
        """Validate that paths are provided"""
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v


class ETLResponse(BaseModel):
    """Response model for ETL process"""
    status: str
    session_id: str
    message: str
    results: Dict[str, Any]


class InspectRequest(BaseModel):
    """Request model for dataset inspection"""
    file_path: str = Field(..., description="Path to ZIP file to inspect")
    
    @validator('file_path')
    def validate_file_path(cls, v):
        """Validate that file path is provided"""
        if not v or not v.strip():
            raise ValueError("File path cannot be empty")
        return v


class FileInfo(BaseModel):
    """Model for file information"""
    name: str
    size: int
    path: str
    is_archive: bool
    is_image: bool
    is_pdf: bool


class InspectResponse(BaseModel):
    """Response model for dataset inspection"""
    status: str
    file_path: str
    total_files: int
    files: List[FileInfo]
    total_size_bytes: int
    total_size_mb: float
    archive_structure: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    version: str


# Initialize FastAPI app
app = FastAPI(
    title="Medical ETL System API",
    description="API for processing medical records with ETL pipeline",
    version="1.0.0"
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API information"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/v1/etl/run", response_model=ETLResponse)
async def run_etl(request: ETLRequest):
    """
    Run the ETL process
    
    This endpoint processes medical files from source to destination.
    Mapping file is optional - if not provided, the system will use OCR and filename parsing.
    """
    try:
        # Validate source path exists
        source_path = Path(request.source_path)
        if not source_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Source path does not exist: {request.source_path}"
            )
        
        # Validate destination path
        destination_path = Path(request.destination_path)
        
        # Validate mapping file if provided
        mapping_file = None
        if request.mapping_file:
            mapping_file = Path(request.mapping_file)
            if not mapping_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Mapping file does not exist: {request.mapping_file}"
                )
        
        # Initialize ETL processor
        processor = MedicalETLProcessor(
            source_path=source_path,
            destination_path=destination_path,
            mapping_file=mapping_file,
            dry_run=request.dry_run
        )
        
        # Run ETL process
        results = processor.run()
        
        # Get session info
        session_id = results.get('session_info', {}).get('session_id', 'unknown')
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "ETL process completed successfully",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running ETL process: {str(e)}"
        )


@app.post("/api/v1/dataset/inspect", response_model=InspectResponse)
async def inspect_dataset(request: InspectRequest):
    """
    Inspect a ZIP file to see its contents
    
    This endpoint allows you to inspect the structure and contents of a ZIP file
    without extracting or processing it. Useful for understanding what's inside
    before running the full ETL process.
    """
    try:
        file_path = Path(request.file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File does not exist: {request.file_path}"
            )
        
        # Validate it's a ZIP file
        if file_path.suffix.lower() != '.zip':
            raise HTTPException(
                status_code=400,
                detail=f"File must be a ZIP archive. Got: {file_path.suffix}"
            )
        
        # Inspect ZIP file
        files_info = []
        total_size = 0
        archive_structure = {}
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Get list of files
                zip_info_list = zip_ref.infolist()
                
                for zip_info in zip_info_list:
                    # Skip directories
                    if zip_info.is_dir():
                        continue
                    
                    file_name = zip_info.filename
                    file_size = zip_info.file_size
                    total_size += file_size
                    
                    # Determine file type
                    file_path_obj = Path(file_name)
                    suffix = file_path_obj.suffix.lower()
                    
                    is_archive = suffix in ['.zip', '.rar', '.7z', '.tar', '.gz']
                    is_image = suffix in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']
                    is_pdf = suffix == '.pdf'
                    
                    files_info.append(FileInfo(
                        name=file_path_obj.name,
                        size=file_size,
                        path=file_name,
                        is_archive=is_archive,
                        is_image=is_image,
                        is_pdf=is_pdf
                    ))
                    
                    # Build directory structure
                    parts = file_path_obj.parts
                    current = archive_structure
                    for i, part in enumerate(parts):
                        if i == len(parts) - 1:
                            # It's a file
                            if 'files' not in current:
                                current['files'] = []
                            current['files'].append({
                                'name': part,
                                'size': file_size,
                                'type': suffix
                            })
                        else:
                            # It's a directory
                            if 'directories' not in current:
                                current['directories'] = {}
                            if part not in current['directories']:
                                current['directories'][part] = {}
                            current = current['directories'][part]
        
        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted ZIP file"
            )
        
        return {
            "status": "success",
            "file_path": str(file_path),
            "total_files": len(files_info),
            "files": files_info,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "archive_structure": archive_structure
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inspecting dataset: {str(e)}"
        )


@app.post("/api/v1/dataset/upload-and-inspect")
async def upload_and_inspect(file: UploadFile = File(...)):
    """
    Upload and inspect a ZIP file
    
    This endpoint allows you to upload a ZIP file and immediately inspect its contents.
    The file is saved temporarily and then inspected.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="Only ZIP files are supported for upload"
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Inspect the uploaded file
            request = InspectRequest(file_path=tmp_file_path)
            result = await inspect_dataset(request)
            
            # Update file_path to show original filename
            result_dict = result.dict()
            result_dict['file_path'] = file.filename
            
            return result_dict
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading and inspecting file: {str(e)}"
        )


if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

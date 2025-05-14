# app/routes/models.py (Hybrid Approach)
"""
API routes for 3D model operations (hybrid filesystem/database approach)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import io

from ..models.model_schema import ModelMetadata, ModelList
from ..services.model_service import (
    upload_model,
    get_model_file_by_id,
    list_models_with_pagination,
    delete_model_by_id,
)

router = APIRouter(prefix="/models", tags=["3D Models"])


@router.post("/", response_model=dict)
async def upload_model_route(
    file: UploadFile = File(...),
    metadata_json: str = Form(...),
):
    """Upload a 3D model file (.fbx, .obj, .usd) with metadata"""
    try:
        # Parse metadata JSON
        metadata_dict = json.loads(metadata_json)
        metadata = ModelMetadata(**metadata_dict)

        # Upload the model
        file_id = await upload_model(file, metadata)

        return {"id": file_id, "message": "Model uploaded successfully"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ModelList)
async def list_models_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tag: Optional[str] = None,
):
    """List all 3D models with optional filtering"""
    models = await list_models_with_pagination(skip, limit, tag)
    return ModelList(models=models)


@router.get("/{model_id}", response_class=StreamingResponse)
async def get_model_by_id_route(model_id: str):
    """Get a 3D model file by its ID"""
    try:
        file_data, document = await get_model_file_by_id(model_id)

        # Determine content type
        content_type = "application/octet-stream"
        if document and "metadata" in document and "format" in document["metadata"]:
            format_ext = document["metadata"]["format"].lower()
            content_type = CONTENT_TYPES.get(format_ext, "application/octet-stream")

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={document.get('filename', 'model')}"
            },
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
async def delete_model_route(model_id: str):
    """Delete a 3D model by its ID"""
    result = await delete_model_by_id(model_id)
    return result


# Define content types here to avoid circular imports
CONTENT_TYPES = {
    "fbx": "application/octet-stream",
    "obj": "application/octet-stream",
    "usd": "application/octet-stream",
    "usda": "text/plain",
    "usdc": "application/octet-stream",
    "usdz": "application/octet-stream",
}

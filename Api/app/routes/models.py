# app/routes/models.py
"""
API routes for 3D model operations
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import io

from ..models.model_schema import ModelMetadata, ModelList
from ..services.model_service import (
    upload_model,
    get_model_by_id,
    get_model_by_name,
    list_models,
    delete_model,
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
    models = await list_models(skip, limit, tag)
    return ModelList(models=models)


@router.get("/{model_id}", response_class=StreamingResponse)
async def get_model_by_id_route(model_id: str):
    """Get a 3D model file by its ID"""
    try:
        file_data, metadata = await get_model_by_id(model_id)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename={metadata.get('filename', 'model')}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/name/{filename}", response_class=StreamingResponse)
async def get_model_by_name_route(filename: str):
    """Get a 3D model file by its filename"""
    try:
        file_data, metadata = await get_model_by_name(filename)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{model_id}")
async def delete_model_route(model_id: str):
    """Delete a 3D model by its ID"""
    result = await delete_model(model_id)
    return result

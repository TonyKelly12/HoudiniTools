# app/routes/textures.py
"""
API routes for texture operations
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional
import json
import io

from ..models.model_schema import TextureMetadata, TextureList, TextureResponse
from ..services.texture_service import (
    upload_texture, get_texture_by_id, get_texture_by_name, 
    list_textures, delete_texture
)

router = APIRouter(prefix="/textures", tags=["Textures"])

@router.post("/", response_model=dict)
async def upload_texture_route(
    file: UploadFile = File(...),
    metadata_json: str = Form(...),
):
    """Upload a texture file with metadata"""
    try:
        # Parse metadata JSON
        metadata_dict = json.loads(metadata_json)
        metadata = TextureMetadata(**metadata_dict)
        
        # Upload the texture
        file_id = await upload_texture(file, metadata)
        
        return {"id": file_id, "message": "Texture uploaded successfully"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=TextureList)
async def list_textures_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    model_id: Optional[str] = None
):
    """List all textures with optional filtering by associated model"""
    textures = await list_textures(skip, limit, model_id)
    return TextureList(textures=textures)

@router.get("/{texture_id}", response_class=StreamingResponse)
async def get_texture_by_id_route(texture_id: str):
    """Get a texture file by its ID"""
    try:
        file_data, metadata = await get_texture_by_id(texture_id)
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("content_type", "image/jpeg"),
            headers={
                "Content-Disposition": f"attachment; filename={metadata.get('filename', 'texture')}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/name/{filename}", response_class=StreamingResponse)
async def get_texture_by_name_route(filename: str):
    """Get a texture file by its filename"""
    try:
        file_data, metadata = await get_texture_by_name(filename)
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("content_type", "image/jpeg"),
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{texture_id}")
async def delete_texture_route(texture_id: str):
    """Delete a texture by its ID"""
    result = await delete_texture(texture_id)
    return result

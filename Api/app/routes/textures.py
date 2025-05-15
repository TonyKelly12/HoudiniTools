# app/routes/textures.py
"""
API routes for texture operations with weapon system support
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import io

from ..models.model_schema import (
    TextureMetadata,
    TextureList,
    TextureResponse,
    WeaponType,
    WeaponPartType,
    TextureType,
)
from ..services.texture_service import (
    upload_texture,
    get_texture_by_id,
    get_texture_by_name,
    list_textures,
    delete_texture,
    get_weapon_textures,
)

router = APIRouter(prefix="/textures", tags=["Textures"])


@router.post("/", response_model=dict)
async def upload_texture_route(
    file: UploadFile = File(...),
    metadata_json: str = Form(...),
):
    """
    Upload a texture file with metadata

    The metadata should include:
    - name: Name of the texture
    - description: Optional description
    - format: File format (jpg, png, exr, etc.)
    - associated_model: Optional ID of the associated model
    - texture_type: Type of texture (diffuse, normal, roughness, etc.)
    - resolution: Optional resolution information
    - is_tiling: Optional boolean indicating if texture tiles

    For weapon textures, also include:
    - weapon_type: Type of weapon (sword, axe, bow, etc.)
    - part_type: Type of part (handle, blade, guard, etc.)
    - variant_name: Optional variant name
    - variant_group: Optional variant group
    """
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
    model_id: Optional[str] = None,
    weapon_type: Optional[WeaponType] = None,
    part_type: Optional[WeaponPartType] = None,
    texture_type: Optional[TextureType] = None,
):
    """
    List all textures with optional filtering

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - model_id: Filter by associated model ID
    - weapon_type: Filter by weapon type
    - part_type: Filter by part type
    - texture_type: Filter by texture type
    """
    result = await list_textures(
        skip, limit, model_id, weapon_type, part_type, texture_type
    )

    return TextureList(
        textures=result["textures"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/weapon/{weapon_type}", response_model=List[TextureResponse])
async def get_weapon_textures_route(
    weapon_type: WeaponType = Path(..., description="Type of weapon"),
    part_type: Optional[WeaponPartType] = Query(None, description="Type of part"),
    texture_type: Optional[TextureType] = Query(None, description="Type of texture"),
    variant: Optional[str] = Query(None, description="Variant name"),
):
    """
    Get textures for a specific weapon type

    This endpoint is specifically for retrieving textures for weapon assembly
    """
    textures = await get_weapon_textures(weapon_type, part_type, texture_type, variant)
    return textures


@router.get("/model/{model_id}", response_model=List[TextureResponse])
async def get_textures_for_model_route(
    model_id: str = Path(..., description="ID of the model"),
    texture_type: Optional[TextureType] = Query(None, description="Type of texture"),
):
    """
    Get all textures associated with a specific model

    Parameters:
    - model_id: ID of the model
    - texture_type: Optional filter by texture type
    """
    result = await list_textures(0, 1000, model_id, None, None, texture_type)
    return result["textures"]


@router.get("/{texture_id}", response_class=StreamingResponse)
async def get_texture_by_id_route(
    texture_id: str = Path(..., description="ID of the texture to retrieve")
):
    """
    Get a texture file by its ID

    Returns the actual texture file with the appropriate content type
    """
    try:
        file_data, metadata = await get_texture_by_id(texture_id)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("metadata", {}).get("content_type", "image/jpeg"),
            headers={
                "Content-Disposition": f"attachment; filename={metadata.get('filename', 'texture')}"
            },
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/metadata/{texture_id}", response_model=TextureResponse)
async def get_texture_metadata_route(
    texture_id: str = Path(..., description="ID of the texture")
):
    """
    Get a texture's metadata without downloading the file

    Returns detailed information about the texture
    """
    try:
        _, document = await get_texture_by_id(texture_id)

        # Convert to response model
        response = TextureResponse(
            id=str(document["_id"]),
            filename=document["filename"],
            metadata=TextureMetadata(**document["metadata"]),
            uploaded_at=document["uploaded_at"],
            size=document["size"],
            file_path=document.get("relative_path", ""),
        )

        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/name/{filename}", response_class=StreamingResponse)
async def get_texture_by_name_route(
    filename: str = Path(..., description="Filename of the texture")
):
    """
    Get a texture file by its filename

    Returns the actual texture file with the appropriate content type
    """
    try:
        file_data, metadata = await get_texture_by_name(filename)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata.get("metadata", {}).get("content_type", "image/jpeg"),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{texture_id}")
async def delete_texture_route(
    texture_id: str = Path(..., description="ID of the texture to delete")
):
    """
    Delete a texture by its ID

    Removes both the file and its metadata
    """
    result = await delete_texture(texture_id)
    return result

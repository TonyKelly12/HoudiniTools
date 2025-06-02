# app/services/texture_service.py
"""
Service layer for texture operations with weapon system support
"""
import os
import re
from bson.errors import InvalidId
from fastapi import UploadFile, HTTPException
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..database import (
    textures_collection,
    store_texture_file,
    get_texture_by_id as get_texture_by_id_db,
    list_textures as list_textures_db,
    delete_texture as delete_texture_db,
)
from ..models.model_schema import (
    TextureMetadata,
    TextureResponse,
    WeaponType,
    WeaponPartType,
    TextureType,
)

# Content types mapping
TEXTURE_CONTENT_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "exr": "application/octet-stream",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "hdr": "application/octet-stream",
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to ensure it's valid and follows conventions
    - Replace spaces with underscores
    - Remove special characters except underscores and hyphens
    - Convert to lowercase
    """
    # Get base name and extension
    base_name, extension = os.path.splitext(filename)

    # Remove special characters and replace spaces
    base_name = re.sub(r"[^\w\-]", "", base_name.replace(" ", "_"))

    # Convert to lowercase
    sanitized = f"{base_name.lower()}{extension.lower()}"

    return sanitized


def generate_texture_path(metadata: TextureMetadata) -> str:
    """
    Generate a standardized path for storing the texture based on metadata
    Format for weapon textures: /{weapon_type}/{part_type}/{texture_type}/
    Format for other textures: /materials/{texture_type}/
    """
    # For weapon-associated textures
    if metadata.weapon_type and metadata.part_type:
        weapon_type = metadata.weapon_type.value
        part_type = metadata.part_type.value
        texture_type = metadata.texture_type.value

        # Add variant info if available
        if metadata.variant_name:
            variant = metadata.variant_name.lower()
            return f"{weapon_type}/{part_type}/variants/{variant}/{texture_type}"

        return f"{weapon_type}/{part_type}/{texture_type}"

    # For textures associated with a specific model but not a weapon part
    elif metadata.associated_model:
        # Just organize by texture type and associated model ID (shortened)
        texture_type = metadata.texture_type.value
        model_id = metadata.associated_model[:8]  # First 8 chars of ID
        return f"materials/{texture_type}/{model_id}"

    # For general textures
    else:
        texture_type = metadata.texture_type.value
        return f"materials/{texture_type}"


async def upload_texture(file: UploadFile, metadata: TextureMetadata):
    """Upload a texture file to the filesystem and store metadata in MongoDB"""
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in TEXTURE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported texture format. Supported formats: {', '.join(TEXTURE_CONTENT_TYPES.keys())}",
        )

    # Set content type based on extension
    content_type = TEXTURE_CONTENT_TYPES.get(file_ext, "application/octet-stream")

    # Read file content
    file_data = await file.read()

    # Update metadata with file format if not already set
    if not metadata.format:
        metadata.format = file_ext

    # Sanitize the filename
    sanitized_filename = sanitize_filename(file.filename)

    # Generate the proper storage path
    storage_path = generate_texture_path(metadata)

    # Add timestamp to filename to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name, extension = os.path.splitext(sanitized_filename)
    unique_filename = f"{base_name}_{timestamp}{extension}"

    # Additional metadata for the database
    additional_metadata = {
        "original_filename": file.filename,
        "sanitized_filename": sanitized_filename,
        "storage_path": storage_path,
        "content_type": content_type,
        "unique_filename": unique_filename,
    }

    # Add content type to metadata for later retrieval
    metadata_dict = metadata.model_dump()
    metadata_dict.update(additional_metadata)

    # Store the file in filesystem and metadata in MongoDB
    file_id, _ = await store_texture_file(
        file_data, unique_filename, metadata_dict, storage_path
    )

    # Return file ID as string
    return file_id


async def get_texture_by_id(texture_id: str):
    """Get a texture by its ID"""
    try:
        # file_id = ObjectId(texture_id)
        pass
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid texture ID format")

    try:
        # Get file path and metadata from database
        file_path, metadata = await get_texture_by_id_db(texture_id)

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Texture file not found")

        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()

        return file_data, metadata
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")


async def get_texture_by_name(filename: str):
    """Get a texture by its filename"""
    try:
        # Query MongoDB for the texture with the given filename
        document = await textures_collection.find_one({"filename": filename})

        if not document:
            raise HTTPException(status_code=404, detail="Texture not found")

        file_path = document["file_path"]

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail="Texture file not found on disk"
            )

        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()

        return file_data, document
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")


async def list_textures(
    skip: int = 0,
    limit: int = 100,
    model_id: str = None,
    weapon_type: Optional[WeaponType] = None,
    part_type: Optional[WeaponPartType] = None,
    texture_type: Optional[TextureType] = None,
) -> Dict[str, Any]:
    """List all textures with optional filtering"""
    # Build filters
    filters = {}

    if model_id:
        filters["metadata.associated_model"] = model_id

    if weapon_type:
        filters["metadata.weapon_type"] = weapon_type.value

    if part_type:
        filters["metadata.part_type"] = part_type.value

    if texture_type:
        filters["metadata.texture_type"] = texture_type.value

    # Use the database function to get textures
    documents, total_count = await list_textures_db(skip, limit, filters)

    textures = []
    for doc in documents:
        textures.append(
            TextureResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                metadata=TextureMetadata(**doc["metadata"]),
                uploaded_at=doc["uploaded_at"],
                size=doc["size"],
                file_path=doc.get("relative_path", ""),
            )
        )

    return {
        "textures": textures,
        "total": total_count,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


async def get_weapon_textures(
    weapon_type: WeaponType,
    part_type: Optional[WeaponPartType] = None,
    texture_type: Optional[TextureType] = None,
    variant: Optional[str] = None,
) -> List[TextureResponse]:
    """Get textures for a specific weapon type, optionally filtered by part and texture type"""
    # Build filters
    filters = {"metadata.weapon_type": weapon_type.value}

    if part_type:
        filters["metadata.part_type"] = part_type.value

    if texture_type:
        filters["metadata.texture_type"] = texture_type.value

    if variant:
        filters["metadata.variant_name"] = variant

    # No pagination for this specific query
    documents, _ = await list_textures_db(0, 1000, filters)

    textures = []
    for doc in documents:
        textures.append(
            TextureResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                metadata=TextureMetadata(**doc["metadata"]),
                uploaded_at=doc["uploaded_at"],
                size=doc["size"],
                file_path=doc.get("relative_path", ""),
            )
        )

    return textures


async def delete_texture(texture_id: str):
    """Delete a texture by its ID"""
    try:
        # Use the database function to delete the texture
        result = await delete_texture_db(texture_id)

        if result:
            return {"message": "Texture deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Texture not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid texture ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting texture: {str(e)}")

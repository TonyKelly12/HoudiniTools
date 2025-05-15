# app/services/texture_service.py
"""
Service layer for texture operations
"""
from bson.objectid import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, HTTPException
import io
import os

from ..database import (
    textures_collection,
    TEXTURES_DIR,
    store_texture_file,
    get_texture_by_id as get_texture_by_id_db,
    list_textures as list_textures_db,
    delete_texture as delete_texture_db,
)
from ..models.model_schema import TextureMetadata, TextureResponse

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

    # Add content type to metadata for later retrieval
    metadata_dict = metadata.model_dump()
    metadata_dict["content_type"] = content_type

    # Store the file in filesystem and metadata in MongoDB
    file_id, _ = await store_texture_file(file_data, file.filename, metadata_dict)

    # Return file ID as string
    return file_id


async def get_texture_by_id(texture_id: str):
    """Get a texture by its ID"""
    try:
        file_id = ObjectId(texture_id)
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
            raise HTTPException(status_code=404, detail="Texture file not found on disk")
        
        # Read file data
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        return file_data, document
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")


async def list_textures(skip: int = 0, limit: int = 100, model_id: str = None):
    """List all textures with optional filtering by associated model"""
    # Use the database function to get textures
    documents = await list_textures_db(skip, limit, model_id)
    
    textures = []
    for doc in documents:
        textures.append(
            TextureResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                metadata=TextureMetadata(**doc["metadata"]),
                uploaded_at=doc["uploaded_at"],
                size=doc["size"],
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

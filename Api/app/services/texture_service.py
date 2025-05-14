# app/services/texture_service.py
"""
Service layer for texture operations
"""
from bson.objectid import ObjectId
from fastapi import UploadFile, HTTPException
import io

from ..database import texture_fs, store_file_to_gridfs, get_file_from_gridfs, get_file_by_name
from ..models.model_schema import TextureMetadata, TextureResponse

# Content types mapping
TEXTURE_CONTENT_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'exr': 'application/octet-stream',
    'tif': 'image/tiff',
    'tiff': 'image/tiff',
    'hdr': 'application/octet-stream',
}

async def upload_texture(file: UploadFile, metadata: TextureMetadata):
    """Upload a texture to GridFS"""
    # Validate file extension
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in TEXTURE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported texture format. Supported formats: {', '.join(TEXTURE_CONTENT_TYPES.keys())}")
    
    # Set content type based on extension
    content_type = TEXTURE_CONTENT_TYPES.get(file_ext, 'application/octet-stream')
    
    # Read file content
    file_data = await file.read()
    
    # Update metadata with file format if not already set
    if not metadata.format:
        metadata.format = file_ext
    
    # Store the file in GridFS
    file_id = await store_file_to_gridfs(
        texture_fs,
        file.filename,
        io.BytesIO(file_data),
        content_type,
        metadata.model_dump()
    )
    
    # Return file ID as string
    return str(file_id)

async def get_texture_by_id(texture_id: str):
    """Get a texture by its ID"""
    try:
        file_id = ObjectId(texture_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid texture ID format")
    
    try:
        file_data, metadata = await get_file_from_gridfs(texture_fs, file_id)
        return file_data, metadata
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")

async def get_texture_by_name(filename: str):
    """Get a texture by its filename"""
    try:
        file_data, metadata = await get_file_by_name(texture_fs, filename)
        if not file_data:
            raise HTTPException(status_code=404, detail="Texture not found")
        return file_data, metadata
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")

async def list_textures(skip: int = 0, limit: int = 100, model_id: str = None):
    """List all textures with optional filtering by associated model"""
    query = {} if not model_id else {"metadata.associated_model": model_id}
    cursor = texture_fs.find(query)
    
    # Skip and limit for pagination
    cursor.skip(skip)
    cursor.limit(limit)
    
    textures = []
    async for texture in cursor:
        textures.append(TextureResponse(
            id=str(texture._id),
            filename=texture.filename,
            metadata=TextureMetadata(**texture.metadata),
            uploaded_at=texture.upload_date,
            size=texture.length
        ))
    
    return textures

async def delete_texture(texture_id: str):
    """Delete a texture by its ID"""
    try:
        file_id = ObjectId(texture_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid texture ID format")
    
    try:
        await texture_fs.delete(file_id)
        return {"message": "Texture deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Texture not found: {str(e)}")

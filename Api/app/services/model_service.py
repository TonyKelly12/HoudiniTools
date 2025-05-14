# app/services/model_service.py
"""
Service layer for 3D model operations
"""
from bson.objectid import ObjectId
from fastapi import UploadFile, HTTPException
import io

from ..database import model_fs, store_file_to_gridfs, get_file_from_gridfs, get_file_by_name
from ..models.model_schema import ModelMetadata, ModelResponse

# Content types mapping
CONTENT_TYPES = {
    'fbx': 'application/octet-stream',
    'obj': 'application/octet-stream',
    'usd': 'application/octet-stream',
    'usda': 'text/plain',
    'usdc': 'application/octet-stream',
    'usdz': 'application/octet-stream',
}

async def upload_model(file: UploadFile, metadata: ModelMetadata):
    """Upload a 3D model to GridFS"""
    # Validate file extension
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['fbx', 'obj', 'usd', 'usda', 'usdc', 'usdz']:
        raise HTTPException(status_code=400, detail="Unsupported file format. Must be .fbx, .obj, or .usd format")
    
    # Set content type based on extension
    content_type = CONTENT_TYPES.get(file_ext, 'application/octet-stream')
    
    # Read file content
    file_data = await file.read()
    
    # Update metadata with file format if not already set
    if not metadata.format:
        metadata.format = file_ext
    
    # Store the file in GridFS
    file_id = await store_file_to_gridfs(
        model_fs,
        file.filename,
        io.BytesIO(file_data),
        content_type,
        metadata.model_dump()
    )
    
    # Return file ID as string
    return str(file_id)

async def get_model_by_id(model_id: str):
    """Get a 3D model by its ID"""
    try:
        file_id = ObjectId(model_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid model ID format")
    
    try:
        file_data, metadata = await get_file_from_gridfs(model_fs, file_id)
        return file_data, metadata
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}")

async def get_model_by_name(filename: str):
    """Get a 3D model by its filename"""
    try:
        file_data, metadata = await get_file_by_name(model_fs, filename)
        if not file_data:
            raise HTTPException(status_code=404, detail="Model not found")
        return file_data, metadata
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}")

async def list_models(skip: int = 0, limit: int = 100, tag: str = None):
    """List all 3D models with optional filtering by tag"""
    cursor = model_fs.find({} if not tag else {"metadata.tags": tag})
    
    # Skip and limit for pagination
    cursor.skip(skip)
    cursor.limit(limit)
    
    models = []
    async for model in cursor:
        models.append(ModelResponse(
            id=str(model._id),
            filename=model.filename,
            metadata=ModelMetadata(**model.metadata),
            uploaded_at=model.upload_date,
            size=model.length
        ))
    
    return models

async def delete_model(model_id: str):
    """Delete a 3D model by its ID"""
    try:
        file_id = ObjectId(model_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid model ID format")
    
    try:
        await model_fs.delete(file_id)
        return {"message": "Model deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Model not found: {str(e)}")

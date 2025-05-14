# app/services/model_service.py (Hybrid Approach)
"""
Service layer for 3D model operations (hybrid filesystem/database approach)
"""
from fastapi import UploadFile, HTTPException
from bson.objectid import ObjectId
from bson.errors import InvalidId

from ..database import store_model_file, get_model_by_id, list_models, delete_model
from ..models.model_schema import ModelMetadata, ModelResponse

# Content types mapping
CONTENT_TYPES = {
    "fbx": "application/octet-stream",
    "obj": "application/octet-stream",
    "usd": "application/octet-stream",
    "usda": "text/plain",
    "usdc": "application/octet-stream",
    "usdz": "application/octet-stream",
}


async def upload_model(file: UploadFile, metadata: ModelMetadata):
    """Upload a 3D model to filesystem and store metadata in database"""
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["fbx", "obj", "usd", "usda", "usdc", "usdz"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Must be .fbx, .obj, or .usd format",
        )

    # Read file content
    file_data = await file.read()

    # Update metadata with file format if not already set
    if not metadata.format:
        metadata.format = file_ext

    # Store the file and metadata
    file_id, file_path = await store_model_file(
        file_data, file.filename, metadata.model_dump()
    )

    # Return file ID as string
    return file_id


async def get_model_file_by_id(model_id: str):
    """Get a 3D model file by its ID"""
    try:
        # Try to convert to ObjectId to validate format
        _ = ObjectId(model_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid model ID format")

    # Get file path and metadata from database
    file_path, document = await get_model_by_id(model_id)

    if not file_path or not document:
        raise HTTPException(status_code=404, detail="Model not found")

    # Read file from filesystem
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found in storage")
    except PermissionError:
        raise HTTPException(
            status_code=500, detail="Permission denied when accessing model file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading model file: {str(e)}"
        )

    return file_data, document


async def list_models_with_pagination(skip: int = 0, limit: int = 100, tag: str = None):
    """List all 3D models with optional filtering by tag"""
    # Get documents from database
    documents = await list_models(skip, limit, tag)

    # Convert to response model
    models = []
    for doc in documents:
        model = ModelResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            metadata=ModelMetadata(**doc["metadata"]),
            uploaded_at=doc["uploaded_at"],
            size=doc["size"],
        )
        models.append(model)

    return models


async def delete_model_by_id(model_id: str):
    """Delete a 3D model by its ID (both file and metadata)"""
    try:
        # Try to convert to ObjectId to validate format
        _ = ObjectId(model_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid model ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating model ID: {str(e)}")

    # Delete the model
    success = await delete_model(model_id)

    if not success:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"message": "Model deleted successfully"}

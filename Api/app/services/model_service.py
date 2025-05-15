# app/services/model_service.py
"""
Service layer for 3D model operations with weapon system support
"""
import os
import re
from fastapi import UploadFile, HTTPException
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..database import store_model_file, get_model_by_id, list_models, delete_model
from ..models.model_schema import (
    ModelMetadata,
    ModelResponse,
    WeaponType,
    WeaponPartType,
)

# Content types mapping
CONTENT_TYPES = {
    "fbx": "application/octet-stream",
    "obj": "application/octet-stream",
    "usd": "application/octet-stream",
    "usda": "text/plain",
    "usdc": "application/octet-stream",
    "usdz": "application/octet-stream",
    "glb": "model/gltf-binary",
    "gltf": "model/gltf+json",
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


def generate_model_path(metadata: ModelMetadata) -> str:
    """
    Generate a standardized path for storing the model based on metadata
    Format: /{category}/{weapon_type}/{part_type}/{name}
    """
    # Default category if not specified
    category = metadata.category or "misc"

    if metadata.is_weapon_part and metadata.weapon_part_metadata:
        weapon_type = metadata.weapon_part_metadata.weapon_type.value
        part_type = metadata.weapon_part_metadata.part_type.value

        # Add variant info if available
        if metadata.weapon_part_metadata.variant_name:
            variant = metadata.weapon_part_metadata.variant_name.lower()
            return f"{category}/{weapon_type}/{part_type}/variants/{variant}"

        return f"{category}/{weapon_type}/{part_type}"
    else:
        # For non-weapon models
        if metadata.tags and len(metadata.tags) > 0:
            # Use first tag as subdirectory
            return f"{category}/{metadata.tags[0].lower()}"

        return f"{category}/misc"


async def upload_model(file: UploadFile, metadata: ModelMetadata) -> str:
    """Upload a 3D model to filesystem and store metadata in database"""
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in CONTENT_TYPES.keys():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Must be one of: {', '.join(CONTENT_TYPES.keys())}",
        )

    # Read file content
    file_data = await file.read()

    # Update metadata with file format if not already set
    if not metadata.format:
        metadata.format = file_ext

    # Sanitize the filename
    sanitized_filename = sanitize_filename(file.filename)

    # Validate weapon part metadata if applicable
    if metadata.is_weapon_part and not metadata.weapon_part_metadata:
        raise HTTPException(
            status_code=400,
            detail="Weapon part metadata is required when is_weapon_part is true",
        )

    # Generate the proper storage path
    storage_path = generate_model_path(metadata)

    # Add timestamp to filename to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name, extension = os.path.splitext(sanitized_filename)
    unique_filename = f"{base_name}_{timestamp}{extension}"

    # Additional metadata for the database
    additional_metadata = {
        "original_filename": file.filename,
        "sanitized_filename": sanitized_filename,
        "storage_path": storage_path,
        "content_type": CONTENT_TYPES.get(file_ext, "application/octet-stream"),
        "unique_filename": unique_filename,
    }

    # Store the file and metadata
    metadata_dict = metadata.model_dump()
    metadata_dict.update(additional_metadata)

    # Pass path info to database layer
    file_id, file_path = await store_model_file(
        file_data, unique_filename, metadata_dict, storage_path
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


async def list_models_with_pagination(
    skip: int = 0,
    limit: int = 100,
    tag: Optional[str] = None,
    weapon_type: Optional[WeaponType] = None,
    part_type: Optional[WeaponPartType] = None,
    category: Optional[str] = None,
    is_weapon_part: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    List all 3D models with optional filtering
    Returns a Dict with models list and pagination info
    """
    # Build query based on filters
    filters = {}

    if tag:
        filters["metadata.tags"] = tag

    if category:
        filters["metadata.category"] = category

    if is_weapon_part is not None:
        filters["metadata.is_weapon_part"] = is_weapon_part

    if weapon_type:
        filters["metadata.weapon_part_metadata.weapon_type"] = weapon_type.value

    if part_type:
        filters["metadata.weapon_part_metadata.part_type"] = part_type.value

    # Get documents from database with count
    documents, total_count = await list_models(skip, limit, filters)

    # Convert to response model
    models = []
    for doc in documents:
        model = ModelResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            metadata=ModelMetadata(**doc["metadata"]),
            uploaded_at=doc["uploaded_at"],
            size=doc["size"],
            file_path=doc.get("relative_path", ""),
        )
        models.append(model)

    return {
        "models": models,
        "total": total_count,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


async def get_weapon_parts(
    weapon_type: WeaponType, part_type: Optional[WeaponPartType] = None
) -> List[ModelResponse]:
    """Get all parts for a specific weapon type, optionally filtered by part type"""
    filters = {
        "metadata.is_weapon_part": True,
        "metadata.weapon_part_metadata.weapon_type": weapon_type.value,
    }

    if part_type:
        filters["metadata.weapon_part_metadata.part_type"] = part_type.value

    # No pagination for this specific query - we want all parts
    documents, _ = await list_models(0, 1000, filters)

    # Convert to response model
    parts = []
    for doc in documents:
        part = ModelResponse(
            id=str(doc["_id"]),
            filename=doc["filename"],
            metadata=ModelMetadata(**doc["metadata"]),
            uploaded_at=doc["uploaded_at"],
            size=doc["size"],
            file_path=doc.get("relative_path", ""),
        )
        parts.append(part)

    return parts


async def delete_model_by_id(model_id: str):
    """Delete a 3D model by its ID (both file and metadata)"""
    try:
        # Try to convert to ObjectId to validate format
        _ = ObjectId(model_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid model ID format")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error validating model ID: {str(e)}"
        )

    # Delete the model
    success = await delete_model(model_id)

    if not success:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"message": "Model deleted successfully"}

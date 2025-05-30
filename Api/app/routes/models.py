# app/routes/models.py (Updated icon handling)
"""
API routes for 3D model operations with weapon system support
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Path
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import io
import os
import uuid
from PIL import Image  # Add Pillow for image processing

from ..config import STORAGE_BASE_DIR

from ..models.model_schema import (
    ModelMetadata,
    ModelList,
    WeaponType,
    WeaponPartType,
    ModelResponse,
)
from ..services.model_service import (
    upload_model,
    get_model_file_by_id,
    list_models_with_pagination,
    delete_model_by_id,
    get_weapon_parts,
)

router = APIRouter(prefix="/models", tags=["3D Models"])

# Content types mapping - Define here to avoid circular imports
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


def create_default_jpeg():
    """Create a 1x1 transparent JPEG image"""
    img = Image.new('RGB', (1, 1), (255, 255, 255))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()


def get_default_jpeg():
    """Load the default JPEG image data"""
    default_icon_path = os.path.join(STORAGE_BASE_DIR, "icons", "default.jpg")
    if not os.path.exists(default_icon_path):
        # Create a simple default icon (1x1 transparent pixel)
        os.makedirs(os.path.dirname(default_icon_path), exist_ok=True)
        with open(default_icon_path, "wb") as f:
            f.write(create_default_jpeg())
    with open(default_icon_path, "rb") as f:
        return f.read()


@router.post("/", response_model=dict)
async def upload_model_route(
    file: UploadFile = File(...),
    icon: UploadFile = File(...),
    metadata_json: str = Form(...),
):
    """
    Upload a 3D model file with metadata

    The metadata should include:
    - name: Name of the model
    - description: Optional description
    - format: File format (fbx, obj, usd, etc.)
    - tags: Optional list of tags
    - category: Optional category (defaults to "misc")
    - is_weapon_part: Boolean indicating if this is a weapon part

    For weapon parts, include weapon_part_metadata with:
    - weapon_type: Type of weapon (sword, axe, bow, etc.)
    - part_type: Type of part (handle, blade, guard, etc.)
    - is_attachment: Optional boolean
    - attachment_points: Optional list of attachment point names
    - slot_id: Optional slot identifier
    - material_slots: Optional list of material slot names
    - variant_name: Optional variant name
    - variant_group: Optional variant group
    """
    try:
        # Parse metadata JSON
        metadata_dict = json.loads(metadata_json)
        metadata = ModelMetadata(**metadata_dict)

        # Process icon file
        icon_data = await icon.read()
        icon_filename = f"icon_{uuid.uuid4()}.png"
        icon_dir = os.path.join(STORAGE_BASE_DIR, "icons")

        # Create icons directory if it doesn't exist
        os.makedirs(icon_dir, exist_ok=True)

        icon_path = os.path.join(icon_dir, icon_filename)

        # Save icon file - Use PIL to ensure valid PNG format
        try:
            # Create a temporary file for the uploaded icon
            temp_icon_path = os.path.join(icon_dir, f"temp_{icon_filename}")
            with open(temp_icon_path, "wb") as f:
                f.write(icon_data)

            # Open and save with PIL to ensure proper formatting
            img = Image.open(temp_icon_path)
            img.save(icon_path, format="PNG")

            # Clean up the temporary file
            os.remove(temp_icon_path)
        except Exception as e:
            # If there's any error processing the icon, use a default one
            print(f"Error processing icon: {str(e)}")
            # Create a default icon
            serve_default_icon(icon_path)

        # Upload the model with icon path
        file_id = await upload_model(file, icon_path, metadata)

        return {"id": file_id, "message": "Model uploaded successfully"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/icons/{model_id}", response_class=StreamingResponse)
async def get_model_icon_route(
    model_id: str = Path(..., description="ID of the model")
):
    """Get a model's icon image by its ID with improved format handling"""
    # Get model metadata
    try:
        _, document = await get_model_file_by_id(model_id)

        if (
            not document
            or "metadata" not in document
            or "icon_path" not in document["metadata"]
        ):
            # Return default icon
            return serve_default_icon()

        # Get icon path from metadata
        icon_path = document["metadata"]["icon_path"]
        full_path = os.path.join(STORAGE_BASE_DIR, icon_path.lstrip("/"))

        # Check if the file exists
        if not os.path.exists(full_path):
            return serve_default_icon()

        # Use Pillow to validate and convert the image if needed
        try:
            with Image.open(full_path) as img:
                # Convert to RGB if image is in RGBA mode with transparency
                if img.mode == "RGBA":
                    # Create a white background
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    # Paste the image on the background
                    background.paste(img, mask=img.split()[3])
                    img = background

                # Determine format (send as JPEG for better compatibility)
                img_format = "JPEG"
                content_type = "image/jpeg"

                # Use BytesIO to avoid disk I/O
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=img_format, quality=85)
                img_byte_arr.seek(0)

                return StreamingResponse(img_byte_arr, media_type=content_type)
        except Exception as e:
            print(f"Error processing icon image: {str(e)}")
            return serve_default_icon()

    except Exception as e:
        print(f"Error getting model icon: {str(e)}")
        return serve_default_icon()


def serve_default_icon():
    """Create and serve a valid default icon"""
    try:
        # Create a simple colored image using PIL
        img = Image.new("RGB", (120, 120), color=(73, 109, 137))

        # Draw some text on it
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)

        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            font = ImageFont.load_default()

        draw.text((20, 50), "No Preview", fill=(255, 255, 255), font=font)

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG", quality=95)
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/jpeg")
    except Exception as e:
        print(f"Error creating default icon: {str(e)}")

        # Last resort - create a tiny valid JPG
        return StreamingResponse(
            io.BytesIO(get_default_jpeg()),
            media_type="image/jpeg",
        )


# Rest of the file remains the same...
@router.get("/", response_model=ModelList)
async def list_models_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tag: Optional[str] = None,
    category: Optional[str] = None,
    is_weapon_part: Optional[bool] = None,
    weapon_type: Optional[WeaponType] = None,
    part_type: Optional[WeaponPartType] = None,
):
    """
    List all 3D models with optional filtering

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - tag: Filter by tag
    - category: Filter by category
    - is_weapon_part: Filter for weapon parts only
    - weapon_type: Filter by weapon type (only for weapon parts)
    - part_type: Filter by part type (only for weapon parts)
    """
    result = await list_models_with_pagination(
        skip, limit, tag, weapon_type, part_type, category, is_weapon_part
    )

    return ModelList(
        models=result["models"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/weapon-parts", response_model=List[ModelResponse])
async def get_weapon_parts_route(
    weapon_type: WeaponType = Query(..., description="Type of weapon"),
    part_type: Optional[WeaponPartType] = Query(None, description="Type of part"),
):
    """
    Get all parts for a specific weapon type, optionally filtered by part type

    This endpoint is specifically for retrieving weapon parts for assembly
    """
    parts = await get_weapon_parts(weapon_type, part_type)
    return parts


@router.get("/{model_id}", response_class=StreamingResponse)
async def get_model_by_id_route(
    model_id: str = Path(..., description="ID of the model to retrieve")
):
    """
    Get a 3D model file by its ID

    Returns the actual model file with the appropriate content type
    """
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


@router.get("/metadata/{model_id}", response_model=ModelResponse)
async def get_model_metadata_route(
    model_id: str = Path(..., description="ID of the model")
):
    """
    Get a 3D model's metadata without downloading the file

    Returns detailed information about the model
    """
    try:
        _, document = await get_model_file_by_id(model_id)

        # Convert to response model
        response = ModelResponse(
            id=str(document["_id"]),
            filename=document["filename"],
            metadata=ModelMetadata(**document["metadata"]),
            uploaded_at=document["uploaded_at"],
            size=document["size"],
            file_path=document.get("relative_path", ""),
        )

        return response
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
async def delete_model_route(
    model_id: str = Path(..., description="ID of the model to delete")
):
    """
    Delete a 3D model by its ID

    Removes both the file and its metadata
    """
    result = await delete_model_by_id(model_id)
    return result

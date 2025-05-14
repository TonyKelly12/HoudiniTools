# app/utils/helpers.py
"""
Helper functions for the application
"""

from fastapi import UploadFile
from typing import Dict, Any


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename"""
    return filename.split(".")[-1].lower() if "." in filename else ""


def is_valid_model_file(filename: str) -> bool:
    """Check if the file is a valid 3D model file"""
    valid_extensions = ["fbx", "obj", "usd", "usda", "usdc", "usdz"]
    extension = get_file_extension(filename)
    return extension in valid_extensions


def is_valid_texture_file(filename: str) -> bool:
    """Check if the file is a valid texture file"""
    valid_extensions = ["jpg", "jpeg", "png", "exr", "tif", "tiff", "hdr"]
    extension = get_file_extension(filename)
    return extension in valid_extensions


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to a human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


async def extract_file_metadata(file: UploadFile) -> Dict[str, Any]:
    """Extract basic metadata from a file"""
    # Read first 1024 bytes to determine file type
    # (in a real implementation, you would use libraries like python-magic for better detection)
    # first_bytes = await file.read(1024)
    # Make sure to reset the file position after reading
    await file.seek(0)

    extension = get_file_extension(file.filename)

    metadata = {
        "filename": file.filename,
        "content_type": file.content_type,
        "extension": extension,
    }

    return metadata

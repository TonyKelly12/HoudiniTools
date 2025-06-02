# app/database.py
"""
MongoDB connection for metadata storage with filesystem for files
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from typing import Tuple, List, Dict, Any

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "model_database")

# File storage settings
STORAGE_BASE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.getcwd(), "storage"))
MODELS_DIR = os.path.join(STORAGE_BASE_DIR, "models")
TEXTURES_DIR = os.path.join(STORAGE_BASE_DIR, "textures")
ASSEMBLIES_DIR = os.path.join(STORAGE_BASE_DIR, "assemblies")

# Create storage directories if they don't exist
Path(MODELS_DIR).mkdir(parents=True, exist_ok=True)
Path(TEXTURES_DIR).mkdir(parents=True, exist_ok=True)
Path(ASSEMBLIES_DIR).mkdir(parents=True, exist_ok=True)

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGO_URI)
db = async_client[DATABASE_NAME]

# Collections for metadata
models_collection = db.models
textures_collection = db.textures
assemblies_collection = db.assemblies


# Generate a unique filename for storage
def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    extension = original_filename.split(".")[-1] if "." in original_filename else ""
    unique_id = str(uuid.uuid4())
    if extension:
        return f"{unique_id}.{extension}"
    return unique_id


async def store_file_to_filesystem(file_data, directory, filename, subpath=None):
    """
    Store a file on the filesystem with a specific path structure
    Returns the unique filename and full path
    """
    # Create full directory path including subpath if provided
    if subpath:
        full_dir = os.path.join(directory, subpath)
        # Create the directory if it doesn't exist
        Path(full_dir).mkdir(parents=True, exist_ok=True)
    else:
        full_dir = directory

    # Full path where the file will be stored
    file_path = os.path.join(full_dir, filename)

    # Relative path from the storage base
    if directory == MODELS_DIR:
        base_dir = "models"
    elif directory == TEXTURES_DIR:
        base_dir = "textures"
    else:
        base_dir = "assemblies"

    relative_path = (
        os.path.join(base_dir, subpath, filename)
        if subpath
        else os.path.join(base_dir, filename)
    )

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(file_data)

    return filename, file_path, relative_path


async def store_model_file(file_data, filename, metadata, subpath=None):
    """Store a model file and its metadata"""
    # Save file to the models directory with provided subpath
    stored_filename, file_path, relative_path = await store_file_to_filesystem(
        file_data, MODELS_DIR, filename, subpath
    )

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document for database
    file_document = {
        "filename": filename,
        "file_path": file_path,
        "relative_path": relative_path,
        "size": file_size,
        "uploaded_at": datetime.utcnow(),
        "metadata": metadata,
    }

    # Insert into database
    result = await models_collection.insert_one(file_document)

    return str(result.inserted_id), file_path


async def store_texture_file(file_data, filename, metadata, subpath=None):
    """Store a texture file and its metadata"""
    # Save file to the textures directory with provided subpath
    stored_filename, file_path, relative_path = await store_file_to_filesystem(
        file_data, TEXTURES_DIR, filename, subpath
    )

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document for database
    file_document = {
        "filename": filename,
        "file_path": file_path,
        "relative_path": relative_path,
        "size": file_size,
        "uploaded_at": datetime.utcnow(),
        "metadata": metadata,
    }

    # Insert into database
    result = await textures_collection.insert_one(file_document)

    return str(result.inserted_id), file_path


async def get_model_by_id(file_id):
    """Get a model's metadata and filepath by ID"""
    # Find the document in the database
    document = await models_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return None, None

    # Return filepath and metadata
    return document["file_path"], document


async def get_texture_by_id(file_id):
    """Get a texture's metadata and filepath by ID"""
    # Find the document in the database
    document = await textures_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return None, None

    # Return filepath and metadata
    return document["file_path"], document


async def list_models(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List models with pagination and filtering
    Returns both the list of documents and the total count
    """
    # Build query based on filters
    query = filters or {}

    # Get total count for pagination
    total_count = await models_collection.count_documents(query)

    # Get cursor with pagination
    cursor = models_collection.find(query).skip(skip).limit(limit)

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def list_textures(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List textures with pagination and filtering
    Returns both the list of documents and the total count
    """
    # Build query based on filters
    query = filters or {}

    # Get total count for pagination
    total_count = await textures_collection.count_documents(query)

    # Get cursor with pagination
    cursor = textures_collection.find(query).skip(skip).limit(limit)

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def delete_model(file_id: str) -> bool:
    """Delete a model by ID (both metadata and file)"""
    # Find the document to get the file path
    document = await models_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return False

    # Delete the file from filesystem
    try:
        os.remove(document["file_path"])
    except (FileNotFoundError, PermissionError):
        # Log the error, but continue to delete the metadata
        print(f"Warning: Could not delete file {document['file_path']}")

    # Delete the metadata
    result = await models_collection.delete_one({"_id": ObjectId(file_id)})

    return result.deleted_count > 0


async def delete_texture(file_id: str) -> bool:
    """Delete a texture by ID (both metadata and file)"""
    # Find the document to get the file path
    document = await textures_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return False

    # Delete the file from filesystem
    try:
        os.remove(document["file_path"])
    except (FileNotFoundError, PermissionError):
        # Log the error, but continue to delete the metadata
        print(f"Warning: Could not delete file {document['file_path']}")

    # Delete the metadata
    result = await textures_collection.delete_one({"_id": ObjectId(file_id)})

    return result.deleted_count > 0


# Assembly operations
async def store_assembly(assembly_data):
    """Store an assembly definition in the database"""
    document = assembly_data.copy()
    document["created_at"] = datetime.utcnow()
    document["updated_at"] = document["created_at"]

    result = await assemblies_collection.insert_one(document)
    return str(result.inserted_id)


async def get_assembly_by_id(assembly_id):
    """Get an assembly by its ID"""
    document = await assemblies_collection.find_one({"_id": ObjectId(assembly_id)})
    return document


async def update_assembly(assembly_id, update_data):
    """Update an assembly definition"""
    update_data["updated_at"] = datetime.utcnow()

    result = await assemblies_collection.update_one(
        {"_id": ObjectId(assembly_id)}, {"$set": update_data}
    )

    return result.modified_count > 0


async def list_assemblies(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List weapon assemblies with pagination and filtering
    Returns both the list of documents and the total count
    """
    # Build query based on filters
    query = filters or {}

    # Get total count for pagination
    total_count = await assemblies_collection.count_documents(query)

    # Get cursor with pagination
    cursor = (
        assemblies_collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
    )

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def delete_assembly(assembly_id):
    """Delete an assembly definition"""
    result = await assemblies_collection.delete_one({"_id": ObjectId(assembly_id)})
    return result.deleted_count > 0

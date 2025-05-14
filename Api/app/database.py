# app/database.py (Hybrid Approach)
"""
MongoDB connection for metadata storage with filesystem for files
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "model_database")

# File storage settings
STORAGE_BASE_DIR = os.getenv("STORAGE_DIR", os.path.join(os.getcwd(), "storage"))
MODELS_DIR = os.path.join(STORAGE_BASE_DIR, "models")
TEXTURES_DIR = os.path.join(STORAGE_BASE_DIR, "textures")

# Create storage directories if they don't exist
Path(MODELS_DIR).mkdir(parents=True, exist_ok=True)
Path(TEXTURES_DIR).mkdir(parents=True, exist_ok=True)

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGO_URI)
db = async_client[DATABASE_NAME]

# Collections for metadata
models_collection = db.models
textures_collection = db.textures


# Generate a unique filename for storage
def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    extension = original_filename.split(".")[-1] if "." in original_filename else ""
    unique_id = str(uuid.uuid4())
    if extension:
        return f"{unique_id}.{extension}"
    return unique_id


async def store_file_to_filesystem(file_data, directory, original_filename):
    """
    Store a file on the filesystem with a unique name
    Returns the unique filename and full path
    """
    # Create a unique filename to avoid collisions
    unique_filename = generate_unique_filename(original_filename)

    # Full path where the file will be stored
    file_path = os.path.join(directory, unique_filename)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(file_data)

    return unique_filename, file_path


async def store_model_file(file_data, original_filename, metadata):
    """Store a model file and its metadata"""
    # Save file to the models directory
    unique_filename, file_path = await store_file_to_filesystem(
        file_data, MODELS_DIR, original_filename
    )

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document for database
    file_document = {
        "filename": original_filename,
        "storage_filename": unique_filename,
        "file_path": file_path,
        "size": file_size,
        "uploaded_at": datetime.utcnow(),
        "metadata": metadata,
    }

    # Insert into database
    result = await models_collection.insert_one(file_document)

    return str(result.inserted_id), file_path


async def store_texture_file(file_data, original_filename, metadata):
    """Store a texture file and its metadata"""
    # Save file to the textures directory
    unique_filename, file_path = await store_file_to_filesystem(
        file_data, TEXTURES_DIR, original_filename
    )

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create document for database
    file_document = {
        "filename": original_filename,
        "storage_filename": unique_filename,
        "file_path": file_path,
        "size": file_size,
        "uploaded_at": datetime.utcnow(),
        "metadata": metadata,
    }

    # Insert into database
    result = await textures_collection.insert_one(file_document)

    return str(result.inserted_id), file_path


async def get_model_by_id(file_id):
    """Get a model's metadata and filepath by ID"""
    from bson.objectid import ObjectId

    # Find the document in the database
    document = await models_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return None, None

    # Return filepath and metadata
    return document["file_path"], document


async def get_texture_by_id(file_id):
    """Get a texture's metadata and filepath by ID"""
    from bson.objectid import ObjectId

    # Find the document in the database
    document = await textures_collection.find_one({"_id": ObjectId(file_id)})

    if not document:
        return None, None

    # Return filepath and metadata
    return document["file_path"], document


async def list_models(skip=0, limit=100, tag=None):
    """List models with pagination and optional tag filtering"""
    # Build query based on tag filter
    query = {} if not tag else {"metadata.tags": tag}

    # Get cursor with pagination
    cursor = models_collection.find(query).skip(skip).limit(limit)

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents


async def list_textures(skip=0, limit=100, model_id=None):
    """List textures with pagination and optional model filtering"""
    # Build query based on model filter
    query = {} if not model_id else {"metadata.associated_model": model_id}

    # Get cursor with pagination
    cursor = textures_collection.find(query).skip(skip).limit(limit)

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents


async def delete_model(file_id):
    """Delete a model by ID (both metadata and file)"""
    from bson.objectid import ObjectId

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


async def delete_texture(file_id):
    """Delete a texture by ID (both metadata and file)"""
    from bson.objectid import ObjectId

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

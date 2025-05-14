# app/database.py
"""
MongoDB database connection and GridFS setup
"""
import os
import motor.motor_asyncio
import gridfs
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "model_database")

# Async client for FastAPI
async_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = async_client[DATABASE_NAME]

# Sync client for GridFS operations (some GridFS operations work better with sync client)
sync_client = MongoClient(MONGO_URI)
sync_db = sync_client[DATABASE_NAME]

# GridFS setup for different file types
model_fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(
    db, bucket_name="models"
)
texture_fs = motor.motor_asyncio.AsyncIOMotorGridFSBucket(
    db, bucket_name="textures"
)

# Sync GridFS for some operations
sync_model_fs = gridfs.GridFSBucket(sync_db, bucket_name="models")
sync_texture_fs = gridfs.GridFSBucket(sync_db, bucket_name="textures")

# Helper functions for common GridFS operations
async def store_file_to_gridfs(bucket, filename, file_data, content_type, metadata=None):
    """Store a file in GridFS with metadata"""
    file_id = await bucket.upload_from_stream(
        filename, 
        file_data,
        metadata={
            "content_type": content_type,
            **(metadata or {})
        }
    )
    return file_id

async def get_file_from_gridfs(bucket, file_id):
    """Retrieve a file from GridFS by its ID"""
    grid_out = await bucket.open_download_stream(file_id)
    file_data = await grid_out.read()
    return file_data, grid_out.metadata

async def get_file_by_name(bucket, filename):
    """Retrieve a file from GridFS by its filename"""
    cursor = bucket.find({"filename": filename})
    file_data = None
    metadata = None
    
    # Get the most recent file with this name
    async for grid_out in cursor:
        file_data = await bucket.open_download_stream(grid_out._id).read()
        metadata = grid_out.metadata
        break
        
    return file_data, metadata

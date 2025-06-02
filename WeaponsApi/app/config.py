# app/config.py
"""
Configuration settings for the application
"""
import os
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
ASSEMBLIES_DIR = os.path.join(STORAGE_BASE_DIR, "assemblies")
ICONS_DIR = os.path.join(STORAGE_BASE_DIR, "icons")

# Make sure all directories exist
for directory in [
    STORAGE_BASE_DIR,
    MODELS_DIR,
    TEXTURES_DIR,
    ASSEMBLIES_DIR,
    ICONS_DIR,
]:
    os.makedirs(directory, exist_ok=True)

# API Settings
API_TITLE = os.getenv("API_TITLE", "3D Model Asset API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# File Size Limits
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 104857600))  # 100MB

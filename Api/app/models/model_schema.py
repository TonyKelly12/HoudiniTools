# app/models/model_schema.py
"""
Pydantic models for data validation and API documentation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ModelMetadata(BaseModel):
    """Metadata for 3D models"""
    name: str
    description: Optional[str] = None
    format: str  # 'fbx', 'obj', 'usd'
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    created_by: Optional[str] = None
    
class TextureMetadata(BaseModel):
    """Metadata for texture files"""
    name: str
    description: Optional[str] = None
    format: str  # 'jpg', 'png', 'exr', etc.
    associated_model: Optional[str] = None
    type: Optional[str] = None  # 'diffuse', 'normal', 'roughness', etc.
    
class ModelResponse(BaseModel):
    """Response model for 3D model info"""
    id: str
    filename: str
    metadata: ModelMetadata
    uploaded_at: datetime
    size: int
    
class TextureResponse(BaseModel):
    """Response model for texture info"""
    id: str
    filename: str
    metadata: TextureMetadata
    uploaded_at: datetime
    size: int
    
class ModelList(BaseModel):
    """List of models for API response"""
    models: List[ModelResponse]
    
class TextureList(BaseModel):
    """List of textures for API response"""
    textures: List[TextureResponse]

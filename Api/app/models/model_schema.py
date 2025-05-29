# app/models/model_schema.py
"""
Pydantic models for data validation and API documentation with weapon system support
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


class WeaponType(str, Enum):
    """Types of weapons supported by the system"""

    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"
    BOW = "bow"
    SPEAR = "spear"
    DAGGER = "dagger"
    STAFF = "staff"
    SHIELD = "shield"
    GUN = "gun"
    RIFLE = "rifle"
    CUSTOM = "custom"


class WeaponPartType(str, Enum):
    """Types of weapon parts"""

    HANDLE = "handle"
    BLADE = "blade"
    GUARD = "guard"
    POMMEL = "pommel"
    HEAD = "head"
    SHAFT = "shaft"
    GRIP = "grip"
    BARREL = "barrel"
    STOCK = "stock"
    SIGHT = "sight"
    MAGAZINE = "magazine"
    TRIGGER = "trigger"
    CUSTOM = "custom"


class WeaponPartMetadata(BaseModel):
    """Metadata specific to weapon parts"""

    weapon_type: WeaponType
    part_type: WeaponPartType
    is_attachment: bool = False
    attachment_points: Optional[List[str]] = None
    slot_id: Optional[str] = None
    material_slots: Optional[List[str]] = None
    scale: Optional[float] = 1.0
    default_position: Optional[Dict[str, float]] = None
    default_rotation: Optional[Dict[str, float]] = None
    variant_name: Optional[str] = None
    variant_group: Optional[str] = None


class ModelMetadata(BaseModel):
    """Metadata for 3D models"""

    name: str
    description: Optional[str] = None
    format: str  # 'fbx', 'obj', 'usd', etc.
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    created_by: Optional[str] = None
    category: Optional[str] = None
    polycount: Optional[int] = None
    is_weapon_part: bool = False
    weapon_part_metadata: Optional[WeaponPartMetadata] = None
    icon_path: Optional[str] = None
    model_config = {"protected_namespaces": ()}


class TextureType(str, Enum):
    """Types of textures"""

    DIFFUSE = "diffuse"
    NORMAL = "normal"
    ROUGHNESS = "roughness"
    METALLIC = "metallic"
    EMISSIVE = "emissive"
    AO = "ambient_occlusion"
    HEIGHT = "height"
    OPACITY = "opacity"
    CUSTOM = "custom"


class TextureMetadata(BaseModel):
    """Metadata for texture files"""

    name: str
    description: Optional[str] = None
    format: str  # 'jpg', 'png', 'exr', etc.
    associated_model: Optional[str] = None  # ID of the model this texture belongs to
    texture_type: TextureType = TextureType.DIFFUSE
    resolution: Optional[Dict[str, int]] = None  # {"width": 2048, "height": 2048}
    is_tiling: bool = False
    tiling_factor: Optional[Dict[str, float]] = None  # {"u": 1.0, "v": 1.0}
    color_space: Optional[str] = None  # "sRGB", "linear", etc.
    weapon_type: Optional[WeaponType] = None
    part_type: Optional[WeaponPartType] = None
    variant_name: Optional[str] = None
    variant_group: Optional[str] = None


class ModelResponse(BaseModel):
    """Response model for 3D model info"""

    id: str
    filename: str
    metadata: ModelMetadata
    uploaded_at: datetime
    size: int
    file_path: str  # Added for easier reference


class TextureResponse(BaseModel):
    """Response model for texture info"""

    id: str
    filename: str
    metadata: TextureMetadata
    uploaded_at: datetime
    size: int
    file_path: str  # Added for easier reference


class ModelList(BaseModel):
    """List of models for API response"""

    models: List[ModelResponse]
    total: int
    page: int
    page_size: int


class TextureList(BaseModel):
    """List of textures for API response"""

    textures: List[TextureResponse]
    total: int
    page: int
    page_size: int


class WeaponAssemblyItem(BaseModel):
    """Item in a weapon assembly"""

    id: str
    part_type: WeaponPartType
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    rotation: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    scale: Dict[str, float] = Field(default_factory=lambda: {"x": 1, "y": 1, "z": 1})
    material_overrides: Optional[Dict[str, str]] = None  # Slot to texture ID mapping


class WeaponAssembly(BaseModel):
    """Weapon assembly definition"""

    id: str
    name: str
    description: Optional[str] = None
    weapon_type: WeaponType
    parts: List[WeaponAssemblyItem]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail_id: Optional[str] = None


class WeaponAssemblyList(BaseModel):
    """List of weapon assemblies for API response"""

    assemblies: List[WeaponAssembly]
    total: int
    page: int
    page_size: int

    # Add to Api/app/models/model_schema.py


class CivilizationCompatibility(BaseModel):
    """Civilization compatibility metadata for assets"""

    # Government compatibility
    government_types: Optional[List[str]] = None  # ["monarchy", "democracy"]
    government_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Technology constraints
    tech_levels: Optional[List[str]] = None  # ["iron_age", "pre_industrial"]
    min_tech_level: Optional[str] = None
    max_tech_level: Optional[str] = None

    # Cultural themes
    cultural_values: Optional[List[str]] = (
        None  # ["honor_based", "achievement_oriented"]
    )
    visual_themes: Optional[List[str]] = None  # ["ornate", "functional", "ceremonial"]

    # Style tags
    architectural_styles: Optional[List[str]] = (
        None  # ["gothic", "classical", "futuristic"]
    )
    material_themes: Optional[List[str]] = (
        None  # ["metallic", "organic", "crystalline"]
    )

    # Compatibility scores
    overall_compatibility: Optional[float] = Field(None, ge=0.0, le=1.0)
    usage_frequency: Optional[int] = Field(0, ge=0)  # Track popular combinations


class EnhancedModelMetadata(ModelMetadata):
    """Extended model metadata with civilization compatibility"""

    civilization_compatibility: Optional[CivilizationCompatibility] = None

    # Additional civilization-specific fields
    historical_period: Optional[str] = None  # "medieval", "renaissance", "modern"
    geographic_origin: Optional[str] = None  # "european", "asian", "fantasy"
    social_class: Optional[str] = None  # "common", "noble", "royal"

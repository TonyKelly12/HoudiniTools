# app/models/context_schema.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum


class GeneratorType(str, Enum):
    WEAPON = "weapon"
    BUILDING = "building"
    ROAD = "road"
    CHARACTER = "character"


class ContextRequest(BaseModel):
    civilization_id: str
    generator_type: GeneratorType
    user_preferences: Optional[Dict] = {}
    override_suggestions: Optional[List[str]] = []


class AssetRecommendation(BaseModel):
    asset_id: str
    asset_type: str
    compatibility_score: float
    reasons: List[str]


class StyleGuide(BaseModel):
    color_palette: List[str]
    materials: List[str]
    visual_themes: List[str]
    design_principles: List[str]


class ContextResponse(BaseModel):
    civilization_name: str
    context_summary: Dict[str, str]
    asset_recommendations: List[AssetRecommendation]
    style_guide: StyleGuide
    prohibited_items: List[str]

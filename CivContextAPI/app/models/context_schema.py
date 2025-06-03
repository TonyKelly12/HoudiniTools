"""
Enhanced context schema with weapons integration
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum


class GeneratorType(str, Enum):
    WEAPON = "weapon"
    BUILDING = "building"
    ROAD = "road"
    CHARACTER = "character"


class AssetRecommendation(BaseModel):
    asset_id: str
    asset_type: str
    compatibility_score: float
    reasons: List[str]
    mesh: Optional[str] = None
    texture: Optional[str] = None
    database_source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WeaponRecommendation(AssetRecommendation):
    """Enhanced recommendation specifically for weapons"""

    weapon_type: Optional[str] = None
    part_type: Optional[str] = None
    technology_level: Optional[str] = None
    cultural_fit: Optional[str] = None
    government_appropriateness: Optional[str] = None


class ContextRequest(BaseModel):
    civilization_id: str
    generator_type: GeneratorType
    user_preferences: Optional[Dict] = {}
    override_suggestions: Optional[List[str]] = []


class StyleGuide(BaseModel):
    color_palette: List[str]
    materials: List[str]
    visual_themes: List[str]
    design_principles: List[str]


class WeaponAnalysis(BaseModel):
    """Analysis of civilization context for weapons"""

    allowed_weapon_types: List[str]
    technology_constraints: Dict[str, Any]
    government_aesthetics: Dict[str, Any]
    cultural_aesthetics: Dict[str, Any]
    military_context: Dict[str, Any]


class ContextResponse(BaseModel):
    civilization_name: str
    context_summary: Dict[str, str]
    asset_recommendations: List[AssetRecommendation]
    style_guide: StyleGuide
    prohibited_items: List[str]


class WeaponContextResponse(BaseModel):
    """Specialized response for weapon context"""

    civilization_id: str
    civilization_name: str
    weapon_analysis: WeaponAnalysis
    recommendations: List[WeaponRecommendation]
    assemblies: Optional[List[Dict[str, Any]]] = None
    style_guide: StyleGuide
    prohibited_weapons: List[str]

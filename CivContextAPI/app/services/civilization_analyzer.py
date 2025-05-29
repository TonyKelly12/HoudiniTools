# app/services/civilization_analyzer.py
import httpx
from typing import Dict


class CivilizationAnalyzer:
    def __init__(self, civ_api_url: str):
        self.civ_api_url = civ_api_url

    async def analyze_civilization(self, civ_id: str) -> Dict:
        """Fetch and analyze civilization data"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.civ_api_url}/civilizations/{civ_id}")
            civ_data = response.json()

        return {
            "government_influence": self._analyze_government(civ_data["metadata"]),
            "tech_constraints": self._analyze_technology(civ_data["metadata"]),
            "cultural_aesthetics": self._analyze_culture(civ_data["metadata"]),
            "military_requirements": self._analyze_military(civ_data["metadata"]),
        }

    def _analyze_government(self, metadata: Dict) -> Dict:
        """Extract government-related aesthetic influences"""
        gov_type = metadata.get("government_type")

        government_aesthetics = {
            "monarchy": {
                "themes": ["royal", "heraldic", "ornate", "hierarchical"],
                "materials": ["gold", "precious_metals", "fine_fabrics"],
                "symbols": ["crowns", "crests", "lions", "eagles"],
            },
            "democracy": {
                "themes": ["accessible", "functional", "diverse", "open"],
                "materials": ["varied", "sustainable", "practical"],
                "symbols": ["doves", "hands", "circles", "balanced_scales"],
            },
            "tribal_council": {
                "themes": ["natural", "communal", "traditional", "organic"],
                "materials": ["wood", "bone", "natural_fibers", "stone"],
                "symbols": ["animals", "spirals", "trees", "circles"],
            },
        }

        return government_aesthetics.get(gov_type, {})

    def _analyze_technology(self, metadata: Dict) -> Dict:
        """Determine technological constraints and opportunities"""
        tech_level = metadata.get("technology_level")

        tech_constraints = {
            "stone_age": {
                "available_materials": ["stone", "wood", "bone", "hide"],
                "prohibited_materials": ["metal", "plastic", "electronics"],
                "complexity_level": "simple",
                "manufacturing": "handcrafted",
            },
            "iron_age": {
                "available_materials": ["iron", "steel", "wood", "leather", "bronze"],
                "prohibited_materials": ["plastic", "electronics", "advanced_alloys"],
                "complexity_level": "moderate",
                "manufacturing": "blacksmithed",
            },
            "post_scarcity": {
                "available_materials": ["all", "smart_materials", "energy_materials"],
                "prohibited_materials": [],
                "complexity_level": "maximum",
                "manufacturing": "automated_advanced",
            },
        }

        return tech_constraints.get(tech_level, {})

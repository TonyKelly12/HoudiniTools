# app/services/civilization_analyzer.py
from typing import Dict, Any


class CivilizationAnalyzer:
    """Analyzes civilization data to determine weapon compatibility"""

    @staticmethod
    def analyze_weapon_compatibility(civ_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze civilization to determine appropriate weapons"""

        tech_level = civ_metadata.get("technology_level", "iron_age")
        government_type = civ_metadata.get("government_type", "monarchy")
        military_structure = civ_metadata.get("military_structure", "militia")
        cultural_values = civ_metadata.get("cultural_values", "honor_based")
        primary_weapons = civ_metadata.get("primary_weapons", "melee")

        # Technology constraints
        tech_weapon_mapping = {
            "stone_age": ["spear", "club", "dagger"],
            "bronze_age": ["sword", "spear", "axe", "bow"],
            "iron_age": ["sword", "spear", "axe", "bow", "mace"],
            "pre_industrial": ["sword", "spear", "axe", "bow", "mace", "rifle"],
            "industrial": ["rifle", "gun", "sword", "bow"],
            "information_age": ["rifle", "gun", "advanced"],
            "post_scarcity": ["rifle", "gun", "advanced", "energy"],
        }

        # Government aesthetic mapping
        government_aesthetics = {
            "monarchy": {
                "preferred_materials": ["gold", "silver", "precious"],
                "style_themes": ["ornate", "royal", "ceremonial"],
                "weapon_preferences": ["sword", "mace"],
            },
            "democracy": {
                "preferred_materials": ["steel", "practical"],
                "style_themes": ["functional", "standardized"],
                "weapon_preferences": ["rifle", "standardized"],
            },
            "tribal_council": {
                "preferred_materials": ["wood", "bone", "natural"],
                "style_themes": ["tribal", "natural", "handcrafted"],
                "weapon_preferences": ["spear", "bow", "axe"],
            },
            "theocracy": {
                "preferred_materials": ["blessed", "ceremonial"],
                "style_themes": ["religious", "ceremonial"],
                "weapon_preferences": ["staff", "mace", "ceremonial"],
            },
        }

        # Cultural aesthetics
        cultural_aesthetics = {
            "honor_based": {
                "style_themes": ["decorated", "personal", "ceremonial"],
                "complexity": "ornate",
            },
            "achievement_oriented": {
                "style_themes": ["efficient", "optimized", "advanced"],
                "complexity": "functional",
            },
            "harmony_focused": {
                "style_themes": ["balanced", "natural", "peaceful"],
                "complexity": "simple",
            },
        }

        return {
            "allowed_weapon_types": tech_weapon_mapping.get(
                tech_level, ["sword", "bow"]
            ),
            "government_aesthetics": government_aesthetics.get(government_type, {}),
            "cultural_aesthetics": cultural_aesthetics.get(cultural_values, {}),
            "tech_constraints": {
                "level": tech_level,
                "advanced_materials": tech_level
                in ["information_age", "post_scarcity"],
                "energy_weapons": tech_level == "post_scarcity",
            },
            "military_context": {
                "structure": military_structure,
                "primary_weapons": primary_weapons,
                "ceremonial_needs": government_type in ["monarchy", "theocracy"],
            },
        }

    @staticmethod
    def calculate_compatibility_score(
        weapon_metadata: Dict, civ_analysis: Dict
    ) -> float:
        """Calculate compatibility score between weapon and civilization"""
        score = 0.0
        max_score = 0.0

        # Check weapon type compatibility
        weapon_part_meta = weapon_metadata.get("weapon_part_metadata", {})
        weapon_type = weapon_part_meta.get("weapon_type", "")

        if weapon_type in civ_analysis.get("allowed_weapon_types", []):
            score += 30
        max_score += 30

        # Check style compatibility
        weapon_tags = weapon_metadata.get("tags", [])
        gov_aesthetics = civ_analysis.get("government_aesthetics", {})

        for theme in gov_aesthetics.get("style_themes", []):
            if theme in weapon_tags:
                score += 20
        max_score += 20 * len(gov_aesthetics.get("style_themes", []))

        # Check cultural compatibility
        cultural_aesthetics = civ_analysis.get("cultural_aesthetics", {})
        for theme in cultural_aesthetics.get("style_themes", []):
            if theme in weapon_tags:
                score += 15
        max_score += 15 * len(cultural_aesthetics.get("style_themes", []))

        # Technology appropriateness
        tech_constraints = civ_analysis.get("tech_constraints", {})
        if "advanced" in weapon_tags and not tech_constraints.get(
            "advanced_materials", False
        ):
            score -= 25  # Penalty for anachronistic tech

        if "energy" in weapon_tags and not tech_constraints.get(
            "energy_weapons", False
        ):
            score -= 40  # Heavy penalty for impossible tech

        max_score += 25  # Base tech score

        return min(1.0, max(0.0, score / max_score)) if max_score > 0 else 0.0

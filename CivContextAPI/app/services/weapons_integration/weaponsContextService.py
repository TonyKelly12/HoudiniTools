from app.services.weapons_integration.weaponsApiClient import WeaponsAPIClient
from app.services.civilization_analyzer import CivilizationAnalyzer
from typing import Dict, Any, List, Optional
import httpx
from fastapi import HTTPException


class WeaponsContextService:
    """Main service for providing weapons recommendations based on civilization context"""

    def __init__(self, weapons_api_url: str, civ_api_url: str):
        self.weapons_client = WeaponsAPIClient(weapons_api_url)
        self.civ_api_url = civ_api_url.rstrip("/")
        self.analyzer = CivilizationAnalyzer()

    async def get_civilization_data(self, civ_id: str) -> Dict[str, Any]:
        """Get civilization data from CivAPI"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.civ_api_url}/civilizations/{civ_id}"
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="CivilizationAPI unavailable")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Civilization not found")
            raise HTTPException(
                status_code=e.response.status_code, detail="CivilizationAPI error"
            )

    async def get_recommended_weapons(
        self,
        civ_id: str,
        weapon_type: Optional[str] = None,
        limit: int = 20,
        min_compatibility: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Get weapon recommendations for a civilization"""

        # Get civilization data
        civ_data = await self.get_civilization_data(civ_id)
        civ_metadata = civ_data["metadata"]

        # Analyze civilization for weapon compatibility
        civ_analysis = self.analyzer.analyze_weapon_compatibility(civ_metadata)

        # Get weapons from WeaponsAPI
        filters = {}
        if weapon_type:
            filters["weapon_type"] = weapon_type

        weapons_response = await self.weapons_client.get_all_models(
            limit=100, **filters
        )
        weapons = weapons_response.get("models", [])

        # Score and filter weapons
        recommendations = []
        for weapon in weapons:
            # Only consider weapon parts
            if not weapon["metadata"].get("is_weapon_part", False):
                continue

            compatibility_score = self.analyzer.calculate_compatibility_score(
                weapon["metadata"], civ_analysis
            )

            if compatibility_score >= min_compatibility:
                recommendations.append(
                    {
                        "weapon": weapon,
                        "compatibility_score": compatibility_score,
                        "reasons": self._generate_compatibility_reasons(
                            weapon["metadata"], civ_analysis, compatibility_score
                        ),
                    }
                )

        # Sort by compatibility score
        recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return recommendations[:limit]

    async def get_weapon_assemblies_for_civilization(
        self, civ_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get complete weapon assemblies suitable for a civilization"""

        civ_data = await self.get_civilization_data(civ_id)
        civ_analysis = self.analyzer.analyze_weapon_compatibility(civ_data["metadata"])

        # Get assemblies from WeaponsAPI
        assemblies_response = await self.weapons_client.get_assemblies()
        assemblies = assemblies_response.get("assemblies", [])

        # Score assemblies based on civilization compatibility
        scored_assemblies = []
        for assembly in assemblies:
            weapon_type = assembly.get("weapon_type", "")

            if weapon_type in civ_analysis.get("allowed_weapon_types", []):
                # Calculate score based on assembly characteristics
                score = 0.7  # Base score for type compatibility

                # Bonus for government fit
                gov_preferences = civ_analysis.get("government_aesthetics", {}).get(
                    "weapon_preferences", []
                )
                if weapon_type in gov_preferences:
                    score += 0.2

                scored_assemblies.append(
                    {
                        "assembly": assembly,
                        "compatibility_score": min(1.0, score),
                        "reasons": [
                            f"Compatible with {civ_data['metadata']['technology_level']} technology"
                        ],
                    }
                )

        scored_assemblies.sort(key=lambda x: x["compatibility_score"], reverse=True)
        return scored_assemblies[:limit]

    def _generate_compatibility_reasons(
        self, weapon_metadata: Dict, civ_analysis: Dict, score: float
    ) -> List[str]:
        """Generate human-readable reasons for compatibility"""
        reasons = []

        # Weapon type compatibility
        weapon_part_meta = weapon_metadata.get("weapon_part_metadata", {})
        weapon_type = weapon_part_meta.get("weapon_type", "")

        if weapon_type in civ_analysis.get("allowed_weapon_types", []):
            tech_level = civ_analysis.get("tech_constraints", {}).get("level", "")
            reasons.append(
                f"Weapon type '{weapon_type}' is compatible with {tech_level} technology"
            )

        # Style compatibility
        weapon_tags = weapon_metadata.get("tags", [])
        gov_aesthetics = civ_analysis.get("government_aesthetics", {})

        for theme in gov_aesthetics.get("style_themes", []):
            if theme in weapon_tags:
                reasons.append(f"Style '{theme}' matches civilization aesthetics")

        # Score-based reasons
        if score > 0.8:
            reasons.append("Excellent fit for this civilization")
        elif score > 0.6:
            reasons.append("Good compatibility with civilization values")
        elif score > 0.4:
            reasons.append("Acceptable for this civilization")
        else:
            reasons.append("Limited compatibility")

        return reasons if reasons else ["Basic compatibility"]

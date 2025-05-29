# scripts/tag_existing_assets.py
"""
Script to add civilization tags to existing assets
"""
import asyncio
import httpx
from typing import Dict


class AssetTagger:
    def __init__(self, asset_api_url: str):
        self.asset_api_url = asset_api_url

    async def tag_all_weapons(self):
        """Add civilization tags to all existing weapons"""

        # Get all weapons
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.asset_api_url}/models/")
            weapons = response.json()["models"]

        for weapon in weapons:
            tags = self.generate_tags_for_weapon(weapon)
            if tags:
                await self.update_weapon_tags(weapon["id"], tags)

    def generate_tags_for_weapon(self, weapon: Dict) -> Dict:
        """Generate civilization tags based on weapon characteristics"""
        name = weapon["metadata"]["name"].lower()
        description = weapon["metadata"].get("description", "").lower()

        tags = {
            "civilization_compatibility": {
                "visual_themes": [],
                "government_types": [],
                "tech_levels": [],
                "cultural_values": [],
            }
        }

        # Technology level inference
        if any(term in name for term in ["laser", "plasma", "energy"]):
            tags["civilization_compatibility"]["tech_levels"] = ["post_scarcity"]
        elif any(term in name for term in ["rifle", "gun", "pistol"]):
            tags["civilization_compatibility"]["tech_levels"] = [
                "industrial",
                "information_age",
            ]
        elif any(term in name for term in ["sword", "axe", "mace"]):
            tags["civilization_compatibility"]["tech_levels"] = [
                "iron_age",
                "pre_industrial",
            ]
        elif any(term in name for term in ["stone", "club", "spear"]):
            tags["civilization_compatibility"]["tech_levels"] = [
                "stone_age",
                "bronze_age",
            ]

        # Visual theme inference
        if any(
            term in name + description for term in ["royal", "crown", "gold", "ornate"]
        ):
            tags["civilization_compatibility"]["visual_themes"].append("royal")
            tags["civilization_compatibility"]["government_types"].append("monarchy")

        if any(term in name + description for term in ["tribal", "primitive", "bone"]):
            tags["civilization_compatibility"]["visual_themes"].append("tribal")
            tags["civilization_compatibility"]["government_types"].append(
                "tribal_council"
            )

        if any(
            term in name + description for term in ["military", "standard", "uniform"]
        ):
            tags["civilization_compatibility"]["visual_themes"].append("military")

        return tags

    async def update_weapon_tags(self, weapon_id: str, tags: Dict):
        """Update weapon with civilization tags"""
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{self.asset_api_url}/models/{weapon_id}", json={"metadata": tags}
            )


# Usage
async def main():
    tagger = AssetTagger("http://localhost:8000")  # Your Asset API URL
    await tagger.tag_all_weapons()
    print("Asset tagging complete!")


if __name__ == "__main__":
    asyncio.run(main())

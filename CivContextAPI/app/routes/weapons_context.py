"""
Routes for weapons context and recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.services.weapons_integration import WeaponsContextService
from app.models.context_schema import AssetRecommendation
import os

router = APIRouter(prefix="/weapons", tags=["Weapons Context"])

# Configuration
WEAPONS_API_URL = os.getenv("WEAPONS_API_URL", "http://weapons-api:8003")
CIV_API_URL = os.getenv("CIV_API_URL", "http://civ-api:8001")


def get_weapons_service() -> WeaponsContextService:
    return WeaponsContextService(WEAPONS_API_URL, CIV_API_URL)


@router.get("/recommendations/{civ_id}", response_model=List[AssetRecommendation])
async def get_weapon_recommendations(
    civ_id: str,
    weapon_type: Optional[str] = Query(None, description="Filter by weapon type"),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum recommendations to return"
    ),
    min_compatibility: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum compatibility score"
    ),
    service: WeaponsContextService = Depends(get_weapons_service),
):
    """
    Get weapon recommendations for a specific civilization

    Returns weapons that are compatible with the civilization's:
    - Technology level
    - Government type and aesthetics
    - Cultural values
    - Military structure
    """
    try:
        recommendations = await service.get_recommended_weapons(
            civ_id=civ_id,
            weapon_type=weapon_type,
            limit=limit,
            min_compatibility=min_compatibility,
        )

        # Convert to AssetRecommendation format
        asset_recommendations = []
        for rec in recommendations:
            weapon = rec["weapon"]
            asset_recommendations.append(
                AssetRecommendation(
                    asset_id=weapon["id"],
                    asset_type="weapon_part",
                    compatibility_score=rec["compatibility_score"],
                    reasons=rec["reasons"],
                    mesh=f"/models/{weapon['id']}",
                    texture=None,  # Could be enhanced to include texture recommendations
                    database_source="WeaponsAPI",
                    metadata={
                        "weapon_type": weapon["metadata"]
                        .get("weapon_part_metadata", {})
                        .get("weapon_type"),
                        "part_type": weapon["metadata"]
                        .get("weapon_part_metadata", {})
                        .get("part_type"),
                        "filename": weapon["filename"],
                        "size": weapon["size"],
                    },
                )
            )

        return asset_recommendations

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/assemblies/{civ_id}")
async def get_weapon_assemblies(
    civ_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum assemblies to return"),
    service: WeaponsContextService = Depends(get_weapons_service),
):
    """
    Get complete weapon assemblies suitable for a civilization

    Returns pre-configured weapon assemblies that match the civilization's
    technology level and cultural aesthetics.
    """
    try:
        assemblies = await service.get_weapon_assemblies_for_civilization(
            civ_id=civ_id, limit=limit
        )

        return {
            "civilization_id": civ_id,
            "assemblies": assemblies,
            "count": len(assemblies),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting assemblies: {str(e)}"
        )


@router.get("/analyze/{civ_id}")
async def analyze_civilization_weapons_context(
    civ_id: str, service: WeaponsContextService = Depends(get_weapons_service)
):
    """
    Analyze a civilization's context for weapons suitability

    Returns detailed analysis of what types of weapons would be
    appropriate for the civilization based on its attributes.
    """
    try:
        civ_data = await service.get_civilization_data(civ_id)
        analysis = service.analyzer.analyze_weapon_compatibility(civ_data["metadata"])

        return {
            "civilization_id": civ_id,
            "civilization_name": civ_data["metadata"]["name"],
            "analysis": analysis,
            "summary": {
                "technology_level": civ_data["metadata"]["technology_level"],
                "government_type": civ_data["metadata"]["government_type"],
                "military_structure": civ_data["metadata"]["military_structure"],
                "allowed_weapon_types": analysis["allowed_weapon_types"],
                "aesthetic_preferences": analysis.get("government_aesthetics", {}).get(
                    "style_themes", []
                ),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing civilization: {str(e)}"
        )


@router.get("/parts/{civ_id}")
async def get_weapon_parts_for_civilization(
    civ_id: str,
    weapon_type: Optional[str] = Query(None, description="Filter by weapon type"),
    part_type: Optional[str] = Query(
        None, description="Filter by part type (handle, blade, etc.)"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum parts to return"),
    service: WeaponsContextService = Depends(get_weapons_service),
):
    """
    Get individual weapon parts suitable for a civilization

    Useful for custom weapon assembly based on civilization context.
    """
    try:
        # Get civilization analysis
        civ_data = await service.get_civilization_data(civ_id)
        civ_analysis = service.analyzer.analyze_weapon_compatibility(
            civ_data["metadata"]
        )

        # Determine weapon types to search if not specified
        search_weapon_types = (
            [weapon_type] if weapon_type else civ_analysis["allowed_weapon_types"]
        )

        all_parts = []
        for wtype in search_weapon_types:
            try:
                parts = await service.weapons_client.get_weapon_parts(
                    weapon_type=wtype, part_type=part_type
                )

                # Score each part
                for part in parts:
                    score = service.analyzer.calculate_compatibility_score(
                        part["metadata"], civ_analysis
                    )

                    all_parts.append(
                        {
                            "part": part,
                            "compatibility_score": score,
                            "weapon_type": wtype,
                        }
                    )

            except Exception:
                # Continue with other weapon types if one fails
                continue

        # Sort and limit
        all_parts.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return {
            "civilization_id": civ_id,
            "parts": all_parts[:limit],
            "total_found": len(all_parts),
            "search_criteria": {
                "weapon_types": search_weapon_types,
                "part_type": part_type,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting weapon parts: {str(e)}"
        )

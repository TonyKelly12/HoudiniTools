from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from pydantic import BaseModel
from app.models.context_schema import AssetRecommendation, GeneratorType

router = APIRouter(prefix="/civilizations", tags=["Civilizations"])

# In-memory store for demo purposes
civilizations: Dict[str, Dict] = {}


class Civilization(BaseModel):
    id: str
    name: str
    description: str = ""
    # Add more fields as needed for your context


@router.post("/", response_model=Civilization)
def create_civilization(civ: Civilization):
    if civ.id in civilizations:
        raise HTTPException(status_code=400, detail="Civilization already exists")
    civilizations[civ.id] = civ.dict()
    return civ


@router.get("/", response_model=List[Civilization])
def list_civilizations():
    return list(civilizations.values())


@router.get("/{civ_id}", response_model=Civilization)
def get_civilization(civ_id: str):
    civ = civilizations.get(civ_id)
    if not civ:
        raise HTTPException(status_code=404, detail="Civilization not found")
    return civ


@router.put("/{civ_id}", response_model=Civilization)
def update_civilization(civ_id: str, civ: Civilization):
    if civ_id not in civilizations:
        raise HTTPException(status_code=404, detail="Civilization not found")
    civilizations[civ_id] = civ.dict()
    return civ


@router.delete("/{civ_id}")
def delete_civilization(civ_id: str):
    if civ_id not in civilizations:
        raise HTTPException(status_code=404, detail="Civilization not found")
    del civilizations[civ_id]
    return {"detail": "Civilization deleted"}


@router.get("/{civ_id}/assets", response_model=List[AssetRecommendation])
def get_asset_recommendations(
    civ_id: str,
    generator_type: GeneratorType = Query(
        ..., description="Type of asset to generate (weapon, building, road, character)"
    ),
):
    # TODO: Integrate with Weapons, Building, Road, Iconography APIs/databases
    # For now, return mock data
    if civ_id not in civilizations:
        raise HTTPException(status_code=404, detail="Civilization not found")
    # Example mock asset
    mock_assets = [
        AssetRecommendation(
            asset_id="mesh_001",
            asset_type=generator_type.value,
            compatibility_score=0.95,
            reasons=["Matches civilization style", "Available in DB"],
            mesh="/meshes/mesh_001.obj",
            texture="/textures/mesh_001_diffuse.png",
            database_source=(
                "Weapons DB"
                if generator_type == GeneratorType.WEAPON
                else "Data Store 2"
            ),
        )
    ]
    return mock_assets


# --- Placeholders for future API integrations ---
# Weapons API integration (to be implemented)
# Building API integration (to be implemented)
# Road API integration (to be implemented)
# Iconography API integration (to be implemented)

# app/routes/civilizations.py
"""
API routes for civilization operations
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List
from datetime import datetime

from ..models.civilization_schema import (
    CivilizationMetadata,
    CivilizationList,
    CivilizationResponse,
    CivilizationRelationshipList,
    CivilizationHistoryList,
)
from ..services.civilization_service import (
    create_civilization,
    get_civilization_by_id_service,
    update_civilization_service,
    list_civilizations_service,
    delete_civilization_service,
    search_civilizations_service,
    get_civilizations_by_attribute_service,
    get_statistics_service,
    get_attribute_distribution_service,
    find_similar_civilizations_service,
    create_relationship_service,
    get_civilization_relationships_service,
    add_history_event_service,
    get_civilization_history_service,
    create_template_service,
    list_templates_service,
    create_civilization_from_template_service,
)

router = APIRouter(prefix="/civilizations", tags=["Civilizations"])


@router.post("/", response_model=dict)
async def create_civilization_route(
    metadata: CivilizationMetadata = Body(..., description="Civilization metadata")
):
    """
    Create a new civilization

    A civilization includes comprehensive attributes covering:
    - Geographic and settlement patterns
    - Political structure and governance
    - Economic systems and trade
    - Social structure and hierarchy
    - Cultural and religious practices
    - Knowledge and education systems
    - Military and defense capabilities
    - Communication and language
    - Environmental relationships
    - Demographics and development metrics
    """
    try:
        civilization_id = await create_civilization(metadata)
        return {"id": civilization_id, "message": "Civilization created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create civilization: {str(e)}"
        )


@router.get("/", response_model=CivilizationList)
async def list_civilizations_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    government_type: Optional[str] = Query(None, description="Filter by government type"),
    technology_level: Optional[str] = Query(None, description="Filter by technology level"),
    population_size: Optional[str] = Query(None, description="Filter by population size"),
    primary_economy: Optional[str] = Query(None, description="Filter by primary economy"),
    primary_religion: Optional[str] = Query(None, description="Filter by primary religion"),
    settlement_pattern: Optional[str] = Query(None, description="Filter by settlement pattern"),
    primary_terrain: Optional[str] = Query(None, description="Filter by primary terrain"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
):
    """
    List all civilizations with optional filtering

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - government_type: Filter by government type (democracy, monarchy, etc.)
    - technology_level: Filter by technology level (stone_age, industrial, etc.)
    - population_size: Filter by population size (tiny, small, medium, etc.)
    - primary_economy: Filter by primary economy (agricultural, industrial, etc.)
    - primary_religion: Filter by primary religion (monotheistic, polytheistic, etc.)
    - settlement_pattern: Filter by settlement pattern (nomadic, settled, etc.)
    - primary_terrain: Filter by primary terrain (desert, forest, etc.)
    - tag: Filter by tag
    """
    result = await list_civilizations_service(
        skip=skip,
        limit=limit,
        government_type=government_type,
        technology_level=technology_level,
        population_size=population_size,
        primary_economy=primary_economy,
        primary_religion=primary_religion,
        settlement_pattern=settlement_pattern,
        primary_terrain=primary_terrain,
        tag=tag,
    )

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/search", response_model=CivilizationList)
async def search_civilizations_route(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Search civilizations by text in name, description, and tags
    """
    result = await search_civilizations_service(q, skip, limit)

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/by-attribute/{attribute_name}", response_model=CivilizationList)
async def get_civilizations_by_attribute_route(
    attribute_name: str = Path(..., description="Attribute name to filter by"),
    attribute_value: str = Query(..., description="Attribute value to match"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get civilizations that have a specific attribute value

    Example: `/civilizations/by-attribute/government_type?attribute_value=democracy`
    """
    result = await get_civilizations_by_attribute_service(
        attribute_name, attribute_value, skip, limit
    )

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/statistics")
async def get_statistics_route():
    """
    Get various statistics about civilizations in the database

    Returns information like total count, distribution of government types,
    technology levels, population sizes, etc.
    """
    stats = await get_statistics_service()
    return stats


@router.get("/attribute-distribution/{attribute_name}")
async def get_attribute_distribution_route(
    attribute_name: str = Path(..., description="Attribute name to analyze")
):
    """
    Get distribution of values for a specific attribute

    Returns a breakdown of how many civilizations have each value
    for the specified attribute.
    """
    distribution = await get_attribute_distribution_service(attribute_name)
    return distribution


@router.get("/{civilization_id}", response_model=CivilizationResponse)
async def get_civilization_route(
    civilization_id: str = Path(..., description="ID of the civilization to retrieve")
):
    """
    Get a civilization by its ID

    Returns the complete civilization definition with all attributes
    """
    civilization = await get_civilization_by_id_service(civilization_id)
    return civilization


@router.put("/{civilization_id}", response_model=dict)
async def update_civilization_route(
    civilization_id: str = Path(..., description="ID of the civilization to update"),
    update_data: dict = Body(..., description="Fields to update (partial update supported)"),
):
    """
    Update a civilization

    Parameters:
    - civilization_id: ID of the civilization to update
    - update_data: Fields to update (can be partial)
    """
    result = await update_civilization_service(civilization_id, update_data)
    return result


@router.delete("/{civilization_id}")
async def delete_civilization_route(
    civilization_id: str = Path(..., description="ID of the civilization to delete")
):
    """
    Delete a civilization by its ID

    This will also delete associated relationships and history events
    """
    result = await delete_civilization_service(civilization_id)
    return result


@router.get("/{civilization_id}/similar")
async def find_similar_civilizations_route(
    civilization_id: str = Path(..., description="ID of the reference civilization"),
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Similarity threshold (0.0 to 1.0)"),
):
    """
    Find civilizations similar to the given one

    Uses attribute matching to find civilizations with similar characteristics.
    Higher threshold means more strict similarity requirements.
    """
    result = await find_similar_civilizations_service(civilization_id, threshold)
    return result


# Relationship endpoints
@router.post("/{civilization_id}/relationships", response_model=dict)
async def create_relationship_route(
    civilization_id: str = Path(..., description="ID of the first civilization"),
    other_civilization_id: str = Body(..., description="ID of the second civilization"),
    relationship_type: str = Body(..., description="Type of relationship"),
    relationship_strength: float = Body(..., ge=-1.0, le=1.0, description="Relationship strength (-1 to 1)"),
    description: Optional[str] = Body(None, description="Optional description"),
):
    """
    Create a relationship between two civilizations

    Relationship types might include: ally, enemy, trade_partner, neutral, vassal, etc.
    Strength ranges from -1 (very hostile) to 1 (very friendly)
    """
    result = await create_relationship_service(
        civilization_id, other_civilization_id, relationship_type, relationship_strength, description
    )
    return result


@router.get("/{civilization_id}/relationships")
async def get_civilization_relationships_route(
    civilization_id: str = Path(..., description="ID of the civilization")
):
    """
    Get all relationships for a specific civilization

    Returns both incoming and outgoing relationships
    """
    relationships = await get_civilization_relationships_service(civilization_id)
    return {"relationships": relationships}


# History endpoints
@router.post("/{civilization_id}/history", response_model=dict)
async def add_history_event_route(
    civilization_id: str = Path(..., description="ID of the civilization"),
    event_type: str = Body(..., description="Type of historical event"),
    title: str = Body(..., description="Title of the event"),
    description: Optional[str] = Body(None, description="Detailed description"),
    year: Optional[int] = Body(None, description="Year the event occurred"),
    era: Optional[str] = Body(None, description="Historical era"),
    impact_level: Optional[str] = Body(None, description="Impact level of the event"),
    affected_attributes: Optional[List[str]] = Body(None, description="Attributes affected by this event"),
):
    """
    Add a historical event to a civilization

    Event types might include: founding, war, discovery, disaster, reform, etc.
    Impact levels: minor, moderate, major, transformative
    """
    result = await add_history_event_service(
        civilization_id, event_type, title, description, year, era, impact_level, affected_attributes
    )
    return result


@router.get("/{civilization_id}/history", response_model=CivilizationHistoryList)
async def get_civilization_history_route(
    civilization_id: str = Path(..., description="ID of the civilization"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get historical events for a civilization

    Events are returned sorted by year (most recent first)
    """
    result = await get_civilization_history_service(civilization_id, skip, limit)
    
    return CivilizationHistoryList(
        events=result["events"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# Template endpoints
@router.post("/templates", response_model=dict)
async def create_template_route(
    name: str = Body(..., description="Template name"),
    metadata: CivilizationMetadata = Body(..., description="Template metadata"),
    description: Optional[str] = Body(None, description="Template description"),
):
    """
    Create a civilization template

    Templates can be used to quickly create new civilizations with predefined attributes
    """
    result = await create_template_service(name, metadata, description)
    return result


@router.get("/templates")
async def list_templates_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    List all civilization templates

    Templates are predefined civilization configurations that can be used
    to quickly create new civilizations
    """
    result = await list_templates_service(skip, limit)
    return result


@router.post("/templates/{template_id}/create", response_model=dict)
async def create_civilization_from_template_route(
    template_id: str = Path(..., description="ID of the template to use"),
    overrides: Optional[dict] = Body(None, description="Override specific attributes"),
):
    """
    Create a new civilization based on a template

    You can optionally override specific attributes from the template
    """
    result = await create_civilization_from_template_service(template_id, overrides)
    return result
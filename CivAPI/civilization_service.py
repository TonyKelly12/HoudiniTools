# app/services/civilization_service.py
"""
Service layer for civilization operations
"""
from fastapi import HTTPException
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..database import (
    store_civilization,
    get_civilization_by_id,
    update_civilization,
    list_civilizations,
    delete_civilization,
    search_civilizations,
    get_civilizations_by_attribute,
    get_civilization_statistics,
    get_attribute_distribution,
    find_similar_civilizations,
    store_relationship,
    get_relationship_by_id,
    update_relationship,
    list_relationships,
    get_civilization_relationships,
    delete_relationship,
    store_history_event,
    get_civilization_history,
    delete_history_event,
    store_template,
    list_templates,
    get_template_by_id,
)
from ..models.civilization_schema import (
    CivilizationMetadata,
    CivilizationResponse,
    CivilizationRelationship,
    CivilizationHistoryEvent,
)


async def create_civilization(metadata: CivilizationMetadata) -> str:
    """Create a new civilization"""
    try:
        # Convert metadata to dict
        civilization_data = {"metadata": metadata.model_dump()}
        
        # Store in database
        civilization_id = await store_civilization(civilization_data)
        
        return civilization_id
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create civilization: {str(e)}"
        )


async def get_civilization_by_id_service(civilization_id: str):
    """Get a civilization by its ID"""
    try:
        # Validate ObjectId format
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        document = await get_civilization_by_id(civilization_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Civilization not found")
        
        # Convert to response model
        response = CivilizationResponse(
            id=str(document["_id"]),
            metadata=CivilizationMetadata(**document["metadata"]),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving civilization: {str(e)}"
        )


async def update_civilization_service(civilization_id: str, update_data: dict):
    """Update a civilization"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        # If metadata is being updated, validate it
        if "metadata" in update_data:
            CivilizationMetadata(**update_data["metadata"])
        
        success = await update_civilization(civilization_id, update_data)
        
        if not success:
            raise HTTPException(status_code=404, detail="Civilization not found")
        
        return {"message": "Civilization updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating civilization: {str(e)}"
        )


async def list_civilizations_service(
    skip: int = 0,
    limit: int = 100,
    government_type: Optional[str] = None,
    technology_level: Optional[str] = None,
    population_size: Optional[str] = None,
    primary_economy: Optional[str] = None,
    primary_religion: Optional[str] = None,
    settlement_pattern: Optional[str] = None,
    primary_terrain: Optional[str] = None,
    tag: Optional[str] = None,
) -> Dict[str, Any]:
    """List civilizations with optional filtering"""
    # Build filters
    filters = {}
    
    if government_type:
        filters["metadata.government_type"] = government_type
    if technology_level:
        filters["metadata.technology_level"] = technology_level
    if population_size:
        filters["metadata.population_size"] = population_size
    if primary_economy:
        filters["metadata.primary_economy"] = primary_economy
    if primary_religion:
        filters["metadata.primary_religion"] = primary_religion
    if settlement_pattern:
        filters["metadata.settlement_pattern"] = settlement_pattern
    if primary_terrain:
        filters["metadata.primary_terrain"] = primary_terrain
    if tag:
        filters["metadata.tags"] = tag

    try:
        documents, total_count = await list_civilizations(skip, limit, filters)
        
        # Convert to response models
        civilizations = []
        for doc in documents:
            civilizations.append(
                CivilizationResponse(
                    id=str(doc["_id"]),
                    metadata=CivilizationMetadata(**doc["metadata"]),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            )
        
        return {
            "civilizations": civilizations,
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing civilizations: {str(e)}"
        )


async def delete_civilization_service(civilization_id: str):
    """Delete a civilization by its ID"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        success = await delete_civilization(civilization_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Civilization not found")
        
        return {"message": "Civilization deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting civilization: {str(e)}"
        )


async def search_civilizations_service(
    query: str, skip: int = 0, limit: int = 100
) -> Dict[str, Any]:
    """Search civilizations by text"""
    try:
        documents, total_count = await search_civilizations(query, skip, limit)
        
        # Convert to response models
        civilizations = []
        for doc in documents:
            civilizations.append(
                CivilizationResponse(
                    id=str(doc["_id"]),
                    metadata=CivilizationMetadata(**doc["metadata"]),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            )
        
        return {
            "civilizations": civilizations,
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "query": query,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error searching civilizations: {str(e)}"
        )


async def get_civilizations_by_attribute_service(
    attribute_name: str, attribute_value: str, skip: int = 0, limit: int = 100
) -> Dict[str, Any]:
    """Get civilizations with a specific attribute value"""
    try:
        documents, total_count = await get_civilizations_by_attribute(
            attribute_name, attribute_value, skip, limit
        )
        
        # Convert to response models
        civilizations = []
        for doc in documents:
            civilizations.append(
                CivilizationResponse(
                    id=str(doc["_id"]),
                    metadata=CivilizationMetadata(**doc["metadata"]),
                    created_at=doc["created_at"],
                    updated_at=doc["updated_at"],
                )
            )
        
        return {
            "civilizations": civilizations,
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
            "attribute": attribute_name,
            "value": attribute_value,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting civilizations by attribute: {str(e)}"
        )


async def get_statistics_service():
    """Get civilization statistics"""
    try:
        stats = await get_civilization_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting statistics: {str(e)}"
        )


async def get_attribute_distribution_service(attribute_name: str):
    """Get distribution of values for a specific attribute"""
    try:
        distribution = await get_attribute_distribution(attribute_name)
        return {
            "attribute": attribute_name,
            "distribution": distribution
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting attribute distribution: {str(e)}"
        )


async def find_similar_civilizations_service(
    civilization_id: str, threshold: float = 0.5
):
    """Find civilizations similar to the given one"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        similar_civs = await find_similar_civilizations(civilization_id, threshold)
        
        # Convert to response models
        civilizations = []
        for doc in similar_civs:
            civ_response = CivilizationResponse(
                id=str(doc["_id"]),
                metadata=CivilizationMetadata(**doc["metadata"]),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
            # Add similarity score to the response
            civilizations.append({
                "civilization": civ_response,
                "similarity_score": doc["similarity_score"]
            })
        
        return {
            "reference_civilization_id": civilization_id,
            "similar_civilizations": civilizations,
            "threshold": threshold
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error finding similar civilizations: {str(e)}"
        )


# Relationship services
async def create_relationship_service(
    civilization_a_id: str,
    civilization_b_id: str,
    relationship_type: str,
    relationship_strength: float,
    description: Optional[str] = None
):
    """Create a relationship between two civilizations"""
    try:
        ObjectId(civilization_a_id)
        ObjectId(civilization_b_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    # Verify both civilizations exist
    civ_a = await get_civilization_by_id(civilization_a_id)
    civ_b = await get_civilization_by_id(civilization_b_id)
    
    if not civ_a or not civ_b:
        raise HTTPException(status_code=404, detail="One or both civilizations not found")

    try:
        relationship_data = {
            "civilization_a_id": civilization_a_id,
            "civilization_b_id": civilization_b_id,
            "relationship_type": relationship_type,
            "relationship_strength": relationship_strength,
            "description": description,
        }
        
        relationship_id = await store_relationship(relationship_data)
        return {"id": relationship_id, "message": "Relationship created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating relationship: {str(e)}"
        )


async def get_civilization_relationships_service(civilization_id: str):
    """Get all relationships for a civilization"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        relationships = await get_civilization_relationships(civilization_id)
        
        # Convert to response models
        response_relationships = []
        for rel in relationships:
            response_relationships.append(
                CivilizationRelationship(
                    id=str(rel["_id"]),
                    civilization_a_id=rel["civilization_a_id"],
                    civilization_b_id=rel["civilization_b_id"],
                    relationship_type=rel["relationship_type"],
                    relationship_strength=rel["relationship_strength"],
                    description=rel.get("description"),
                    created_at=rel["created_at"],
                    updated_at=rel["updated_at"],
                )
            )
        
        return response_relationships
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting relationships: {str(e)}"
        )


# History services
async def add_history_event_service(
    civilization_id: str,
    event_type: str,
    title: str,
    description: Optional[str] = None,
    year: Optional[int] = None,
    era: Optional[str] = None,
    impact_level: Optional[str] = None,
    affected_attributes: Optional[List[str]] = None
):
    """Add a historical event to a civilization"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    # Verify civilization exists
    civ = await get_civilization_by_id(civilization_id)
    if not civ:
        raise HTTPException(status_code=404, detail="Civilization not found")

    try:
        event_data = {
            "civilization_id": civilization_id,
            "event_type": event_type,
            "title": title,
            "description": description,
            "year": year,
            "era": era,
            "impact_level": impact_level,
            "affected_attributes": affected_attributes,
        }
        
        event_id = await store_history_event(event_data)
        return {"id": event_id, "message": "History event added successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error adding history event: {str(e)}"
        )


async def get_civilization_history_service(
    civilization_id: str, skip: int = 0, limit: int = 100
):
    """Get history events for a civilization"""
    try:
        ObjectId(civilization_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid civilization ID format")

    try:
        documents, total_count = await get_civilization_history(civilization_id, skip, limit)
        
        # Convert to response models
        events = []
        for doc in documents:
            events.append(
                CivilizationHistoryEvent(
                    id=str(doc["_id"]),
                    civilization_id=doc["civilization_id"],
                    event_type=doc["event_type"],
                    title=doc["title"],
                    description=doc.get("description"),
                    year=doc.get("year"),
                    era=doc.get("era"),
                    impact_level=doc.get("impact_level"),
                    affected_attributes=doc.get("affected_attributes"),
                    created_at=doc["created_at"],
                )
            )
        
        return {
            "events": events,
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting civilization history: {str(e)}"
        )


# Template services
async def create_template_service(name: str, metadata: CivilizationMetadata, description: Optional[str] = None):
    """Create a civilization template"""
    try:
        template_data = {
            "name": name,
            "description": description,
            "metadata": metadata.model_dump(),
        }
        
        template_id = await store_template(template_data)
        return {"id": template_id, "message": "Template created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating template: {str(e)}"
        )


async def list_templates_service(skip: int = 0, limit: int = 100):
    """List civilization templates"""
    try:
        documents, total_count = await list_templates(skip, limit)
        
        templates = []
        for doc in documents:
            templates.append({
                "id": str(doc["_id"]),
                "name": doc["name"],
                "description": doc.get("description"),
                "metadata": doc["metadata"],
                "created_at": doc["created_at"],
                "updated_at": doc["updated_at"],
            })
        
        return {
            "templates": templates,
            "total": total_count,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing templates: {str(e)}"
        )


async def create_civilization_from_template_service(template_id: str, overrides: Optional[dict] = None):
    """Create a new civilization based on a template"""
    try:
        ObjectId(template_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    try:
        template = await get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Start with template metadata
        metadata_dict = template["metadata"].copy()
        
        # Apply any overrides
        if overrides:
            metadata_dict.update(overrides)
        
        # Create civilization metadata
        metadata = CivilizationMetadata(**metadata_dict)
        
        # Create the civilization
        civilization_id = await create_civilization(metadata)
        
        return {"id": civilization_id, "message": "Civilization created from template successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error creating civilization from template: {str(e)}"
        )
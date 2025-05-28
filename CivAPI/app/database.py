# app/database.py
"""
MongoDB connection for civilization data storage
"""
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from typing import Tuple, List, Dict, Any

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "civilization_database")

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGO_URI)
db = async_client[DATABASE_NAME]

# Collections for civilization data
civilizations_collection = db.civilizations
relationships_collection = db.relationships
history_collection = db.history
templates_collection = db.templates  # For civilization templates/presets


async def store_civilization(civilization_data):
    """Store a civilization definition in the database"""
    document = civilization_data.copy()
    document["created_at"] = datetime.utcnow()
    document["updated_at"] = document["created_at"]

    result = await civilizations_collection.insert_one(document)
    return str(result.inserted_id)


async def get_civilization_by_id(civilization_id):
    """Get a civilization by its ID"""
    document = await civilizations_collection.find_one({"_id": ObjectId(civilization_id)})
    return document


async def update_civilization(civilization_id, update_data):
    """Update a civilization definition"""
    update_data["updated_at"] = datetime.utcnow()

    result = await civilizations_collection.update_one(
        {"_id": ObjectId(civilization_id)}, {"$set": update_data}
    )

    return result.modified_count > 0


async def list_civilizations(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List civilizations with pagination and filtering
    Returns both the list of documents and the total count
    """
    # Build query based on filters
    query = filters or {}

    # Get total count for pagination
    total_count = await civilizations_collection.count_documents(query)

    # Get cursor with pagination
    cursor = (
        civilizations_collection.find(query)
        .skip(skip)
        .limit(limit)
        .sort("updated_at", -1)
    )

    # Convert to list
    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def delete_civilization(civilization_id):
    """Delete a civilization definition"""
    result = await civilizations_collection.delete_one({"_id": ObjectId(civilization_id)})
    return result.deleted_count > 0


async def search_civilizations(
    query_text: str, skip=0, limit=100
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Search civilizations by text in name, description, and tags
    """
    # Create text search query
    search_query = {
        "$or": [
            {"metadata.name": {"$regex": query_text, "$options": "i"}},
            {"metadata.description": {"$regex": query_text, "$options": "i"}},
            {"metadata.tags": {"$regex": query_text, "$options": "i"}},
        ]
    }

    # Get total count
    total_count = await civilizations_collection.count_documents(search_query)

    # Get documents
    cursor = (
        civilizations_collection.find(search_query)
        .skip(skip)
        .limit(limit)
        .sort("updated_at", -1)
    )

    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def get_civilizations_by_attribute(
    attribute_name: str, attribute_value: str, skip=0, limit=100
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get civilizations that have a specific attribute value
    """
    query = {f"metadata.{attribute_name}": attribute_value}

    total_count = await civilizations_collection.count_documents(query)

    cursor = (
        civilizations_collection.find(query)
        .skip(skip)
        .limit(limit)
        .sort("updated_at", -1)
    )

    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


# Relationship operations
async def store_relationship(relationship_data):
    """Store a relationship between civilizations"""
    document = relationship_data.copy()
    document["created_at"] = datetime.utcnow()
    document["updated_at"] = document["created_at"]

    result = await relationships_collection.insert_one(document)
    return str(result.inserted_id)


async def get_relationship_by_id(relationship_id):
    """Get a relationship by its ID"""
    document = await relationships_collection.find_one({"_id": ObjectId(relationship_id)})
    return document


async def update_relationship(relationship_id, update_data):
    """Update a relationship definition"""
    update_data["updated_at"] = datetime.utcnow()

    result = await relationships_collection.update_one(
        {"_id": ObjectId(relationship_id)}, {"$set": update_data}
    )

    return result.modified_count > 0


async def list_relationships(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    List relationships with pagination and filtering
    """
    query = filters or {}

    total_count = await relationships_collection.count_documents(query)

    cursor = (
        relationships_collection.find(query)
        .skip(skip)
        .limit(limit)
        .sort("updated_at", -1)
    )

    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def get_civilization_relationships(civilization_id):
    """Get all relationships for a specific civilization"""
    query = {
        "$or": [
            {"civilization_a_id": civilization_id},
            {"civilization_b_id": civilization_id}
        ]
    }

    cursor = relationships_collection.find(query).sort("updated_at", -1)

    relationships = []
    async for document in cursor:
        relationships.append(document)

    return relationships


async def delete_relationship(relationship_id):
    """Delete a relationship"""
    result = await relationships_collection.delete_one({"_id": ObjectId(relationship_id)})
    return result.deleted_count > 0


# History operations
async def store_history_event(event_data):
    """Store a historical event"""
    document = event_data.copy()
    document["created_at"] = datetime.utcnow()

    result = await history_collection.insert_one(document)
    return str(result.inserted_id)


async def get_civilization_history(
    civilization_id, skip=0, limit=100
) -> Tuple[List[Dict[str, Any]], int]:
    """Get history events for a civilization"""
    query = {"civilization_id": civilization_id}

    total_count = await history_collection.count_documents(query)

    cursor = (
        history_collection.find(query)
        .skip(skip)
        .limit(limit)
        .sort("year", -1)  # Sort by year descending (most recent first)
    )

    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def delete_history_event(event_id):
    """Delete a history event"""
    result = await history_collection.delete_one({"_id": ObjectId(event_id)})
    return result.deleted_count > 0


# Template operations (for civilization presets)
async def store_template(template_data):
    """Store a civilization template"""
    document = template_data.copy()
    document["created_at"] = datetime.utcnow()
    document["updated_at"] = document["created_at"]

    result = await templates_collection.insert_one(document)
    return str(result.inserted_id)


async def list_templates(
    skip=0, limit=100, filters=None
) -> Tuple[List[Dict[str, Any]], int]:
    """List civilization templates"""
    query = filters or {}

    total_count = await templates_collection.count_documents(query)

    cursor = (
        templates_collection.find(query)
        .skip(skip)
        .limit(limit)
        .sort("name", 1)
    )

    documents = []
    async for document in cursor:
        documents.append(document)

    return documents, total_count


async def get_template_by_id(template_id):
    """Get a template by its ID"""
    document = await templates_collection.find_one({"_id": ObjectId(template_id)})
    return document


# Analytics and aggregation functions
async def get_civilization_statistics():
    """Get various statistics about civilizations in the database"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_civilizations": {"$sum": 1},
                "government_types": {"$addToSet": "$metadata.government_type"},
                "technology_levels": {"$addToSet": "$metadata.technology_level"},
                "population_sizes": {"$addToSet": "$metadata.population_size"},
            }
        }
    ]

    result = await civilizations_collection.aggregate(pipeline).to_list(1)
    return result[0] if result else {}


async def get_attribute_distribution(attribute_name: str):
    """Get distribution of values for a specific attribute"""
    pipeline = [
        {
            "$group": {
                "_id": f"$metadata.{attribute_name}",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]

    result = await civilizations_collection.aggregate(pipeline).to_list(None)
    return result


async def find_similar_civilizations(civilization_id, similarity_threshold=0.5):
    """
    Find civilizations similar to the given one based on shared attributes
    This is a simplified similarity algorithm - in production you might want
    a more sophisticated approach
    """
    # Get the reference civilization
    reference = await get_civilization_by_id(civilization_id)
    if not reference:
        return []

    # Get all other civilizations
    all_civs, _ = await list_civilizations(limit=1000)  # Adjust limit as needed

    similar_civs = []
    ref_metadata = reference.get("metadata", {})

    # Define which attributes to compare for similarity
    comparable_attributes = [
        "government_type", "primary_economy", "social_stratification",
        "technology_level", "primary_religion", "cultural_values",
        "settlement_pattern", "primary_terrain"
    ]

    for civ in all_civs:
        if str(civ["_id"]) == civilization_id:
            continue  # Skip the reference civilization

        civ_metadata = civ.get("metadata", {})
        
        # Calculate similarity score
        matches = 0
        total_comparable = 0

        for attr in comparable_attributes:
            if attr in ref_metadata and attr in civ_metadata:
                total_comparable += 1
                if ref_metadata[attr] == civ_metadata[attr]:
                    matches += 1

        if total_comparable > 0:
            similarity_score = matches / total_comparable
            if similarity_score >= similarity_threshold:
                civ["similarity_score"] = similarity_score
                similar_civs.append(civ)

    # Sort by similarity score descending
    similar_civs.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return similar_civs[:10]  # Return top 10 most similar
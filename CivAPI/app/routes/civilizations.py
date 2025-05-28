# app/routes/civilizations.py
"""
API routes for civilization operations with comprehensive attribute support
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List, Dict, Any


from ..models.civilization_schema import (
    CivilizationMetadata,
    CivilizationList,
    CivilizationResponse,
    CivilizationHistoryList,
    AttributeDistribution,
    CivilizationComparison,
    ATTRIBUTE_CATEGORIES,
    # Import all enums for filtering
    SettlementPattern,
    PrimaryTerrain,
    PopulationDensity,
    ArchitectureStyle,
    GovernmentType,
    LeadershipSelection,
    CentralizationLevel,
    LegalSystem,
    PrimaryEconomy,
    TradeOrientation,
    CurrencyType,
    PropertyRights,
    SocialStratification,
    GenderRoles,
    FamilyStructure,
    AgeHierarchy,
    PrimaryReligion,
    ReligiousInfluence,
    ArtFocus,
    CulturalValues,
    EducationSystem,
    LiteracyRate,
    KnowledgeBasis,
    TechnologyLevel,
    MilitaryStructure,
    WarfareApproach,
    PrimaryWeapons,
    LanguageComplexity,
    WritingSystem,
    CommunicationMethods,
    ResourceUse,
    AgricultureType,
    EnergySources,
    PopulationSize,
    LifeExpectancy,
    TechnologicalAdoption,
    ExternalRelations,
    ChangeRate,
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
    metadata: CivilizationMetadata = Body(
        ..., description="Comprehensive civilization metadata"
    )
):
    """
    Create a new civilization with comprehensive attributes

    A civilization includes detailed attributes across multiple categories:
    - Geographic & Settlement: terrain, population density, architecture
    - Political Structure: government, leadership, legal systems
    - Economic Systems: economy type, trade, currency, property
    - Social Structure: stratification, gender roles, family structure
    - Cultural & Religious: religion, art, values, influence
    - Knowledge & Education: education, literacy, knowledge basis
    - Military & Defense: structure, approach, weapons
    - Communication & Language: complexity, writing, methods
    - Environmental Relations: resource use, agriculture, energy
    - Additional Attributes: population, life expectancy, adoption rates
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
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    # Geographic & Settlement filters
    settlement_pattern: Optional[SettlementPattern] = Query(
        None, description="Filter by settlement pattern"
    ),
    primary_terrain: Optional[PrimaryTerrain] = Query(
        None, description="Filter by primary terrain"
    ),
    population_density: Optional[PopulationDensity] = Query(
        None, description="Filter by population density"
    ),
    architecture_style: Optional[ArchitectureStyle] = Query(
        None, description="Filter by architecture style"
    ),
    # Political Structure filters
    government_type: Optional[GovernmentType] = Query(
        None, description="Filter by government type"
    ),
    leadership_selection: Optional[LeadershipSelection] = Query(
        None, description="Filter by leadership selection"
    ),
    centralization_level: Optional[CentralizationLevel] = Query(
        None, description="Filter by centralization level"
    ),
    legal_system: Optional[LegalSystem] = Query(
        None, description="Filter by legal system"
    ),
    # Economic System filters
    primary_economy: Optional[PrimaryEconomy] = Query(
        None, description="Filter by primary economy"
    ),
    trade_orientation: Optional[TradeOrientation] = Query(
        None, description="Filter by trade orientation"
    ),
    currency_type: Optional[CurrencyType] = Query(
        None, description="Filter by currency type"
    ),
    property_rights: Optional[PropertyRights] = Query(
        None, description="Filter by property rights"
    ),
    # Social Structure filters
    social_stratification: Optional[SocialStratification] = Query(
        None, description="Filter by social stratification"
    ),
    gender_roles: Optional[GenderRoles] = Query(
        None, description="Filter by gender roles"
    ),
    family_structure: Optional[FamilyStructure] = Query(
        None, description="Filter by family structure"
    ),
    age_hierarchy: Optional[AgeHierarchy] = Query(
        None, description="Filter by age hierarchy"
    ),
    # Cultural & Religious filters
    primary_religion: Optional[PrimaryReligion] = Query(
        None, description="Filter by primary religion"
    ),
    religious_influence: Optional[ReligiousInfluence] = Query(
        None, description="Filter by religious influence"
    ),
    art_focus: Optional[ArtFocus] = Query(None, description="Filter by art focus"),
    cultural_values: Optional[CulturalValues] = Query(
        None, description="Filter by cultural values"
    ),
    # Knowledge & Education filters
    education_system: Optional[EducationSystem] = Query(
        None, description="Filter by education system"
    ),
    literacy_rate: Optional[LiteracyRate] = Query(
        None, description="Filter by literacy rate"
    ),
    knowledge_basis: Optional[KnowledgeBasis] = Query(
        None, description="Filter by knowledge basis"
    ),
    technology_level: Optional[TechnologyLevel] = Query(
        None, description="Filter by technology level"
    ),
    # Military & Defense filters
    military_structure: Optional[MilitaryStructure] = Query(
        None, description="Filter by military structure"
    ),
    warfare_approach: Optional[WarfareApproach] = Query(
        None, description="Filter by warfare approach"
    ),
    primary_weapons: Optional[PrimaryWeapons] = Query(
        None, description="Filter by primary weapons"
    ),
    # Communication & Language filters
    language_complexity: Optional[LanguageComplexity] = Query(
        None, description="Filter by language complexity"
    ),
    writing_system: Optional[WritingSystem] = Query(
        None, description="Filter by writing system"
    ),
    communication_methods: Optional[CommunicationMethods] = Query(
        None, description="Filter by communication methods"
    ),
    # Environmental Relations filters
    resource_use: Optional[ResourceUse] = Query(
        None, description="Filter by resource use"
    ),
    agriculture_type: Optional[AgricultureType] = Query(
        None, description="Filter by agriculture type"
    ),
    energy_sources: Optional[EnergySources] = Query(
        None, description="Filter by energy sources"
    ),
    # Additional Attributes filters
    population_size: Optional[PopulationSize] = Query(
        None, description="Filter by population size"
    ),
    life_expectancy: Optional[LifeExpectancy] = Query(
        None, description="Filter by life expectancy"
    ),
    technological_adoption: Optional[TechnologicalAdoption] = Query(
        None, description="Filter by technological adoption"
    ),
    external_relations: Optional[ExternalRelations] = Query(
        None, description="Filter by external relations"
    ),
    change_rate: Optional[ChangeRate] = Query(
        None, description="Filter by change rate"
    ),
    # General filters
    tag: Optional[str] = Query(None, description="Filter by tag"),
):
    """
    List all civilizations with comprehensive filtering options

    Supports filtering by any civilization attribute across all categories.
    Use multiple filters to narrow down results to specific civilization types.
    """
    # Build filter dictionary
    filters = {}

    # Helper function to add filter if value exists
    def add_filter(field_name: str, value: Any):
        if value is not None:
            filters[f"metadata.{field_name}"] = (
                value.value if hasattr(value, "value") else value
            )

    # Geographic & Settlement
    add_filter("settlement_pattern", settlement_pattern)
    add_filter("primary_terrain", primary_terrain)
    add_filter("population_density", population_density)
    add_filter("architecture_style", architecture_style)

    # Political Structure
    add_filter("government_type", government_type)
    add_filter("leadership_selection", leadership_selection)
    add_filter("centralization_level", centralization_level)
    add_filter("legal_system", legal_system)

    # Economic System
    add_filter("primary_economy", primary_economy)
    add_filter("trade_orientation", trade_orientation)
    add_filter("currency_type", currency_type)
    add_filter("property_rights", property_rights)

    # Social Structure
    add_filter("social_stratification", social_stratification)
    add_filter("gender_roles", gender_roles)
    add_filter("family_structure", family_structure)
    add_filter("age_hierarchy", age_hierarchy)

    # Cultural & Religious
    add_filter("primary_religion", primary_religion)
    add_filter("religious_influence", religious_influence)
    add_filter("art_focus", art_focus)
    add_filter("cultural_values", cultural_values)

    # Knowledge & Education
    add_filter("education_system", education_system)
    add_filter("literacy_rate", literacy_rate)
    add_filter("knowledge_basis", knowledge_basis)
    add_filter("technology_level", technology_level)

    # Military & Defense
    add_filter("military_structure", military_structure)
    add_filter("warfare_approach", warfare_approach)
    add_filter("primary_weapons", primary_weapons)

    # Communication & Language
    add_filter("language_complexity", language_complexity)
    add_filter("writing_system", writing_system)
    add_filter("communication_methods", communication_methods)

    # Environmental Relations
    add_filter("resource_use", resource_use)
    add_filter("agriculture_type", agriculture_type)
    add_filter("energy_sources", energy_sources)

    # Additional Attributes
    add_filter("population_size", population_size)
    add_filter("life_expectancy", life_expectancy)
    add_filter("technological_adoption", technological_adoption)
    add_filter("external_relations", external_relations)
    add_filter("change_rate", change_rate)

    # General filters
    if tag:
        filters["metadata.tags"] = tag

    result = await list_civilizations_service(skip=skip, limit=limit, filters=filters)

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/attributes", response_model=Dict[str, Any])
async def get_attribute_metadata():
    """
    Get metadata about all available civilization attributes

    Returns information about attribute categories and their possible values.
    Useful for building dynamic filters and understanding the data model.
    """
    # Get all enum values for each attribute
    attribute_metadata = {}

    for category_key, category_info in ATTRIBUTE_CATEGORIES.items():
        attribute_metadata[category_key] = {
            "name": category_info["name"],
            "attributes": {},
        }

        for attr_name in category_info["attributes"]:
            # Get the corresponding enum class
            enum_class = None
            if attr_name == "settlement_pattern":
                enum_class = SettlementPattern
            elif attr_name == "primary_terrain":
                enum_class = PrimaryTerrain
            elif attr_name == "population_density":
                enum_class = PopulationDensity
            elif attr_name == "architecture_style":
                enum_class = ArchitectureStyle
            elif attr_name == "government_type":
                enum_class = GovernmentType
            elif attr_name == "leadership_selection":
                enum_class = LeadershipSelection
            elif attr_name == "centralization_level":
                enum_class = CentralizationLevel
            elif attr_name == "legal_system":
                enum_class = LegalSystem
            elif attr_name == "primary_economy":
                enum_class = PrimaryEconomy
            elif attr_name == "trade_orientation":
                enum_class = TradeOrientation
            elif attr_name == "currency_type":
                enum_class = CurrencyType
            elif attr_name == "property_rights":
                enum_class = PropertyRights
            elif attr_name == "social_stratification":
                enum_class = SocialStratification
            elif attr_name == "gender_roles":
                enum_class = GenderRoles
            elif attr_name == "family_structure":
                enum_class = FamilyStructure
            elif attr_name == "age_hierarchy":
                enum_class = AgeHierarchy
            elif attr_name == "primary_religion":
                enum_class = PrimaryReligion
            elif attr_name == "religious_influence":
                enum_class = ReligiousInfluence
            elif attr_name == "art_focus":
                enum_class = ArtFocus
            elif attr_name == "cultural_values":
                enum_class = CulturalValues
            elif attr_name == "education_system":
                enum_class = EducationSystem
            elif attr_name == "literacy_rate":
                enum_class = LiteracyRate
            elif attr_name == "knowledge_basis":
                enum_class = KnowledgeBasis
            elif attr_name == "technology_level":
                enum_class = TechnologyLevel
            elif attr_name == "military_structure":
                enum_class = MilitaryStructure
            elif attr_name == "warfare_approach":
                enum_class = WarfareApproach
            elif attr_name == "primary_weapons":
                enum_class = PrimaryWeapons
            elif attr_name == "language_complexity":
                enum_class = LanguageComplexity
            elif attr_name == "writing_system":
                enum_class = WritingSystem
            elif attr_name == "communication_methods":
                enum_class = CommunicationMethods
            elif attr_name == "resource_use":
                enum_class = ResourceUse
            elif attr_name == "agriculture_type":
                enum_class = AgricultureType
            elif attr_name == "energy_sources":
                enum_class = EnergySources
            elif attr_name == "population_size":
                enum_class = PopulationSize
            elif attr_name == "life_expectancy":
                enum_class = LifeExpectancy
            elif attr_name == "technological_adoption":
                enum_class = TechnologicalAdoption
            elif attr_name == "external_relations":
                enum_class = ExternalRelations
            elif attr_name == "change_rate":
                enum_class = ChangeRate

            if enum_class:
                attribute_metadata[category_key]["attributes"][attr_name] = {
                    "values": [member.value for member in enum_class],
                    "description": f"Available values for {attr_name.replace('_', ' ').title()}",
                }

    return {
        "categories": attribute_metadata,
        "total_attributes": sum(
            len(cat["attributes"]) for cat in attribute_metadata.values()
        ),
    }


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
    Works with any attribute from the civilization model.
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


@router.get("/by-category/{category_name}", response_model=CivilizationList)
async def get_civilizations_by_category_route(
    category_name: str = Path(
        ..., description="Category name (e.g., 'political_structure')"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get civilizations grouped by attribute category

    Available categories:
    - geographic_settlement
    - political_structure
    - economic_system
    - social_structure
    - cultural_religious
    - knowledge_education
    - military_defense
    - communication_language
    - environmental_relations
    - additional_attributes
    """
    if category_name not in ATTRIBUTE_CATEGORIES:
        raise HTTPException(
            status_code=404,
            detail=f"Category '{category_name}' not found. Available categories: {list(ATTRIBUTE_CATEGORIES.keys())}",
        )

    # This would require a custom service method to aggregate by category
    # For now, return a simple list
    result = await list_civilizations_service(skip=skip, limit=limit)

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics_route():
    """
    Get comprehensive statistics about civilizations in the database

    Returns information about:
    - Total civilization count
    - Distribution across major attribute categories
    - Most common values for key attributes
    """
    stats = await get_statistics_service()
    return stats


@router.get(
    "/attribute-distribution/{attribute_name}", response_model=AttributeDistribution
)
async def get_attribute_distribution_route(
    attribute_name: str = Path(..., description="Attribute name to analyze")
):
    """
    Get distribution of values for a specific attribute

    Returns a breakdown showing how many civilizations have each value
    for the specified attribute. Useful for understanding data patterns.
    """
    distribution = await get_attribute_distribution_service(attribute_name)

    return AttributeDistribution(
        attribute_name=attribute_name,
        distribution=distribution["distribution"],
        total_civilizations=sum(item["count"] for item in distribution["distribution"]),
    )


@router.post("/advanced-search", response_model=CivilizationList)
async def advanced_search_route(
    filters: Dict[str, Any] = Body(..., description="Advanced filter criteria"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Advanced search with multiple attribute filters

    Send a JSON body with multiple attribute filters:
    ```json
    {
        "government_type": "democracy",
        "technology_level": "information_age",
        "primary_economy": "service",
        "population_size": "large"
    }
    ```
    """
    # Convert filters to the format expected by the service
    formatted_filters = {}
    for key, value in filters.items():
        formatted_filters[f"metadata.{key}"] = value

    result = await list_civilizations_service(
        skip=skip, limit=limit, filters=formatted_filters
    )

    return CivilizationList(
        civilizations=result["civilizations"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


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
    update_data: dict = Body(
        ..., description="Fields to update (partial update supported)"
    ),
):
    """
    Update a civilization's attributes

    Supports partial updates - only include the fields you want to change.
    Can update any attribute from any category.
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


@router.get("/{civilization_id}/similar", response_model=Dict[str, Any])
async def find_similar_civilizations_route(
    civilization_id: str = Path(..., description="ID of the reference civilization"),
    threshold: float = Query(
        0.5, ge=0.0, le=1.0, description="Similarity threshold (0.0 to 1.0)"
    ),
    focus_attributes: Optional[List[str]] = Query(
        None, description="Specific attributes to focus on for similarity"
    ),
):
    """
    Find civilizations similar to the given one

    Uses attribute matching across all categories to find similar civilizations.
    Optionally focus on specific attributes for targeted similarity matching.
    """
    result = await find_similar_civilizations_service(civilization_id, threshold)
    return result


@router.post(
    "/{civilization_a_id}/compare/{civilization_b_id}",
    response_model=CivilizationComparison,
)
async def compare_civilizations_route(
    civilization_a_id: str = Path(..., description="ID of the first civilization"),
    civilization_b_id: str = Path(..., description="ID of the second civilization"),
):
    """
    Compare two civilizations across all attributes

    Returns detailed comparison showing similarities, differences, and overall similarity score.
    """
    # Get both civilizations
    civ_a = await get_civilization_by_id_service(civilization_a_id)
    civ_b = await get_civilization_by_id_service(civilization_b_id)

    # Calculate similarities and differences
    similarities = []
    differences = []
    matches = 0
    total_attributes = 0

    # Compare all attributes
    for attr_name in civ_a.metadata.model_fields.keys():
        if attr_name in [
            "name",
            "description",
            "tags",
            "created_by",
            "exact_population",
            "exact_life_expectancy",
            "territory_size_km2",
        ]:
            continue  # Skip these for comparison

        total_attributes += 1
        value_a = getattr(civ_a.metadata, attr_name)
        value_b = getattr(civ_b.metadata, attr_name)

        if value_a == value_b:
            matches += 1
            similarities.append(f"{attr_name.replace('_', ' ').title()}: {value_a}")
        else:
            differences.append(
                f"{attr_name.replace('_', ' ').title()}: "
                f"{civ_a.metadata.name} has '{value_a}', "
                f"{civ_b.metadata.name} has '{value_b}'"
            )

    similarity_score = matches / total_attributes if total_attributes > 0 else 0

    return CivilizationComparison(
        civilization_a=civ_a,
        civilization_b=civ_b,
        similarities=similarities,
        differences=differences,
        similarity_score=round(similarity_score, 3),
    )


# Relationship endpoints
@router.post("/{civilization_id}/relationships", response_model=dict)
async def create_relationship_route(
    civilization_id: str = Path(..., description="ID of the first civilization"),
    other_civilization_id: str = Body(..., description="ID of the second civilization"),
    relationship_type: str = Body(..., description="Type of relationship"),
    relationship_strength: float = Body(
        ..., ge=-1.0, le=1.0, description="Relationship strength (-1 to 1)"
    ),
    description: Optional[str] = Body(None, description="Optional description"),
):
    """
    Create a relationship between two civilizations

    Relationship types might include: ally, enemy, trade_partner, neutral, vassal, etc.
    Strength ranges from -1 (very hostile) to 1 (very friendly)
    """
    result = await create_relationship_service(
        civilization_id,
        other_civilization_id,
        relationship_type,
        relationship_strength,
        description,
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
    affected_attributes: Optional[List[str]] = Body(
        None, description="Attributes affected by this event"
    ),
):
    """
    Add a historical event to a civilization

    Event types might include: founding, war, discovery, disaster, reform, etc.
    Impact levels: minor, moderate, major, transformative
    """
    result = await add_history_event_service(
        civilization_id,
        event_type,
        title,
        description,
        year,
        era,
        impact_level,
        affected_attributes,
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

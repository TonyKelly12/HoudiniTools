"""
Civilization Database API Package

A comprehensive API for managing and analyzing civilization data with detailed attributes.
"""

from .civilization_schema import (
    CivilizationMetadata,
    CivilizationResponse,
    CivilizationList,
    CivilizationRelationship,
    CivilizationRelationshipList,
    CivilizationHistoryEvent,
    CivilizationHistoryList,
    # Export all enums for easy access
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

from .civilization_service import (
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

from .civilizations import router as civilizations_router

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "API for storing, retrieving, and analyzing civilization data"

# app/models/__init__.py
"""
Data models for the Civilization Database API
"""

__all__ = [
    "CivilizationMetadata",
    "CivilizationResponse",
    "CivilizationList",
    "CivilizationRelationship",
    "CivilizationRelationshipList",
    "CivilizationHistoryEvent",
    "CivilizationHistoryList",
    # Enums
    "SettlementPattern",
    "PrimaryTerrain",
    "PopulationDensity",
    "ArchitectureStyle",
    "GovernmentType",
    "LeadershipSelection",
    "CentralizationLevel",
    "LegalSystem",
    "PrimaryEconomy",
    "TradeOrientation",
    "CurrencyType",
    "PropertyRights",
    "SocialStratification",
    "GenderRoles",
    "FamilyStructure",
    "AgeHierarchy",
    "PrimaryReligion",
    "ReligiousInfluence",
    "ArtFocus",
    "CulturalValues",
    "EducationSystem",
    "LiteracyRate",
    "KnowledgeBasis",
    "TechnologyLevel",
    "MilitaryStructure",
    "WarfareApproach",
    "PrimaryWeapons",
    "LanguageComplexity",
    "WritingSystem",
    "CommunicationMethods",
    "ResourceUse",
    "AgricultureType",
    "EnergySources",
    "PopulationSize",
    "LifeExpectancy",
    "TechnologicalAdoption",
    "ExternalRelations",
    "ChangeRate",
]

# app/services/__init__.py
"""
Service layer for business logic
"""

__all__ = [
    "create_civilization",
    "get_civilization_by_id_service",
    "update_civilization_service",
    "list_civilizations_service",
    "delete_civilization_service",
    "search_civilizations_service",
    "get_civilizations_by_attribute_service",
    "get_statistics_service",
    "get_attribute_distribution_service",
    "find_similar_civilizations_service",
    "create_relationship_service",
    "get_civilization_relationships_service",
    "add_history_event_service",
    "get_civilization_history_service",
    "create_template_service",
    "list_templates_service",
    "create_civilization_from_template_service",
]

# app/routes/__init__.py
"""
API routes package
"""

__all__ = ["civilizations_router"]

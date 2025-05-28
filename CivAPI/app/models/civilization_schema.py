# app/models/civilization_schema.py
"""
Pydantic models for civilization data validation and API documentation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any  # Added Any import
from enum import Enum
from datetime import datetime


# Geographic & Settlement Enums
class SettlementPattern(str, Enum):
    NOMADIC = "nomadic"
    SEMI_NOMADIC = "semi_nomadic"
    SETTLED = "settled"
    URBAN = "urban"
    RURAL = "rural"
    MIXED = "mixed"


class PrimaryTerrain(str, Enum):
    DESERT = "desert"
    FOREST = "forest"
    MOUNTAINS = "mountains"
    PLAINS = "plains"
    COASTAL = "coastal"
    ISLAND = "island"
    ARCTIC = "arctic"
    UNDERGROUND = "underground"


class PopulationDensity(str, Enum):
    SPARSE = "sparse"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MEGACITY = "megacity"


class ArchitectureStyle(str, Enum):
    TEMPORARY_STRUCTURES = "temporary_structures"
    WOOD = "wood"
    STONE = "stone"
    CLAY_ADOBE = "clay_adobe"
    METAL = "metal"
    MIXED_MATERIALS = "mixed_materials"


# Political Structure Enums
class GovernmentType(str, Enum):
    DEMOCRACY = "democracy"
    MONARCHY = "monarchy"
    OLIGARCHY = "oligarchy"
    THEOCRACY = "theocracy"
    TRIBAL_COUNCIL = "tribal_council"
    ANARCHY = "anarchy"
    DICTATORSHIP = "dictatorship"
    REPUBLIC = "republic"


class LeadershipSelection(str, Enum):
    HEREDITARY = "hereditary"
    ELECTED = "elected"
    APPOINTED = "appointed"
    COMBAT_TRIAL = "combat_trial"
    RELIGIOUS_SELECTION = "religious_selection"
    MERITOCRATIC = "meritocratic"


class CentralizationLevel(str, Enum):
    HIGHLY_CENTRALIZED = "highly_centralized"
    FEDERAL = "federal"
    CONFEDERATED = "confederated"
    DECENTRALIZED = "decentralized"
    TRIBAL = "tribal"


class LegalSystem(str, Enum):
    COMMON_LAW = "common_law"
    CIVIL_LAW = "civil_law"
    RELIGIOUS_LAW = "religious_law"
    CUSTOMARY_LAW = "customary_law"
    MIXED = "mixed"


# Economic System Enums
class PrimaryEconomy(str, Enum):
    HUNTER_GATHERER = "hunter_gatherer"
    AGRICULTURAL = "agricultural"
    PASTORAL = "pastoral"
    TRADE_BASED = "trade_based"
    INDUSTRIAL = "industrial"
    SERVICE = "service"
    MIXED = "mixed"


class TradeOrientation(str, Enum):
    ISOLATIONIST = "isolationist"
    LOCAL_TRADE_ONLY = "local_trade_only"
    REGIONAL_TRADE = "regional_trade"
    INTERNATIONAL_TRADE = "international_trade"
    TRADE_EMPIRE = "trade_empire"


class CurrencyType(str, Enum):
    BARTER = "barter"
    COMMODITY_MONEY = "commodity_money"
    METAL_COINS = "metal_coins"
    PAPER_CURRENCY = "paper_currency"
    DIGITAL = "digital"
    MIXED = "mixed"


class PropertyRights(str, Enum):
    COMMUNAL = "communal"
    PRIVATE = "private"
    MIXED = "mixed"
    STATE_OWNED = "state_owned"


# Social Structure Enums
class SocialStratification(str, Enum):
    EGALITARIAN = "egalitarian"
    CASTE_SYSTEM = "caste_system"
    CLASS_BASED = "class_based"
    MERITOCRATIC = "meritocratic"
    MIXED = "mixed"


class GenderRoles(str, Enum):
    EGALITARIAN = "egalitarian"
    PATRIARCHAL = "patriarchal"
    MATRIARCHAL = "matriarchal"
    COMPLEMENTARY = "complementary"
    FLUID = "fluid"


class FamilyStructure(str, Enum):
    NUCLEAR = "nuclear"
    EXTENDED = "extended"
    CLAN_BASED = "clan_based"
    COMMUNAL = "communal"
    MATRILINEAL = "matrilineal"
    PATRILINEAL = "patrilineal"


class AgeHierarchy(str, Enum):
    ELDER_LED = "elder_led"
    YOUTH_ORIENTED = "youth_oriented"
    AGE_EGALITARIAN = "age_egalitarian"
    MIXED = "mixed"


# Cultural & Religious Enums
class PrimaryReligion(str, Enum):
    MONOTHEISTIC = "monotheistic"
    POLYTHEISTIC = "polytheistic"
    ANIMISTIC = "animistic"
    ATHEISTIC = "atheistic"
    ANCESTOR_WORSHIP = "ancestor_worship"
    NATURE_WORSHIP = "nature_worship"
    MIXED = "mixed"


class ReligiousInfluence(str, Enum):
    SECULAR = "secular"
    MODERATE_INFLUENCE = "moderate_influence"
    STRONG_INFLUENCE = "strong_influence"
    THEOCRATIC = "theocratic"


class ArtFocus(str, Enum):
    VISUAL_ARTS = "visual_arts"
    MUSIC = "music"
    LITERATURE = "literature"
    PERFORMANCE = "performance"
    CRAFTS = "crafts"
    ARCHITECTURE = "architecture"
    MIXED = "mixed"


class CulturalValues(str, Enum):
    INDIVIDUALISTIC = "individualistic"
    COLLECTIVISTIC = "collectivistic"
    HONOR_BASED = "honor_based"
    HARMONY_FOCUSED = "harmony_focused"
    ACHIEVEMENT_ORIENTED = "achievement_oriented"


# Knowledge & Education Enums
class EducationSystem(str, Enum):
    APPRENTICESHIP = "apprenticeship"
    FORMAL_SCHOOLS = "formal_schools"
    RELIGIOUS_EDUCATION = "religious_education"
    ORAL_TRADITION = "oral_tradition"
    SCIENTIFIC_METHOD = "scientific_method"
    MIXED = "mixed"


class LiteracyRate(str, Enum):
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNIVERSAL = "universal"


class KnowledgeBasis(str, Enum):
    EMPIRICAL_SCIENTIFIC = "empirical_scientific"
    TRADITIONAL_CULTURAL = "traditional_cultural"
    RELIGIOUS_MYSTICAL = "religious_mystical"
    MIXED = "mixed"


class TechnologyLevel(str, Enum):
    STONE_AGE = "stone_age"
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"
    PRE_INDUSTRIAL = "pre_industrial"
    INDUSTRIAL = "industrial"
    INFORMATION_AGE = "information_age"
    POST_SCARCITY = "post_scarcity"


# Military & Defense Enums
class MilitaryStructure(str, Enum):
    NO_MILITARY = "no_military"
    MILITIA = "militia"
    PROFESSIONAL_ARMY = "professional_army"
    WARRIOR_CLASS = "warrior_class"
    CONSCRIPTION = "conscription"
    MERCENARY = "mercenary"


class WarfareApproach(str, Enum):
    PACIFIST = "pacifist"
    DEFENSIVE_ONLY = "defensive_only"
    EXPANSIONIST = "expansionist"
    RAIDING_CULTURE = "raiding_culture"
    DIPLOMATIC = "diplomatic"


class PrimaryWeapons(str, Enum):
    MELEE = "melee"
    RANGED_PRIMITIVE = "ranged_primitive"
    GUNPOWDER = "gunpowder"
    MODERN_FIREARMS = "modern_firearms"
    ADVANCED_TECHNOLOGY = "advanced_technology"


# Communication & Language Enums
class LanguageComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MULTIPLE_LANGUAGES = "multiple_languages"


class WritingSystem(str, Enum):
    NONE = "none"
    PICTOGRAPHIC = "pictographic"
    IDEOGRAPHIC = "ideographic"
    ALPHABETIC = "alphabetic"
    MIXED = "mixed"


class CommunicationMethods(str, Enum):
    ORAL_ONLY = "oral_only"
    WRITTEN = "written"
    DIGITAL = "digital"
    TELEPATHIC_OTHER = "telepathic_other"


# Environmental Relations Enums
class ResourceUse(str, Enum):
    SUSTAINABLE = "sustainable"
    EXPLOITATIVE = "exploitative"
    CONSERVATION_FOCUSED = "conservation_focused"
    MIXED = "mixed"


class AgricultureType(str, Enum):
    NONE = "none"
    SUBSISTENCE = "subsistence"
    INTENSIVE = "intensive"
    PERMACULTURE = "permaculture"
    INDUSTRIAL = "industrial"


class EnergySources(str, Enum):
    HUMAN_ANIMAL = "human_animal"
    WOOD_BIOMASS = "wood_biomass"
    FOSSIL_FUELS = "fossil_fuels"
    RENEWABLE = "renewable"
    NUCLEAR = "nuclear"
    OTHER = "other"


# Additional Attributes Enums
class PopulationSize(str, Enum):
    TINY = "tiny"  # <1,000
    SMALL = "small"  # 1,000-10,000
    MEDIUM = "medium"  # 10,000-100,000
    LARGE = "large"  # 100,000-1,000,000
    MASSIVE = "massive"  # >1,000,000


class LifeExpectancy(str, Enum):
    VERY_SHORT = "very_short"  # <30
    SHORT = "short"  # 30-50
    MODERATE = "moderate"  # 50-70
    LONG = "long"  # 70-90
    VERY_LONG = "very_long"  # >90


class TechnologicalAdoption(str, Enum):
    TECHNOPHOBIC = "technophobic"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    PROGRESSIVE = "progressive"
    TECHNOPHILIC = "technophilic"


class ExternalRelations(str, Enum):
    XENOPHOBIC = "xenophobic"
    ISOLATIONIST = "isolationist"
    CAUTIOUS = "cautious"
    OPEN = "open"
    COSMOPOLITAN = "cosmopolitan"


class ChangeRate(str, Enum):
    STATIC = "static"
    SLOW_CHANGING = "slow_changing"
    MODERATE = "moderate"
    RAPID_CHANGE = "rapid_change"
    REVOLUTIONARY = "revolutionary"


# Main Pydantic Models
class CivilizationMetadata(BaseModel):
    """Comprehensive civilization metadata with all attributes"""

    # Basic Information
    name: str = Field(..., max_length=200, description="Name of the civilization")
    description: Optional[str] = Field(
        None, max_length=5000, description="Detailed description"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, max_items=50, description="Classification tags"
    )
    created_by: Optional[str] = Field(
        None, description="Creator of this civilization record"
    )

    # Geographic & Settlement
    settlement_pattern: SettlementPattern = Field(
        ..., description="Primary settlement pattern"
    )
    primary_terrain: PrimaryTerrain = Field(..., description="Primary terrain type")
    population_density: PopulationDensity = Field(
        ..., description="Population density classification"
    )
    architecture_style: ArchitectureStyle = Field(
        ..., description="Primary architectural style"
    )

    # Political Structure
    government_type: GovernmentType = Field(..., description="Type of government")
    leadership_selection: LeadershipSelection = Field(
        ..., description="How leaders are chosen"
    )
    centralization_level: CentralizationLevel = Field(
        ..., description="Level of political centralization"
    )
    legal_system: LegalSystem = Field(..., description="Primary legal system")

    # Economic Systems
    primary_economy: PrimaryEconomy = Field(..., description="Primary economic system")
    trade_orientation: TradeOrientation = Field(
        ..., description="Trade scope and orientation"
    )
    currency_type: CurrencyType = Field(..., description="Type of currency used")
    property_rights: PropertyRights = Field(
        ..., description="Property ownership system"
    )

    # Social Structure
    social_stratification: SocialStratification = Field(
        ..., description="Social hierarchy system"
    )
    gender_roles: GenderRoles = Field(..., description="Gender role structure")
    family_structure: FamilyStructure = Field(..., description="Family organization")
    age_hierarchy: AgeHierarchy = Field(..., description="Age-based social structure")

    # Cultural & Religious
    primary_religion: PrimaryReligion = Field(
        ..., description="Primary religious system"
    )
    religious_influence: ReligiousInfluence = Field(
        ..., description="Influence of religion on society"
    )
    art_focus: ArtFocus = Field(..., description="Primary artistic focus")
    cultural_values: CulturalValues = Field(..., description="Core cultural values")

    # Knowledge & Education
    education_system: EducationSystem = Field(..., description="Educational system")
    literacy_rate: LiteracyRate = Field(..., description="Literacy level")
    knowledge_basis: KnowledgeBasis = Field(..., description="Primary knowledge system")
    technology_level: TechnologyLevel = Field(
        ..., description="Technological development level"
    )

    # Military & Defense
    military_structure: MilitaryStructure = Field(
        ..., description="Military organization"
    )
    warfare_approach: WarfareApproach = Field(..., description="Approach to warfare")
    primary_weapons: PrimaryWeapons = Field(
        ..., description="Primary weapon technology"
    )

    # Communication & Language
    language_complexity: LanguageComplexity = Field(
        ..., description="Language complexity"
    )
    writing_system: WritingSystem = Field(..., description="Writing system used")
    communication_methods: CommunicationMethods = Field(
        ..., description="Primary communication methods"
    )

    # Environmental Relations
    resource_use: ResourceUse = Field(
        ..., description="Approach to resource utilization"
    )
    agriculture_type: AgricultureType = Field(..., description="Agricultural system")
    energy_sources: EnergySources = Field(..., description="Primary energy sources")

    # Additional Attributes
    population_size: PopulationSize = Field(..., description="Population size category")
    life_expectancy: LifeExpectancy = Field(..., description="Life expectancy category")
    technological_adoption: TechnologicalAdoption = Field(
        ..., description="Attitude toward new technology"
    )
    external_relations: ExternalRelations = Field(
        ..., description="Approach to external relations"
    )
    change_rate: ChangeRate = Field(..., description="Rate of societal change")

    # Exact Values (Optional for more precision)
    exact_population: Optional[int] = Field(
        None, ge=0, description="Exact population number"
    )
    exact_life_expectancy: Optional[float] = Field(
        None, ge=0, le=200, description="Exact life expectancy in years"
    )
    territory_size_km2: Optional[float] = Field(
        None, ge=0, description="Territory size in square kilometers"
    )

    model_config = {"protected_namespaces": ()}


class CivilizationResponse(BaseModel):
    """Response model for civilization data"""

    id: str
    metadata: CivilizationMetadata
    created_at: datetime
    updated_at: datetime


class CivilizationList(BaseModel):
    """List response for civilizations"""

    civilizations: List[CivilizationResponse]
    total: int
    page: int
    page_size: int


class AttributeDistribution(BaseModel):
    """Distribution of values for a specific attribute"""

    attribute_name: str
    distribution: List[Dict[str, Any]]  # Fixed: changed 'any' to 'Any'
    total_civilizations: int


class AttributeFilter(BaseModel):
    """Filter for querying by attributes"""

    attribute_name: str
    attribute_value: str


class CivilizationComparison(BaseModel):
    """Comparison between civilizations"""

    civilization_a: CivilizationResponse
    civilization_b: CivilizationResponse
    similarities: List[str]
    differences: List[str]
    similarity_score: float


class CivilizationRelationship(BaseModel):
    """Relationship between civilizations"""

    id: str
    civilization_a_id: str
    civilization_b_id: str
    relationship_type: str
    relationship_strength: float = Field(..., ge=-1.0, le=1.0)
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CivilizationRelationshipList(BaseModel):
    """List of civilization relationships"""

    relationships: List[CivilizationRelationship]
    total: int
    page: int
    page_size: int


class CivilizationHistoryEvent(BaseModel):
    """Historical event for a civilization"""

    id: str
    civilization_id: str
    event_type: str
    title: str
    description: Optional[str] = None
    year: Optional[int] = None
    era: Optional[str] = None
    impact_level: Optional[str] = None  # minor, moderate, major, transformative
    affected_attributes: Optional[List[str]] = None
    created_at: datetime


class CivilizationHistoryList(BaseModel):
    """List of historical events"""

    events: List[CivilizationHistoryEvent]
    total: int
    page: int
    page_size: int


# Attribute Metadata for API documentation
ATTRIBUTE_CATEGORIES = {
    "geographic_settlement": {
        "name": "Geographic & Settlement",
        "attributes": [
            "settlement_pattern",
            "primary_terrain",
            "population_density",
            "architecture_style",
        ],
    },
    "political_structure": {
        "name": "Political Structure",
        "attributes": [
            "government_type",
            "leadership_selection",
            "centralization_level",
            "legal_system",
        ],
    },
    "economic_system": {
        "name": "Economic System",
        "attributes": [
            "primary_economy",
            "trade_orientation",
            "currency_type",
            "property_rights",
        ],
    },
    "social_structure": {
        "name": "Social Structure",
        "attributes": [
            "social_stratification",
            "gender_roles",
            "family_structure",
            "age_hierarchy",
        ],
    },
    "cultural_religious": {
        "name": "Cultural & Religious",
        "attributes": [
            "primary_religion",
            "religious_influence",
            "art_focus",
            "cultural_values",
        ],
    },
    "knowledge_education": {
        "name": "Knowledge & Education",
        "attributes": [
            "education_system",
            "literacy_rate",
            "knowledge_basis",
            "technology_level",
        ],
    },
    "military_defense": {
        "name": "Military & Defense",
        "attributes": ["military_structure", "warfare_approach", "primary_weapons"],
    },
    "communication_language": {
        "name": "Communication & Language",
        "attributes": [
            "language_complexity",
            "writing_system",
            "communication_methods",
        ],
    },
    "environmental_relations": {
        "name": "Environmental Relations",
        "attributes": ["resource_use", "agriculture_type", "energy_sources"],
    },
    "additional_attributes": {
        "name": "Additional Attributes",
        "attributes": [
            "population_size",
            "life_expectancy",
            "technological_adoption",
            "external_relations",
            "change_rate",
        ],
    },
}

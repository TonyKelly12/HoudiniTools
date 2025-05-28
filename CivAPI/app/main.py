# app/main.py
"""
Main FastAPI application for Civilization Database API
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# Import routers
from .routes.civilizations import router as civilizations_router

app = FastAPI(
    title="Civilization Database API",
    description="API for storing, retrieving, and analyzing civilization data with comprehensive attributes",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {str(exc)}"}
    )


# Include routers
app.include_router(civilizations_router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to the Civilization Database API",
        "docs": "/docs",
        "version": "1.0.0",
        "features": [
            "Comprehensive civilization attributes",
            "Advanced search and filtering",
            "Civilization relationships",
            "Historical event tracking",
            "Templates and presets",
            "Similarity analysis",
            "Statistical insights"
        ]
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "civilization-database-api"}


# Custom OpenAPI schema with better documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Civilization Database API",
        version="1.0.0",
        description="""
        # Civilization Database API

        A comprehensive API for managing and analyzing civilization data with detailed attributes.

        ## Features

        - **Comprehensive Attributes**: Store detailed civilization data across multiple domains:
          - Geographic & Settlement patterns
          - Political structure & governance
          - Economic systems & trade
          - Social structure & hierarchy
          - Cultural & religious practices
          - Knowledge & education systems
          - Military & defense capabilities
          - Communication & language
          - Environmental relationships
          - Demographics & development metrics

        - **Advanced Search**: Full-text search across names, descriptions, and tags
        - **Filtering**: Filter civilizations by any attribute value
        - **Relationships**: Track relationships between civilizations
        - **History**: Record historical events and their impacts
        - **Templates**: Create reusable civilization templates
        - **Analytics**: Get statistics and attribute distributions
        - **Similarity**: Find civilizations with similar characteristics

        ## Data Model

        Each civilization contains over 30 categorized attributes covering all aspects of society,
        from basic demographics to complex cultural and technological characteristics.

        ## Use Cases

        - World building for games and stories
        - Historical research and analysis
        - Sociological studies
        - Educational simulations
        - Comparative civilization analysis

        ## Authentication

        This API uses standard HTTP methods and JSON responses. Authentication can be added
        based on your deployment requirements.
        """,
        routes=app.routes,
    )

    # Add documentation for custom tags
    openapi_schema["tags"] = [
        {
            "name": "Civilizations",
            "description": "Operations for managing civilization data with comprehensive attributes",
        },
        {
            "name": "Root",
            "description": "Root endpoint operations and API information",
        },
        {
            "name": "Health", 
            "description": "Health check and monitoring endpoints",
        },
    ]

    # Add examples to the schema
    openapi_schema["components"]["examples"] = {
        "BasicCivilization": {
            "summary": "Basic Medieval Civilization",
            "description": "A simple example of a medieval agricultural civilization",
            "value": {
                "name": "Kingdom of Aethermoor",
                "description": "A medieval kingdom known for its fertile plains and skilled craftsmen",
                "tags": ["medieval", "agricultural", "monarchy"],
                "settlement_pattern": "settled",
                "primary_terrain": "plains",
                "population_density": "medium",
                "architecture_style": "stone",
                "government_type": "monarchy",
                "leadership_selection": "hereditary",
                "centralization_level": "highly_centralized",
                "legal_system": "common_law",
                "primary_economy": "agricultural",
                "trade_orientation": "regional_trade",
                "currency_type": "metal_coins",
                "property_rights": "private",
                "social_stratification": "class_based",
                "gender_roles": "patriarchal",
                "family_structure": "extended",
                "age_hierarchy": "elder_led",
                "primary_religion": "monotheistic",
                "religious_influence": "strong_influence",
                "art_focus": "architecture",
                "cultural_values": "honor_based",
                "education_system": "apprenticeship",
                "literacy_rate": "low",
                "knowledge_basis": "traditional_cultural",
                "technology_level": "iron_age",
                "military_structure": "professional_army",
                "warfare_approach": "defensive_only",
                "primary_weapons": "melee",
                "language_complexity": "moderate",
                "writing_system": "alphabetic",
                "communication_methods": "written",
                "resource_use": "sustainable",
                "agriculture_type": "intensive",
                "energy_sources": "human_animal",
                "population_size": "medium",
                "life_expectancy": "short",
                "technological_adoption": "conservative",
                "external_relations": "cautious",
                "change_rate": "slow_changing"
            }
        },
        "AdvancedCivilization": {
            "summary": "Advanced Space-Age Civilization",
            "description": "An example of a highly advanced technological civilization",
            "value": {
                "name": "Stellar Confederation",
                "description": "An advanced space-faring civilization spanning multiple star systems",
                "tags": ["space-age", "democratic", "post-scarcity"],
                "settlement_pattern": "urban",
                "primary_terrain": "mixed",
                "population_density": "high",
                "architecture_style": "metal",
                "government_type": "democracy",
                "leadership_selection": "elected",
                "centralization_level": "federal",
                "legal_system": "civil_law",
                "primary_economy": "service",
                "trade_orientation": "international_trade",
                "currency_type": "digital",
                "property_rights": "mixed",
                "social_stratification": "meritocratic",
                "gender_roles": "egalitarian",
                "family_structure": "nuclear",
                "age_hierarchy": "age_egalitarian",
                "primary_religion": "atheistic",
                "religious_influence": "secular",
                "art_focus": "mixed",
                "cultural_values": "achievement_oriented",
                "education_system": "formal_schools",
                "literacy_rate": "universal",
                "knowledge_basis": "empirical_scientific",
                "technology_level": "post_scarcity",
                "military_structure": "professional_army",
                "warfare_approach": "diplomatic",
                "primary_weapons": "advanced_technology",
                "language_complexity": "complex",
                "writing_system": "alphabetic",
                "communication_methods": "digital",
                "resource_use": "sustainable",
                "agriculture_type": "industrial",
                "energy_sources": "renewable",
                "population_size": "massive",
                "life_expectancy": "very_long",
                "technological_adoption": "technophilic",
                "external_relations": "cosmopolitan",
                "change_rate": "rapid_change"
            }
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
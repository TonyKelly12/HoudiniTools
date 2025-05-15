# app/main.py
"""
Main FastAPI application with weapon assembly system support
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# Import routers directly instead of through routes package
from .routes.models import router as models_router
from .routes.textures import router as textures_router
from .routes.assembly import router as assembly_router

app = FastAPI(
    title="3D Weapon Assembly API",
    description="API for storing, retrieving, and assembling 3D weapon models and textures",
    version="2.0.0",
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


# Include routers directly
app.include_router(models_router)
app.include_router(textures_router)
app.include_router(assembly_router)


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to the 3D Weapon Assembly API",
        "docs": "/docs",
        "version": "2.0.0",
    }


# Custom OpenAPI schema with better documentation
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="3D Weapon Assembly API",
        version="2.0.0",
        description="""
        # 3D Weapon Assembly API

        This API provides endpoints for managing 3D models and textures with a focus on weapon assembly.

        ## Features

        - **Model Management**: Upload, retrieve, and manage 3D models with comprehensive metadata
        - **Texture Management**: Upload, retrieve, and manage textures with proper organization
        - **Weapon Parts**: Specialized support for weapon components (handles, blades, etc.)
        - **Assembly System**: Create and manage weapon assemblies with positioning information

        ## File Storage

        Files are stored on the filesystem with a carefully designed directory structure:

        - Models: `/storage/models/{category}/{weapon_type}/{part_type}/...`
        - Textures: `/storage/textures/{weapon_type}/{part_type}/{texture_type}/...`
        - General assets: `/storage/models/{category}/...`

        ## Authentication

        This API uses API key authentication. Include your API key in the `X-API-Key` header for all requests.
        """,
        routes=app.routes,
    )

    # Add documentation for custom tags
    openapi_schema["tags"] = [
        {
            "name": "3D Models",
            "description": "Operations for managing 3D model assets with weapon part support",
        },
        {
            "name": "Textures",
            "description": "Operations for managing texture assets with specialized organization",
        },
        {
            "name": "Weapon Assemblies",
            "description": "Operations for creating and managing weapon assemblies",
        },
        {"name": "Root", "description": "Root endpoint operations"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

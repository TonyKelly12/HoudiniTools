"""
Enhanced CivilizationContextAPI with WeaponsAPI integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.civilizations import router as civilizations_router
from app.routes.weapons_context import router as weapons_router

app = FastAPI(
    title="Civilization Context API",
    description="Middleware API for providing contextual asset recommendations based on civilization data",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(civilizations_router)
app.include_router(weapons_router)


@app.get("/")
async def root():
    return {
        "message": "Civilization Context API",
        "description": "Middleware for contextual asset recommendations",
        "version": "1.0.0",
        "endpoints": {
            "civilizations": "/civilizations/",
            "weapons": "/weapons/",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "civilization-context-api",
        "integrations": {
            "weapons_api": "http://weapons-api:8003",
            "civilization_api": "http://civ-api:8001",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

# Project Structure Guide

```
project_root/                   # Root directory of the project
│
├── app/                        # Main application package
│   ├── __init__.py            # Makes app a proper Python package
│   ├── main.py                # FastAPI application entry point
│   ├── database.py            # MongoDB and GridFS connections
│   │
│   ├── models/                # Data validation models (Pydantic)
│   │   ├── __init__.py
│   │   └── model_schema.py    # Schema definitions
│   │
│   ├── routes/                # API endpoints
│   │   ├── __init__.py
│   │   ├── models.py          # 3D model routes
│   │   └── textures.py        # Texture routes
│   │
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── model_service.py   # 3D model services
│   │   └── texture_service.py # Texture services
│   │
│   └── utils/                 # Helper utilities
│       ├── __init__.py
│       └── helpers.py         # Helper functions
│
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Example environment variables
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker configuration
├── requirements.txt            # Python dependencies
└── run.py                      # Script to run the application
```

## Key Components

### FastAPI Application (`app/main.py`)
- Initializes FastAPI app
- Sets up CORS middleware
- Registers exception handlers
- Includes routers for models and textures
- Defines root endpoint

### Database Connection (`app/database.py`)
- Initializes MongoDB connections (both sync and async)
- Sets up GridFS buckets for models and textures
- Provides helper functions for GridFS operations

### Pydantic Models (`app/models/model_schema.py`)
- Defines data validation schemas
- Used for request/response validation
- Provides automatic API documentation

### API Routes
- **Models Routes** (`app/routes/models.py`)
  - Endpoints for 3D model operations
  - Upload, download, list, and delete models
  
- **Textures Routes** (`app/routes/textures.py`)
  - Endpoints for texture operations
  - Upload, download, list, and delete textures

### Service Layer
- **Model Service** (`app/services/model_service.py`)
  - Business logic for 3D model operations
  - Handles validation and database interactions
  
- **Texture Service** (`app/services/texture_service.py`)
  - Business logic for texture operations
  - Handles validation and database interactions

### Utilities (`app/utils/helpers.py`)
- Helper functions for file operations
- Validation utilities
- Formatting functions

## Docker Setup
- `Dockerfile` - Defines the application container
- `docker-compose.yml` - Orchestrates app and MongoDB containers

## Configuration
- `.env.example` - Template for environment variables
- Copy to `.env` and customize as needed

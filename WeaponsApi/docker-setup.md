# Docker Setup Instructions for 3D Model API

## File Organization

Ensure your project structure matches this pattern:

```
project_root/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env (optional for additional configuration)
```

## Setup Steps

1. **Create Dockerfile and docker-compose.yml**
   - Save the provided Dockerfile and docker-compose.yml files to your project root

2. **Create or update requirements.txt**
   - Make sure all dependencies are listed
   ```
   fastapi==0.105.0
   uvicorn==0.24.0
   pymongo==4.6.0
   motor==3.3.2
   python-multipart==0.0.6
   pydantic==2.5.2
   aiofiles==23.2.1
   python-dotenv==1.0.0
   ```

3. **Build and run the containers**
   - Open a terminal in your project directory
   - Run the following commands:

## Docker Commands

### Building and Starting the Application

```bash
# Build and start containers in detached mode
docker-compose up -d --build
```

### View Logs

```bash
# View logs from both containers
docker-compose logs -f

# View logs from just the API application
docker-compose logs -f app
```

### Stopping the Application

```bash
# Stop containers without removing them
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers and delete volumes (will delete MongoDB data)
docker-compose down -v
```

### Inspecting the MongoDB Data

```bash
# Access MongoDB shell inside the container
docker-compose exec mongodb mongosh

# In the MongoDB shell, navigate to the model database
use model_database

# List collections (should show models.files, models.chunks, etc.)
show collections

# Query models collection
db.models.files.find()
```

## Testing the API

Once the containers are running, you can access:
- API Documentation: http://localhost:8000/docs
- API Root: http://localhost:8000/

### Example cURL Commands

Upload a 3D model:
```bash
curl -X POST "http://localhost:8000/models/" \
  -F "file=@path/to/your/model.fbx" \
  -F 'metadata_json={"name": "Sample Model", "description": "A test model", "format": "fbx", "tags": ["sample", "test"]}'
```

List all models:
```bash
curl -X GET "http://localhost:8000/models/"
```

Download a model by ID:
```bash
curl -X GET "http://localhost:8000/models/{model_id}" --output downloaded_model.fbx
```

## Production Considerations

For production deployment, consider:
1. Adding a reverse proxy like Nginx
2. Using Docker Swarm or Kubernetes for orchestration
3. Adding MongoDB authentication
4. Setting up a MongoDB replica set for high availability
5. Implementing proper backup strategies for MongoDB volumes

# Civilization Database API

A comprehensive FastAPI-based service for storing, retrieving, and analyzing civilization data with detailed attributes covering all aspects of societal development.

## 🌟 Features

### Comprehensive Civilization Attributes
- **Geographic & Settlement**: Terrain, population density, architecture, settlement patterns
- **Political Structure**: Government types, leadership selection, legal systems, centralization
- **Economic Systems**: Primary economy, trade orientation, currency, property rights
- **Social Structure**: Stratification, gender roles, family structure, age hierarchy
- **Cultural & Religious**: Religion, art focus, cultural values, religious influence
- **Knowledge & Education**: Education systems, literacy, knowledge basis, technology level
- **Military & Defense**: Military structure, warfare approach, primary weapons
- **Communication & Language**: Language complexity, writing systems, communication methods
- **Environmental Relations**: Resource use, agriculture, energy sources
- **Demographics**: Population size, life expectancy, technological adoption, external relations

### Advanced Functionality
- 🔍 **Full-text search** across names, descriptions, and tags
- 🎯 **Advanced filtering** by any attribute value
- 🔗 **Relationship tracking** between civilizations
- 📚 **Historical event** recording and timeline management
- 📋 **Templates system** for quick civilization creation
- 📊 **Analytics and statistics** with attribute distribution analysis
- 🎲 **Similarity matching** to find comparable civilizations
- 🚀 **High performance** with MongoDB and async operations

## 🏗️ Architecture

- **FastAPI** - Modern, fast web framework for building APIs
- **MongoDB** - Document database for flexible civilization data storage
- **Motor** - Async MongoDB driver for Python
- **Pydantic** - Data validation and serialization using Python type hints
- **Docker** - Containerization for easy deployment

## 📋 Requirements

- Python 3.11+
- MongoDB 6.0+
- Docker (optional, for containerized deployment)

## 🚀 Quick Start

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd civilization-database-api
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the API**
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- MongoDB Admin: http://localhost:8081

### Option 2: Local Development

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up MongoDB**
```bash
# Install and start MongoDB locally
# Or use MongoDB Atlas cloud service
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your MongoDB connection details
```

4. **Run the application**
```bash
python run.py
```

## 📖 API Documentation

### Core Endpoints

#### Civilizations
- `POST /civilizations/` - Create a new civilization
- `GET /civilizations/` - List civilizations with filtering
- `GET /civilizations/{id}` - Get specific civilization
- `PUT /civilizations/{id}` - Update civilization
- `DELETE /civilizations/{id}` - Delete civilization

#### Search & Analytics
- `GET /civilizations/search?q={query}` - Full-text search
- `GET /civilizations/statistics` - Get database statistics
- `GET /civilizations/attribute-distribution/{attribute}` - Attribute analysis
- `GET /civilizations/{id}/similar` - Find similar civilizations

#### Relationships
- `POST /civilizations/{id}/relationships` - Create relationship
- `GET /civilizations/{id}/relationships` - Get civilization relationships

#### History
- `POST /civilizations/{id}/history` - Add historical event
- `GET /civilizations/{id}/history` - Get civilization history

#### Templates
- `POST /civilizations/templates` - Create template
- `GET /civilizations/templates` - List templates
- `POST /civilizations/templates/{id}/create` - Create civilization from template

### Interactive API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation with example requests and responses.

## 💡 Usage Examples

### Creating a Medieval Kingdom

```python
import requests

civilization_data = {
    "name": "Kingdom of Aethermoor",
    "description": "A medieval kingdom known for fertile plains",
    "tags": ["medieval", "agricultural", "monarchy"],
    "settlement_pattern": "settled",
    "primary_terrain": "plains",
    "government_type": "monarchy",
    "primary_economy": "agricultural",
    "technology_level": "iron_age",
    "population_size": "medium",
    "exact_population": 150000
}

response = requests.post(
    "http://localhost:8000/civilizations/",
    json=civilization_data
)
print(response.json())
```

### Searching Civilizations

```python
# Search for space-age civilizations
response = requests.get(
    "http://localhost:8000/civilizations/search",
    params={"q": "space technology"}
)

# Filter by government type
response = requests.get(
    "http://localhost:8000/civilizations/",
    params={"government_type": "democracy", "limit": 10}
)
```

### Getting Statistics

```python
response = requests.get("http://localhost:8000/civilizations/statistics")
stats = response.json()
print(f"Total civilizations: {stats['total_civilizations']}")
```

## 🗂️ Project Structure

```
civilization-database-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── database.py            # MongoDB operations
│   ├── models/
│   │   ├── __init__.py
│   │   └── civilization_schema.py  # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── civilizations.py    # API endpoints
│   └── services/
│       ├── __init__.py
│       └── civilization_service.py  # Business logic
├── tests/                     # Test files
├── docker-compose.yml         # Docker services
├── Dockerfile                # Container definition
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── run.py                   # Application launcher
└── README.md               # This file
```

## 🔧 Configuration

Key environment variables:

```bash
# Database
MONGO_URI=mongodb://localhost:27017
DB_NAME=civilization_database

# API Settings
DEBUG=True
API_TITLE=Civilization Database API
API_VERSION=1.0.0

# Pagination
DEFAULT_PAGE_SIZE=100
MAX_PAGE_SIZE=1000

# Features
ENABLE_ANALYTICS=True
SIMILARITY_THRESHOLD=0.5
```

## 🧪 Testing

Run the example test script:

```bash
python test_examples.py
```

This will create sample civilizations and demonstrate API functionality.

## 📊 Data Model

### Civilization Attributes

Each civilization contains comprehensive attributes organized into categories:

**Geographic & Settlement**
- Settlement Pattern (nomadic, settled, urban, etc.)
- Primary Terrain (desert, forest, mountains, etc.)
- Population Density (sparse, low, medium, high, megacity)
- Architecture Style (wood, stone, metal, etc.)

**Political Structure**
- Government Type (democracy, monarchy, oligarchy, etc.)
- Leadership Selection (hereditary, elected, appointed, etc.)
- Centralization Level (centralized, federal, tribal, etc.)
- Legal System (common law, civil law, religious law, etc.)

*...and 20+ more categories with detailed attributes*

### Relationships

Track relationships between civilizations:
- Relationship type (ally, enemy, trade partner, etc.)
- Relationship strength (-1.0 to 1.0 scale)
- Historical context and descriptions

### Historical Events

Record significant events in civilization history:
- Event types (founding, war, discovery, disaster, etc.)
- Timeline information (year, era)
- Impact assessment (minor, major, transformative)
- Affected attributes tracking

## 🚀 Deployment

### Production Deployment

1. **Use production docker-compose profile**
```bash
docker-compose --profile production up -d
```

2. **Configure environment variables**
```bash
ENVIRONMENT=production
DEBUG=False
MONGO_URI=mongodb://your-production-mongo
```

3. **Set up reverse proxy (Nginx)**
```bash
# nginx.conf included for SSL and load balancing
```

### Scaling Considerations

- **Database**: Use MongoDB replica sets for high availability
- **Application**: Deploy multiple API instances behind a load balancer  
- **Caching**: Enable Redis caching for frequently accessed data
- **Monitoring**: Set up health checks and metrics collection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 **Documentation**: Visit `/docs` endpoint for interactive API documentation
- 🐛 **Issues**: Report bugs and request features via GitHub Issues
- 💬 **Discussions**: Join community discussions for questions and ideas

## 🎯 Use Cases

- **World Building**: Create detailed fictional worlds for games and stories
- **Historical Research**: Analyze and compare historical civilizations
- **Educational Simulations**: Teach comparative government and sociology
- **Game Development**: Backend for civilization or strategy games
- **Academic Research**: Comparative civilization studies and analysis

## 🔮 Future Enhancements

- **Geographic Information System (GIS)** integration
- **Machine Learning** for civilization development prediction
- **Export formats** (JSON, CSV, XML)
- **Import tools** for existing civilization databases
- **Advanced visualization** dashboards
- **Multi-language support** for international use
- **Real-time collaboration** features
- **Advanced analytics** and trend analysis
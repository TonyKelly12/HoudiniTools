# app/config.py
"""
Configuration settings for the Civilization Database API
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DB_NAME", "civilization_database")

# API Settings
API_TITLE = os.getenv("API_TITLE", "Civilization Database API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Pagination limits
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", 100))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", 1000))

# Search settings
SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", 1000))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.5))

# Cache settings (if implementing caching)
CACHE_EXPIRE_SECONDS = int(os.getenv("CACHE_EXPIRE_SECONDS", 300))  # 5 minutes

# Security settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
API_KEY_HEADER = os.getenv("API_KEY_HEADER", "X-API-Key")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Rate limiting (if implementing)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", 60))  # seconds

# Validation settings
MAX_TAGS_PER_CIVILIZATION = int(os.getenv("MAX_TAGS_PER_CIVILIZATION", 50))
MAX_DESCRIPTION_LENGTH = int(os.getenv("MAX_DESCRIPTION_LENGTH", 5000))
MAX_NAME_LENGTH = int(os.getenv("MAX_NAME_LENGTH", 200))

# Analytics settings
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"
ANALYTICS_BATCH_SIZE = int(os.getenv("ANALYTICS_BATCH_SIZE", 1000))

# Export settings
EXPORT_FORMAT_DEFAULT = os.getenv("EXPORT_FORMAT_DEFAULT", "json")
EXPORT_MAX_RECORDS = int(os.getenv("EXPORT_MAX_RECORDS", 10000))

# Template settings
MAX_TEMPLATES_PER_USER = int(os.getenv("MAX_TEMPLATES_PER_USER", 100))
TEMPLATE_NAME_MAX_LENGTH = int(os.getenv("TEMPLATE_NAME_MAX_LENGTH", 100))

# History settings
MAX_HISTORY_EVENTS_PER_CIVILIZATION = int(os.getenv("MAX_HISTORY_EVENTS_PER_CIVILIZATION", 1000))
HISTORY_RETENTION_DAYS = int(os.getenv("HISTORY_RETENTION_DAYS", 3650))  # 10 years

# Relationship settings
MAX_RELATIONSHIPS_PER_CIVILIZATION = int(os.getenv("MAX_RELATIONSHIPS_PER_CIVILIZATION", 1000))
RELATIONSHIP_STRENGTH_PRECISION = int(os.getenv("RELATIONSHIP_STRENGTH_PRECISION", 2))

# Backup settings (if implementing automated backups)
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "False").lower() == "true"
BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Daily at 2 AM
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", 30))

# Monitoring settings
HEALTH_CHECK_TIMEOUT = int(os.getenv("HEALTH_CHECK_TIMEOUT", 5))
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "True").lower() == "true"

# Development settings
RELOAD_ON_CHANGE = os.getenv("RELOAD_ON_CHANGE", "True").lower() == "true" if DEBUG else False
ENABLE_PROFILING = os.getenv("ENABLE_PROFILING", "False").lower() == "true"

# Environment info
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"
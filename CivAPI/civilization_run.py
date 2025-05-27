# run.py
"""
Launch script for the Civilization Database API
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    reload = os.getenv("RELOAD_ON_CHANGE", str(debug)).lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # Print startup information
    print("Starting Civilization Database API...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Auto-reload: {reload}")
    print(f"Log level: {log_level}")
    print("-" * 40)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        timeout_keep_alive=120,
        access_log=debug
    )
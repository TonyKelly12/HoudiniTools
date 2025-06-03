import hou
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtNetwork import QNetworkAccessManager, QNetworkReply
import time
import os
import requests
import json
import tempfile


class WeaponAssemblyAPI:
    """Class to handle communication with the 3D Weapon Assembly API"""

    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Cache API responses to reduce network calls
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.cache_timestamps = {}

    def _check_cache(self, cache_key):
        """Check if valid cache exists for the key"""
        if cache_key in self.cache and cache_key in self.cache_timestamps:
            cache_time = self.cache_timestamps[cache_key]
            if time.time() - cache_time < self.cache_timeout:
                return True
        return False

    def clear_cache(self):
        """Clear the API cache to force fresh data"""
        self.cache = {}
        self.cache_timestamps = {}
        print("API cache cleared")

    def _update_cache(self, cache_key, data):
        """Update cache with new data"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()

    def test_connection(self):
        """Test connection to the API"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"API connection error: {str(e)}")
            return False

    def get_weapon_types(self):
        """Get list of available weapon types"""
        cache_key = "weapon_types"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # For now, return the enum values from model_schema.py directly
        # In a real implementation, this would be a dedicated API endpoint
        weapon_types = [
            "sword",
            "axe",
            "mace",
            "bow",
            "spear",
            "dagger",
            "staff",
            "shield",
            "gun",
            "rifle",
            "custom",
        ]
        self._update_cache(cache_key, weapon_types)
        return weapon_types

    def get_part_types(self, weapon_type):
        """Get list of available part types for a specific weapon type"""
        cache_key = f"part_types_{weapon_type}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # Get appropriate part types based on weapon type
        # In a real implementation, this would be a dedicated API endpoint
        common_parts = ["handle", "grip"]

        part_types = {
            "sword": common_parts + ["blade", "guard", "pommel"],
            "axe": common_parts + ["head"],
            "mace": common_parts + ["head"],
            "bow": common_parts + ["limbs", "string"],
            "spear": common_parts + ["shaft", "head"],
            "dagger": common_parts + ["blade", "guard"],
            "staff": common_parts + ["shaft", "head"],
            "shield": ["body", "border", "boss"],
            "gun": ["handle", "barrel", "trigger", "magazine", "sight"],
            "rifle": ["stock", "barrel", "trigger", "magazine", "sight"],
            "custom": ["handle", "body", "custom"],
        }

        result = part_types.get(weapon_type.lower(), common_parts)
        self._update_cache(cache_key, result)
        return result

    def get_weapon_parts(self, weapon_type, part_type, page=1, limit=10):
        """Get parts for a specific weapon type and part type with pagination"""
        cache_key = f"parts_{weapon_type}_{part_type}_{page}_{limit}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        try:
            skip = (page - 1) * limit
            url = (
                f"{self.base_url}/models/weapon-parts"
                f"?weapon_type={weapon_type}"
                f"&part_type={part_type}"
                f"&skip={skip}"
                f"&limit={limit}"
            )
            print(f"Requesting URL: {url}")
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Handle both direct list responses and paginated responses
                    if isinstance(data, dict) and "models" in data:
                        parts = data["models"]
                        print(f"Retrieved {len(parts)} parts from paginated response")
                    elif isinstance(data, list):
                        parts = data
                        print(f"Retrieved {len(parts)} parts from list response")
                    else:
                        print(f"Unexpected response format: {type(data)}")
                        parts = []

                    self._update_cache(cache_key, parts)
                    return parts
                except ValueError as e:
                    print(f"JSON parsing error: {str(e)}")
                    print(f"Response text: {response.text[:200]}")
                    return []
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"Error getting weapon parts: {str(e)}")
            return []

    def download_model(self, model_id, target_path=None):
        """Download a model file by its ID"""
        try:
            url = f"{self.base_url}/models/{model_id}"
            response = requests.get(url, stream=True)

            if response.status_code == 200:
                if target_path is None:
                    # Create a temporary file if no path specified
                    fd, target_path = tempfile.mkstemp(suffix=".fbx")
                    os.close(fd)

                with open(target_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return target_path
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            return None

    # Add to WeaponAssemblyAPI class
    def upload_model(self, model_file_path, icon_file_path, metadata):
        """Upload a model file with metadata to the API"""
        try:
            url = f"{self.base_url}/models/"

            # Prepare files
            files = {
                "file": (
                    os.path.basename(model_file_path),
                    open(model_file_path, "rb"),
                    "application/octet-stream",
                ),
                "icon": (
                    os.path.basename(icon_file_path),
                    open(icon_file_path, "rb"),
                    "image/png",
                ),
                "metadata_json": (None, json.dumps(metadata)),
            }

            # Make the request
            response = requests.post(url, files=files)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error uploading model: {str(e)}")
            return None

    def get_model_metadata(self, model_id):
        """Get metadata for a specific model"""
        cache_key = f"metadata_{model_id}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        try:
            url = f"{self.base_url}/models/metadata/{model_id}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                self._update_cache(cache_key, data)
                return data
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error getting model metadata: {str(e)}")
            return None

    def create_assembly(self, assembly_data):
        """Create a new weapon assembly"""
        try:
            url = f"{self.base_url}/assemblies"
            response = requests.post(url, json=assembly_data, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error creating assembly: {str(e)}")
            return None

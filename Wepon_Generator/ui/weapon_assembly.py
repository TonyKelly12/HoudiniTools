import hou
from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtNetwork import QNetworkAccessManager, QNetworkReply
import time
import os
import requests
import json
import tempfile


class WeaponAssemblyAPI:
    """Class to handle communication with the CivContextAPI for civilization-aware weapon generation"""

    def __init__(self, base_url="http://localhost:8002", weapons_api_url="http://localhost:8003"):
        self.base_url = base_url  # CivContextAPI
        self.weapons_api_url = weapons_api_url  # Direct WeaponsAPI for fallback
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Cache API responses to reduce network calls
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.cache_timestamps = {}
        self.current_civilization_id = None

    def set_civilization_context(self, civilization_id):
        """Set the current civilization context for weapon recommendations"""
        self.current_civilization_id = civilization_id
        # Clear cache when civilization changes
        if civilization_id:
            self.clear_cache()

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
        """Test connection to the CivContextAPI"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"CivContextAPI connection error: {str(e)}")
            # Fallback to direct WeaponsAPI
            try:
                response = requests.get(f"{self.weapons_api_url}/", timeout=5)
                return response.status_code == 200
            except Exception as e2:
                print(f"WeaponsAPI fallback connection error: {str(e2)}")
                return False

    def get_weapon_types(self):
        """Get list of available weapon types"""
        cache_key = "weapon_types"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # If we have a civilization context, get analyzed weapon types
        if self.current_civilization_id:
            try:
                url = f"{self.base_url}/weapons/analyze/{self.current_civilization_id}"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    analysis = response.json()
                    weapon_types = analysis.get("analysis", {}).get("allowed_weapon_types", [])
                    if weapon_types:
                        self._update_cache(cache_key, weapon_types)
                        return weapon_types
            except Exception as e:
                print(f"Error getting civilization weapon types: {str(e)}")

        # Fallback to standard weapon types
        weapon_types = [
            "sword", "axe", "mace", "bow", "spear", "dagger", 
            "staff", "shield", "gun", "rifle", "custom"
        ]
        self._update_cache(cache_key, weapon_types)
        return weapon_types

    def get_part_types(self, weapon_type):
        """Get list of available part types for a specific weapon type"""
        cache_key = f"part_types_{weapon_type}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # Standard part types mapping
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
        """Get parts for a specific weapon type and part type with civilization context"""
        cache_key = f"parts_{weapon_type}_{part_type}_{page}_{limit}_{self.current_civilization_id}"
        if self._check_cache(cache_key):
            return self.cache[cache_key]

        # If we have civilization context, use CivContextAPI
        if self.current_civilization_id:
            try:
                url = f"{self.base_url}/weapons/parts/{self.current_civilization_id}"
                params = {
                    "weapon_type": weapon_type,
                    "part_type": part_type,
                    "limit": limit
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract parts from the response
                    parts = []
                    for item in data.get("parts", []):
                        part_data = item.get("part", {})
                        # Add compatibility score to metadata for sorting
                        if "metadata" not in part_data:
                            part_data["metadata"] = {}
                        part_data["metadata"]["compatibility_score"] = item.get("compatibility_score", 0.0)
                        parts.append(part_data)
                    
                    # Sort by compatibility score
                    parts.sort(key=lambda x: x.get("metadata", {}).get("compatibility_score", 0), reverse=True)
                    
                    print(f"Retrieved {len(parts)} civilization-aware parts for {weapon_type}/{part_type}")
                    self._update_cache(cache_key, parts)
                    return parts
                else:
                    print(f"CivContextAPI Error ({response.status_code}): {response.text}")
            except Exception as e:
                print(f"Error getting civilization-aware weapon parts: {str(e)}")

        # Fallback to direct WeaponsAPI call
        try:
            skip = (page - 1) * limit
            url = (
                f"{self.weapons_api_url}/models/weapon-parts"
                f"?weapon_type={weapon_type}"
                f"&part_type={part_type}"
                f"&skip={skip}"
                f"&limit={limit}"
            )
            print(f"Fallback to direct WeaponsAPI: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    # Handle both direct list responses and paginated responses
                    if isinstance(data, dict) and "models" in data:
                        parts = data["models"]
                    elif isinstance(data, list):
                        parts = data
                    else:
                        parts = []

                    print(f"Retrieved {len(parts)} parts from fallback WeaponsAPI")
                    self._update_cache(cache_key, parts)
                    return parts
                except ValueError as e:
                    print(f"JSON parsing error: {str(e)}")
                    return []
            else:
                print(f"WeaponsAPI Error ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"Error getting weapon parts from fallback API: {str(e)}")
            return []

    def get_weapon_recommendations(self, weapon_type=None, limit=20, min_compatibility=0.3):
        """Get weapon recommendations for the current civilization"""
        if not self.current_civilization_id:
            print("No civilization context set for recommendations")
            return []

        try:
            url = f"{self.base_url}/weapons/recommendations/{self.current_civilization_id}"
            params = {
                "limit": limit,
                "min_compatibility": min_compatibility
            }
            if weapon_type:
                params["weapon_type"] = weapon_type

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                recommendations = response.json()
                print(f"Retrieved {len(recommendations)} weapon recommendations")
                return recommendations
            else:
                print(f"Error getting recommendations ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"Error getting weapon recommendations: {str(e)}")
            return []

    def get_weapon_assemblies(self, limit=10):
        """Get weapon assemblies for the current civilization"""
        if not self.current_civilization_id:
            print("No civilization context set for assemblies")
            return []

        try:
            url = f"{self.base_url}/weapons/assemblies/{self.current_civilization_id}"
            params = {"limit": limit}

            response = requests.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                assemblies = data.get("assemblies", [])
                print(f"Retrieved {len(assemblies)} weapon assemblies")
                return assemblies
            else:
                print(f"Error getting assemblies ({response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"Error getting weapon assemblies: {str(e)}")
            return []

    def analyze_civilization_context(self):
        """Get detailed analysis of civilization weapon context"""
        if not self.current_civilization_id:
            return None

        try:
            url = f"{self.base_url}/weapons/analyze/{self.current_civilization_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error analyzing civilization ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error analyzing civilization context: {str(e)}")
            return None

    def download_model(self, model_id, target_path=None):
        """Download a model file by its ID (fallback to WeaponsAPI)"""
        try:
            url = f"{self.weapons_api_url}/models/{model_id}"
            response = requests.get(url, stream=True, timeout=30)

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
                print(f"Model download error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error downloading model: {str(e)}")
            return None

    def upload_model(self, model_file_path, icon_file_path, metadata):
        """Upload a model file with metadata to the WeaponsAPI"""
        try:
            url = f"{self.weapons_api_url}/models/"

            # Prepare files
            with open(model_file_path, "rb") as model_file, open(icon_file_path, "rb") as icon_file:
                files = {
                    "file": (os.path.basename(model_file_path), model_file, "application/octet-stream"),
                    "icon": (os.path.basename(icon_file_path), icon_file, "image/png"),
                }
                data = {"metadata_json": json.dumps(metadata)}

                # Make the request
                response = requests.post(url, files=files, data=data, timeout=120)

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Upload error ({response.status_code}): {response.text}")
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
            url = f"{self.weapons_api_url}/models/metadata/{model_id}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self._update_cache(cache_key, data)
                return data
            else:
                print(f"Metadata error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error getting model metadata: {str(e)}")
            return None

    def create_assembly(self, assembly_data):
        """Create a new weapon assembly (fallback to WeaponsAPI)"""
        try:
            url = f"{self.weapons_api_url}/assemblies"
            response = requests.post(url, json=assembly_data, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Assembly creation error ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"Error creating assembly: {str(e)}")
            return None
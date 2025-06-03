import httpx
from typing import List, Dict, Optional, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class WeaponsAPIClient:
    """Client for interacting with the WeaponsAPI"""
    
    def __init__(self, weapons_api_url: str):
        self.weapons_api_url = weapons_api_url.rstrip('/')
        self.timeout = 30.0
    
    async def get_all_models(self, skip: int = 0, limit: int = 100, **filters) -> Dict[str, Any]:
        """Get models from WeaponsAPI with filtering"""
        try:
            params = {"skip": skip, "limit": limit}
            params.update(filters)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.weapons_api_url}/models/",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error getting models: {e}")
            raise HTTPException(status_code=503, detail="WeaponsAPI unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting models: {e}")
            raise HTTPException(status_code=e.response.status_code, detail="WeaponsAPI error")
    
    async def get_weapon_parts(self, weapon_type: str, part_type: Optional[str] = None) -> List[Dict]:
        """Get weapon parts by type"""
        try:
            params = {"weapon_type": weapon_type}
            if part_type:
                params["part_type"] = part_type
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.weapons_api_url}/models/weapon-parts",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error getting weapon parts: {e}")
            raise HTTPException(status_code=503, detail="WeaponsAPI unavailable")
    
    async def get_model_by_id(self, model_id: str) -> Dict[str, Any]:
        """Get specific model by ID"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.weapons_api_url}/models/metadata/{model_id}"
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error getting model {model_id}: {e}")
            raise HTTPException(status_code=503, detail="WeaponsAPI unavailable")
    
    async def get_textures_for_weapon(self, weapon_type: str, part_type: Optional[str] = None) -> List[Dict]:
        """Get textures for weapon type"""
        try:
            params = {}
            if part_type:
                params["part_type"] = part_type
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.weapons_api_url}/textures/weapon/{weapon_type}",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error getting textures: {e}")
            raise HTTPException(status_code=503, detail="WeaponsAPI unavailable")
    
    async def get_assemblies(self, weapon_type: Optional[str] = None) -> Dict[str, Any]:
        """Get weapon assemblies"""
        try:
            params = {}
            if weapon_type:
                params["weapon_type"] = weapon_type
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.weapons_api_url}/assemblies/",
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error getting assemblies: {e}")
            raise HTTPException(status_code=503, detail="WeaponsAPI unavailable")
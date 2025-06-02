# 3D Weapon Assembly API - Implementation Guide

This document provides an overview of the enhanced API for managing 3D weapon models, textures, and assemblies.

## Core Features Added

1. **Weapon-Specific Metadata**
   - Support for categorizing models as weapon parts
   - Detailed metadata for weapon part types (handle, blade, etc.)
   - Attachment point and material slot tracking

2. **Intelligent File Organization**
   - Hierarchical file storage for easy retrieval
   - Path generation based on metadata
   - Standardized naming conventions with sanitization

3. **Weapon Assembly System**
   - Creation and management of complete weapons
   - Positioning and rotation information for each part
   - Support for material assignments

4. **Enhanced API Routes**
   - Specialized endpoints for weapon part retrieval
   - Filtered texture access by weapon and part type
   - Assembly duplication and management

## Model Structure

The API now supports the following type hierarchies:

### Weapon Types
- Sword
- Axe
- Mace
- Bow
- Spear
- Dagger
- Staff
- Shield
- Gun
- Rifle
- Custom

### Weapon Part Types
- Handle
- Blade
- Guard
- Pommel
- Head
- Shaft
- Grip
- Barrel
- Stock
- Sight
- Magazine
- Trigger
- Custom

### Texture Types
- Diffuse
- Normal
- Roughness
- Metallic
- Emissive
- Ambient Occlusion
- Height
- Opacity
- Custom

## File Organization

The API organizes files in a structured manner:

### Models
```
/storage/models/
  ├── weapons/
  │   ├── sword/
  │   │   ├── handle/
  │   │   │   ├── base/
  │   │   │   └── variants/
  │   │   │       ├── ornate/
  │   │   │       └── simple/
  │   │   ├── blade/
  │   │   │   ├── base/
  │   │   │   └── variants/
  │   │   └── guard/
  │   ├── axe/
  │   │   ├── handle/
  │   │   └── head/
  │   └── ...
  └── misc/
      └── ...
```

### Textures
```
/storage/textures/
  ├── sword/
  │   ├── handle/
  │   │   ├── diffuse/
  │   │   ├── normal/
  │   │   └── roughness/
  │   ├── blade/
  │   │   ├── diffuse/
  │   │   ├── normal/
  │   │   └── metallic/
  │   └── ...
  └── materials/
      ├── diffuse/
      ├── normal/
      └── ...
```

## Key APIs

### Model Management

- `POST /models/` - Upload a model with weapon metadata
- `GET /models/` - List models with filtering options
- `GET /models/weapon-parts` - Get specific weapon parts
- `GET /models/{model_id}` - Download a model file
- `GET /models/metadata/{model_id}` - Get model metadata
- `DELETE /models/{model_id}` - Delete a model

### Texture Management

- `POST /textures/` - Upload a texture with metadata
- `GET /textures/` - List textures with filtering
- `GET /textures/weapon/{weapon_type}` - Get textures for weapon type
- `GET /textures/model/{model_id}` - Get textures for specific model
- `GET /textures/{texture_id}` - Download a texture
- `GET /textures/metadata/{texture_id}` - Get texture metadata
- `DELETE /textures/{texture_id}` - Delete a texture

### Weapon Assembly

- `POST /assemblies/` - Create a weapon assembly
- `GET /assemblies/` - List assemblies with filtering
- `GET /assemblies/{assembly_id}` - Get a specific assembly
- `PUT /assemblies/{assembly_id}` - Update an assembly
- `PATCH /assemblies/{assembly_id}/parts` - Update just the parts
- `DELETE /assemblies/{assembly_id}` - Delete an assembly
- `POST /assemblies/{assembly_id}/duplicate` - Duplicate an assembly

## Usage Examples

### Creating a Sword with Multiple Parts

1. Upload the handle model:
```json
POST /models/
{
  "name": "Steel Sword Handle",
  "description": "Basic steel sword handle",
  "format": "fbx",
  "category": "weapons",
  "is_weapon_part": true,
  "weapon_part_metadata": {
    "weapon_type": "sword",
    "part_type": "handle",
    "material_slots": ["handle_mat"]
  }
}
```

2. Upload the blade model:
```json
POST /models/
{
  "name": "Steel Sword Blade",
  "description": "Sharp steel blade",
  "format": "fbx",
  "category": "weapons",
  "is_weapon_part": true,
  "weapon_part_metadata": {
    "weapon_type": "sword",
    "part_type": "blade",
    "material_slots": ["blade_mat"]
  }
}
```

3. Upload textures for the handle:
```json
POST /textures/
{
  "name": "Steel Handle Diffuse",
  "format": "png",
  "texture_type": "diffuse",
  "associated_model": "handle_model_id",
  "weapon_type": "sword",
  "part_type": "handle"
}
```

4. Create the sword assembly:
```json
POST /assemblies/
{
  "name": "Basic Steel Sword",
  "description": "A simple steel sword",
  "weapon_type": "sword",
  "parts": [
    {
      "model_id": "handle_model_id",
      "part_type": "handle",
      "position": {"x": 0, "y": 0, "z": 0},
      "rotation": {"x": 0, "y": 0, "z": 0},
      "scale": {"x": 1, "y": 1, "z": 1}
    },
    {
      "model_id": "blade_model_id",
      "part_type": "blade",
      "position": {"x": 0, "y": 0.5, "z": 0},
      "rotation": {"x": 0, "y": 0, "z": 0},
      "scale": {"x": 1, "y": 1, "z": 1},
      "material_overrides": {
        "blade_mat": "blade_texture_id"
      }
    }
  ]
}
```

## Next Steps

1. **Authentication** - Implement proper authentication and authorization
2. **Validation** - Add more comprehensive validation for uploaded files
3. **Preview Generation** - Auto-generate thumbnails for models and assemblies
4. **Client Integration** - Create client libraries for popular 3D software
5. **Version Control** - Add versioning for models and assemblies

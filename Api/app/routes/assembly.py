# app/routes/assembly.py
"""
API routes for weapon assembly operations
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List
from datetime import datetime


from ..models.model_schema import (
    WeaponAssembly,
    WeaponAssemblyList,
    WeaponAssemblyItem,
    WeaponType,
)
from ..database import (
    store_assembly,
    get_assembly_by_id,
    update_assembly,
    list_assemblies,
    delete_assembly,
)

router = APIRouter(prefix="/assemblies", tags=["Weapon Assemblies"])


@router.post("/", response_model=dict)
async def create_assembly_route(
    assembly: WeaponAssembly = Body(..., description="Weapon assembly definition")
):
    """
    Create a new weapon assembly

    An assembly is a collection of weapon parts with positioning information
    """
    try:
        # Set creation timestamps
        now = datetime.utcnow()
        assembly_dict = assembly.model_dump()
        assembly_dict["created_at"] = now
        assembly_dict["updated_at"] = now

        # Store in database
        assembly_id = await store_assembly(assembly_dict)

        return {"id": assembly_id, "message": "Weapon assembly created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create assembly: {str(e)}"
        )


@router.get("/", response_model=WeaponAssemblyList)
async def list_assemblies_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    weapon_type: Optional[WeaponType] = None,
    tag: Optional[str] = None,
):
    """
    List all weapon assemblies with optional filtering

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - weapon_type: Filter by weapon type
    - tag: Filter by tag
    """
    # Build filters
    filters = {}

    if weapon_type:
        filters["weapon_type"] = weapon_type.value

    if tag:
        filters["tags"] = tag

    # Get assemblies
    documents, total_count = await list_assemblies(skip, limit, filters)

    # Convert to response model
    assemblies = []
    for doc in documents:
        doc["id"] = str(doc.pop("_id"))
        assemblies.append(WeaponAssembly(**doc))

    return WeaponAssemblyList(
        assemblies=assemblies,
        total=total_count,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{assembly_id}", response_model=WeaponAssembly)
async def get_assembly_route(
    assembly_id: str = Path(..., description="ID of the assembly to retrieve")
):
    """
    Get a weapon assembly by its ID

    Returns the complete assembly definition
    """
    try:
        document = await get_assembly_by_id(assembly_id)

        if not document:
            raise HTTPException(status_code=404, detail="Assembly not found")

        # Convert to response model
        document["id"] = str(document.pop("_id"))
        return WeaponAssembly(**document)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error retrieving assembly: {str(e)}"
        )


@router.put("/{assembly_id}", response_model=dict)
async def update_assembly_route(
    assembly_id: str = Path(..., description="ID of the assembly to update"),
    update_data: dict = Body(..., description="Fields to update"),
):
    """
    Update a weapon assembly

    Parameters:
    - assembly_id: ID of the assembly to update
    - update_data: Fields to update (partial update supported)
    """
    try:
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Update in database
        success = await update_assembly(assembly_id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail="Assembly not found")

        return {"message": "Assembly updated successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error updating assembly: {str(e)}"
        )


@router.patch("/{assembly_id}/parts", response_model=dict)
async def update_assembly_parts_route(
    assembly_id: str = Path(..., description="ID of the assembly to update"),
    parts: List[WeaponAssemblyItem] = Body(..., description="Updated parts list"),
):
    """
    Update only the parts of a weapon assembly

    This is a specialized endpoint for more efficient updates when only modifying parts
    """
    try:
        # Convert parts to dict for update
        parts_data = [part.model_dump() for part in parts]

        # Update only the parts field and the updated_at timestamp
        update_data = {"parts": parts_data, "updated_at": datetime.utcnow()}

        # Update in database
        success = await update_assembly(assembly_id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail="Assembly not found")

        return {"message": "Assembly parts updated successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error updating assembly parts: {str(e)}"
        )


@router.delete("/{assembly_id}")
async def delete_assembly_route(
    assembly_id: str = Path(..., description="ID of the assembly to delete")
):
    """
    Delete a weapon assembly by its ID

    This only deletes the assembly definition, not the referenced models or textures
    """
    try:
        success = await delete_assembly(assembly_id)

        if not success:
            raise HTTPException(status_code=404, detail="Assembly not found")

        return {"message": "Assembly deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error deleting assembly: {str(e)}"
        )


@router.post("/{assembly_id}/duplicate", response_model=dict)
async def duplicate_assembly_route(
    assembly_id: str = Path(..., description="ID of the assembly to duplicate"),
    new_name: Optional[str] = Query(None, description="Name for the new assembly"),
):
    """
    Duplicate an existing weapon assembly

    Creates a new assembly with the same parts and properties but a different ID
    """
    try:
        # Get the existing assembly
        document = await get_assembly_by_id(assembly_id)

        if not document:
            raise HTTPException(status_code=404, detail="Assembly not found")

        # Remove the _id field to create a new document
        document.pop("_id")

        # Update the name if provided
        if new_name:
            document["name"] = new_name
        else:
            document["name"] = f"{document['name']} (Copy)"

        # Update timestamps
        now = datetime.utcnow()
        document["created_at"] = now
        document["updated_at"] = now

        # Store as a new assembly
        new_assembly_id = await store_assembly(document)

        return {"id": new_assembly_id, "message": "Assembly duplicated successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error duplicating assembly: {str(e)}"
        )

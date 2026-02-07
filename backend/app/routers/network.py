"""
Create-network API (wireframe). In-memory store; extend later with DB.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.network import NetworkCreate, NetworkResponse
from app.middleware.auth import get_optional_user

router = APIRouter()

# In-memory store (wireframe); replace with DB later
_networks: dict[str, dict] = {}


@router.post("/", response_model=NetworkResponse)
async def create_network(
    body: NetworkCreate,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Create a single network. Returns id and params; use id later for simulation if needed.
    """
    network_id = str(uuid.uuid4())
    record = {
        "id": network_id,
        "name": body.name,
        "num_banks": body.num_banks,
        "connection_density": body.connection_density,
        "description": body.description,
        "status": "created",
    }
    _networks[network_id] = record
    return NetworkResponse(
        id=record["id"],
        name=record["name"],
        num_banks=record["num_banks"],
        connection_density=record["connection_density"],
        description=record["description"],
        status=record["status"],
    )


@router.get("/")
async def list_networks(current_user: Optional[dict] = Depends(get_optional_user)):
    """List all created networks (wireframe: in-memory)."""
    return {"networks": list(_networks.values())}


@router.get("/{network_id}", response_model=NetworkResponse)
async def get_network(
    network_id: str,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Get a single network by id."""
    if network_id not in _networks:
        raise HTTPException(status_code=404, detail="Network not found")
    r = _networks[network_id]
    return NetworkResponse(
        id=r["id"],
        name=r["name"],
        num_banks=r["num_banks"],
        connection_density=r["connection_density"],
        description=r.get("description"),
        status=r.get("status", "created"),
    )

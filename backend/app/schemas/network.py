"""
Schemas for create-network API (wireframe).
"""
from typing import Optional
from pydantic import BaseModel, Field


class NetworkCreate(BaseModel):
    """Payload to create a single network."""

    name: str = Field(..., min_length=1, max_length=200, description="Network name")
    num_banks: int = Field(default=20, ge=1, le=100, description="Number of banks in the network")
    connection_density: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Interbank connection density (0–1); higher = more links between banks",
    )
    description: Optional[str] = Field(default=None, max_length=500)


class NetworkResponse(BaseModel):
    """Response after creating a network."""

    id: str
    name: str
    num_banks: int
    connection_density: float
    description: Optional[str] = None
    status: str = "created"

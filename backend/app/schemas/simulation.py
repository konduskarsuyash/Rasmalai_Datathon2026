"""
Pydantic schemas for simulation API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SimulationRunRequest(BaseModel):
    """Request body for POST /api/simulation/run."""
    num_banks: int = Field(default=20, ge=1, le=100, description="Number of banks")
    num_steps: int = Field(default=30, ge=1, le=200, description="Simulation steps")
    use_featherless: bool = Field(default=False, description="Use Featherless for priority (if API key set)")
    verbose: bool = Field(default=False, description="Include verbose logs in response")
    lending_amount: float = Field(default=10.0, ge=0)
    investment_amount: float = Field(default=10.0, ge=0)


class SimulationRunResponse(BaseModel):
    """Response for POST /api/simulation/run."""
    summary: Dict[str, Any]
    steps_count: int
    defaults_over_time: List[int]
    total_equity_over_time: List[float]
    market_prices: List[Dict]
    cascade_events: List[Dict]
    system_logs: List[Dict]
    bank_logs: Optional[List[Dict]] = None  # Can be large; optional in response

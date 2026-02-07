"""
Pydantic schemas for simulation API.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NodeParameters(BaseModel):
    """Simplified parameters for a single node/bank in the simulation."""
    node_id: Optional[str] = None
    initial_capital: float = Field(default=100.0, ge=0, description="Initial capital")
    target_leverage: float = Field(default=3.0, ge=1, le=10, description="Target leverage ratio (1-10x)")
    risk_factor: float = Field(default=0.2, ge=0, le=1, description="Risk tolerance (0-1)")


class SimulationRunRequest(BaseModel):
    """Request body for POST /api/simulation/run."""
    num_banks: int = Field(default=20, ge=1, le=100, description="Number of banks")
    num_steps: int = Field(default=30, ge=1, le=200, description="Simulation steps")
    use_featherless: bool = Field(default=True, description="Use Featherless for priority (if API key set)")
    use_game_theory: bool = Field(default=True, description="Use Nash equilibrium game theory (recommended) vs heuristics")
    verbose: bool = Field(default=False, description="Include verbose logs in response")
    lending_amount: float = Field(default=10.0, ge=0, description="Default lending amount if node params not provided")
    investment_amount: float = Field(default=10.0, ge=0, description="Default investment amount if node params not provided")
    node_parameters: Optional[List[NodeParameters]] = Field(
        default=None, 
        description="Optional per-node parameters. If provided, will override default values for each bank."
    )
    connection_density: float = Field(default=0.2, ge=0, le=1, description="Interbank connection density")


class TransactionEvent(BaseModel):
    """Real-time transaction event for streaming."""
    time_step: int
    from_bank: int
    to_bank: Optional[int] = None
    transaction_type: str
    amount: float
    reason: str


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

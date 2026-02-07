from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EquilibriumComputeRequest(BaseModel):
    network_id: str
    max_iterations: int = Field(1000, ge=1, le=5000)
    convergence_threshold: float = Field(1e-3, gt=0)
    analyze_stability: bool = True


class StrategyProfile(BaseModel):
    lending_limits: Dict[str, float]
    margin_requirements: Dict[str, float]
    interest_rates: Dict[str, float]


class EquilibriumComputeResponse(BaseModel):
    network_id: str
    converged: bool
    iterations: Optional[int] = None
    equilibrium: Dict[str, StrategyProfile]
    stability: Optional[Dict] = None  # is_stable, deviation_impacts

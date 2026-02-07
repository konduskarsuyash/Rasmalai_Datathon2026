from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ContagionSimulateRequest(BaseModel):
    network_id: str
    # DebtRank: initial distress per node (0-1)
    initial_shock: Optional[Dict[str, float]] = None
    # Threshold cascade: initial defaulters
    initial_defaults: Optional[List[str]] = None
    threshold: float = Field(1.0, ge=0)
    mode: str = "debtrank"  # "debtrank" | "threshold"
    max_iterations: int = Field(100, ge=1, le=500)


class ContagionSimulateResponse(BaseModel):
    network_id: str
    mode: str
    debtrank: Optional[Dict[str, float]] = None
    max_debtrank: Optional[float] = None
    systemic_risk: Optional[float] = None
    # Threshold cascade
    timeline: Optional[List[dict]] = None
    defaulted_institutions: Optional[List[str]] = None
    total_defaults: Optional[int] = None
    default_rate: Optional[float] = None
    total_loss: Optional[float] = None
    loss_rate: Optional[float] = None


class StressTestScenario(BaseModel):
    name: str
    type: str  # debtrank | threshold
    initial_shock: Optional[Dict[str, float]] = None
    initial_defaults: Optional[List[str]] = None
    threshold: float = 1.0


class StressTestRequest(BaseModel):
    network_id: str
    scenarios: List[StressTestScenario]


class StressTestResponse(BaseModel):
    network_id: str
    results: List[dict]

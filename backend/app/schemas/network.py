from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class InstitutionCreate(BaseModel):
    id: str
    type: str = "bank"  # bank | hedge_fund | clearing_house | insurance
    capital: float = Field(..., gt=0)
    assets: float = Field(..., gt=0)
    liabilities: float = Field(..., ge=0)
    risk_aversion: float = Field(1.0, ge=0)
    systemic_awareness: float = Field(0.1, ge=0, le=1)


class InstitutionResponse(BaseModel):
    id: str
    type: str
    capital: float
    assets: float
    liabilities: float
    risk_aversion: float
    systemic_awareness: float


class ExposureCreate(BaseModel):
    creditor_id: str
    debtor_id: str
    amount: float = Field(..., gt=0)
    maturity_days: int = Field(..., ge=1)
    interest_rate: float = Field(0.02, ge=0)
    collateral: float = Field(0.0, ge=0)


class ExposureResponse(BaseModel):
    creditor_id: str
    debtor_id: str
    amount: float
    maturity_days: int
    interest_rate: float
    collateral: float


class NetworkCreate(BaseModel):
    id: str
    name: Optional[str] = None
    institutions: List[InstitutionCreate] = []
    exposures: List[ExposureCreate] = []


class NetworkResponse(BaseModel):
    id: str
    name: Optional[str] = None
    institutions: List[InstitutionResponse]
    exposures: List[ExposureResponse]
    node_ids: List[str]


class NetworkMetricsResponse(BaseModel):
    network_id: str
    node_ids: List[str]
    degree_centrality: Dict[str, float]
    betweenness_centrality: Dict[str, float]
    density: float
    avg_clustering: float
    spectral_radius: float
    is_stable: bool
    core_periphery: Dict[str, str]
    exposure_matrix: List[List[float]]
    capital_vector: List[float]

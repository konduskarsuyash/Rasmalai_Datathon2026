"""
Equilibrium Engine API: Nash equilibrium via fictitious play, stability analysis.
"""
from fastapi import APIRouter, HTTPException

from ..schemas.equilibrium import (
    EquilibriumComputeRequest,
    EquilibriumComputeResponse,
    StrategyProfile,
)
from ..services.equilibrium_service import EquilibriumService

router = APIRouter()


@router.post("/compute", response_model=EquilibriumComputeResponse)
async def compute_equilibrium(req: EquilibriumComputeRequest):
    """
    Compute Nash equilibrium (fictitious play) and optionally analyze stability.
    """
    try:
        result = EquilibriumService.compute_equilibrium(
            req.network_id,
            max_iterations=req.max_iterations,
            convergence_threshold=req.convergence_threshold,
            analyze_stability=req.analyze_stability,
        )
        equilibrium = {
            agent_id: StrategyProfile(**s)
            for agent_id, s in result["equilibrium"].items()
        }
        return EquilibriumComputeResponse(
            network_id=req.network_id,
            converged=result["converged"],
            iterations=None,
            equilibrium=equilibrium,
            stability=result.get("stability"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

"""
Contagion Engine API: DebtRank and threshold cascade simulation.
"""
from fastapi import APIRouter, HTTPException

from ..schemas.contagion import (
    ContagionSimulateRequest,
    ContagionSimulateResponse,
    StressTestRequest,
    StressTestResponse,
)
from ..services.contagion_service import ContagionService

router = APIRouter()


@router.post("/simulate", response_model=ContagionSimulateResponse)
async def simulate_contagion(req: ContagionSimulateRequest):
    """
    Run contagion: DebtRank (initial_shock) or threshold cascade (initial_defaults).
    """
    try:
        if req.mode == "debtrank":
            result = ContagionService.run_debtrank(
                req.network_id,
                req.initial_shock,
                req.max_iterations,
            )
            return ContagionSimulateResponse(
                network_id=req.network_id,
                mode="debtrank",
                debtrank=result["debtrank"],
                max_debtrank=result["max_debtrank"],
                systemic_risk=result["systemic_risk"],
            )
        else:
            if not req.initial_defaults:
                raise HTTPException(
                    status_code=400,
                    detail="initial_defaults required for threshold mode",
                )
            result = ContagionService.run_threshold_cascade(
                req.network_id,
                req.initial_defaults,
                req.threshold,
            )
            return ContagionSimulateResponse(
                network_id=req.network_id,
                mode="threshold",
                timeline=result["timeline"],
                defaulted_institutions=result["defaulted_institutions"],
                total_defaults=result["total_defaults"],
                default_rate=result["default_rate"],
                total_loss=result["total_loss"],
                loss_rate=result["loss_rate"],
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/stress-test", response_model=StressTestResponse)
async def stress_test(req: StressTestRequest):
    """Run multiple shock scenarios on the same network."""
    try:
        scenarios = [s.model_dump() for s in req.scenarios]
        results = ContagionService.run_stress_test(req.network_id, scenarios)
        return StressTestResponse(network_id=req.network_id, results=results)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

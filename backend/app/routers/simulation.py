"""
Simulation API: run v2 simulation (core + config + ml + optional featherless).
"""
from typing import Optional

from fastapi import APIRouter, Depends
from app.core import run_simulation_v2, SimulationConfig
from app.middleware.auth import get_optional_user
from app.schemas.simulation import SimulationRunRequest, SimulationRunResponse

router = APIRouter()


def _get_featherless_fn():
    """Return featherless priority function if API key is set, else None."""
    try:
        from app.config.settings import FEATHERLESS_API_KEY
        if not FEATHERLESS_API_KEY:
            return None
        from app.featherless.decision_engine import get_strategic_priority, create_featherless_client
        client = create_featherless_client()
        if client is None:
            return None

        def fn(observation):
            return get_strategic_priority(observation, client)

        return fn
    except Exception:
        return None


@router.post("/run", response_model=SimulationRunResponse)
async def run_simulation(
    body: SimulationRunRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Run financial network simulation v2 (balance-sheet, ML policy, optional Featherless).
    """
    config = SimulationConfig(
        num_banks=body.num_banks,
        num_steps=body.num_steps,
        use_featherless=body.use_featherless,
        verbose=body.verbose,
        lending_amount=body.lending_amount,
        investment_amount=body.investment_amount,
    )
    featherless_fn = _get_featherless_fn() if body.use_featherless else None
    history = run_simulation_v2(config, featherless_fn=featherless_fn)
    return SimulationRunResponse(
        summary=history["summary"],
        steps_count=len(history["steps"]),
        defaults_over_time=history["defaults_over_time"],
        total_equity_over_time=history["total_equity_over_time"],
        market_prices=history["market_prices"],
        cascade_events=history["cascade_events"],
        system_logs=history["system_logs"],
        bank_logs=history.get("bank_logs") if body.verbose else None,
    )

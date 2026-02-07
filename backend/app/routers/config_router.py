"""
Config API: return public config (no secrets).
"""
from fastapi import APIRouter, Depends
from typing import Optional
from app.config.settings import (
    NUM_AGENTS,
    TIME_STEPS,
    DEFAULT_CAPITAL,
    DEFAULT_LIQUIDITY,
    DEFAULT_THRESHOLD,
    FEATHERLESS_AGENT_RATIO,
    FEATHERLESS_BASE_URL,
    FEATHERLESS_MODEL,
    SHOCK_MAGNITUDE,
    SHOCK_PROBABILITY,
    VERBOSE,
)
from app.schemas.config_schema import ConfigResponse
from app.middleware.auth import get_optional_user

router = APIRouter()


@router.get("/", response_model=ConfigResponse)
async def get_config(current_user: Optional[dict] = Depends(get_optional_user)):
    """Return public configuration (no API keys)."""
    return ConfigResponse(
        NUM_AGENTS=NUM_AGENTS,
        TIME_STEPS=TIME_STEPS,
        DEFAULT_CAPITAL=DEFAULT_CAPITAL,
        DEFAULT_LIQUIDITY=DEFAULT_LIQUIDITY,
        DEFAULT_THRESHOLD=DEFAULT_THRESHOLD,
        FEATHERLESS_AGENT_RATIO=FEATHERLESS_AGENT_RATIO,
        FEATHERLESS_BASE_URL=FEATHERLESS_BASE_URL,
        FEATHERLESS_MODEL=FEATHERLESS_MODEL,
        SHOCK_MAGNITUDE=SHOCK_MAGNITUDE,
        SHOCK_PROBABILITY=SHOCK_PROBABILITY,
        VERBOSE=VERBOSE,
    )

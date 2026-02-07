"""
Pydantic schemas for config API.
"""
from pydantic import BaseModel


class ConfigResponse(BaseModel):
    """Public config (no secrets)."""
    NUM_AGENTS: int
    TIME_STEPS: int
    DEFAULT_CAPITAL: float
    DEFAULT_LIQUIDITY: float
    DEFAULT_THRESHOLD: float
    FEATHERLESS_AGENT_RATIO: float
    FEATHERLESS_BASE_URL: str
    FEATHERLESS_MODEL: str
    SHOCK_MAGNITUDE: float
    SHOCK_PROBABILITY: float
    VERBOSE: bool

"""
Featherless.ai Decision Engine (optional).
Returns PROFIT, LIQUIDITY, or STABILITY for simulation v2.
"""
from typing import Dict, Optional
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.config.settings import FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, FEATHERLESS_MODEL


class StrategicPriority(Enum):
    PROFIT = "PROFIT"
    LIQUIDITY = "LIQUIDITY"
    STABILITY = "STABILITY"


def create_featherless_client():
    if not FEATHERLESS_API_KEY or OpenAI is None:
        return None
    return OpenAI(base_url=FEATHERLESS_BASE_URL, api_key=FEATHERLESS_API_KEY)


def get_strategic_priority(observation: Dict, client=None, use_llm: bool = True) -> StrategicPriority:
    """Rule-based priority when LLM unavailable; otherwise can call Featherless."""
    bank_id = observation.get("bank_id", 0)
    cash = observation.get("cash", 100)
    equity = observation.get("equity", 50)
    leverage = observation.get("leverage", 2.0)
    liquidity_ratio = observation.get("liquidity_ratio", 0.5)
    local_stress = observation.get("local_stress", 0.0)

    if local_stress > 0.4:
        return StrategicPriority.STABILITY
    if equity < 20 or cash < 20:
        return StrategicPriority.LIQUIDITY
    if leverage > 4.0:
        return StrategicPriority.STABILITY
    if liquidity_ratio < 0.15:
        return StrategicPriority.LIQUIDITY
    bank_type = bank_id % 4
    if bank_type == 0 and leverage < 2.0 and cash > 120:
        return StrategicPriority.PROFIT
    if bank_type == 1 and equity > 60 and liquidity_ratio > 0.3:
        return StrategicPriority.PROFIT
    if bank_type == 3 and equity > 50:
        return StrategicPriority.PROFIT
    return StrategicPriority.STABILITY

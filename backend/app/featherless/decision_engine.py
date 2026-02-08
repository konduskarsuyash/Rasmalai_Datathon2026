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
    """Rule-based priority when LLM unavailable; otherwise can call Featherless.
    
    Banks with healthy financials should pursue PROFIT (which enables market investment).
    Only under genuine stress should they switch to STABILITY or LIQUIDITY.
    """
    bank_id = observation.get("bank_id", 0)
    cash = observation.get("cash", 100)
    equity = observation.get("equity", 50)
    leverage = observation.get("leverage", 2.0)
    liquidity_ratio = observation.get("liquidity_ratio", 0.5)
    local_stress = observation.get("local_stress", 0.0)
    risk_appetite = observation.get("risk_appetite", 0.5)

    # === EMERGENCY: only in genuine crisis ===
    if local_stress > 0.5:
        return StrategicPriority.STABILITY
    if equity < 15 or cash < 15:
        return StrategicPriority.LIQUIDITY
    if leverage > 5.0:
        return StrategicPriority.STABILITY
    if liquidity_ratio < 0.12:
        return StrategicPriority.LIQUIDITY
    
    # === NORMAL OPERATION: most banks should pursue profit ===
    # High risk appetite → always PROFIT (aggressive banks invest/lend freely)
    if risk_appetite > 0.6:
        return StrategicPriority.PROFIT
    
    # Healthy financials → PROFIT
    if cash > 40 and equity > 30 and leverage < 3.0:
        return StrategicPriority.PROFIT
    
    # Moderate stress but not critical → STABILITY with caution
    if local_stress > 0.3 or leverage > 3.5:
        return StrategicPriority.STABILITY
    
    # Default: banks with moderate health → PROFIT to keep the economy moving
    if cash > 25 and equity > 20:
        return StrategicPriority.PROFIT
    
    return StrategicPriority.STABILITY

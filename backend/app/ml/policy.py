"""
ML Policy for Financial Network MVP v2.
"""
from typing import Dict, Optional
from enum import Enum


class BankAction(Enum):
    INCREASE_LENDING = "INCREASE_LENDING"
    DECREASE_LENDING = "DECREASE_LENDING"
    INVEST_MARKET = "INVEST_MARKET"
    DIVEST_MARKET = "DIVEST_MARKET"
    HOARD_CASH = "HOARD_CASH"


class StrategicPriority(Enum):
    PROFIT = "PROFIT"
    LIQUIDITY = "LIQUIDITY"
    STABILITY = "STABILITY"


class MLPolicy:
    def __init__(self, model_type: str = "rule_based"):
        self.model_type = model_type

    def select_action(self, observation: Dict, priority_value: Optional[str] = None) -> BankAction:
        bank_id = observation.get("bank_id", 0)
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        liquidity_ratio = observation.get("liquidity_ratio", 0.5)
        market_exposure = observation.get("market_exposure", 0.0)
        leverage_gap = observation.get("leverage_gap", 0.0)
        liquidity_gap = observation.get("liquidity_gap", 0.0)
        exposure_gap = observation.get("exposure_gap", 0.0)
        local_stress = observation.get("local_stress", 0.0)

        if priority_value == "LIQUIDITY":
            if cash < 30 or liquidity_ratio < 0.2:
                return BankAction.DIVEST_MARKET
            return BankAction.HOARD_CASH
        if priority_value == "STABILITY":
            if leverage > 2.5:
                return BankAction.DECREASE_LENDING
            if market_exposure > 0.15:
                return BankAction.DIVEST_MARKET
            return BankAction.HOARD_CASH

        if local_stress > 0.3:
            if liquidity_ratio < 0.25:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        if equity < 30:
            return BankAction.HOARD_CASH
        if cash > 80 and liquidity_ratio > 0.5:
            if bank_id % 3 == 0:
                return BankAction.INCREASE_LENDING
            elif bank_id % 3 == 1:
                return BankAction.INVEST_MARKET
            return BankAction.INCREASE_LENDING
        if cash < 30:
            if market_exposure > 0.1:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING

        gaps = {"leverage": abs(leverage_gap), "liquidity": abs(liquidity_gap), "exposure": abs(exposure_gap)}
        priority_gap = max(gaps, key=gaps.get)
        if priority_gap == "leverage":
            return BankAction.DECREASE_LENDING if leverage_gap > 0 else BankAction.INCREASE_LENDING
        elif priority_gap == "liquidity":
            return BankAction.HOARD_CASH if liquidity_gap > 0 else BankAction.INVEST_MARKET
        elif priority_gap == "exposure":
            return BankAction.DIVEST_MARKET if exposure_gap > 0 else BankAction.INVEST_MARKET
        return BankAction.HOARD_CASH

    def get_action_reason(self, observation: Dict, action: BankAction, priority_value: Optional[str] = None) -> str:
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        parts = []
        if priority_value:
            parts.append(f"priority={priority_value}")
        parts.extend([f"cash=${cash:.0f}", f"eq=${equity:.0f}", f"lev={leverage:.1f}x"])
        return f"{action.value} ({', '.join(parts)})"


_policy = MLPolicy()


def select_action(observation: Dict, priority=None) -> tuple:
    priority_value = None
    if priority is not None:
        priority_value = priority.value if hasattr(priority, "value") else str(priority)
    action = _policy.select_action(observation, priority_value)
    reason = _policy.get_action_reason(observation, action, priority_value)
    return action, reason

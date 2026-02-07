"""
ML Policy for Financial Network MVP v2.
Selects discrete actions based on current state and target gaps.
Rule-based initially, designed to be swappable with ML model later.
"""
from typing import Dict, Optional
from enum import Enum


class BankAction(Enum):
    """Discrete actions a bank can take."""
    INCREASE_LENDING = "INCREASE_LENDING"
    DECREASE_LENDING = "DECREASE_LENDING"
    INVEST_MARKET = "INVEST_MARKET"
    DIVEST_MARKET = "DIVEST_MARKET"
    HOARD_CASH = "HOARD_CASH"


class StrategicPriority(Enum):
    """Strategic priorities from Featherless."""
    PROFIT = "PROFIT"
    LIQUIDITY = "LIQUIDITY"
    STABILITY = "STABILITY"


class MLPolicy:
    """
    ML-based action selector for banks.
    
    Uses bank-specific features (cash, leverage, gaps) to select actions.
    Each bank will get DIFFERENT actions based on their unique state.
    """
    
    def __init__(self, model_type: str = "rule_based"):
        self.model_type = model_type
    
    def select_action(
        self,
        observation: Dict,
        priority_value: Optional[str] = None  # Accept string, not enum
    ) -> BankAction:
        """
        Select an action based on observation and optional priority override.
        
        Args:
            observation: Dict from bank.observe_local_state()
            priority_value: Priority string ("PROFIT", "LIQUIDITY", "STABILITY")
            
        Returns:
            Selected action
        """
        # Extract bank-specific features
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
        
        # ============================================================
        # PRIORITY OVERRIDES (Featherless influence)
        # ============================================================
        if priority_value == "LIQUIDITY":
            # Low cash → divest from markets
            if cash < 30 or liquidity_ratio < 0.2:
                return BankAction.DIVEST_MARKET
            # Otherwise just hoard
            return BankAction.HOARD_CASH
        
        if priority_value == "STABILITY":
            # High leverage → reduce lending
            if leverage > 2.5:
                return BankAction.DECREASE_LENDING
            # High market exposure → divest
            if market_exposure > 0.15:
                return BankAction.DIVEST_MARKET
            return BankAction.HOARD_CASH
        
        # ============================================================
        # PROFIT MODE or NO PRIORITY: Select based on target gaps
        # Each bank has different gaps, so different actions
        # ============================================================
        
        # High stress → be conservative
        if local_stress > 0.3:
            if liquidity_ratio < 0.25:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        
        # Low equity warning → protect capital
        if equity < 30:
            return BankAction.HOARD_CASH
        
        # Rich in cash → can be aggressive
        if cash > 80 and liquidity_ratio > 0.5:
            # Alternate between lending and investing based on bank_id
            if bank_id % 3 == 0:
                return BankAction.INCREASE_LENDING
            elif bank_id % 3 == 1:
                return BankAction.INVEST_MARKET
            else:
                return BankAction.INCREASE_LENDING
        
        # Low on cash → need to build reserves
        if cash < 30:
            if market_exposure > 0.1:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        
        # Target-gap based decisions
        gaps = {
            "leverage": abs(leverage_gap),
            "liquidity": abs(liquidity_gap),
            "exposure": abs(exposure_gap),
        }
        
        priority_gap = max(gaps, key=gaps.get)
        
        if priority_gap == "leverage":
            if leverage_gap > 0:  # Over-leveraged
                return BankAction.DECREASE_LENDING
            else:  # Under-leveraged, can take more risk
                return BankAction.INCREASE_LENDING
        
        elif priority_gap == "liquidity":
            if liquidity_gap > 0:  # Below target liquidity
                return BankAction.HOARD_CASH
            else:  # Above target, can invest
                return BankAction.INVEST_MARKET
        
        elif priority_gap == "exposure":
            if exposure_gap > 0:  # Over-exposed to market
                return BankAction.DIVEST_MARKET
            else:  # Under-exposed
                return BankAction.INVEST_MARKET
        
        return BankAction.HOARD_CASH
    
    def get_action_reason(
        self,
        observation: Dict,
        action: BankAction,
        priority_value: Optional[str] = None
    ) -> str:
        """Generate explanation for why this action was chosen."""
        reasons = []
        
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        
        if priority_value:
            reasons.append(f"priority={priority_value}")
        
        reasons.append(f"cash=${cash:.0f}")
        reasons.append(f"eq=${equity:.0f}")
        reasons.append(f"lev={leverage:.1f}x")
        
        return f"{action.value} ({', '.join(reasons)})"


# Singleton policy instance
_policy = MLPolicy()


def select_action(
    observation: Dict,
    priority = None  # Accept any type
) -> tuple:
    """
    Convenience function to select action using default policy.
    
    Returns:
        tuple: (action, reason)
    """
    # Convert priority to string if it's an enum
    priority_value = None
    if priority is not None:
        if hasattr(priority, 'value'):
            priority_value = priority.value
        else:
            priority_value = str(priority)
    
    action = _policy.select_action(observation, priority_value)
    reason = _policy.get_action_reason(observation, action, priority_value)
    return action, reason

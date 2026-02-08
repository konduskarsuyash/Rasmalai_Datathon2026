"""
ML Policy for Financial Network MVP v2.
Integrates Game-Theoretic Nash Equilibrium decision making and ML-based Risk Assessment
"""
from typing import Dict, Optional
from enum import Enum

# Import Nash equilibrium game theory engine
try:
    from .game_theory import get_nash_equilibrium_action, GameAction as GTGameAction
    GAME_THEORY_AVAILABLE = True
except ImportError:
    GAME_THEORY_AVAILABLE = False

# Import risk assessment
try:
    from .risk_models import assess_lending_risk, RiskLevel
    RISK_ASSESSMENT_AVAILABLE = True
except ImportError:
    RISK_ASSESSMENT_AVAILABLE = False


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
        """
        Initialize policy
        
        Args:
            model_type: "rule_based" (heuristics) or "game_theory" (Nash equilibrium)
        """
        self.model_type = model_type
        self.use_game_theory = (model_type == "game_theory" and GAME_THEORY_AVAILABLE)
        
        if model_type == "game_theory" and not GAME_THEORY_AVAILABLE:
            print("Warning: Game theory requested but not available. Falling back to rule_based.")
            self.use_game_theory = False

    def select_action(self, observation: Dict, priority_value: Optional[str] = None, 
                     network_default_rate: float = 0.0) -> BankAction:
        """
        Select action using either game theory (Nash equilibrium) or heuristics.
        
        Economic logic:
        - High risk_appetite banks: borrow → invest in markets (carry trade for higher returns)
        - Low risk_appetite banks: lend to other banks (earn interest income safely)
        - This creates a natural economic cycle where borrowing has PURPOSE
        """
        
        # === GAME THEORY MODE: Nash Equilibrium ===
        if self.use_game_theory:
            return self._select_action_game_theoretic(observation, priority_value, network_default_rate)
        
        # === HEURISTIC MODE: Rule-based ===
        return self._select_action_heuristic(observation, priority_value)
    
    def _select_action_game_theoretic(self, observation: Dict, priority_value: Optional[str],
                                     network_default_rate: float) -> BankAction:
        """
        Game-theoretic decision using Nash equilibrium best response.
        Uses risk_appetite to balance between market investment and interbank lending.
        """
        import random
        
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        market_exposure = observation.get("market_exposure", 0.0)
        liquidity_ratio = observation.get("liquidity_ratio", 0.5)
        risk_appetite = observation.get("risk_appetite", 0.5)
        has_markets = observation.get("has_markets", True)
        local_stress = observation.get("local_stress", 0.0)
        
        # Get Nash equilibrium action (LEND or HOARD)
        gt_action, reasoning = get_nash_equilibrium_action(observation, network_default_rate)
        
        # Map game theory action to bank actions
        if gt_action.value == "LEND":
            # Nash equilibrium says LEND — deploy capital productively
            
            # Emergency: too little cash to do anything useful
            if cash < 15 or liquidity_ratio < 0.1:
                return BankAction.HOARD_CASH
            
            # Decide between INVEST_MARKET vs INCREASE_LENDING using risk_appetite
            # High risk_appetite (>0.5) → prefer market investment (higher potential returns)
            # Low risk_appetite (<0.5) → prefer interbank lending (stable interest income)
            
            if has_markets and cash > 20:
                # Investment probability scales with risk_appetite
                # risk_appetite=0.0 → 15% chance to invest (conservative banks still diversify a bit)
                # risk_appetite=0.5 → 50% chance to invest
                # risk_appetite=1.0 → 85% chance to invest (aggressive banks love markets)
                invest_prob = 0.15 + (risk_appetite * 0.70)
                
                # Reduce invest probability if already heavily exposed to markets
                # Allow up to 50% market exposure (was 20% before — way too restrictive)
                if market_exposure > 0.5:
                    invest_prob *= 0.2  # Heavily reduce but don't eliminate
                elif market_exposure > 0.35:
                    invest_prob *= 0.5  # Moderate reduction
                
                # Increase invest probability if cash is plentiful (put money to work)
                if liquidity_ratio > 0.6:
                    invest_prob = min(0.95, invest_prob * 1.3)
                
                # Under stress, reduce market appetite
                if local_stress > 0.3:
                    invest_prob *= 0.5
                
                if random.random() < invest_prob:
                    return BankAction.INVEST_MARKET
                else:
                    if cash > 20:
                        return BankAction.INCREASE_LENDING
                    return BankAction.HOARD_CASH
            
            elif cash > 20:
                # No markets available — lend to other banks
                return BankAction.INCREASE_LENDING
            else:
                return BankAction.HOARD_CASH
        
        else:  # gt_action == HOARD
            # Nash equilibrium says HOARD — preserve capital
            # Liquidate positions and pull back
            if market_exposure > 0.1 and random.random() < 0.6:
                return BankAction.DIVEST_MARKET  # Exit market positions
            elif liquidity_ratio < 0.25:
                return BankAction.DECREASE_LENDING  # Recall loans
            else:
                return BankAction.HOARD_CASH
    
    def _select_action_heuristic(self, observation: Dict, priority_value: Optional[str]) -> BankAction:
        """
        Heuristic-based decision making with risk_appetite-driven market investment.
        """
        import random
        
        bank_id = observation.get("bank_id", 0)
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        liquidity_ratio = observation.get("liquidity_ratio", 0.5)
        market_exposure = observation.get("market_exposure", 0.0)
        risk_appetite = observation.get("risk_appetite", 0.5)
        has_markets = observation.get("has_markets", True)
        local_stress = observation.get("local_stress", 0.0)

        # Priority-based strategies (override normal logic)
        if priority_value == "LIQUIDITY":
            if cash < 30 or liquidity_ratio < 0.2:
                if market_exposure > 0.05:
                    return BankAction.DIVEST_MARKET
                return BankAction.DECREASE_LENDING
            return BankAction.HOARD_CASH
            
        if priority_value == "STABILITY":
            if leverage > 2.5:
                return BankAction.DECREASE_LENDING
            if market_exposure > 0.3:
                return BankAction.DIVEST_MARKET
            return BankAction.HOARD_CASH

        # === Emergency liquidation ===
        if cash < 15 or liquidity_ratio < 0.12:
            if market_exposure > 0.03:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        
        # === Stress response ===
        if local_stress > 0.4:
            if market_exposure > 0.1:
                return BankAction.DIVEST_MARKET
            if liquidity_ratio < 0.25:
                return BankAction.DECREASE_LENDING
            return BankAction.HOARD_CASH
            
        if equity < 20:
            return BankAction.HOARD_CASH
        
        # === Productive capital deployment ===
        # Banks with cash should PUT IT TO WORK — either invest or lend
        # The split is driven by risk_appetite:
        #   high risk → markets (higher returns, higher risk)
        #   low risk → interbank lending (stable interest income)
        
        if cash > 25:
            if has_markets and market_exposure < 0.5:
                # Probability of investing vs lending based on risk appetite
                invest_prob = 0.2 + (risk_appetite * 0.6)
                
                # Banks with lots of idle cash should be more aggressive
                if cash > 60:
                    invest_prob = min(0.9, invest_prob + 0.15)
                
                if random.random() < invest_prob:
                    return BankAction.INVEST_MARKET
            
            # Fall through to lending
            return BankAction.INCREASE_LENDING
        
        return BankAction.HOARD_CASH
    
    def get_action_reason(self, observation: Dict, action: BankAction,
                         priority_value: Optional[str] = None,
                         network_default_rate: float = 0.0) -> str:
        """Generate reasoning string for the action"""
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        
        if self.use_game_theory:
            # Get game theory reasoning
            try:
                _, gt_reasoning = get_nash_equilibrium_action(observation, network_default_rate)
                return gt_reasoning
            except Exception:
                pass
        
        # Heuristic reasoning
        parts = []
        if priority_value:
            parts.append(f"priority={priority_value}")
        parts.extend([f"cash=${cash:.0f}", f"eq=${equity:.0f}", f"lev={leverage:.1f}x"])
        return f"{action.value} ({', '.join(parts)})"


# Global policy instances
_policy_heuristic = MLPolicy(model_type="rule_based")
_policy_game_theory = MLPolicy(model_type="game_theory")

# Default to game theory if available
_policy = _policy_game_theory if _policy_game_theory.use_game_theory else _policy_heuristic


def select_action(observation: Dict, priority=None, use_game_theory: bool = True,
                 network_default_rate: float = 0.0) -> tuple:
    """
    Select action using either game theory or heuristics
    
    Args:
        observation: Bank's state
        priority: Strategic priority
        use_game_theory: If True, use Nash equilibrium; else use heuristics
        network_default_rate: System default rate for game theory
        
    Returns:
        (action, reasoning_string)
    """
    # Select policy
    policy = _policy_game_theory if (use_game_theory and GAME_THEORY_AVAILABLE) else _policy_heuristic
    
    priority_value = None
    if priority is not None:
        priority_value = priority.value if hasattr(priority, "value") else str(priority)
    
    action = policy.select_action(observation, priority_value, network_default_rate)
    reason = policy.get_action_reason(observation, action, priority_value, network_default_rate)
    
    return action, reason


def set_default_policy_mode(use_game_theory: bool = True):
    """
    Set the default policy mode globally
    
    Args:
        use_game_theory: True for Nash equilibrium, False for heuristics
    """
    global _policy
    if use_game_theory and GAME_THEORY_AVAILABLE:
        _policy = _policy_game_theory
        print("✓ Policy mode: GAME THEORY (Nash Equilibrium)")
    else:
        _policy = _policy_heuristic
        print("✓ Policy mode: HEURISTIC (Rule-based)")


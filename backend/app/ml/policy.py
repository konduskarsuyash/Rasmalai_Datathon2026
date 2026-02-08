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
        Game-theoretic decision using Nash equilibrium + Featherless AI priority.
        Featherless priority guides the decision but doesn't block investment entirely.
        """
        import random
        
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        market_exposure = observation.get("market_exposure", 0.0)
        liquidity_ratio = observation.get("liquidity_ratio", 0.5)
        risk_appetite = observation.get("risk_appetite", 0.5)
        has_markets = observation.get("has_markets", True)
        local_stress = observation.get("local_stress", 0.0)
        best_market_return = observation.get("best_market_return", 0.0)
        best_market_position = observation.get("best_market_position", 0.0)
        total_invested = observation.get("total_invested", 0.0)
        
        # === PROFIT-TAKING: If investments are profitable, actively divest to lock in gains ===
        if total_invested > 5 and best_market_return > 0.05:
            # Return > 5%: consider taking profits
            # Higher returns → higher probability of profit-taking
            profit_take_prob = min(0.80, 0.20 + best_market_return * 2.0)
            
            # Aggressive banks hold longer, conservative banks take profits earlier
            if risk_appetite < 0.4:
                profit_take_prob += 0.15  # Conservative: take profits sooner
            elif risk_appetite > 0.7:
                profit_take_prob -= 0.15  # Aggressive: hold for bigger gains
            
            # Under stress, always take profits to raise cash
            if local_stress > 0.2:
                profit_take_prob += 0.25
            
            # Low liquidity → need cash → take profits
            if liquidity_ratio < 0.2:
                profit_take_prob += 0.20
            
            profit_take_prob = max(0.10, min(0.90, profit_take_prob))
            
            if random.random() < profit_take_prob:
                return BankAction.DIVEST_MARKET
        
        # Get Nash equilibrium action (LEND or HOARD)
        gt_action, reasoning = get_nash_equilibrium_action(observation, network_default_rate)
        
        # --- Priority adjustments from Featherless AI ---
        # Priority influences investment probability but NEVER completely blocks it
        priority_invest_modifier = 1.0
        if priority_value == "PROFIT":
            priority_invest_modifier = 1.3  # Boost investment
        elif priority_value == "LIQUIDITY":
            priority_invest_modifier = 0.5  # Reduce but still allow
        elif priority_value == "STABILITY":
            priority_invest_modifier = 0.3  # Significantly reduce but still possible
        
        # Map game theory action to bank actions
        if gt_action.value == "LEND":
            # Nash equilibrium says LEND — deploy capital productively
            
            # Emergency: genuinely no cash
            if cash < 10 or equity < 5:
                return BankAction.HOARD_CASH
            
            if has_markets and cash > 15:
                # Base investment probability from risk_appetite
                invest_prob = 0.20 + (risk_appetite * 0.65)
                
                # Apply Featherless AI priority modifier
                invest_prob *= priority_invest_modifier
                
                # Reduce if heavily exposed already
                if market_exposure > 0.5:
                    invest_prob *= 0.15
                elif market_exposure > 0.35:
                    invest_prob *= 0.4
                
                # Boost if lots of idle cash (bank should deploy capital)
                if liquidity_ratio > 0.6:
                    invest_prob = min(0.95, invest_prob * 1.4)
                elif liquidity_ratio > 0.4:
                    invest_prob = min(0.90, invest_prob * 1.2)
                
                # Stress reduces appetite
                if local_stress > 0.3:
                    invest_prob *= 0.4
                
                # Clamp
                invest_prob = max(0.05, min(0.95, invest_prob))
                
                if random.random() < invest_prob:
                    return BankAction.INVEST_MARKET
                else:
                    if cash > 15:
                        return BankAction.INCREASE_LENDING
                    return BankAction.HOARD_CASH
            
            elif cash > 15:
                return BankAction.INCREASE_LENDING
            else:
                return BankAction.HOARD_CASH
        
        else:  # gt_action == HOARD
            # Nash says HOARD — but even in hoarding, allow some investment
            # if the bank is flush with cash and markets are up
            if has_markets and cash > 40 and liquidity_ratio > 0.5 and risk_appetite > 0.6:
                # Aggressive banks may still invest even when Nash says hoard
                if random.random() < 0.3 * priority_invest_modifier:
                    return BankAction.INVEST_MARKET
            
            if market_exposure > 0.1 and random.random() < 0.5:
                return BankAction.DIVEST_MARKET
            elif liquidity_ratio < 0.25:
                return BankAction.DECREASE_LENDING
            else:
                return BankAction.HOARD_CASH
    
    def _select_action_heuristic(self, observation: Dict, priority_value: Optional[str]) -> BankAction:
        """
        Heuristic-based decision making with Featherless AI priority and risk_appetite.
        Priority guides but never fully blocks investment when markets exist.
        """
        import random
        
        cash = observation.get("cash", 100)
        equity = observation.get("equity", 50)
        leverage = observation.get("leverage", 1.0)
        liquidity_ratio = observation.get("liquidity_ratio", 0.5)
        market_exposure = observation.get("market_exposure", 0.0)
        risk_appetite = observation.get("risk_appetite", 0.5)
        has_markets = observation.get("has_markets", True)
        local_stress = observation.get("local_stress", 0.0)
        best_market_return = observation.get("best_market_return", 0.0)
        best_market_position = observation.get("best_market_position", 0.0)
        total_invested = observation.get("total_invested", 0.0)
        
        # Priority invest modifier from Featherless AI
        priority_invest_modifier = 1.0
        if priority_value == "PROFIT":
            priority_invest_modifier = 1.3
        elif priority_value == "LIQUIDITY":
            priority_invest_modifier = 0.4
        elif priority_value == "STABILITY":
            priority_invest_modifier = 0.25
        
        # === PROFIT-TAKING: Sell investments when they're profitable ===
        if total_invested > 5 and best_market_return > 0.03:
            # Heuristic mode uses a lower threshold (3%) for profit-taking
            profit_take_prob = min(0.75, 0.15 + best_market_return * 2.5)
            
            # Priority influences profit-taking
            if priority_value == "PROFIT":
                # PROFIT priority: take profits aggressively when return is good
                profit_take_prob += 0.15
            elif priority_value == "LIQUIDITY":
                # LIQUIDITY: always want cash, take profits eagerly
                profit_take_prob += 0.25
            
            if risk_appetite < 0.4:
                profit_take_prob += 0.10
            
            if local_stress > 0.2:
                profit_take_prob += 0.20
            
            if liquidity_ratio < 0.25:
                profit_take_prob += 0.20
            
            profit_take_prob = max(0.10, min(0.85, profit_take_prob))
            
            if random.random() < profit_take_prob:
                return BankAction.DIVEST_MARKET

        # === Genuine emergency ===
        if cash < 10 or equity < 5:
            if market_exposure > 0.03:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        
        # === Severe stress ===
        if local_stress > 0.5 and liquidity_ratio < 0.2:
            if market_exposure > 0.1:
                return BankAction.DIVEST_MARKET
            return BankAction.DECREASE_LENDING
        
        # === Capital deployment — the core logic ===
        if cash > 15:
            if has_markets and market_exposure < 0.55:
                # Base probability from risk appetite
                invest_prob = 0.25 + (risk_appetite * 0.55)
                
                # Apply Featherless AI priority
                invest_prob *= priority_invest_modifier
                
                # Lots of idle cash → invest more aggressively
                if cash > 60:
                    invest_prob = min(0.95, invest_prob + 0.2)
                elif cash > 35:
                    invest_prob = min(0.90, invest_prob + 0.1)
                
                # Stress adjustment
                if local_stress > 0.3:
                    invest_prob *= 0.5
                
                invest_prob = max(0.05, min(0.95, invest_prob))
                
                if random.random() < invest_prob:
                    return BankAction.INVEST_MARKET
            
            # Not investing → lend to other banks
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


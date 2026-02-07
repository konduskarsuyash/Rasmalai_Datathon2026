"""
Game-Theoretic Decision Engine for Financial Network Simulation
Implements Nash Equilibrium computation for strategic bank interactions
"""
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np
from dataclasses import dataclass


class GameAction(Enum):
    """Strategic actions in the 2x2 lending game"""
    LEND = "LEND"
    HOARD = "HOARD"


class MarketState(Enum):
    """Market conditions affecting payoffs"""
    STABLE = "STABLE"
    DISTRESSED = "DISTRESSED"


@dataclass
class PayoffMatrix:
    """
    Payoff structure for 2x2 game between two banks
    Rows: My actions, Columns: Other's actions
    """
    my_lend_other_lend: float  # Both lend
    my_lend_other_hoard: float  # I lend, other hoards
    my_hoard_other_lend: float  # I hoard, other lends
    my_hoard_other_hoard: float  # Both hoard
    
    def get_payoff(self, my_action: GameAction, other_action: GameAction) -> float:
        """Get payoff for action pair"""
        if my_action == GameAction.LEND and other_action == GameAction.LEND:
            return self.my_lend_other_lend
        elif my_action == GameAction.LEND and other_action == GameAction.HOARD:
            return self.my_lend_other_hoard
        elif my_action == GameAction.HOARD and other_action == GameAction.LEND:
            return self.my_hoard_other_lend
        else:  # Both hoard
            return self.my_hoard_other_hoard


class NashEquilibriumSolver:
    """
    Solves for Nash Equilibrium in 2x2 strategic games
    Uses best-response dynamics and mixed strategy computation
    """
    
    def __init__(self):
        self.history = []
    
    def compute_best_response(self, 
                             my_payoffs: PayoffMatrix,
                             other_action_prob: float) -> Tuple[GameAction, float]:
        """
        Compute best response to opponent's mixed strategy
        
        Args:
            my_payoffs: My payoff matrix
            other_action_prob: Probability opponent plays LEND
        
        Returns:
            (best_action, expected_payoff)
        """
        # Expected payoff if I LEND
        ev_lend = (other_action_prob * my_payoffs.my_lend_other_lend + 
                   (1 - other_action_prob) * my_payoffs.my_lend_other_hoard)
        
        # Expected payoff if I HOARD
        ev_hoard = (other_action_prob * my_payoffs.my_hoard_other_lend + 
                    (1 - other_action_prob) * my_payoffs.my_hoard_other_hoard)
        
        if ev_lend > ev_hoard:
            return GameAction.LEND, ev_lend
        else:
            return GameAction.HOARD, ev_hoard
    
    def find_pure_nash_equilibrium(self, 
                                   p1_payoffs: PayoffMatrix,
                                   p2_payoffs: PayoffMatrix) -> List[Tuple[GameAction, GameAction]]:
        """
        Find all pure strategy Nash equilibria
        
        Returns:
            List of (player1_action, player2_action) Nash equilibria
        """
        nash_equilibria = []
        
        actions = [GameAction.LEND, GameAction.HOARD]
        
        for a1 in actions:
            for a2 in actions:
                # Check if (a1, a2) is a Nash equilibrium
                p1_current = p1_payoffs.get_payoff(a1, a2)
                p2_current = p2_payoffs.get_payoff(a2, a1)
                
                # Check if P1 can improve by deviating
                p1_can_improve = False
                for a1_alt in actions:
                    if a1_alt != a1:
                        if p1_payoffs.get_payoff(a1_alt, a2) > p1_current:
                            p1_can_improve = True
                            break
                
                # Check if P2 can improve by deviating
                p2_can_improve = False
                for a2_alt in actions:
                    if a2_alt != a2:
                        if p2_payoffs.get_payoff(a2_alt, a1) > p2_current:
                            p2_can_improve = True
                            break
                
                # Nash equilibrium if neither can improve
                if not p1_can_improve and not p2_can_improve:
                    nash_equilibria.append((a1, a2))
        
        return nash_equilibria
    
    def compute_mixed_strategy_equilibrium(self,
                                          p1_payoffs: PayoffMatrix,
                                          p2_payoffs: PayoffMatrix) -> Tuple[float, float]:
        """
        Compute mixed strategy Nash equilibrium probabilities
        
        Returns:
            (p1_lend_prob, p2_lend_prob)
        """
        # For 2x2 game, mixed strategy equilibrium exists when opponent is indifferent
        
        # P2 indifferent means: EV(P1 lends) = EV(P1 hoards) for P2
        # p1 * payoff(lend, lend) + (1-p1) * payoff(hoard, lend) = 
        # p1 * payoff(lend, hoard) + (1-p1) * payoff(hoard, hoard)
        
        try:
            # P1's mixing probability makes P2 indifferent
            numerator = (p2_payoffs.my_hoard_other_hoard - p2_payoffs.my_hoard_other_lend)
            denominator = (p2_payoffs.my_lend_other_lend - p2_payoffs.my_lend_other_hoard - 
                          p2_payoffs.my_hoard_other_lend + p2_payoffs.my_hoard_other_hoard)
            
            if abs(denominator) < 1e-6:
                p1_lend_prob = 0.5
            else:
                p1_lend_prob = numerator / denominator
                p1_lend_prob = max(0.0, min(1.0, p1_lend_prob))  # Clamp to [0, 1]
            
            # P2's mixing probability makes P1 indifferent
            numerator = (p1_payoffs.my_hoard_other_hoard - p1_payoffs.my_hoard_other_lend)
            denominator = (p1_payoffs.my_lend_other_lend - p1_payoffs.my_lend_other_hoard - 
                          p1_payoffs.my_hoard_other_lend + p1_payoffs.my_hoard_other_hoard)
            
            if abs(denominator) < 1e-6:
                p2_lend_prob = 0.5
            else:
                p2_lend_prob = numerator / denominator
                p2_lend_prob = max(0.0, min(1.0, p2_lend_prob))
            
            return p1_lend_prob, p2_lend_prob
        
        except (ZeroDivisionError, ValueError):
            # Fallback to uniform mixed strategy
            return 0.5, 0.5


class FinancialGameTheory:
    """
    Main game theory engine for financial network strategic interactions
    Models lending decisions as strategic games under uncertainty
    """
    
    def __init__(self):
        self.solver = NashEquilibriumSolver()
        self.use_mixed_strategies = True
    
    def construct_payoff_matrix(self,
                                bank_observation: Dict,
                                market_state: MarketState,
                                network_stress: float) -> PayoffMatrix:
        """
        Construct payoff matrix based on bank's current state and market conditions
        
        Payoffs represent expected utility from actions:
        - Lending generates return but exposes to counterparty risk
        - Hoarding preserves safety but foregoes profit
        
        Args:
            bank_observation: Bank's local state (equity, cash, leverage, etc.)
            market_state: Current market conditions
            network_stress: Level of systemic stress (0-1)
        
        Returns:
            PayoffMatrix for this bank's strategic game
        """
        cash = bank_observation.get("cash", 100)
        equity = bank_observation.get("equity", 50)
        leverage = bank_observation.get("leverage", 1.0)
        liquidity_ratio = bank_observation.get("liquidity_ratio", 0.5)
        local_stress = bank_observation.get("local_stress", 0.0)
        
        # Base payoff parameters
        lending_return = 0.05  # 5% return on lending
        default_risk = 0.02 + local_stress * 0.10  # Risk increases with stress
        hoarding_cost = 0.01  # Opportunity cost of not lending
        
        # Coordination benefit (both lend = liquid market)
        coordination_bonus = 0.02
        
        # Distressed market adjustments
        if market_state == MarketState.DISTRESSED:
            default_risk *= 2.5  # Much higher risk
            lending_return *= 0.7  # Lower returns
            hoarding_cost *= 0.5  # Lower opportunity cost (cash is valuable)
        
        # Payoff calculations normalized to bank's equity scale
        equity_scale = max(equity, 1.0)
        
        # Both lend: High return + coordination, but exposed to risk
        both_lend = (lending_return + coordination_bonus - default_risk) * equity_scale
        
        # I lend, other hoards: I'm exposed but no coordination benefit
        # Worse because market is less liquid
        lend_other_hoard = (lending_return * 0.7 - default_risk * 1.3) * equity_scale
        
        # I hoard, other lends: I'm safe, small opportunity cost
        # Benefit from others providing liquidity
        hoard_other_lend = (-hoarding_cost * 0.5) * equity_scale
        
        # Both hoard: Safe but high opportunity cost + market dries up
        both_hoard = (-hoarding_cost * 1.5) * equity_scale
        
        # Adjust based on bank's financial health
        if liquidity_ratio < 0.2:  # Low liquidity - need to preserve cash
            both_lend *= 0.5
            lend_other_hoard *= 0.3
            hoard_other_lend *= 1.2
            both_hoard *= 1.1
        
        if leverage > 3.0:  # High leverage - risky
            both_lend *= 0.6
            lend_other_hoard *= 0.4
        
        return PayoffMatrix(
            my_lend_other_lend=both_lend,
            my_lend_other_hoard=lend_other_hoard,
            my_hoard_other_lend=hoard_other_lend,
            my_hoard_other_hoard=both_hoard
        )
    
    def estimate_market_state(self, 
                              bank_observation: Dict,
                              network_default_rate: float = 0.0) -> MarketState:
        """
        Estimate current market state based on observable signals
        
        Args:
            bank_observation: Bank's local observations
            network_default_rate: Fraction of banks defaulted
        
        Returns:
            STABLE or DISTRESSED
        """
        local_stress = bank_observation.get("local_stress", 0.0)
        
        # Market is distressed if:
        # - High local stress (neighbors defaulting)
        # - High network default rate
        # - Low system liquidity
        
        distress_score = (
            0.5 * local_stress +
            0.3 * network_default_rate +
            0.2 * (1.0 - bank_observation.get("liquidity_ratio", 0.5))
        )
        
        if distress_score > 0.4:
            return MarketState.DISTRESSED
        else:
            return MarketState.STABLE
    
    def estimate_others_strategy(self,
                                bank_observation: Dict,
                                market_state: MarketState) -> float:
        """
        Estimate probability that other banks will lend (vs hoard)
        Based on observable market conditions and strategic reasoning
        
        Returns:
            Probability in [0, 1] that others will choose LEND
        """
        local_stress = bank_observation.get("local_stress", 0.0)
        
        if market_state == MarketState.DISTRESSED:
            # In distress, most banks hoard
            base_lend_prob = 0.3
        else:
            # In stable markets, most banks lend
            base_lend_prob = 0.7
        
        # Adjust based on local stress
        lend_prob = base_lend_prob * (1.0 - 0.5 * local_stress)
        
        return max(0.1, min(0.9, lend_prob))
    
    def make_strategic_decision(self,
                               bank_observation: Dict,
                               market_state: Optional[MarketState] = None,
                               network_default_rate: float = 0.0) -> Tuple[GameAction, float, str]:
        """
        Make strategic decision using Nash equilibrium reasoning
        
        Args:
            bank_observation: Bank's state and local information
            market_state: Current market conditions (estimated if None)
            network_default_rate: System-wide default rate
        
        Returns:
            (action, expected_payoff, reasoning)
        """
        # Estimate market state if not provided
        if market_state is None:
            market_state = self.estimate_market_state(bank_observation, network_default_rate)
        
        # Construct my payoff matrix
        my_payoffs = self.construct_payoff_matrix(
            bank_observation, 
            market_state,
            network_default_rate
        )
        
        # Estimate what others will do
        others_lend_prob = self.estimate_others_strategy(bank_observation, market_state)
        
        # Compute best response
        best_action, expected_payoff = self.solver.compute_best_response(
            my_payoffs,
            others_lend_prob
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            best_action,
            market_state,
            bank_observation,
            others_lend_prob
        )
        
        return best_action, expected_payoff, reasoning
    
    def _generate_reasoning(self,
                           action: GameAction,
                           market_state: MarketState,
                           observation: Dict,
                           others_lend_prob: float) -> str:
        """Generate human-readable reasoning for the decision"""
        
        equity = observation.get("equity", 50)
        cash = observation.get("cash", 100)
        local_stress = observation.get("local_stress", 0.0)
        
        market_desc = "distressed" if market_state == MarketState.DISTRESSED else "stable"
        others_strategy = "lending" if others_lend_prob > 0.5 else "hoarding"
        
        if action == GameAction.LEND:
            return (f"Nash-BR: LEND in {market_desc} market "
                   f"(others {int(others_lend_prob*100)}% {others_strategy}, "
                   f"equity=${equity:.0f}, stress={local_stress:.2f})")
        else:
            return (f"Nash-BR: HOARD in {market_desc} market "
                   f"(others {int(others_lend_prob*100)}% {others_strategy}, "
                   f"cash=${cash:.0f}, stress={local_stress:.2f})")


# Global game theory engine instance
_game_engine = FinancialGameTheory()


def get_nash_equilibrium_action(bank_observation: Dict,
                                network_default_rate: float = 0.0) -> Tuple[GameAction, str]:
    """
    Main entry point for game-theoretic decision making
    
    Args:
        bank_observation: Bank's current state
        network_default_rate: System-wide default rate
    
    Returns:
        (strategic_action, reasoning)
    """
    action, payoff, reasoning = _game_engine.make_strategic_decision(
        bank_observation,
        network_default_rate=network_default_rate
    )
    
    return action, reasoning


def compute_nash_equilibrium_for_pair(bank1_obs: Dict,
                                     bank2_obs: Dict,
                                     market_state: MarketState) -> Tuple[GameAction, GameAction]:
    """
    Compute Nash equilibrium for a specific pair of banks
    
    Returns:
        (bank1_action, bank2_action) in equilibrium
    """
    engine = FinancialGameTheory()
    
    # Construct payoff matrices for both banks
    p1_payoffs = engine.construct_payoff_matrix(bank1_obs, market_state, 0.0)
    p2_payoffs = engine.construct_payoff_matrix(bank2_obs, market_state, 0.0)
    
    # Find pure Nash equilibria
    pure_equilibria = engine.solver.find_pure_nash_equilibrium(p1_payoffs, p2_payoffs)
    
    if pure_equilibria:
        # Return first pure Nash equilibrium
        return pure_equilibria[0]
    else:
        # Compute mixed strategy equilibrium
        p1_prob, p2_prob = engine.solver.compute_mixed_strategy_equilibrium(p1_payoffs, p2_payoffs)
        
        # Sample from mixed strategies
        import random
        a1 = GameAction.LEND if random.random() < p1_prob else GameAction.HOARD
        a2 = GameAction.LEND if random.random() < p2_prob else GameAction.HOARD
        
        return a1, a2

"""
Reward Computation for Policy Learning.
Each bank computes a LOCAL scalar reward after each action.
This is internal learning signal - NOT exposed to Featherless.
"""
from typing import Dict
from dataclasses import dataclass


@dataclass
class RewardWeights:
    """Weights for reward components - tunable."""
    profit_weight: float = 1.0
    liquidity_penalty_weight: float = 2.0
    leverage_penalty_weight: float = 1.5
    exposure_penalty_weight: float = 2.5
    
    # Thresholds
    min_liquidity_ratio: float = 0.2
    max_leverage: float = 4.0


# Default weights
DEFAULT_WEIGHTS = RewardWeights()


def compute_reward(
    bank_state_before: Dict,
    bank_state_after: Dict,
    action_taken: str,
    neighbor_defaults: int = 0,
    weights: RewardWeights = DEFAULT_WEIGHTS
) -> Dict:
    """
    Compute LOCAL reward for a single bank after an action.
    
    This is bounded rational learning signal, not optimal control.
    Rewards are scaled to be in a reasonable range (-5 to +5 typical).
    
    Args:
        bank_state_before: Balance sheet snapshot before action
        bank_state_after: Balance sheet snapshot after action
        action_taken: The action string
        neighbor_defaults: Number of defaults in neighborhood
        weights: Reward component weights
        
    Returns:
        Dict with total reward and component breakdown
    """
    # ========================================
    # PROFIT COMPONENT (positive)
    # ========================================
    
    # Equity change (did we grow?) - scale down for reasonable values
    equity_before = bank_state_before.get("equity", 50)
    equity_after = bank_state_after.get("equity", 50)
    equity_delta = (equity_after - equity_before) / 10  # Scale down
    
    # Cash stability bonus (maintaining cash is good)
    cash_before = bank_state_before.get("cash", 100)
    cash_after = bank_state_after.get("cash", 100)
    
    # Bonus for maintaining/increasing cash, small penalty for big drops
    if cash_after >= cash_before:
        cash_bonus = 0.5  # Small bonus for stability
    else:
        cash_drop_ratio = (cash_before - cash_after) / cash_before
        cash_bonus = -cash_drop_ratio * 2  # Penalty proportional to % drop
    
    # Base action reward (some actions are inherently slightly positive)
    action_base = {
        "HOARD_CASH": 0.2,
        "INVEST_MARKET": 0.3,
        "DIVEST_MARKET": 0.1,
        "INCREASE_LENDING": 0.3,
        "DECREASE_LENDING": 0.1
    }.get(action_taken, 0.0)
    
    profit = equity_delta + cash_bonus + action_base
    
    # ========================================
    # RISK PENALTIES (SMALL, not crushing)
    # ========================================
    
    # Liquidity penalty: small penalty if below threshold
    liquidity_ratio = bank_state_after.get("liquidity_ratio", 0.5)
    if liquidity_ratio < weights.min_liquidity_ratio:
        shortfall = weights.min_liquidity_ratio - liquidity_ratio
        liquidity_penalty = shortfall * weights.liquidity_penalty_weight * 5  # Reduced from 100
    else:
        liquidity_penalty = 0.0
    
    # Leverage penalty: small penalty if above threshold
    leverage = bank_state_after.get("leverage", 2.0)
    if leverage > weights.max_leverage:
        excess = leverage - weights.max_leverage
        leverage_penalty = excess * weights.leverage_penalty_weight * 0.5  # Reduced from 10
    else:
        leverage_penalty = 0.0
    
    # Default exposure penalty
    exposure_penalty = neighbor_defaults * weights.exposure_penalty_weight * 0.5  # Reduced
    
    # ========================================
    # TOTAL REWARD
    # ========================================
    total_reward = (
        profit * weights.profit_weight
        - liquidity_penalty
        - leverage_penalty
        - exposure_penalty
    )
    
    # Clamp to reasonable range
    total_reward = max(-10, min(10, total_reward))
    
    return {
        "total": round(total_reward, 2),
        "profit": round(profit, 2),
        "liquidity_penalty": round(liquidity_penalty, 2),
        "leverage_penalty": round(leverage_penalty, 2),
        "exposure_penalty": round(exposure_penalty, 2),
        "action": action_taken
    }


def reward_summary(reward_dict: Dict) -> str:
    """Generate human-readable reward summary for logging."""
    total = reward_dict["total"]
    sign = "+" if total >= 0 else ""
    
    parts = []
    if reward_dict["profit"] != 0:
        parts.append(f"profit={reward_dict['profit']:+.1f}")
    if reward_dict["liquidity_penalty"] > 0:
        parts.append(f"liq_pen=-{reward_dict['liquidity_penalty']:.1f}")
    if reward_dict["leverage_penalty"] > 0:
        parts.append(f"lev_pen=-{reward_dict['leverage_penalty']:.1f}")
    if reward_dict["exposure_penalty"] > 0:
        parts.append(f"exp_pen=-{reward_dict['exposure_penalty']:.1f}")
    
    detail = ", ".join(parts) if parts else "neutral"
    return f"Reward: {sign}{total:.1f} ({detail})"

"""
Policy Learning Module for Financial Network MVP.
Implements lightweight, online policy adaptation.

This is:
- Bandit-style action preference updates
- Slow target adaptation
- Local, per-bank learning

This is NOT:
- Deep RL / backprop
- Shared learning
- Optimal control
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
import math


# Action names for preference tracking
ACTIONS = [
    "INCREASE_LENDING",
    "DECREASE_LENDING",
    "INVEST_MARKET",
    "DIVEST_MARKET",
    "HOARD_CASH"
]


@dataclass
class LearningConfig:
    """Configuration for policy learning."""
    # Action preference learning rate
    alpha: float = 0.1
    
    # Target adaptation rate (SLOW)
    target_alpha: float = 0.02
    
    # Memory size
    memory_size: int = 10
    
    # Temperature for softmax action selection
    temperature: float = 1.0
    
    # Target adaptation thresholds
    liquidity_stress_threshold: int = 3  # N consecutive stress events
    profit_streak_threshold: int = 5     # N consecutive profitable actions


@dataclass
class LearningState:
    """
    Learning state for a single bank.
    Each bank has its own, independent learning state.
    """
    # Action preference scores (higher = more preferred)
    action_scores: Dict[str, float] = field(default_factory=lambda: {
        "INCREASE_LENDING": 0.0,
        "DECREASE_LENDING": 0.0,
        "INVEST_MARKET": 0.0,
        "DIVEST_MARKET": 0.0,
        "HOARD_CASH": 0.0
    })
    
    # Strategy memory (last N outcomes)
    action_history: deque = field(default_factory=lambda: deque(maxlen=10))
    reward_history: deque = field(default_factory=lambda: deque(maxlen=10))
    priority_history: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Streak tracking for target adaptation
    liquidity_stress_count: int = 0
    profit_streak: int = 0
    
    # Target deltas (cumulative adjustments)
    leverage_target_delta: float = 0.0
    liquidity_target_delta: float = 0.0
    exposure_target_delta: float = 0.0
    
    def record_step(self, action: str, reward: float, priority: Optional[str] = None):
        """Record a step in memory."""
        self.action_history.append(action)
        self.reward_history.append(reward)
        self.priority_history.append(priority)


def update_policy(
    state: LearningState,
    action_taken: str,
    reward: float,
    config: LearningConfig = LearningConfig()
) -> Dict:
    """
    Update action preferences based on observed reward.
    Uses exponentially weighted update (bandit-style).
    
    Args:
        state: Bank's learning state
        action_taken: The action that was executed
        reward: Observed reward for this action
        config: Learning configuration
        
    Returns:
        Dict with update summary
    """
    old_score = state.action_scores.get(action_taken, 0.0)
    
    # Exponential moving average update
    # Good rewards → increase score, bad rewards → decrease score
    new_score = old_score + config.alpha * (reward - old_score)
    state.action_scores[action_taken] = new_score
    
    # Track in memory
    state.record_step(action_taken, reward, None)
    
    # Compute direction
    delta = new_score - old_score
    direction = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
    
    return {
        "action": action_taken,
        "old_score": round(old_score, 2),
        "new_score": round(new_score, 2),
        "delta": round(delta, 2),
        "direction": direction,
        "summary": f"{action_taken} preference {direction}"
    }


def adapt_targets(
    state: LearningState,
    reward: float,
    liquidity_ratio: float,
    config: LearningConfig = LearningConfig()
) -> Dict:
    """
    Slowly adapt target ratios based on outcomes.
    Banks learn to adjust their risk tolerance.
    
    Rules:
    - Targets change SLOWLY (small increments)
    - No oscillations (one-way adjustments per streak)
    
    Args:
        state: Bank's learning state
        reward: Current step reward
        liquidity_ratio: Current liquidity ratio
        config: Learning configuration
        
    Returns:
        Dict with target adjustment summary
    """
    adjustments = []
    
    # Track liquidity stress
    if liquidity_ratio < 0.2:
        state.liquidity_stress_count += 1
    else:
        state.liquidity_stress_count = max(0, state.liquidity_stress_count - 1)
    
    # Track profit streak
    if reward > 0:
        state.profit_streak += 1
    else:
        state.profit_streak = 0
    
    # Adapt liquidity target after repeated stress
    if state.liquidity_stress_count >= config.liquidity_stress_threshold:
        adjustment = config.target_alpha * 0.05  # +5% per trigger
        state.liquidity_target_delta += adjustment
        state.liquidity_target_delta = min(0.2, state.liquidity_target_delta)  # Cap at +20%
        state.liquidity_stress_count = 0  # Reset counter
        adjustments.append(f"Liquidity target +{adjustment*100:.0f}%")
    
    # Adapt leverage target after profit streak
    if state.profit_streak >= config.profit_streak_threshold:
        adjustment = config.target_alpha * 0.5  # +0.5x leverage
        state.leverage_target_delta += adjustment
        state.leverage_target_delta = min(1.0, state.leverage_target_delta)  # Cap at +1.0x
        state.profit_streak = 0  # Reset counter
        adjustments.append(f"Leverage target +{adjustment:.1f}x")
    
    return {
        "adjustments": adjustments,
        "leverage_delta": round(state.leverage_target_delta, 2),
        "liquidity_delta": round(state.liquidity_target_delta, 2),
        "summary": "; ".join(adjustments) if adjustments else "No target change"
    }


def get_action_preferences(state: LearningState) -> Dict[str, float]:
    """Get current action preferences as probabilities (softmax)."""
    scores = state.action_scores
    
    # Softmax with temperature
    max_score = max(scores.values())
    exp_scores = {k: math.exp((v - max_score) / 1.0) for k, v in scores.items()}
    total = sum(exp_scores.values())
    
    probs = {k: v / total for k, v in exp_scores.items()}
    return probs


def learning_summary(
    policy_update: Dict,
    target_update: Dict,
    reward: float
) -> str:
    """Generate human-readable learning summary for logs."""
    parts = [
        f"Reward: {reward:+.1f}",
        f"Policy: {policy_update['summary']}",
    ]
    
    if target_update["adjustments"]:
        parts.append(f"Targets: {target_update['summary']}")
    
    return " | ".join(parts)

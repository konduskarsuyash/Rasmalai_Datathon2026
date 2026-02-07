"""
Featherless.ai Decision Engine v2.
Featherless acts as a META-STRATEGY SELECTOR.
It ONLY outputs: PROFIT, LIQUIDITY, or STABILITY.
It NEVER sets numeric values or executes transactions.
"""
import random
from typing import Dict, Optional
from enum import Enum
from openai import OpenAI
from config.settings import FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, FEATHERLESS_MODEL


class StrategicPriority(Enum):
    """The ONLY outputs Featherless can return."""
    PROFIT = "PROFIT"       # Allow aggressive ML actions
    LIQUIDITY = "LIQUIDITY"  # Override to cash-hoarding actions
    STABILITY = "STABILITY"  # Override to deleveraging actions


def create_featherless_client() -> OpenAI:
    """Create OpenAI-compatible client for Featherless.ai."""
    if not FEATHERLESS_API_KEY:
        raise ValueError("FEATHERLESS_API_KEY not set")
    
    return OpenAI(
        base_url=FEATHERLESS_BASE_URL,
        api_key=FEATHERLESS_API_KEY
    )


def get_strategic_priority(
    observation: Dict,
    client: Optional[OpenAI] = None,
    use_llm: bool = True
) -> StrategicPriority:
    """
    Get strategic priority.
    
    For efficiency, only calls Featherless LLM for high-value decisions.
    Otherwise uses fast rule-based logic.
    
    Args:
        observation: Bank's local state observation
        client: Featherless client (optional)
        use_llm: Whether to attempt LLM call
        
    Returns:
        StrategicPriority: PROFIT, LIQUIDITY, or STABILITY
    """
    # Only call LLM for subset of banks to reduce API calls and add variance
    bank_id = observation.get("bank_id", 0)
    local_stress = observation.get("local_stress", 0.0)
    
    # Call LLM only for: stressed banks OR every 3rd bank
    should_use_llm = use_llm and client and (local_stress > 0.2 or bank_id % 3 == 0)
    
    if should_use_llm:
        try:
            prompt = _build_priority_prompt(observation)
            response = client.chat.completions.create(
                model=FEATHERLESS_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a financial strategy advisor for a bank.
Based on the bank's financial status, output EXACTLY ONE word: PROFIT, LIQUIDITY, or STABILITY.

Decision guide:
- PROFIT: Bank is healthy, can pursue growth
- LIQUIDITY: Bank needs more cash reserves
- STABILITY: Bank should reduce risk/leverage

Output ONLY the single word, nothing else."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.7  # Higher temp for more variance
            )
            
            result = response.choices[0].message.content.strip().upper()
            return _parse_priority(result)
            
        except Exception:
            pass  # Fall through to rule-based
    
    # Rule-based priority (fast, bank-specific)
    return _rule_based_priority(observation)


def _build_priority_prompt(observation: Dict) -> str:
    """Build the prompt for Featherless priority selection."""
    cash = observation.get('cash', 100)
    equity = observation.get('equity', 50)
    leverage = observation.get('leverage', 2.0)
    liquidity_ratio = observation.get('liquidity_ratio', 0.3)
    stress = observation.get('local_stress', 0.0)
    
    # Characterize the bank
    health = "healthy" if equity > 80 else "moderate" if equity > 40 else "stressed"
    cash_level = "high" if cash > 100 else "moderate" if cash > 50 else "low"
    
    return f"""Bank Status:
- Health: {health} (equity ${equity:.0f})
- Cash level: {cash_level} (${cash:.0f})
- Leverage: {leverage:.1f}x
- Liquidity: {liquidity_ratio:.0%}
- Stress: {stress:.0%}

What should this bank prioritize? Answer with ONE word: PROFIT, LIQUIDITY, or STABILITY"""


def _parse_priority(result: str) -> StrategicPriority:
    """Parse LLM output to StrategicPriority enum."""
    result = result.strip().upper()
    
    if "PROFIT" in result:
        return StrategicPriority.PROFIT
    elif "LIQUIDITY" in result:
        return StrategicPriority.LIQUIDITY
    elif "STABILITY" in result:
        return StrategicPriority.STABILITY
    else:
        return StrategicPriority.STABILITY


def _rule_based_priority(observation: Dict) -> StrategicPriority:
    """
    Fast rule-based priority selection.
    Provides diverse priorities based on bank-specific state.
    """
    bank_id = observation.get("bank_id", 0)
    cash = observation.get("cash", 100)
    equity = observation.get("equity", 50)
    leverage = observation.get("leverage", 2.0)
    liquidity_ratio = observation.get("liquidity_ratio", 0.5)
    local_stress = observation.get("local_stress", 0.0)
    
    # HIGH STRESS → STABILITY (all banks)
    if local_stress > 0.4:
        return StrategicPriority.STABILITY
    
    # CRITICAL STATE → LIQUIDITY (urgent cash need)
    if equity < 20 or cash < 20:
        return StrategicPriority.LIQUIDITY
    
    # OVER-LEVERAGED → STABILITY
    if leverage > 4.0:
        return StrategicPriority.STABILITY
    
    # LOW LIQUIDITY → LIQUIDITY
    if liquidity_ratio < 0.15:
        return StrategicPriority.LIQUIDITY
    
    # HEALTHY BANKS: Priority based on bank type/ID for diversity
    # Large banks (type 0): Tend toward STABILITY
    # Medium banks (type 1): Balanced, can be PROFIT
    # Small banks (type 2): Need LIQUIDITY
    # Aggressive banks (type 3): Want PROFIT
    
    bank_type = bank_id % 4
    
    if bank_type == 0:  # Large bank
        if leverage < 2.0 and cash > 120:
            return StrategicPriority.PROFIT
        return StrategicPriority.STABILITY
    
    elif bank_type == 1:  # Medium bank
        if equity > 60 and liquidity_ratio > 0.3:
            return StrategicPriority.PROFIT
        return StrategicPriority.LIQUIDITY
    
    elif bank_type == 2:  # Small bank
        if cash > 50:
            return StrategicPriority.STABILITY
        return StrategicPriority.LIQUIDITY
    
    else:  # Aggressive bank
        if equity > 50:
            return StrategicPriority.PROFIT
        if leverage > 3.0:
            return StrategicPriority.STABILITY
        return StrategicPriority.PROFIT


# ============================================================
# V1 COMPATIBILITY (Legacy support for existing code)
# ============================================================

def featherless_decision(observation: Dict, client: Optional[OpenAI] = None) -> Dict:
    """Legacy v1 API - returns credit/margin decisions."""
    priority = get_strategic_priority(observation, client)
    
    if priority == StrategicPriority.PROFIT:
        return {"credit": "HIGH", "margin": "LOOSE"}
    elif priority == StrategicPriority.LIQUIDITY:
        return {"credit": "LOW", "margin": "TIGHT"}
    else:
        return {"credit": "MEDIUM", "margin": "NORMAL"}

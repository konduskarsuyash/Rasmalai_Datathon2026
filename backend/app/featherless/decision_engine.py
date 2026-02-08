"""
Featherless.ai Decision Engine — MANDATORY for every bank at every timestep.
Calls the Featherless LLM API to get strategic priority (PROFIT, LIQUIDITY, STABILITY).
Falls back to rule-based only if the API call fails.
"""
from typing import Dict, Optional
from enum import Enum
import json
import time

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app.config.settings import FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, FEATHERLESS_MODEL


class StrategicPriority(Enum):
    PROFIT = "PROFIT"
    LIQUIDITY = "LIQUIDITY"
    STABILITY = "STABILITY"


# Simple in-memory cache to avoid hammering the API for identical states
_priority_cache: Dict[str, tuple] = {}  # key -> (priority, timestamp)
_CACHE_TTL = 5.0  # seconds


def create_featherless_client():
    if not FEATHERLESS_API_KEY or OpenAI is None:
        print("[FEATHERLESS] No API key or OpenAI package missing — LLM calls disabled")
        return None
    client = OpenAI(base_url=FEATHERLESS_BASE_URL, api_key=FEATHERLESS_API_KEY)
    print(f"[FEATHERLESS] Client created, model={FEATHERLESS_MODEL}")
    return client


def _build_prompt(observation: Dict) -> str:
    """Build a concise prompt for the LLM with the bank's financial state."""
    return f"""You are a financial strategist for a bank in an interbank network simulation.
Given this bank's current state, decide its strategic priority for the next time step.

Bank State:
- Bank ID: {observation.get('bank_id', 0)}
- Cash: ${observation.get('cash', 100):.1f}M
- Equity: ${observation.get('equity', 50):.1f}M
- Leverage: {observation.get('leverage', 2.0):.2f}x
- Liquidity Ratio: {observation.get('liquidity_ratio', 0.5):.2f}
- Market Exposure: {observation.get('market_exposure', 0.0):.2f}
- Investments: ${observation.get('investments', 0):.1f}M
- Loans Given: ${observation.get('loans_given', 0):.1f}M
- Borrowed: ${observation.get('borrowed', 50):.1f}M
- Risk Appetite: {observation.get('risk_appetite', 0.5):.2f} (0=conservative, 1=aggressive)
- Neighbor Defaults: {observation.get('neighbor_defaults', 0)}
- Local Stress: {observation.get('local_stress', 0.0):.2f}
- Markets Available: {observation.get('has_markets', False)}

Choose exactly ONE strategic priority:
- PROFIT: Actively deploy capital — invest in markets and grow the portfolio. Best when the bank is financially healthy and should seek returns.
- LIQUIDITY: Preserve and build cash reserves. Best in moderate stress or when cash is low.
- STABILITY: De-risk the portfolio by reducing leverage and exposure. Best in crisis or near-default.

IMPORTANT: Banks need to invest in markets to generate returns. A bank with good health and available markets should generally choose PROFIT. Only choose STABILITY/LIQUIDITY under genuine financial stress.

Respond with ONLY one word: PROFIT, LIQUIDITY, or STABILITY."""


def _strip_think_tags(text: str) -> str:
    """Strip <THINK>...</THINK> chain-of-thought tags from model response."""
    import re
    # Remove everything between <THINK> and </THINK> (case-insensitive)
    cleaned = re.sub(r'<THINK>.*?</THINK>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # If there's an unclosed <THINK> (model ran out of tokens), remove from <THINK> to end
    cleaned = re.sub(r'<THINK>.*', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    return cleaned.strip()


def _call_featherless_llm(observation: Dict, client) -> Optional[StrategicPriority]:
    """Call the Featherless LLM API and parse the response."""
    try:
        prompt = _build_prompt(observation)
        
        response = client.chat.completions.create(
            model=FEATHERLESS_MODEL,
            messages=[
                {"role": "system", "content": "You are a financial strategist. Do NOT think or explain. Respond with ONLY one word: PROFIT, LIQUIDITY, or STABILITY. No other text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3,
        )
        
        raw_answer = response.choices[0].message.content.strip()
        
        # Strip <THINK>...</THINK> chain-of-thought tags (DeepSeek uses these)
        answer = _strip_think_tags(raw_answer).upper()
        
        # If stripping left nothing, also check the raw response
        if not answer:
            answer = raw_answer.upper()
        
        # Parse the response — check for keywords
        if "PROFIT" in answer:
            return StrategicPriority.PROFIT
        elif "LIQUIDITY" in answer:
            return StrategicPriority.LIQUIDITY
        elif "STABILITY" in answer:
            return StrategicPriority.STABILITY
        else:
            # Last resort: check raw response too (in case tags weren't properly closed)
            raw_upper = raw_answer.upper()
            if "PROFIT" in raw_upper:
                return StrategicPriority.PROFIT
            elif "LIQUIDITY" in raw_upper:
                return StrategicPriority.LIQUIDITY
            elif "STABILITY" in raw_upper:
                return StrategicPriority.STABILITY
            
            print(f"[FEATHERLESS] Unexpected LLM response: '{raw_answer[:80]}', falling back")
            return None
            
    except Exception as e:
        print(f"[FEATHERLESS] LLM call failed: {e}")
        return None


def _cache_key(observation: Dict) -> str:
    """Generate a cache key from observation — bucket numeric values to avoid cache misses."""
    return f"{observation.get('bank_id', 0)}-{int(observation.get('cash', 0) / 10)}-{int(observation.get('equity', 0) / 10)}-{int(observation.get('leverage', 0))}-{observation.get('neighbor_defaults', 0)}"


def _rule_based_fallback(observation: Dict) -> StrategicPriority:
    """
    Rule-based priority when LLM is unavailable.
    Biased toward PROFIT so banks actually invest and the economy moves.
    """
    cash = observation.get("cash", 100)
    equity = observation.get("equity", 50)
    leverage = observation.get("leverage", 2.0)
    liquidity_ratio = observation.get("liquidity_ratio", 0.5)
    local_stress = observation.get("local_stress", 0.0)
    risk_appetite = observation.get("risk_appetite", 0.5)

    # === GENUINE CRISIS: only switch away from PROFIT in real emergencies ===
    if equity < 10 or cash < 10:
        return StrategicPriority.LIQUIDITY
    if local_stress > 0.6:
        return StrategicPriority.STABILITY
    if leverage > 6.0:
        return StrategicPriority.STABILITY
    if liquidity_ratio < 0.08:
        return StrategicPriority.LIQUIDITY
    
    # === EVERYTHING ELSE: PROFIT — banks need to deploy capital ===
    return StrategicPriority.PROFIT


def get_strategic_priority(observation: Dict, client=None, use_llm: bool = True) -> StrategicPriority:
    """
    Get strategic priority for a bank — calls Featherless LLM API.
    Falls back to rule-based heuristics only if the API call fails.
    
    This function is called for EVERY bank at EVERY timestep (mandatory).
    """
    # Check cache first
    key = _cache_key(observation)
    now = time.time()
    if key in _priority_cache:
        cached_priority, cached_time = _priority_cache[key]
        if now - cached_time < _CACHE_TTL:
            return cached_priority
    
    # Try LLM call
    priority = None
    if client is not None and use_llm:
        priority = _call_featherless_llm(observation, client)
        if priority:
            print(f"[FEATHERLESS] Bank {observation.get('bank_id', '?')}: LLM → {priority.value}")
    
    # Fallback to rule-based if LLM failed
    if priority is None:
        priority = _rule_based_fallback(observation)
        print(f"[FEATHERLESS] Bank {observation.get('bank_id', '?')}: Fallback → {priority.value}")
    
    # Cache the result
    _priority_cache[key] = (priority, now)
    
    return priority

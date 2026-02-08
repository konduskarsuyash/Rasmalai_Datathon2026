"""
Market Nodes for Financial Network MVP v2.
"""
from dataclasses import dataclass, field
from typing import Dict, List
import random


@dataclass
class Market:
    market_id: str
    name: str
    initial_price: float = 100.0
    total_invested: float = 0.0
    price_history: List[float] = field(default_factory=list)
    flow_history: List[float] = field(default_factory=list)
    price_sensitivity: float = 0.002  # Increased from 0.001 for more volatility
    volatility: float = 0.03  # 3% random volatility per step

    def __post_init__(self):
        self.price = self.initial_price
        self.price_history = [self.price]

    def apply_flow(self, net_flow: float):
        """Apply supply/demand dynamics + random market fluctuations."""
        # Supply/demand impact: positive flow (investment) increases price, negative (divestment) decreases
        supply_demand_impact = net_flow * self.price_sensitivity
        
        # Random market volatility (-3% to +3%)
        random_shock = random.uniform(-self.volatility, self.volatility) * self.price
        
        # Momentum effect: if price has been rising, add small upward bias
        momentum = 0.0
        if len(self.price_history) >= 3:
            recent_change = self.price_history[-1] - self.price_history[-3]
            momentum = recent_change * 0.1  # 10% of recent trend
        
        # Total price change
        price_change = supply_demand_impact + random_shock + momentum
        
        # Update price (floor at 1.0, can go very high)
        self.price = max(1.0, self.price + price_change)
        self.total_invested += net_flow
        self.flow_history.append(net_flow)
        self.price_history.append(self.price)

    def get_return(self) -> float:
        return (self.price - self.initial_price) / self.initial_price

    def snapshot(self) -> Dict:
        return {
            "market_id": self.market_id,
            "name": self.name,
            "price": round(self.price, 2),
            "total_invested": round(self.total_invested, 2),
            "return": round(self.get_return() * 100, 2),
        }


class MarketSystem:
    def __init__(self):
        self.markets: Dict[str, Market] = {}
        self._pending_flows: Dict[str, float] = {}

    def add_market(self, market_id: str, name: str, initial_price: float = 100.0):
        self.markets[market_id] = Market(market_id, name, initial_price)
        self._pending_flows[market_id] = 0.0

    def get_market(self, market_id: str) -> Market:
        return self.markets.get(market_id)

    def record_flow(self, market_id: str, amount: float):
        if market_id in self._pending_flows:
            self._pending_flows[market_id] += amount

    def apply_all_flows(self):
        for market_id, flow in self._pending_flows.items():
            if market_id in self.markets and flow != 0:
                self.markets[market_id].apply_flow(flow)
            self._pending_flows[market_id] = 0.0

    def snapshot(self) -> Dict:
        return {mid: m.snapshot() for mid, m in self.markets.items()}


def create_default_markets() -> MarketSystem:
    system = MarketSystem()
    system.add_market("BANK_INDEX", "Bank Sector Index", 100.0)
    system.add_market("FIN_SERVICES", "Financial Services Index", 100.0)
    return system


def create_markets_from_config(market_configs: list) -> MarketSystem:
    """Create a MarketSystem from user-provided market configurations.
    
    Each config should have: {"market_id": str, "name": str, "initial_price": float}
    If no configs provided, returns an empty MarketSystem (no markets).
    """
    system = MarketSystem()
    for mc in market_configs:
        system.add_market(
            market_id=mc.get("market_id", mc.get("id", f"MARKET_{len(system.markets)}")),
            name=mc.get("name", f"Market {len(system.markets) + 1}"),
            initial_price=mc.get("initial_price", 100.0),
        )
    return system

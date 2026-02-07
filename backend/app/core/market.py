"""
Market Nodes for Financial Network MVP v2.
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Market:
    market_id: str
    name: str
    initial_price: float = 100.0
    total_invested: float = 0.0
    price_history: List[float] = field(default_factory=list)
    flow_history: List[float] = field(default_factory=list)
    price_sensitivity: float = 0.001

    def __post_init__(self):
        self.price = self.initial_price
        self.price_history = [self.price]

    def apply_flow(self, net_flow: float):
        price_change = net_flow * self.price_sensitivity
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
        if len(self.markets) >= 2:
            raise ValueError("Maximum 2 markets allowed")
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

"""
Market Nodes for Financial Network MVP v2.
Markets are NON-STRATEGIC - they react mechanically to flows.
"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Market:
    """
    A market/index node (e.g., BANK_INDEX, FINANCIAL_SERVICES_INDEX).
    
    Markets are NOT agents - they react mechanically to net inflow/outflow.
    They do NOT make decisions.
    """
    market_id: str
    name: str
    initial_price: float = 100.0
    
    # Current state
    price: float = field(init=False)
    total_invested: float = 0.0  # Total money invested in this market
    
    # History for logging
    price_history: List[float] = field(default_factory=list)
    flow_history: List[float] = field(default_factory=list)  # Net flows per step
    
    # Price sensitivity to flows (higher = more volatile)
    price_sensitivity: float = 0.001
    
    def __post_init__(self):
        self.price = self.initial_price
        self.price_history.append(self.price)
    
    def apply_flow(self, net_flow: float):
        """
        Update market price based on net inflow/outflow.
        
        Args:
            net_flow: Positive = inflow (price up), Negative = outflow (price down)
        """
        # Price change proportional to flow
        price_change = net_flow * self.price_sensitivity
        self.price = max(1.0, self.price + price_change)  # Floor at 1.0
        
        self.total_invested += net_flow
        self.flow_history.append(net_flow)
        self.price_history.append(self.price)
    
    def get_return(self) -> float:
        """Get current return relative to initial price."""
        return (self.price - self.initial_price) / self.initial_price
    
    def snapshot(self) -> Dict:
        """Return snapshot for logging."""
        return {
            "market_id": self.market_id,
            "name": self.name,
            "price": round(self.price, 2),
            "total_invested": round(self.total_invested, 2),
            "return": round(self.get_return() * 100, 2),  # As percentage
        }
    
    def __repr__(self):
        return f"Market({self.name}, price={self.price:.2f}, invested={self.total_invested:.2f})"


class MarketSystem:
    """
    Container for all markets in the simulation.
    Limited to 2 markets as per spec.
    """
    
    def __init__(self):
        self.markets: Dict[str, Market] = {}
        self._pending_flows: Dict[str, float] = {}  # Accumulate flows per step
    
    def add_market(self, market_id: str, name: str, initial_price: float = 100.0):
        """Add a market to the system."""
        if len(self.markets) >= 2:
            raise ValueError("Maximum 2 markets allowed (per spec)")
        self.markets[market_id] = Market(market_id, name, initial_price)
        self._pending_flows[market_id] = 0.0
    
    def get_market(self, market_id: str) -> Market:
        """Get a market by ID."""
        return self.markets.get(market_id)
    
    def record_flow(self, market_id: str, amount: float):
        """
        Record a pending flow to be applied at end of step.
        Positive = investment, Negative = divestment.
        """
        if market_id in self._pending_flows:
            self._pending_flows[market_id] += amount
    
    def apply_all_flows(self):
        """Apply all pending flows to markets. Called at end of each step."""
        for market_id, flow in self._pending_flows.items():
            if market_id in self.markets and flow != 0:
                self.markets[market_id].apply_flow(flow)
            self._pending_flows[market_id] = 0.0
    
    def snapshot(self) -> Dict:
        """Return snapshot of all markets."""
        return {mid: m.snapshot() for mid, m in self.markets.items()}
    
    def __repr__(self):
        return f"MarketSystem({list(self.markets.keys())})"


def create_default_markets() -> MarketSystem:
    """Create the default market system with 2 indices."""
    system = MarketSystem()
    system.add_market("BANK_INDEX", "Bank Sector Index", initial_price=100.0)
    system.add_market("FIN_SERVICES", "Financial Services Index", initial_price=100.0)
    return system

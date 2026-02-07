"""
Balance Sheet for Financial Institutions.
Core data structure for v2 - all defaults happen via equity < 0.
"""
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum


class AssetType(Enum):
    """Types of assets a bank can hold."""
    CASH = "cash"
    INVESTMENTS = "investments"  # Market investments
    LOANS = "loans"  # Loans given to other banks


@dataclass
class BalanceSheet:
    """
    Bank balance sheet with Assets, Liabilities, and derived Equity.
    
    Default condition: equity < 0
    """
    # Assets
    cash: float = 100.0
    investments: float = 0.0  # Total market investments
    loans_given: float = 0.0  # Total loans to other banks
    
    # Liabilities
    borrowed: float = 50.0  # Deposits / borrowed funds
    
    # Tracking
    investment_positions: Dict[str, float] = field(default_factory=dict)  # market_id -> amount
    loan_positions: Dict[int, float] = field(default_factory=dict)  # bank_id -> amount
    
    @property
    def total_assets(self) -> float:
        """Total assets = cash + investments + loans."""
        return self.cash + self.investments + self.loans_given
    
    @property
    def total_liabilities(self) -> float:
        """Total liabilities = borrowed funds."""
        return self.borrowed
    
    @property
    def equity(self) -> float:
        """Equity = Assets - Liabilities."""
        return self.total_assets - self.total_liabilities
    
    @property
    def is_defaulted(self) -> bool:
        """Bank defaults when equity < 0."""
        return self.equity < 0
    
    def compute_ratios(self) -> Dict[str, float]:
        """
        Compute key financial ratios.
        
        Returns:
            leverage: total_assets / equity (higher = more risk)
            liquidity_ratio: cash / total_assets
            market_exposure: investments / total_assets
        """
        equity = max(self.equity, 0.01)  # Avoid division by zero
        total = max(self.total_assets, 0.01)
        
        return {
            "leverage": self.total_assets / equity,
            "liquidity_ratio": self.cash / total,
            "market_exposure": self.investments / total,
            "loan_exposure": self.loans_given / total,
        }
    
    def snapshot(self) -> Dict:
        """Return a snapshot of the balance sheet for logging."""
        return {
            "cash": round(self.cash, 2),
            "investments": round(self.investments, 2),
            "loans_given": round(self.loans_given, 2),
            "borrowed": round(self.borrowed, 2),
            "equity": round(self.equity, 2),
            "is_defaulted": self.is_defaulted,
            "ratios": {k: round(v, 3) for k, v in self.compute_ratios().items()}
        }
    
    def __repr__(self):
        return f"BalanceSheet(equity={self.equity:.2f}, cash={self.cash:.2f}, investments={self.investments:.2f}, loans={self.loans_given:.2f})"

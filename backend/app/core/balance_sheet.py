"""
Balance Sheet for Financial Institutions (v2).
"""
from dataclasses import dataclass, field
from typing import Dict
from enum import Enum


class AssetType(Enum):
    CASH = "cash"
    INVESTMENTS = "investments"
    LOANS = "loans"


@dataclass
class BalanceSheet:
    cash: float = 100.0
    investments: float = 0.0
    loans_given: float = 0.0
    borrowed: float = 50.0
    investment_positions: Dict[str, float] = field(default_factory=dict)
    loan_positions: Dict[int, float] = field(default_factory=dict)

    @property
    def total_assets(self) -> float:
        return self.cash + self.investments + self.loans_given

    @property
    def total_liabilities(self) -> float:
        return self.borrowed

    @property
    def equity(self) -> float:
        return self.total_assets - self.total_liabilities

    @property
    def is_defaulted(self) -> bool:
        return self.equity < 0

    def compute_ratios(self) -> Dict[str, float]:
        equity = max(self.equity, 0.01)
        total = max(self.total_assets, 0.01)
        return {
            "leverage": self.total_assets / equity,
            "capital_ratio": equity / total,  # Equity / Total Assets
            "liquidity_ratio": self.cash / total,
            "market_exposure": self.investments / total,
            "loan_exposure": self.loans_given / total,
        }

    def snapshot(self) -> Dict:
        return {
            "cash": round(self.cash, 2),
            "investments": round(self.investments, 2),
            "loans_given": round(self.loans_given, 2),
            "borrowed": round(self.borrowed, 2),
            "equity": round(self.equity, 2),
            "is_defaulted": self.is_defaulted,
            "ratios": {k: round(v, 3) for k, v in self.compute_ratios().items()}
        }

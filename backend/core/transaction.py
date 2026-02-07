"""
Transaction and Ledger for Financial Network MVP v2.
Every financial action MUST generate a transaction log.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class TransactionType(Enum):
    """Types of transactions in the system."""
    LOAN = "LOAN"           # Bank lends to another bank
    REPAY = "REPAY"         # Loan repayment
    INVEST = "INVEST"       # Bank invests in market
    DIVEST = "DIVEST"       # Bank divests from market
    DEFAULT_LOSS = "DEFAULT_LOSS"  # Loss from counterparty default


@dataclass
class Transaction:
    """
    A single financial transaction.
    Every action that changes financial state MUST create one.
    """
    time_step: int
    initiator_id: int              # Bank that initiated
    counterparty_id: Optional[int]  # Bank ID or None for market
    counterparty_type: str          # "bank" or "market"
    counterparty_name: str          # Bank ID or market name
    transaction_type: TransactionType
    amount: float
    reason: str = ""               # Why this action was taken
    priority: str = ""             # Featherless priority (PROFIT/LIQUIDITY/STABILITY)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "time": self.time_step,
            "initiator": self.initiator_id,
            "counterparty": self.counterparty_name,
            "counterparty_type": self.counterparty_type,
            "type": self.transaction_type.value,
            "amount": round(self.amount, 2),
            "reason": self.reason
        }
    
    def __repr__(self):
        base = f"[T{self.time_step}] Bank{self.initiator_id} -> {self.counterparty_name}: {self.transaction_type.value} ${self.amount:.2f}"
        if self.priority:
            base += f" [{self.priority}]"
        return base


class Ledger:
    """
    Global transaction ledger with per-bank filtering.
    Used for debugging, explainability, and demo logs.
    """
    
    def __init__(self):
        self._transactions: List[Transaction] = []
    
    def log(self, transaction: Transaction):
        """Add a transaction to the ledger."""
        self._transactions.append(transaction)
    
    def get_all(self) -> List[Transaction]:
        """Get all transactions."""
        return self._transactions
    
    def get_by_bank(self, bank_id: int) -> List[Transaction]:
        """Get all transactions involving a specific bank."""
        return [
            t for t in self._transactions
            if t.initiator_id == bank_id or 
               (t.counterparty_type == "bank" and t.counterparty_id == bank_id)
        ]
    
    def get_by_type(self, tx_type: TransactionType) -> List[Transaction]:
        """Get all transactions of a specific type."""
        return [t for t in self._transactions if t.transaction_type == tx_type]
    
    def get_by_time(self, time_step: int) -> List[Transaction]:
        """Get all transactions at a specific time step."""
        return [t for t in self._transactions if t.time_step == time_step]
    
    def summary(self) -> dict:
        """Get ledger summary statistics."""
        by_type = {}
        for tx_type in TransactionType:
            txs = self.get_by_type(tx_type)
            by_type[tx_type.value] = {
                "count": len(txs),
                "total_amount": sum(t.amount for t in txs)
            }
        return {
            "total_transactions": len(self._transactions),
            "by_type": by_type
        }
    
    def print_log(self, last_n: int = 10):
        """Print recent transactions."""
        print(f"\n📒 TRANSACTION LEDGER (last {last_n}):")
        print("-" * 60)
        for tx in self._transactions[-last_n:]:
            print(f"  {tx}")
        print("-" * 60)
    
    def clear(self):
        """Clear all transactions."""
        self._transactions = []


# Global ledger instance
GLOBAL_LEDGER = Ledger()


def log_transaction(
    time_step: int,
    initiator_id: int,
    counterparty_id: Optional[int],
    counterparty_type: str,
    counterparty_name: str,
    tx_type: TransactionType,
    amount: float,
    reason: str = "",
    priority: str = ""
) -> Transaction:
    """
    Create and log a transaction to the global ledger.
    This is the ONLY way to record financial actions.
    """
    tx = Transaction(
        time_step=time_step,
        initiator_id=initiator_id,
        counterparty_id=counterparty_id,
        counterparty_type=counterparty_type,
        counterparty_name=counterparty_name,
        transaction_type=tx_type,
        amount=amount,
        reason=reason,
        priority=priority
    )
    GLOBAL_LEDGER.log(tx)
    return tx

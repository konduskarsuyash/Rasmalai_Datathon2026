"""
Transaction and Ledger for Financial Network MVP v2.
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class TransactionType(Enum):
    LOAN = "LOAN"
    REPAY = "REPAY"
    INVEST = "INVEST"
    DIVEST = "DIVEST"
    DEFAULT_LOSS = "DEFAULT_LOSS"


@dataclass
class Transaction:
    time_step: int
    initiator_id: int
    counterparty_id: Optional[int]
    counterparty_type: str
    counterparty_name: str
    transaction_type: TransactionType
    amount: float
    reason: str = ""
    priority: str = ""

    def to_dict(self) -> dict:
        return {
            "time": self.time_step,
            "initiator": self.initiator_id,
            "counterparty": self.counterparty_name,
            "counterparty_type": self.counterparty_type,
            "type": self.transaction_type.value,
            "amount": round(self.amount, 2),
            "reason": self.reason
        }


class Ledger:
    def __init__(self):
        self._transactions: List[Transaction] = []

    def log(self, transaction: Transaction):
        self._transactions.append(transaction)

    def get_all(self) -> List[Transaction]:
        return self._transactions

    def get_by_bank(self, bank_id: int) -> List[Transaction]:
        return [
            t for t in self._transactions
            if t.initiator_id == bank_id or
               (t.counterparty_type == "bank" and t.counterparty_id == bank_id)
        ]

    def get_by_type(self, tx_type: TransactionType) -> List[Transaction]:
        return [t for t in self._transactions if t.transaction_type == tx_type]

    def get_by_time(self, time_step: int) -> List[Transaction]:
        return [t for t in self._transactions if t.time_step == time_step]

    def summary(self) -> dict:
        by_type = {}
        for tx_type in TransactionType:
            txs = self.get_by_type(tx_type)
            by_type[tx_type.value] = {"count": len(txs), "total_amount": sum(t.amount for t in txs)}
        return {"total_transactions": len(self._transactions), "by_type": by_type}

    def clear(self):
        self._transactions = []


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

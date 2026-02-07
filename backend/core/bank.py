"""
Bank Agent for Financial Network MVP v2.
Strategic agents with balance sheets, targets, and actions.
Every action generates a transaction log.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random

from .balance_sheet import BalanceSheet
from .transaction import (
    Transaction, TransactionType, log_transaction, GLOBAL_LEDGER
)


class BankAction(Enum):
    """Discrete actions a bank can take."""
    INCREASE_LENDING = "INCREASE_LENDING"
    DECREASE_LENDING = "DECREASE_LENDING"
    INVEST_MARKET = "INVEST_MARKET"
    DIVEST_MARKET = "DIVEST_MARKET"
    HOARD_CASH = "HOARD_CASH"


class StrategicPriority(Enum):
    """Strategic priorities from Featherless."""
    PROFIT = "PROFIT"       # Aggressive actions allowed
    LIQUIDITY = "LIQUIDITY"  # Override to cash-hoarding
    STABILITY = "STABILITY"  # Override to deleveraging


@dataclass
class BankTargets:
    """Target ratios that drive bank behavior."""
    target_leverage: float = 3.0        # target: assets / equity
    target_liquidity: float = 0.3       # target: cash / assets
    target_market_exposure: float = 0.2  # target: investments / assets


@dataclass
class Bank:
    """
    A bank / financial institution agent.
    
    Each bank:
    - Has a balance sheet (assets, liabilities, equity)
    - Operates toward target ratios
    - Only sees local state (own balance + neighbor defaults)
    - Every action produces a transaction log
    - Learns from rewards (bounded rational learning)
    """
    bank_id: int
    name: str = ""
    
    # Core financial state
    balance_sheet: BalanceSheet = field(default_factory=BalanceSheet)
    targets: BankTargets = field(default_factory=BankTargets)
    
    # Learning state (per-bank, independent)
    learning_state: "LearningState" = None  # Initialized in __post_init__
    
    # Tracking
    is_defaulted: bool = False
    action_history: List[Dict] = field(default_factory=list)
    last_action: Optional[BankAction] = None
    last_priority: Optional[StrategicPriority] = None
    last_reward: float = 0.0
    
    def __post_init__(self):
        if not self.name:
            self.name = f"Bank_{self.bank_id}"
        # Initialize learning state
        if self.learning_state is None:
            from ml.learning import LearningState
            self.learning_state = LearningState()
    
    def observe_local_state(self, neighbor_defaults: int = 0) -> Dict:
        """
        Observe local state (agents never see full network).
        
        Args:
            neighbor_defaults: Number of defaulted neighbors (stress signal)
            
        Returns:
            Dictionary of observable state for ML policy
        """
        ratios = self.balance_sheet.compute_ratios()
        
        # Compute gaps from targets
        leverage_gap = ratios["leverage"] - self.targets.target_leverage
        liquidity_gap = self.targets.target_liquidity - ratios["liquidity_ratio"]
        exposure_gap = ratios["market_exposure"] - self.targets.target_market_exposure
        
        return {
            "bank_id": self.bank_id,
            "equity": self.balance_sheet.equity,
            "cash": self.balance_sheet.cash,
            
            # Current ratios
            "leverage": ratios["leverage"],
            "liquidity_ratio": ratios["liquidity_ratio"],
            "market_exposure": ratios["market_exposure"],
            
            # Target gaps (positive = above target, negative = below)
            "leverage_gap": leverage_gap,
            "liquidity_gap": liquidity_gap,
            "exposure_gap": exposure_gap,
            
            # Stress indicator
            "neighbor_defaults": neighbor_defaults,
            "local_stress": min(1.0, neighbor_defaults / 5.0),
            
            # State flags
            "is_defaulted": self.is_defaulted,
        }
    
    def execute_action(
        self,
        action: BankAction,
        time_step: int,
        counterparty_id: Optional[int] = None,
        market_id: str = "BANK_INDEX",
        amount: float = 10.0,
        reason: str = ""
    ) -> Optional[Transaction]:
        """
        Execute a financial action. ALWAYS logs a transaction.
        
        Args:
            action: The action to take
            time_step: Current simulation time
            counterparty_id: Target bank for lending (optional)
            market_id: Target market for investment (optional)
            amount: Amount for the transaction
            reason: Why this action was taken (for logging)
            
        Returns:
            Transaction object (also logged to global ledger)
        """
        if self.is_defaulted:
            return None
        
        # Clamp amount to available resources
        amount = max(0, min(amount, self.balance_sheet.cash * 0.3))  # Max 30% of cash
        
        transaction = None
        
        if action == BankAction.INCREASE_LENDING:
            if counterparty_id is not None and amount > 0:
                self.balance_sheet.cash -= amount
                self.balance_sheet.loans_given += amount
                self.balance_sheet.loan_positions[counterparty_id] = \
                    self.balance_sheet.loan_positions.get(counterparty_id, 0) + amount
                
                transaction = log_transaction(
                    time_step=time_step,
                    initiator_id=self.bank_id,
                    counterparty_id=counterparty_id,
                    counterparty_type="bank",
                    counterparty_name=f"Bank_{counterparty_id}",
                    tx_type=TransactionType.LOAN,
                    amount=amount,
                    reason=reason or "Increase lending"
                )
        
        elif action == BankAction.DECREASE_LENDING:
            if counterparty_id is not None:
                # Reduce loan to specific bank
                current_loan = self.balance_sheet.loan_positions.get(counterparty_id, 0)
                reduce_amount = min(amount, current_loan)
                if reduce_amount > 0:
                    self.balance_sheet.cash += reduce_amount
                    self.balance_sheet.loans_given -= reduce_amount
                    self.balance_sheet.loan_positions[counterparty_id] -= reduce_amount
                    
                    transaction = log_transaction(
                        time_step=time_step,
                        initiator_id=self.bank_id,
                        counterparty_id=counterparty_id,
                        counterparty_type="bank",
                        counterparty_name=f"Bank_{counterparty_id}",
                        tx_type=TransactionType.REPAY,
                        amount=reduce_amount,
                        reason=reason or "Reduce lending"
                    )
        
        elif action == BankAction.INVEST_MARKET:
            if amount > 0:
                self.balance_sheet.cash -= amount
                self.balance_sheet.investments += amount
                self.balance_sheet.investment_positions[market_id] = \
                    self.balance_sheet.investment_positions.get(market_id, 0) + amount
                
                transaction = log_transaction(
                    time_step=time_step,
                    initiator_id=self.bank_id,
                    counterparty_id=None,
                    counterparty_type="market",
                    counterparty_name=market_id,
                    tx_type=TransactionType.INVEST,
                    amount=amount,
                    reason=reason or "Market investment"
                )
        
        elif action == BankAction.DIVEST_MARKET:
            current_position = self.balance_sheet.investment_positions.get(market_id, 0)
            divest_amount = min(amount, current_position)
            if divest_amount > 0:
                self.balance_sheet.cash += divest_amount
                self.balance_sheet.investments -= divest_amount
                self.balance_sheet.investment_positions[market_id] -= divest_amount
                
                transaction = log_transaction(
                    time_step=time_step,
                    initiator_id=self.bank_id,
                    counterparty_id=None,
                    counterparty_type="market",
                    counterparty_name=market_id,
                    tx_type=TransactionType.DIVEST,
                    amount=divest_amount,
                    reason=reason or "Market divestment"
                )
        
        elif action == BankAction.HOARD_CASH:
            # No transaction for hoarding - just skip other actions
            # But we still log for audit trail
            transaction = log_transaction(
                time_step=time_step,
                initiator_id=self.bank_id,
                counterparty_id=None,
                counterparty_type="self",
                counterparty_name="SELF",
                tx_type=TransactionType.REPAY,  # Using REPAY for internal
                amount=0,
                reason=reason or "Hoarding cash - no action"
            )
        
        # Record action
        self.last_action = action
        self.action_history.append({
            "time": time_step,
            "action": action.value,
            "amount": amount,
            "reason": reason
        })
        
        return transaction
    
    def receive_loan(self, lender_id: int, amount: float):
        """Receive a loan from another bank (increases borrowed)."""
        self.balance_sheet.cash += amount
        self.balance_sheet.borrowed += amount
    
    def apply_loss(self, amount: float, time_step: int, source: str = "default"):
        """
        Apply a loss to the bank (reduces cash/assets).
        Used for counterparty default propagation.
        """
        actual_loss = min(amount, self.balance_sheet.cash)
        self.balance_sheet.cash -= actual_loss
        
        log_transaction(
            time_step=time_step,
            initiator_id=self.bank_id,
            counterparty_id=None,
            counterparty_type="system",
            counterparty_name=source,
            tx_type=TransactionType.DEFAULT_LOSS,
            amount=actual_loss,
            reason=f"Loss from {source}"
        )
        
        return actual_loss
    
    def check_default(self) -> bool:
        """Check if bank has defaulted (equity < 0)."""
        if self.balance_sheet.is_defaulted and not self.is_defaulted:
            self.is_defaulted = True
            return True
        return False
    
    def snapshot(self) -> Dict:
        """Return snapshot for logging."""
        return {
            "bank_id": self.bank_id,
            "name": self.name,
            "is_defaulted": self.is_defaulted,
            "last_action": self.last_action.value if self.last_action else None,
            "last_priority": self.last_priority.value if self.last_priority else None,
            "balance_sheet": self.balance_sheet.snapshot(),
        }
    
    def __repr__(self):
        status = "DEFAULTED" if self.is_defaulted else "active"
        return f"Bank({self.bank_id}, equity={self.balance_sheet.equity:.2f}, {status})"


def create_banks(num_banks: int, randomize: bool = True) -> List[Bank]:
    """
    Create a list of banks with DIVERSE initial states.
    Each bank has different capital, borrowed, and investments.
    
    Bank types (distributed evenly):
    - Large banks: High capital, more stable
    - Medium banks: Average capital
    - Small banks: Low capital, more fragile
    - Aggressive banks: High investments, high leverage
    """
    banks = []
    
    for i in range(num_banks):
        # Determine bank type based on index
        bank_type = i % 4
        
        if bank_type == 0:  # Large, stable bank
            cash = random.uniform(150, 200)
            investments = random.uniform(10, 30)
            target_leverage = 2.0
        elif bank_type == 1:  # Medium bank
            cash = random.uniform(80, 120)
            investments = random.uniform(20, 40)
            target_leverage = 3.0
        elif bank_type == 2:  # Small, fragile bank
            cash = random.uniform(40, 70)
            investments = random.uniform(5, 20)
            target_leverage = 2.5
        else:  # Aggressive, high-leverage bank
            cash = random.uniform(70, 100)
            investments = random.uniform(40, 60)
            target_leverage = 4.0  # Slightly lower initial leverage to be safe
        
        # Calculate borrowed amount to hit target leverage initially
        # Leverage = Assets / Equity
        # Equity = Assets - Borrowed
        # Borrowed = Assets * (1 - 1/Leverage)
        total_assets = cash + investments
        borrowed = total_assets * (1 - 1/target_leverage)
        
        # Add some noise to borrowed amount (+/- 5%) but ensure equity > 5
        borrowed *= random.uniform(0.95, 1.05)
        if total_assets - borrowed < 5:
            borrowed = total_assets - 5
            
        balance_sheet = BalanceSheet(
            cash=cash,
            investments=investments,
            loans_given=0.0,
            borrowed=borrowed
        )
        
        # Customize targets based on bank type
        if bank_type == 0:  # Large bank - conservative targets
            targets = BankTargets(
                target_leverage=2.0,
                target_liquidity=0.4,
                target_market_exposure=0.1
            )
        elif bank_type == 1:  # Medium bank - balanced targets
            targets = BankTargets(
                target_leverage=3.0,
                target_liquidity=0.3,
                target_market_exposure=0.2
            )
        elif bank_type == 2:  # Small bank - high liquidity need
            targets = BankTargets(
                target_leverage=2.5,
                target_liquidity=0.5,
                target_market_exposure=0.1
            )
        else:  # Aggressive bank (type 3) - high leverage tolerance
            targets = BankTargets(
                target_leverage=4.5,
                target_liquidity=0.15,
                target_market_exposure=0.35
            )
        
        bank = Bank(
            bank_id=i,
            balance_sheet=balance_sheet,
            targets=targets
        )
        banks.append(bank)
    
    return banks

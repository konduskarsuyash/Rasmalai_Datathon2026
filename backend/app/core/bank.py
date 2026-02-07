"""
Bank Agent for Financial Network MVP v2.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import random

from .balance_sheet import BalanceSheet
from .transaction import Transaction, TransactionType, log_transaction, GLOBAL_LEDGER


class BankAction(Enum):
    INCREASE_LENDING = "INCREASE_LENDING"
    DECREASE_LENDING = "DECREASE_LENDING"
    INVEST_MARKET = "INVEST_MARKET"
    DIVEST_MARKET = "DIVEST_MARKET"
    HOARD_CASH = "HOARD_CASH"


class StrategicPriority(Enum):
    PROFIT = "PROFIT"
    LIQUIDITY = "LIQUIDITY"
    STABILITY = "STABILITY"


@dataclass
class BankTargets:
    target_leverage: float = 3.0
    target_liquidity: float = 0.3
    target_market_exposure: float = 0.2


@dataclass
class Bank:
    bank_id: int
    name: str = ""
    balance_sheet: BalanceSheet = field(default_factory=BalanceSheet)
    targets: BankTargets = field(default_factory=BankTargets)
    is_defaulted: bool = False
    action_history: List[Dict] = field(default_factory=list)
    last_action: Optional[BankAction] = None
    last_priority: Optional[StrategicPriority] = None
    
    # Risk tracking features for ML
    past_defaults: int = 0  # Number of past defaults
    risk_appetite: float = 0.5  # 0.0 (conservative) to 1.0 (aggressive)
    investment_volatility: float = 0.0  # Volatility of investment returns
    default_step: Optional[int] = None  # Step when bank defaulted (if ever)

    def __post_init__(self):
        if not self.name:
            self.name = f"Bank_{self.bank_id}"

    def observe_local_state(self, neighbor_defaults: int = 0) -> Dict:
        ratios = self.balance_sheet.compute_ratios()
        leverage_gap = ratios["leverage"] - self.targets.target_leverage
        liquidity_gap = self.targets.target_liquidity - ratios["liquidity_ratio"]
        exposure_gap = ratios["market_exposure"] - self.targets.target_market_exposure
        return {
            "bank_id": self.bank_id,
            "equity": self.balance_sheet.equity,
            "cash": self.balance_sheet.cash,
            "leverage": ratios["leverage"],
            "liquidity_ratio": ratios["liquidity_ratio"],
            "market_exposure": ratios["market_exposure"],
            "capital_ratio": ratios["capital_ratio"],
            "leverage_gap": leverage_gap,
            "liquidity_gap": liquidity_gap,
            "exposure_gap": exposure_gap,
            "neighbor_defaults": neighbor_defaults,
            "local_stress": min(1.0, neighbor_defaults / 5.0),
            "is_defaulted": self.is_defaulted,
            # Risk assessment features
            "past_defaults": self.past_defaults,
            "risk_appetite": self.risk_appetite,
            "investment_volatility": self.investment_volatility,
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
        if self.is_defaulted:
            return None
        # Allow banks to use more cash for actions (up to 50% instead of 30%)
        amount = max(0, min(amount, self.balance_sheet.cash * 0.5))
        transaction = None

        if action == BankAction.INCREASE_LENDING:
            if counterparty_id is not None and amount > 0:
                self.balance_sheet.cash -= amount
                self.balance_sheet.loans_given += amount
                self.balance_sheet.loan_positions[counterparty_id] = \
                    self.balance_sheet.loan_positions.get(counterparty_id, 0) + amount
                transaction = log_transaction(
                    time_step, self.bank_id, counterparty_id, "bank", f"Bank_{counterparty_id}",
                    TransactionType.LOAN, amount, reason or "Increase lending"
                )
        elif action == BankAction.DECREASE_LENDING:
            if counterparty_id is not None:
                current_loan = self.balance_sheet.loan_positions.get(counterparty_id, 0)
                reduce_amount = min(amount, current_loan)
                if reduce_amount > 0:
                    self.balance_sheet.cash += reduce_amount
                    self.balance_sheet.loans_given -= reduce_amount
                    self.balance_sheet.loan_positions[counterparty_id] -= reduce_amount
                    transaction = log_transaction(
                        time_step, self.bank_id, counterparty_id, "bank", f"Bank_{counterparty_id}",
                        TransactionType.REPAY, reduce_amount, reason or "Reduce lending"
                    )
        elif action == BankAction.INVEST_MARKET:
            if amount > 0:
                self.balance_sheet.cash -= amount
                self.balance_sheet.investments += amount
                self.balance_sheet.investment_positions[market_id] = \
                    self.balance_sheet.investment_positions.get(market_id, 0) + amount
                transaction = log_transaction(
                    time_step, self.bank_id, None, "market", market_id,
                    TransactionType.INVEST, amount, reason or "Market investment"
                )
        elif action == BankAction.DIVEST_MARKET:
            current_position = self.balance_sheet.investment_positions.get(market_id, 0)
            divest_amount = min(amount, current_position)
            if divest_amount > 0:
                # Get market for calculating realized returns
                from ..core.market import Market
                market = None
                # This will be passed from the simulation context
                # For now, divest at book value (will be enhanced in execute_action call)
                
                self.balance_sheet.cash += divest_amount
                self.balance_sheet.investments -= divest_amount
                self.balance_sheet.investment_positions[market_id] -= divest_amount
                transaction = log_transaction(
                    time_step, self.bank_id, None, "market", market_id,
                    TransactionType.DIVEST, divest_amount, reason or "Market divestment"
                )
        elif action == BankAction.HOARD_CASH:
            transaction = log_transaction(
                time_step, self.bank_id, None, "self", "SELF",
                TransactionType.REPAY, 0, reason or "Hoarding cash - no action"
            )

        self.last_action = action
        self.action_history.append({"time": time_step, "action": action.value, "amount": amount, "reason": reason})
        return transaction

    def apply_loss(self, amount: float, time_step: int, source: str = "default"):
        actual_loss = min(amount, self.balance_sheet.cash)
        self.balance_sheet.cash -= actual_loss
        log_transaction(
            time_step, self.bank_id, None, "system", source,
            TransactionType.DEFAULT_LOSS, actual_loss, f"Loss from {source}"
        )
        return actual_loss

    def check_default(self) -> bool:
        if self.balance_sheet.is_defaulted and not self.is_defaulted:
            self.is_defaulted = True
            self.past_defaults += 1
            return True
        return False

    def book_investment_profit(self, markets_dict: Dict, time_step: int) -> float:
        """
        Book profits/losses from market investments based on current market returns.
        Returns total profit/loss booked.
        """
        if self.is_defaulted:
            return 0.0
        
        total_profit = 0.0
        
        for market_id, invested_amount in self.balance_sheet.investment_positions.items():
            if market_id in markets_dict and invested_amount > 0:
                market = markets_dict[market_id]
                market_return = market.get_return()
                
                # Calculate profit based on return
                profit = invested_amount * market_return
                
                # Book the profit by increasing cash
                self.balance_sheet.cash += profit
                total_profit += profit
                
                # Log the profit booking
                if profit != 0:
                    log_transaction(
                        time_step, self.bank_id, None, "market", market_id,
                        TransactionType.INVEST if profit > 0 else TransactionType.DIVEST,
                        abs(profit), f"Profit booking: {market_return*100:.1f}% return"
                    )
        
        return total_profit

    def snapshot(self) -> Dict:
        return {
            "bank_id": self.bank_id,
            "name": self.name,
            "is_defaulted": self.is_defaulted,
            "last_action": self.last_action.value if self.last_action else None,
            "last_priority": self.last_priority.value if self.last_priority else None,
            # Risk metrics for frontend display
            "past_defaults": self.past_defaults,
            "risk_appetite": self.risk_appetite,
            "investment_volatility": self.investment_volatility,
            "balance_sheet": self.balance_sheet.snapshot(),
        }


def create_banks(num_banks: int, randomize: bool = True, bank_configs: Optional[List] = None) -> List[Bank]:
    """
    Create banks with optional per-bank configurations.
    
    Args:
        num_banks: Number of banks to create
        randomize: If True and no configs provided, randomize bank parameters
        bank_configs: Optional list of BankConfig objects with per-bank settings
    """
    banks = []
    for i in range(num_banks):
        # Check if we have a specific config for this bank
        if bank_configs and i < len(bank_configs):
            config = bank_configs[i]
            # Initialize with proper leverage
            # equity = config.initial_capital
            # target_leverage = total_assets / equity
            # Therefore: total_assets = equity * target_leverage
            
            equity = config.initial_capital
            target_leverage = max(1.0, config.target_leverage)  # At least 1x
            total_assets = equity * target_leverage
            
            # Distribute assets
            cash = total_assets * 0.5  # 50% cash
            investments = total_assets * 0.3  # 30% investments
            loans_given = total_assets * 0.2  # 20% loans
            
            # Calculate borrowed to maintain equity
            # equity = total_assets - borrowed
            # borrowed = total_assets - equity
            borrowed = total_assets - equity
            
            # Map risk factor to targets (lower risk = more conservative)
            if config.risk_factor < 0.3:
                # Conservative
                targets = BankTargets(
                    target_leverage=max(1.5, config.target_leverage * 0.7),
                    target_liquidity=0.4,
                    target_market_exposure=0.1
                )
            elif config.risk_factor > 0.6:
                # Aggressive
                targets = BankTargets(
                    target_leverage=min(10.0, config.target_leverage * 1.3),
                    target_liquidity=0.15,
                    target_market_exposure=0.35
                )
            else:
                # Balanced
                targets = BankTargets(
                    target_leverage=config.target_leverage,
                    target_liquidity=0.3,
                    target_market_exposure=0.2
                )
                
            bs = BalanceSheet(cash=cash, investments=investments, loans_given=loans_given, borrowed=borrowed)
            bank = Bank(bank_id=i, balance_sheet=bs, targets=targets)
            banks.append(bank)
        else:
            # Use default randomized approach
            bank_type = i % 4
            if bank_type == 0:
                cash, borrowed, investments = random.uniform(150, 200), random.uniform(30, 50), random.uniform(0, 10)
            elif bank_type == 1:
                cash, borrowed, investments = random.uniform(80, 120), random.uniform(50, 70), random.uniform(10, 30)
            elif bank_type == 2:
                cash, borrowed, investments = random.uniform(30, 60), random.uniform(20, 40), random.uniform(0, 15)
            else:
                cash, borrowed, investments = random.uniform(60, 90), random.uniform(80, 120), random.uniform(30, 50)
            bs = BalanceSheet(cash=cash, investments=investments, loans_given=0.0, borrowed=borrowed)
            if bank_type == 0:
                targets = BankTargets(2.0, 0.4, 0.1)
            elif bank_type == 1:
                targets = BankTargets(3.0, 0.3, 0.2)
            elif bank_type == 2:
                targets = BankTargets(2.5, 0.5, 0.1)
            else:
                targets = BankTargets(4.5, 0.15, 0.35)
            banks.append(Bank(bank_id=i, balance_sheet=bs, targets=targets))
    return banks

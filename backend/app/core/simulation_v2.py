"""
Simulation Engine v2 for Financial Network MVP.
"""
import random
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

from .bank import Bank, BankAction, create_banks
from .market import MarketSystem, create_default_markets
from .transaction import GLOBAL_LEDGER, TransactionType
from .balance_sheet import BalanceSheet
from app.ml.policy import select_action


@dataclass
class BankConfig:
    """Configuration for individual bank initialization with dynamic amounts."""
    initial_capital: float = 100.0
    target_leverage: float = 3.0
    risk_factor: float = 0.3  # 0.0 (conservative) to 1.0 (aggressive)


@dataclass
class SimulationConfig:
    num_banks: int = 20
    num_steps: int = 30
    use_featherless: bool = True
    use_game_theory: bool = True  # Enable Nash equilibrium decision-making
    shock_probability: float = 0.1
    verbose: bool = True
    lending_amount: float = 10.0
    investment_amount: float = 10.0
    connection_density: float = 0.2
    bank_configs: Optional[List[BankConfig]] = None


@dataclass
class SimulationState:
    time_step: int = 0
    banks: List[Bank] = field(default_factory=list)
    markets: MarketSystem = field(default_factory=create_default_markets)
    defaults_this_step: List[int] = field(default_factory=list)
    cascade_depth: int = 0


def run_simulation_v2(config: SimulationConfig, featherless_fn: Optional[Callable] = None) -> Dict:
    GLOBAL_LEDGER.clear()
    state = SimulationState()
    state.banks = create_banks(config.num_banks, bank_configs=config.bank_configs)
    state.markets = create_default_markets()
    _create_interbank_network(state.banks, connection_density=config.connection_density)

    history = {
        "steps": [],
        "defaults_over_time": [],
        "total_equity_over_time": [],
        "market_prices": [],
        "cascade_events": [],
        "system_logs": [],
        "bank_logs": [],
    }

    for t in range(config.num_steps):
        state.time_step = t
        state.defaults_this_step = []
        state.cascade_depth = 0
        step_log = {"time": t, "actions": [], "defaults": [], "cascades": 0, "market_flows": {}}
        market_flows = {"BANK_INDEX": 0.0, "FIN_SERVICES": 0.0}

        for bank_idx, bank in enumerate(state.banks):
            if bank.is_defaulted:
                continue
            neighbor_defaults = _count_neighbor_defaults(bank, state.banks)
            observation = bank.observe_local_state(neighbor_defaults)
            
            # Calculate network default rate for game theory
            total_defaults = sum(1 for b in state.banks if b.is_defaulted)
            network_default_rate = total_defaults / config.num_banks if config.num_banks > 0 else 0.0
            
            priority = None
            if config.use_featherless and featherless_fn:
                try:
                    priority = featherless_fn(observation)
                    bank.last_priority = priority
                except Exception:
                    priority = None
            
            # Use game theory or heuristics based on config
            ml_action, reason = select_action(
                observation, 
                priority, 
                use_game_theory=config.use_game_theory,
                network_default_rate=network_default_rate
            )
            action = BankAction[ml_action.value]
            counterparty_id = _select_counterparty(bank, state.banks, action)
            market_id = random.choice(["BANK_INDEX", "FIN_SERVICES"])
            
            # Calculate dynamic transaction amounts based on bank characteristics
            ratios = bank.balance_sheet.compute_ratios()
            cash = bank.balance_sheet.cash
            equity = bank.balance_sheet.equity
            
            # Base amount scales with bank size (5-15% of cash)
            base_pct = 0.08 + (observation.get('leverage_gap', 0) * 0.02)
            
            # Risk factor influences transaction size
            risk_multiplier = 1.0
            if config.bank_configs and bank_idx < len(config.bank_configs):
                risk_factor = config.bank_configs[bank_idx].risk_factor
                risk_multiplier = 0.7 + (risk_factor * 0.8)  # 0.7x to 1.5x
            
            # Calculate amount based on action type
            if action in [BankAction.INVEST_MARKET, BankAction.DIVEST_MARKET]:
                amount = cash * base_pct * risk_multiplier * 1.2
            elif action == BankAction.INCREASE_LENDING:
                amount = cash * base_pct * risk_multiplier * 1.4
            elif action == BankAction.DECREASE_LENDING:
                amount = cash * base_pct * 0.6
            else:
                amount = cash * 0.02
            
            # Clamp to reasonable bounds (5M to 50M)
            amount = max(5.0, min(50.0, amount))
            amount = min(amount, equity * 0.3)
            
            bank.execute_action(
                action=action,
                time_step=t,
                counterparty_id=counterparty_id,
                market_id=market_id,
                amount=amount,
                reason=reason,
            )
            if action == BankAction.INVEST_MARKET:
                market_flows[market_id] += investment_amt
            elif action == BankAction.DIVEST_MARKET:
                market_flows[market_id] -= investment_amt
            step_log["actions"].append({
                "bank_id": bank.bank_id,
                "action": action.value,
                "priority": priority.value if priority else None,
                "reason": reason,
            })
            history["bank_logs"].append({
                "time": t,
                "bank_id": bank.bank_id,
                "balance_sheet": bank.balance_sheet.snapshot(),
                "action": action.value,
                "reason": reason,
            })

        for market_id, flow in market_flows.items():
            state.markets.record_flow(market_id, flow)
        state.markets.apply_all_flows()
        step_log["market_flows"] = market_flows

        new_defaults = []
        for bank in state.banks:
            if not bank.is_defaulted and bank.check_default():
                new_defaults.append(bank.bank_id)
                state.defaults_this_step.append(bank.bank_id)
                history["system_logs"].append({
                    "time": t,
                    "event": "DEFAULT",
                    "bank_id": bank.bank_id,
                    "equity": bank.balance_sheet.equity,
                })

        if new_defaults:
            cascade_count = _propagate_cascades(state, t, config.verbose)
            step_log["cascades"] = cascade_count
            if cascade_count > 0:
                history["cascade_events"].append({
                    "time": t,
                    "initial_defaults": new_defaults,
                    "cascade_count": cascade_count,
                })
                history["system_logs"].append({"time": t, "event": "CASCADE", "cascade_count": cascade_count})

        step_log["defaults"] = state.defaults_this_step.copy()
        total_defaults = sum(1 for b in state.banks if b.is_defaulted)
        total_equity = sum(b.balance_sheet.equity for b in state.banks if not b.is_defaulted)
        history["defaults_over_time"].append(total_defaults)
        history["total_equity_over_time"].append(total_equity)
        history["market_prices"].append(state.markets.snapshot())
        history["steps"].append(step_log)

        if total_defaults >= config.num_banks:
            break

    history["summary"] = _create_summary(state, history, config)
    return history


def _create_interbank_network(banks: List[Bank], connection_density: float = 0.2):
    num_banks = len(banks)
    
    # Can't create interbank network with only 1 bank
    if num_banks < 2:
        return
    
    num_connections = int(num_banks * (num_banks - 1) * connection_density / 2)
    for _ in range(num_connections):
        lender = random.choice(banks)
        potential_borrowers = [b for b in banks if b.bank_id != lender.bank_id]
        
        # Safety check (shouldn't happen with num_banks >= 2, but just in case)
        if not potential_borrowers:
            continue
            
        borrower = random.choice(potential_borrowers)
        amount = random.uniform(5, 15)
        if lender.balance_sheet.cash >= amount:
            lender.balance_sheet.cash -= amount
            lender.balance_sheet.loans_given += amount
            lender.balance_sheet.loan_positions[borrower.bank_id] = \
                lender.balance_sheet.loan_positions.get(borrower.bank_id, 0) + amount
            borrower.balance_sheet.cash += amount
            borrower.balance_sheet.borrowed += amount


def _count_neighbor_defaults(bank: Bank, all_banks: List[Bank]) -> int:
    count = 0
    for counterparty_id in bank.balance_sheet.loan_positions:
        for b in all_banks:
            if b.bank_id == counterparty_id and b.is_defaulted:
                count += 1
    return count


def _select_counterparty(bank: Bank, all_banks: List[Bank], action: BankAction) -> Optional[int]:
    if action == BankAction.INCREASE_LENDING:
        candidates = [b for b in all_banks if b.bank_id != bank.bank_id and not b.is_defaulted]
        if candidates:
            return random.choice(candidates).bank_id
    elif action == BankAction.DECREASE_LENDING:
        if bank.balance_sheet.loan_positions:
            return random.choice(list(bank.balance_sheet.loan_positions.keys()))
    return None


def _propagate_cascades(state: SimulationState, time_step: int, verbose: bool) -> int:
    cascade_count = 0
    for _ in range(5):
        new_cascade_defaults = []
        for defaulted_id in state.defaults_this_step:
            for bank in state.banks:
                if bank.is_defaulted:
                    continue
                exposure = bank.balance_sheet.loan_positions.get(defaulted_id, 0)
                if exposure > 0:
                    bank.apply_loss(exposure, time_step, f"Bank_{defaulted_id}_default")
                    bank.balance_sheet.loans_given -= exposure
                    del bank.balance_sheet.loan_positions[defaulted_id]
                    if bank.check_default():
                        new_cascade_defaults.append(bank.bank_id)
                        cascade_count += 1
        if not new_cascade_defaults:
            break
        state.defaults_this_step.extend(new_cascade_defaults)
        state.cascade_depth += 1
    return cascade_count


def _create_summary(state: SimulationState, history: Dict, config: SimulationConfig) -> Dict:
    total_defaults = sum(1 for b in state.banks if b.is_defaulted)
    surviving = [b for b in state.banks if not b.is_defaulted]
    return {
        "total_steps": len(history["steps"]),
        "total_defaults": total_defaults,
        "default_rate": total_defaults / config.num_banks,
        "total_cascade_events": len(history["cascade_events"]),
        "surviving_banks": len(surviving),
        "final_total_equity": sum(b.balance_sheet.equity for b in surviving),
        "transactions_logged": len(GLOBAL_LEDGER.get_all()),
        "system_collapsed": total_defaults >= config.num_banks,
    }

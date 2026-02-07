"""
Simulation Engine v2 for Financial Network MVP.
Strict loop order as per spec - DO NOT REORDER.
"""
import random
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field

from .bank import Bank, BankAction, create_banks
from .market import MarketSystem, create_default_markets
from .transaction import GLOBAL_LEDGER, TransactionType
from .balance_sheet import BalanceSheet

# Import ML policy (uses string-based action matching)
from ml.policy import select_action


@dataclass
class SimulationConfig:
    """Configuration for v2 simulation."""
    num_banks: int = 20
    num_steps: int = 30
    use_featherless: bool = True
    shock_probability: float = 0.1
    verbose: bool = True
    
    # Interbank lending parameters
    lending_amount: float = 10.0
    investment_amount: float = 10.0


@dataclass 
class SimulationState:
    """Current simulation state."""
    time_step: int = 0
    banks: List[Bank] = field(default_factory=list)
    markets: MarketSystem = field(default_factory=create_default_markets)
    defaults_this_step: List[int] = field(default_factory=list)
    cascade_depth: int = 0


def run_simulation_v2(
    config: SimulationConfig,
    featherless_fn: Optional[Callable] = None
) -> Dict:
    """
    Run v2 simulation with strict loop order.
    
    STRICT ORDER (DO NOT REORDER):
    1. Each active bank observes local state
    2. ML policy proposes an action
    3. Featherless may override action priority
    4. Action is executed
    5. Transaction is logged
    6. Markets update prices
    7. Defaults are evaluated
    8. Cascades propagate
    
    Args:
        config: Simulation configuration
        featherless_fn: Function to get Featherless priority (optional)
        
    Returns:
        Simulation history and results
    """
    # Clear ledger from previous runs
    GLOBAL_LEDGER.clear()
    
    # Initialize state
    state = SimulationState()
    state.banks = create_banks(config.num_banks)
    state.markets = create_default_markets()
    
    # Create interbank network (random connections)
    _create_interbank_network(state.banks, connection_density=0.2)
    
    # History tracking
    history = {
        "steps": [],
        "defaults_over_time": [],
        "total_equity_over_time": [],
        "market_prices": [],
        "cascade_events": [],
        "system_logs": [],
        "bank_logs": []
    }
    
    if config.verbose:
        print("=" * 60)
        print("🏦 FINANCIAL NETWORK SIMULATION v2")
        print("   Balance Sheet-Based Strategic Model")
        print("=" * 60)
        print(f"\n📊 Initialized {config.num_banks} banks, 2 markets")
        print(f"   Featherless: {'enabled' if featherless_fn else 'rule-based'}")
        print("-" * 60)
    
    # Main simulation loop
    for t in range(config.num_steps):
        state.time_step = t
        state.defaults_this_step = []
        state.cascade_depth = 0
        
        step_log = {
            "time": t,
            "actions": [],
            "defaults": [],
            "cascades": 0,
            "market_flows": {}
        }
        
        if config.verbose:
            print(f"\n=== Time Step {t} ===")
        
        # Track market flows this step
        market_flows = {"BANK_INDEX": 0.0, "FIN_SERVICES": 0.0}
        
        # ============================================================
        # STEP 1-5: Process each active bank
        # ============================================================
        for bank in state.banks:
            if bank.is_defaulted:
                continue
            
            # STEP 1: Bank observes local state
            neighbor_defaults = _count_neighbor_defaults(bank, state.banks)
            observation = bank.observe_local_state(neighbor_defaults)
            
            # STEP 2: ML policy proposes action
            priority = None
            
            # STEP 3: Featherless may override priority
            if config.use_featherless and featherless_fn:
                try:
                    priority = featherless_fn(observation)
                    bank.last_priority = priority
                except Exception:
                    priority = None
            
            # Get action from ML policy (returns action, reason)
            ml_action, reason = select_action(observation, priority)
            
            # Convert ML action to bank's BankAction enum
            action = BankAction[ml_action.value]  # Match by value
            
            # Pick counterparty for lending actions
            counterparty_id = _select_counterparty(bank, state.banks, action)
            market_id = random.choice(["BANK_INDEX", "FIN_SERVICES"])
            
            # STEP 4 & 5: Execute action (transaction logged internally)
            tx = bank.execute_action(
                action=action,
                time_step=t,
                counterparty_id=counterparty_id,
                market_id=market_id,
                amount=config.lending_amount if "LENDING" in action.value else config.investment_amount,
                reason=reason
            )
            
            # Track market flows
            if action == BankAction.INVEST_MARKET:
                market_flows[market_id] += config.investment_amount
            elif action == BankAction.DIVEST_MARKET:
                market_flows[market_id] -= config.investment_amount
            
            # Log bank action
            step_log["actions"].append({
                "bank_id": bank.bank_id,
                "action": action.value,
                "priority": priority.value if priority else None,
                "reason": reason
            })
            
            # Bank-level log
            history["bank_logs"].append({
                "time": t,
                "bank_id": bank.bank_id,
                "balance_sheet": bank.balance_sheet.snapshot(),
                "action": action.value,
                "reason": reason
            })
            
            # Always show action in verbose mode with key bank info
            if config.verbose:
                bs = bank.balance_sheet
                priority_str = f" [{priority.value}]" if priority else ""
                print(f"  Bank{bank.bank_id}: {action.value}{priority_str} | cash=${bs.cash:.0f} eq=${bs.equity:.0f}")
        
        # ============================================================
        # STEP 6: Markets update prices
        # ============================================================
        for market_id, flow in market_flows.items():
            state.markets.record_flow(market_id, flow)
        state.markets.apply_all_flows()
        
        step_log["market_flows"] = market_flows
        
        # ============================================================
        # STEP 7: Evaluate defaults (equity < 0)
        # ============================================================
        new_defaults = []
        for bank in state.banks:
            if not bank.is_defaulted and bank.check_default():
                new_defaults.append(bank.bank_id)
                state.defaults_this_step.append(bank.bank_id)
                
                if config.verbose:
                    print(f"  💥 Bank{bank.bank_id} DEFAULTED (equity={bank.balance_sheet.equity:.2f})")
                
                history["system_logs"].append({
                    "time": t,
                    "event": "DEFAULT",
                    "bank_id": bank.bank_id,
                    "equity": bank.balance_sheet.equity
                })
        
        # ============================================================
        # STEP 8: Cascade propagation
        # ============================================================
        if new_defaults:
            cascade_count = _propagate_cascades(state, t, config.verbose)
            step_log["cascades"] = cascade_count
            
            if cascade_count > 0:
                history["cascade_events"].append({
                    "time": t,
                    "initial_defaults": new_defaults,
                    "cascade_count": cascade_count
                })
                history["system_logs"].append({
                    "time": t,
                    "event": "CASCADE",
                    "cascade_count": cascade_count
                })
        
        step_log["defaults"] = state.defaults_this_step.copy()
        
        # Record metrics
        total_defaults = sum(1 for b in state.banks if b.is_defaulted)
        total_equity = sum(b.balance_sheet.equity for b in state.banks if not b.is_defaulted)
        
        history["defaults_over_time"].append(total_defaults)
        history["total_equity_over_time"].append(total_equity)
        history["market_prices"].append(state.markets.snapshot())
        history["steps"].append(step_log)
        
        if config.verbose:
            print(f"  📊 Defaults: {total_defaults}/{config.num_banks}, Equity: ${total_equity:.0f}")
        
        # Check for system collapse
        if total_defaults >= config.num_banks:
            if config.verbose:
                print("\n💀 TOTAL SYSTEM COLLAPSE!")
            break
    
    # Summary
    history["summary"] = _create_summary(state, history, config)
    
    if config.verbose:
        _print_report(history)
    
    return history


def _create_interbank_network(banks: List[Bank], connection_density: float = 0.2):
    """Create random interbank lending relationships."""
    num_banks = len(banks)
    num_connections = int(num_banks * (num_banks - 1) * connection_density / 2)
    
    for _ in range(num_connections):
        lender = random.choice(banks)
        borrower = random.choice([b for b in banks if b.bank_id != lender.bank_id])
        
        amount = random.uniform(5, 15)
        if lender.balance_sheet.cash >= amount:
            lender.balance_sheet.cash -= amount
            lender.balance_sheet.loans_given += amount
            lender.balance_sheet.loan_positions[borrower.bank_id] = \
                lender.balance_sheet.loan_positions.get(borrower.bank_id, 0) + amount
            
            borrower.balance_sheet.cash += amount
            borrower.balance_sheet.borrowed += amount


def _count_neighbor_defaults(bank: Bank, all_banks: List[Bank]) -> int:
    """Count defaults among banks that this bank has exposure to."""
    count = 0
    for counterparty_id in bank.balance_sheet.loan_positions.keys():
        for b in all_banks:
            if b.bank_id == counterparty_id and b.is_defaulted:
                count += 1
    return count


def _select_counterparty(bank: Bank, all_banks: List[Bank], action: BankAction) -> Optional[int]:
    """Select a counterparty for lending actions."""
    if action == BankAction.INCREASE_LENDING:
        candidates = [b for b in all_banks if b.bank_id != bank.bank_id and not b.is_defaulted]
        if candidates:
            return random.choice(candidates).bank_id
    elif action == BankAction.DECREASE_LENDING:
        if bank.balance_sheet.loan_positions:
            return random.choice(list(bank.balance_sheet.loan_positions.keys()))
    return None


def _propagate_cascades(state: SimulationState, time_step: int, verbose: bool) -> int:
    """
    Propagate default losses to lenders.
    Returns count of new cascade defaults.
    """
    cascade_count = 0
    max_rounds = 5
    
    for round_num in range(max_rounds):
        new_cascade_defaults = []
        
        for defaulted_id in state.defaults_this_step:
            # Find all lenders to this defaulted bank
            for bank in state.banks:
                if bank.is_defaulted:
                    continue
                
                # Check if bank has exposure to defaulted bank
                exposure = bank.balance_sheet.loan_positions.get(defaulted_id, 0)
                if exposure > 0:
                    # Apply loss
                    loss = bank.apply_loss(exposure, time_step, f"Bank_{defaulted_id}_default")
                    
                    # Remove the loan from positions
                    bank.balance_sheet.loans_given -= exposure
                    del bank.balance_sheet.loan_positions[defaulted_id]
                    
                    if verbose:
                        print(f"    📉 Bank{bank.bank_id} lost ${loss:.2f} from Bank{defaulted_id} default")
                    
                    # Check if this triggers a new default
                    if bank.check_default():
                        new_cascade_defaults.append(bank.bank_id)
                        cascade_count += 1
                        if verbose:
                            print(f"    💥 CASCADE: Bank{bank.bank_id} defaulted!")
        
        if not new_cascade_defaults:
            break
        
        state.defaults_this_step.extend(new_cascade_defaults)
        state.cascade_depth += 1
    
    return cascade_count


def _create_summary(state: SimulationState, history: Dict, config: SimulationConfig) -> Dict:
    """Create simulation summary."""
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
        "system_collapsed": total_defaults >= config.num_banks
    }


def _print_report(history: Dict) -> None:
    """Print simulation report."""
    s = history["summary"]
    print("\n" + "=" * 60)
    print("📊 SIMULATION REPORT v2")
    print("=" * 60)
    print(f"  Steps completed:      {s['total_steps']}")
    print(f"  Final defaults:       {s['total_defaults']} ({s['default_rate']:.1%})")
    print(f"  Cascade events:       {s['total_cascade_events']}")
    print(f"  Surviving banks:      {s['surviving_banks']}")
    print(f"  Total equity:         ${s['final_total_equity']:.0f}")
    print(f"  Transactions logged:  {s['transactions_logged']}")
    print("=" * 60)
    
    # Print recent transactions
    GLOBAL_LEDGER.print_log(last_n=10)

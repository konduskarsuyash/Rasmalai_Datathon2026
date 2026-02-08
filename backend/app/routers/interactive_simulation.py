"""
Interactive Simulation API: Real-time simulation with pause/resume/modify capabilities.
"""
from typing import Optional, Dict
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core import SimulationConfig, GLOBAL_LEDGER
from app.core.simulation_v2 import BankConfig
from app.middleware.auth import get_optional_user

router = APIRouter()

# Global simulation state (one active simulation per server instance)
ACTIVE_SIMULATION = {
    "state": None,
    "is_running": False,
    "is_paused": False,
    "control_queue": asyncio.Queue(),
}


class SimulationCommand(BaseModel):
    """Command to control running simulation."""
    command: str = Field(..., description="Command: pause, resume, stop, delete_bank, add_capital, financial_crisis")
    bank_id: Optional[int] = Field(None, description="Bank ID for bank-specific commands")
    amount: Optional[float] = Field(None, description="Amount for add_capital command")


class InteractiveSimulationRequest(BaseModel):
    """Request to start interactive simulation."""
    num_banks: int = Field(default=20, ge=1, le=100)
    num_steps: int = Field(default=30, ge=1, le=200)
    node_parameters: Optional[list] = None
    market_nodes: Optional[list] = Field(default=None, description="Market nodes from the UI: [{id, name}]")
    connection_density: float = Field(default=0.2, ge=0, le=1)
    use_featherless: bool = Field(default=True)
    use_game_theory: bool = Field(default=True, description="Use Nash equilibrium game theory")


async def interactive_simulation_generator(config: SimulationConfig, control_queue: asyncio.Queue, featherless_fn):
    """Generator for interactive simulation with pause/resume/modify."""
    from app.core.simulation_v2 import (
        SimulationState, create_default_markets, _create_interbank_network,
        _count_neighbor_defaults, _select_counterparty, _propagate_cascades,
        create_banks
    )
    from app.core.market import create_markets_from_config
    from app.core.bank import BankAction
    from app.ml.policy import select_action
    import random
    
    GLOBAL_LEDGER.clear()
    state = SimulationState()
    state.banks = create_banks(config.num_banks, bank_configs=config.bank_configs)
    
    # Use market configs from UI if provided, otherwise create defaults
    if config.market_configs and len(config.market_configs) > 0:
        state.markets = create_markets_from_config(config.market_configs)
        print(f"[INTERACTIVE SIM] Using {len(config.market_configs)} user-defined markets")
    else:
        # No markets from UI — create default markets so banks can invest
        # Banks NEED markets to invest in; without them the economy stagnates
        default_market_configs = [
            {"market_id": "BANK_INDEX", "name": "Bank Index Fund", "initial_price": 100.0},
            {"market_id": "FIN_SERVICES", "name": "Financial Services", "initial_price": 100.0},
        ]
        state.markets = create_markets_from_config(default_market_configs)
        print(f"[INTERACTIVE SIM] No markets from UI — created {len(default_market_configs)} default markets")
    
    _create_interbank_network(state.banks, connection_density=config.connection_density)
    
    print(f"[INTERACTIVE SIM] Initialized with {len(state.banks)} banks")
    
    # Store in global state
    ACTIVE_SIMULATION["state"] = state
    ACTIVE_SIMULATION["is_running"] = True
    ACTIVE_SIMULATION["is_paused"] = False
    
    # Send initial state
    initial_banks = [
        {
            "id": bank.bank_id,
            "name": bank.name,
            "capital": bank.balance_sheet.equity,
            "cash": bank.balance_sheet.cash,
            "is_defaulted": bank.is_defaulted,
        }
        for bank in state.banks
    ]
    
    initial_markets = []
    for market_id, market in state.markets.markets.items():
        initial_markets.append({
            "id": market_id,
            "name": market.name,
            "price": market.price,
            "total_invested": market.total_invested,
        })
    
    initial_connections = []
    for bank in state.banks:
        for counterparty_id, amount in bank.balance_sheet.loan_positions.items():
            initial_connections.append({
                "from": bank.bank_id,
                "to": counterparty_id,
                "amount": amount,
            })
    
    yield f"data: {json.dumps({'type': 'init', 'banks': initial_banks, 'markets': initial_markets, 'connections': initial_connections})}\n\n"
    
    print(f"[INTERACTIVE SIM] Sent init event with {len(initial_banks)} banks, {len(initial_markets)} markets")
    
    # Run simulation step by step
    for t in range(config.num_steps):
        print(f"[INTERACTIVE SIM] Starting step {t}")
        
        # Check for pause
        while ACTIVE_SIMULATION["is_paused"]:
            yield f"data: {json.dumps({'type': 'paused', 'step': t})}\n\n"
            await asyncio.sleep(0.5)
            
            # Process control commands during pause
            try:
                command = await asyncio.wait_for(control_queue.get(), timeout=0.1)
                
                if command["command"] == "resume":
                    ACTIVE_SIMULATION["is_paused"] = False
                    yield f"data: {json.dumps({'type': 'resumed', 'step': t})}\n\n"
                    
                elif command["command"] == "stop":
                    ACTIVE_SIMULATION["is_running"] = False
                    yield f"data: {json.dumps({'type': 'stopped', 'step': t})}\n\n"
                    return
                    
                elif command["command"] == "delete_bank":
                    bank_id = command["bank_id"]
                    bank = next((b for b in state.banks if b.bank_id == bank_id), None)
                    if bank:
                        bank.is_defaulted = True
                        yield f"data: {json.dumps({'type': 'bank_deleted', 'bank_id': bank_id})}\n\n"
                        
                elif command["command"] == "add_capital":
                    bank_id = command["bank_id"]
                    amount = command["amount"]
                    bank = next((b for b in state.banks if b.bank_id == bank_id), None)
                    if bank:
                        bank.balance_sheet.cash += amount
                        yield f"data: {json.dumps({'type': 'capital_added', 'bank_id': bank_id, 'amount': amount, 'new_capital': bank.balance_sheet.equity})}\n\n"
                        
            except asyncio.TimeoutError:
                continue
        
        if not ACTIVE_SIMULATION["is_running"]:
            break
            
        state.time_step = t
        state.defaults_this_step = []
        
        # Send step start event
        yield f"data: {json.dumps({'type': 'step_start', 'step': t})}\n\n"
        await asyncio.sleep(0.8)
        
        # Process each bank
        # Track market flows this step for price updates
        market_ids = list(state.markets.markets.keys())
        step_market_flows = {mid: 0.0 for mid in market_ids}
        has_markets = len(market_ids) > 0
        
        for bank_idx, bank in enumerate(state.banks):
            if bank.is_defaulted:
                continue
                
            neighbor_defaults = _count_neighbor_defaults(bank, state.banks)
            observation = bank.observe_local_state(neighbor_defaults)
            
            # Inject market availability so the ML policy knows whether markets exist
            observation["has_markets"] = has_markets
            
            # Add balance sheet details for Featherless AI prompt
            observation["investments"] = bank.balance_sheet.investments
            observation["loans_given"] = bank.balance_sheet.loans_given
            observation["borrowed"] = bank.balance_sheet.borrowed
            
            # Add market return info so policy can make profit-taking decisions
            best_market_return = 0.0
            best_market_id = None
            best_market_position = 0.0
            for mid, pos in bank.balance_sheet.investment_positions.items():
                if pos > 0 and mid in state.markets.markets:
                    mkt_return = state.markets.markets[mid].get_return()
                    if mkt_return > best_market_return:
                        best_market_return = mkt_return
                        best_market_id = mid
                        best_market_position = pos
            observation["best_market_return"] = best_market_return
            observation["best_market_position"] = best_market_position
            observation["total_invested"] = bank.balance_sheet.investments
            
            # Featherless AI is MANDATORY for every bank at every timestep
            priority = None
            if featherless_fn:
                try:
                    priority = featherless_fn(observation)
                    bank.last_priority = priority
                except Exception as e:
                    print(f"[FEATHERLESS] Error for bank {bank.bank_id}: {e}")
                    priority = None
            
            # If no Featherless client, use rule-based fallback directly
            if priority is None:
                from app.featherless.decision_engine import _rule_based_fallback, StrategicPriority as SP
                priority = _rule_based_fallback(observation)
                bank.last_priority = priority
            ml_action, reason = select_action(observation, priority)
            action = BankAction[ml_action.value]
            counterparty_id = _select_counterparty(bank, state.banks, action)
            
            # For DIVEST_MARKET: pick the market where bank has the most invested
            if action == BankAction.DIVEST_MARKET and has_markets:
                # Find the market with highest position for this bank
                best_divest_market = None
                best_divest_amount = 0.0
                for mid, pos in bank.balance_sheet.investment_positions.items():
                    if pos > best_divest_amount:
                        best_divest_amount = pos
                        best_divest_market = mid
                market_id = best_divest_market if best_divest_market else random.choice(market_ids)
            else:
                market_id = random.choice(market_ids) if has_markets else None
            
            # Fix: If lending action but no valid counterparty (e.g., only 1 bank), switch to market action
            if action in [BankAction.INCREASE_LENDING, BankAction.DECREASE_LENDING] and counterparty_id is None:
                # Check if there are any other non-defaulted banks
                other_banks = [b for b in state.banks if b.bank_id != bank.bank_id and not b.is_defaulted]
                
                if len(other_banks) == 0:
                    # Only bank in the system or all others defaulted - can't do interbank lending
                    # Switch to market investment if markets exist, otherwise hoard cash
                    if has_markets and bank.balance_sheet.cash > 30:
                        action = BankAction.INVEST_MARKET
                    else:
                        action = BankAction.HOARD_CASH
                    reason = f"No lending counterparties available - switching to {action.value}"
                    counterparty_id = None
                    print(f"[SOLO BANK FIX] Bank {bank.bank_id}: No counterparties, action changed to {action.value}")
            
            # Fix: If market action but no markets exist, switch to lending or hoard
            if action in [BankAction.INVEST_MARKET, BankAction.DIVEST_MARKET] and not has_markets:
                other_banks = [b for b in state.banks if b.bank_id != bank.bank_id and not b.is_defaulted]
                if len(other_banks) > 0 and bank.balance_sheet.cash > 15:
                    action = BankAction.INCREASE_LENDING
                    counterparty_id = _select_counterparty(bank, state.banks, action)
                else:
                    action = BankAction.HOARD_CASH
                reason = f"No markets available - switching to {action.value}"
                print(f"[NO MARKET FIX] Bank {bank.bank_id}: No markets, action changed to {action.value}")
            
            # Calculate dynamic transaction amounts using game theory principles
            ratios = bank.balance_sheet.compute_ratios()
            cash = bank.balance_sheet.cash
            equity = bank.balance_sheet.equity
            
            # Base amount with significant randomness (5-20% of cash)
            base_pct = random.uniform(0.05, 0.20)
            
            # Game theory: adapt to network state
            # More neighbors defaulted = more cautious (smaller amounts)
            caution_factor = 1.0 - (neighbor_defaults * 0.15)  # Reduce by 15% per defaulted neighbor
            caution_factor = max(0.3, caution_factor)
            
            # Risk factor from config influences transaction size
            risk_multiplier = 1.0
            if config.bank_configs and bank_idx < len(config.bank_configs):
                risk_factor = config.bank_configs[bank_idx].risk_factor
                # Higher risk = larger transactions (0.5x to 2.0x for more variance)
                risk_multiplier = 0.5 + (risk_factor * 1.5)
            
            # Add strategic randomness based on market conditions
            market_sentiment = random.uniform(0.7, 1.3)  # 70% to 130% of base
            
            # Calculate amount based on action type with game theory
            if action == BankAction.INVEST_MARKET:
                # Market investments: aggressive when others are cautious (contrarian)
                amount = cash * base_pct * risk_multiplier * market_sentiment * 1.5
            elif action == BankAction.DIVEST_MARKET:
                # Divesting: larger amounts when stressed (need liquidity)
                stress_multiplier = 2.0 if observation.get('liquidity_ratio', 1.0) < 0.25 else 1.0
                amount = cash * base_pct * stress_multiplier * 1.2
            elif action == BankAction.INCREASE_LENDING:
                # Lending: cautious in stressed environment
                amount = cash * base_pct * risk_multiplier * caution_factor * 1.3
            elif action == BankAction.DECREASE_LENDING:
                # Deleveraging: variable based on urgency
                urgency = 2.0 if observation.get('leverage', 1.0) > 3.0 else 1.0
                amount = cash * base_pct * urgency * 0.8
            else:
                # HOARD_CASH or other: minimal but still variable
                amount = cash * random.uniform(0.01, 0.05)
            
            # Add final random jitter (±20%)
            jitter = random.uniform(0.8, 1.2)
            amount = amount * jitter
            
            # Clamp to reasonable bounds (3M to 80M for more range)
            amount = max(3.0, min(80.0, amount))
            
            # Further limit by equity size to prevent over-extension
            amount = min(amount, equity * 0.4)
            
            # Log dynamic amount calculation for debugging
            if bank_idx < 3 and t == 0:  # Log first 3 banks on first step
                print(f"[DYNAMIC AMOUNT] Bank {bank.bank_id}: action={action.value}, "
                      f"cash=${cash:.1f}M, equity=${equity:.1f}M, risk_mult={risk_multiplier:.2f}, "
                      f"amount=${amount:.1f}M")
            
            # Track cash before action for logging
            cash_before = bank.balance_sheet.cash
            investments_before = bank.balance_sheet.investments
            
            # Execute action
            bank.execute_action(
                action=action,
                time_step=t,
                counterparty_id=counterparty_id,
                market_id=market_id,
                amount=amount,
                reason=reason,
            )
            
            # Log cash changes for first 3 banks on first 2 steps
            if bank_idx < 3 and t < 2:
                cash_after = bank.balance_sheet.cash
                cash_change = cash_after - cash_before
                investments_after = bank.balance_sheet.investments
                inv_change = investments_after - investments_before
                print(f"[CASH FLOW] Step {t} Bank {bank.bank_id}: {action.value} ${amount:.1f}M")
                print(f"  Cash: ${cash_before:.1f}M → ${cash_after:.1f}M (change: ${cash_change:+.1f}M)")
                print(f"  Investments: ${investments_before:.1f}M → ${investments_after:.1f}M (change: ${inv_change:+.1f}M)")
            
            # Track market flows for price updates
            if action == BankAction.INVEST_MARKET and market_id in step_market_flows:
                step_market_flows[market_id] += amount  # Positive flow (buying)
            elif action == BankAction.DIVEST_MARKET and market_id in step_market_flows:
                step_market_flows[market_id] -= amount  # Negative flow (selling)
            
            # Special handling for DIVEST_MARKET: realize gains/losses based on market price
            market_gain = 0.0
            if action == BankAction.DIVEST_MARKET and market_id in state.markets.markets:
                market = state.markets.markets[market_id]
                market_return = market.get_return()
                
                # Calculate realized gain/loss on the divested amount
                market_gain = amount * market_return
                
                # Add gain/loss to bank's cash (this is in addition to getting principal back)
                bank.balance_sheet.cash += market_gain
                
                # Update equity directly with the gain/loss
                # (equity = assets - liabilities, cash is an asset)
                
                if abs(market_gain) > 0.5:
                    gain_event = {
                        "type": "market_gain",
                        "step": t,
                        "bank_id": bank.bank_id,
                        "market_id": market_id,
                        "divested_amount": round(amount, 2),
                        "market_return": round(market_return * 100, 2),
                        "realized_gain": round(market_gain, 2),
                        "new_cash": round(bank.balance_sheet.cash, 2),
                    }
                    yield f"data: {json.dumps(gain_event)}\n\n"
            
            # Send transaction event
            transaction_event = {
                "type": "transaction",
                "step": t,
                "from_bank": bank.bank_id,
                "to_bank": counterparty_id,
                "market_id": market_id if action in [BankAction.INVEST_MARKET, BankAction.DIVEST_MARKET] else None,
                "action": action.value,
                "amount": amount,
                "reason": reason,
                "cash_before": round(cash_before, 2),
                "cash_after": round(bank.balance_sheet.cash, 2),
                "cash_change": round(bank.balance_sheet.cash - cash_before, 2),
            }
            yield f"data: {json.dumps(transaction_event)}\n\n"
            await asyncio.sleep(0.4)
        
        print(f"[INTERACTIVE SIM] Processed {len([b for b in state.banks if not b.is_defaulted])} banks at step {t}")
        
        # === AUTOMATIC PROFIT-TAKING PASS ===
        # After all bank actions, banks with highly profitable positions
        # automatically sell a portion to lock in gains (like a trailing stop)
        for bank in state.banks:
            if bank.is_defaulted or bank.balance_sheet.investments < 5:
                continue
            
            for mid, position in list(bank.balance_sheet.investment_positions.items()):
                if position < 2 or mid not in state.markets.markets:
                    continue
                
                market = state.markets.markets[mid]
                mkt_return = market.get_return()
                
                # Auto-take profits when return exceeds thresholds
                # > 10% return: sell 30-50% of position
                # > 20% return: sell 40-60% of position
                # > 30% return: sell 50-70% of position
                sell_fraction = 0.0
                if mkt_return > 0.30:
                    sell_fraction = random.uniform(0.50, 0.70)
                elif mkt_return > 0.20:
                    sell_fraction = random.uniform(0.40, 0.60)
                elif mkt_return > 0.10:
                    sell_fraction = random.uniform(0.30, 0.50)
                elif mkt_return > 0.05 and bank.risk_appetite < 0.4:
                    # Conservative banks take profits earlier
                    sell_fraction = random.uniform(0.15, 0.30)
                
                # Also sell if market is crashing (stop-loss at -10%)
                if mkt_return < -0.10 and position > 5:
                    sell_fraction = max(sell_fraction, random.uniform(0.40, 0.70))
                
                if sell_fraction > 0:
                    sell_amount = position * sell_fraction
                    sell_amount = max(2.0, min(sell_amount, position))
                    
                    # Execute the divestment
                    realized_gain = sell_amount * mkt_return
                    bank.balance_sheet.cash += sell_amount + realized_gain
                    bank.balance_sheet.investments -= sell_amount
                    bank.balance_sheet.investment_positions[mid] -= sell_amount
                    
                    # Track market flow
                    step_market_flows[mid] = step_market_flows.get(mid, 0.0) - sell_amount
                    
                    # Emit profit-taking event
                    profit_take_event = {
                        "type": "transaction",
                        "step": t,
                        "from_bank": bank.bank_id,
                        "to_bank": None,
                        "market_id": mid,
                        "action": "DIVEST_MARKET",
                        "amount": round(sell_amount, 2),
                        "reason": f"Profit-taking: {mkt_return*100:.1f}% return, sold {sell_fraction*100:.0f}%",
                        "cash_before": round(bank.balance_sheet.cash - sell_amount - realized_gain, 2),
                        "cash_after": round(bank.balance_sheet.cash, 2),
                        "cash_change": round(sell_amount + realized_gain, 2),
                    }
                    yield f"data: {json.dumps(profit_take_event)}\n\n"
                    
                    if abs(realized_gain) > 0.5:
                        gain_event = {
                            "type": "market_gain",
                            "step": t,
                            "bank_id": bank.bank_id,
                            "market_id": mid,
                            "divested_amount": round(sell_amount, 2),
                            "market_return": round(mkt_return * 100, 2),
                            "realized_gain": round(realized_gain, 2),
                            "new_cash": round(bank.balance_sheet.cash, 2),
                        }
                        yield f"data: {json.dumps(gain_event)}\n\n"
                    
                    if t < 5:
                        print(f"[PROFIT-TAKE] Step {t} Bank {bank.bank_id}: Sold ${sell_amount:.1f}M from {mid} "
                              f"(return: {mkt_return*100:.1f}%, gain: ${realized_gain:.1f}M)")
        
        # Book profits from investments (every 5 steps) — mark-to-market accounting
        if t % 5 == 0:
            for bank in state.banks:
                if not bank.is_defaulted:
                    profit = bank.book_investment_profit(state.markets.markets, t)
                    if abs(profit) > 0.1:
                        profit_event = {
                            "type": "profit_booking",
                            "step": t,
                            "bank_id": bank.bank_id,
                            "profit": round(profit, 2),
                        }
                        yield f"data: {json.dumps(profit_event)}\n\n"
        
        # Process loan interest and repayments
        for lender in state.banks:
            if lender.is_defaulted:
                continue
            
            for borrower_id, loan_amount in list(lender.balance_sheet.loan_positions.items()):
                if loan_amount <= 0:
                    continue
                    
                borrower = next((b for b in state.banks if b.bank_id == borrower_id), None)
                if not borrower or borrower.is_defaulted:
                    continue
                
                # Interest payment (5% per step on outstanding loan)
                interest = loan_amount * 0.05
                if borrower.balance_sheet.cash >= interest:
                    borrower.balance_sheet.cash -= interest
                    lender.balance_sheet.cash += interest
                    
                    interest_event = {
                        "type": "interest_payment",
                        "step": t,
                        "from_bank": borrower_id,
                        "to_bank": lender.bank_id,
                        "amount": round(interest, 2),
                        "loan_balance": round(loan_amount, 2),
                    }
                    yield f"data: {json.dumps(interest_event)}\n\n"
                
                # Loan repayment (10% of principal per step)
                repayment = min(loan_amount * 0.1, borrower.balance_sheet.cash * 0.3)
                if repayment > 0:
                    borrower.balance_sheet.cash -= repayment
                    borrower.balance_sheet.borrowed -= repayment
                    lender.balance_sheet.cash += repayment
                    lender.balance_sheet.loans_given -= repayment
                    lender.balance_sheet.loan_positions[borrower_id] -= repayment
                    
                    repayment_event = {
                        "type": "loan_repayment",
                        "step": t,
                        "from_bank": borrower_id,
                        "to_bank": lender.bank_id,
                        "amount": round(repayment, 2),
                        "remaining_balance": round(loan_amount - repayment, 2),
                    }
                    yield f"data: {json.dumps(repayment_event)}\n\n"
        
        # Check for defaults
        new_defaults = []
        for bank in state.banks:
            if not bank.is_defaulted and bank.check_default():
                new_defaults.append(bank.bank_id)
                state.defaults_this_step.append(bank.bank_id)
                
                default_event = {
                    "type": "default",
                    "step": t,
                    "bank_id": bank.bank_id,
                    "equity": bank.balance_sheet.equity,
                }
                yield f"data: {json.dumps(default_event)}\n\n"
        
        # Handle cascades
        if new_defaults:
            cascade_count = _propagate_cascades(state, t, config.verbose)
            if cascade_count > 0:
                cascade_event = {
                    "type": "cascade",
                    "step": t,
                    "initial_defaults": new_defaults,
                    "cascade_count": cascade_count,
                }
                yield f"data: {json.dumps(cascade_event)}\n\n"
        
        # === DYNAMIC RISK UPDATE ===
        # Risk factor (risk_appetite) updates each step based on financial health
        # This represents evolving default risk: bad decisions → higher risk → fewer counterparties
        for bank in state.banks:
            if bank.is_defaulted:
                continue
            ratios = bank.balance_sheet.compute_ratios()
            
            # Compute a "health score" from 0 (terrible) to 1 (excellent)
            leverage_score = max(0, 1.0 - (ratios["leverage"] / 8.0))  # 8x leverage = 0
            liquidity_score = min(1.0, ratios["liquidity_ratio"] / 0.5)  # 50% liquid = 1.0
            equity_score = min(1.0, bank.balance_sheet.equity / 100.0)  # $100M equity = 1.0
            stress_penalty = bank.observe_local_state(
                _count_neighbor_defaults(bank, state.banks)
            ).get("local_stress", 0.0)
            
            health = (leverage_score * 0.3 + liquidity_score * 0.3 + equity_score * 0.3) * (1.0 - stress_penalty * 0.5)
            health = max(0.05, min(0.95, health))
            
            # Blend current risk_appetite toward health score (gradual update, 20% per step)
            old_risk = bank.risk_appetite
            bank.risk_appetite = old_risk * 0.8 + health * 0.2
            bank.risk_appetite = max(0.05, min(0.95, bank.risk_appetite))
        
        # Apply market flows: aggregate all investment/divestment activity and update prices
        # Use the tracked flows from this step
        for market_id, market in state.markets.markets.items():
            # Get net flow from all banks' actions this step
            net_flow = step_market_flows.get(market_id, 0.0)
            
            # Apply the flow (this includes supply/demand impact + random volatility + momentum)
            market.apply_flow(net_flow)
            
            # Log significant price movements
            if len(market.price_history) >= 2:
                price_change = market.price_history[-1] - market.price_history[-2]
                price_change_pct = (price_change / market.price_history[-2]) * 100
                
                if abs(price_change_pct) > 2.0:  # Log if price moved more than 2%
                    price_move_event = {
                        "type": "market_movement",
                        "step": t,
                        "market_id": market_id,
                        "old_price": round(market.price_history[-2], 2),
                        "new_price": round(market.price, 2),
                        "change_pct": round(price_change_pct, 2),
                    }
                    yield f"data: {json.dumps(price_move_event)}\n\n"
        
        # Send step summary
        total_defaults = sum(1 for b in state.banks if b.is_defaulted)
        total_equity = sum(b.balance_sheet.equity for b in state.banks if not b.is_defaulted)
        
        bank_states = []
        for bank in state.banks:
            ratios = bank.balance_sheet.compute_ratios()
            bank_states.append({
                "bank_id": bank.bank_id,
                "capital": bank.balance_sheet.equity,
                "cash": bank.balance_sheet.cash,
                "investments": bank.balance_sheet.investments,
                "loans_given": bank.balance_sheet.loans_given,
                "borrowed": bank.balance_sheet.borrowed,
                "equity": bank.balance_sheet.equity,
                "leverage": ratios.get("leverage", 0),
                "capital_ratio": ratios.get("capital_ratio", 0),
                "liquidity_ratio": ratios.get("liquidity_ratio", 0),
                "risk_appetite": round(bank.risk_appetite, 3),
                "is_defaulted": bank.is_defaulted,
            })
        
        market_states = []
        for market_id, market in state.markets.markets.items():
            market_states.append({
                "market_id": market_id,
                "name": market.name,
                "price": market.price,
                "total_invested": market.total_invested,
                "return": market.get_return(),
            })
        
        step_summary = {
            "type": "step_end",
            "step": t,
            "total_defaults": total_defaults,
            "total_equity": total_equity,
            "bank_states": bank_states,
            "market_states": market_states,
        }
        yield f"data: {json.dumps(step_summary)}\n\n"
        
        print(f"[INTERACTIVE SIM] Completed step {t}, defaults: {total_defaults}/{config.num_banks}")
        
        if total_defaults >= config.num_banks:
            break
    
    # Cleanup
    ACTIVE_SIMULATION["state"] = None
    ACTIVE_SIMULATION["is_running"] = False
    
    final_summary = {
        "type": "complete",
        "total_steps": t + 1,
        "total_defaults": sum(1 for b in state.banks if b.is_defaulted),
        "surviving_banks": sum(1 for b in state.banks if not b.is_defaulted),
    }
    yield f"data: {json.dumps(final_summary)}\n\n"
    print(f"[INTERACTIVE SIM] Simulation complete")


@router.post("/start")
async def start_interactive_simulation(
    body: InteractiveSimulationRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Start an interactive simulation with pause/resume/modify capabilities."""
    # Log the received request for debugging
    print(f"[INTERACTIVE SIM] Request: num_banks={body.num_banks}, market_nodes={body.market_nodes}, "
          f"node_params={len(body.node_parameters) if body.node_parameters else 0}, "
          f"featherless={body.use_featherless}, game_theory={body.use_game_theory}")
    
    if ACTIVE_SIMULATION["is_running"]:
        # Force cleanup if stuck
        print("[INTERACTIVE SIM] Force stopping stuck simulation")
        ACTIVE_SIMULATION["is_running"] = False
        ACTIVE_SIMULATION["is_paused"] = False
        ACTIVE_SIMULATION["state"] = None
        # Wait a moment for cleanup
        await asyncio.sleep(0.5)
    
    # Convert node parameters to BankConfig
    bank_configs = None
    if body.node_parameters:
        from app.schemas.simulation import NodeParameters
        bank_configs = [
            BankConfig(
                initial_capital=node.get("initial_capital", 100),
                target_leverage=node.get("target_leverage", 3.0),
                risk_factor=node.get("risk_factor", 0.2),
            )
            for node in body.node_parameters
        ]
    
    # Convert market nodes to market configs
    market_configs = None
    if body.market_nodes and len(body.market_nodes) > 0:
        market_configs = [
            {
                "market_id": m.get("id", f"MARKET_{i}"),
                "name": m.get("name", f"Market {i+1}"),
                "initial_price": m.get("initial_price", 100.0),
            }
            for i, m in enumerate(body.market_nodes)
        ]
        print(f"[INTERACTIVE SIM] Received {len(market_configs)} market configs from UI")
    
    config = SimulationConfig(
        num_banks=body.num_banks,
        num_steps=body.num_steps,
        use_featherless=body.use_featherless,
        use_game_theory=body.use_game_theory,
        verbose=False,
        lending_amount=15.0,
        investment_amount=15.0,
        connection_density=body.connection_density,
        bank_configs=bank_configs,
        market_configs=market_configs,
    )
    
    # Create new control queue
    ACTIVE_SIMULATION["control_queue"] = asyncio.Queue()
    
    # Featherless AI is MANDATORY — always create the client
    from app.routers.simulation import _get_featherless_fn
    featherless_fn = _get_featherless_fn()
    if featherless_fn is None:
        print("[INTERACTIVE SIM] WARNING: Featherless client unavailable, using rule-based fallback")
    else:
        print("[INTERACTIVE SIM] Featherless AI client ready — mandatory for all banks")
    
    return StreamingResponse(
        interactive_simulation_generator(config, ACTIVE_SIMULATION["control_queue"], featherless_fn),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/control")
async def control_simulation(
    command: SimulationCommand,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Send control command to running simulation."""
    if not ACTIVE_SIMULATION["is_running"]:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    if command.command == "pause":
        ACTIVE_SIMULATION["is_paused"] = True
        return {"status": "paused"}
    
    elif command.command in ["resume", "stop", "delete_bank", "add_capital"]:
        await ACTIVE_SIMULATION["control_queue"].put({
            "command": command.command,
            "bank_id": command.bank_id,
            "amount": command.amount,
        })
        return {"status": f"{command.command} queued"}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {command.command}")


@router.get("/status")
async def get_simulation_status(
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Get current simulation status."""
    return {
        "is_running": ACTIVE_SIMULATION["is_running"],
        "is_paused": ACTIVE_SIMULATION["is_paused"],
        "current_step": ACTIVE_SIMULATION["state"].time_step if ACTIVE_SIMULATION["state"] else None,
    }


@router.post("/trigger_default")
async def trigger_default(
    command: SimulationCommand,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Manually trigger a bank default for cascade testing."""
    if not ACTIVE_SIMULATION["is_running"]:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    if not command.bank_id:
        raise HTTPException(status_code=400, detail="bank_id is required")
    
    state = ACTIVE_SIMULATION["state"]
    if not state:
        raise HTTPException(status_code=404, detail="No simulation state available")
    
    # Find the bank
    target_bank = None
    for bank in state.banks:
        if bank.bank_id == command.bank_id:
            target_bank = bank
            break
    
    if not target_bank:
        raise HTTPException(status_code=404, detail=f"Bank {command.bank_id} not found")
    
    if target_bank.is_defaulted:
        raise HTTPException(status_code=400, detail=f"Bank {command.bank_id} is already defaulted")
    
    # Force default by draining equity
    target_bank.balance_sheet.equity = -1
    target_bank.is_defaulted = True
    target_bank.default_time = state.time_step
    state.defaults_this_step.append(command.bank_id)
    
    # Trigger cascade propagation
    from app.core.simulation_v2 import _propagate_cascades
    cascade_count = _propagate_cascades(state, state.time_step, verbose=False)
    
    # Get all affected banks
    affected_banks = [command.bank_id] + state.defaults_this_step[1:]  # Initial + cascaded
    
    return {
        "status": "default_triggered",
        "bank_id": command.bank_id,
        "cascade_count": cascade_count,
        "affected_banks": affected_banks,
        "cascade_depth": state.cascade_depth,
    }

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
    connection_density: float = Field(default=0.2, ge=0, le=1)
    use_featherless: bool = Field(default=False)


async def interactive_simulation_generator(config: SimulationConfig, control_queue: asyncio.Queue, featherless_fn):
    """Generator for interactive simulation with pause/resume/modify."""
    from app.core.simulation_v2 import (
        SimulationState, create_default_markets, _create_interbank_network,
        _count_neighbor_defaults, _select_counterparty, _propagate_cascades,
        create_banks
    )
    from app.core.bank import BankAction
    from app.ml.policy import select_action
    import random
    
    GLOBAL_LEDGER.clear()
    state = SimulationState()
    state.banks = create_banks(config.num_banks, bank_configs=config.bank_configs)
    state.markets = create_default_markets()
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
        step_market_flows = {"BANK_INDEX": 0.0, "FIN_SERVICES": 0.0}
        
        for bank_idx, bank in enumerate(state.banks):
            if bank.is_defaulted:
                continue
                
            neighbor_defaults = _count_neighbor_defaults(bank, state.banks)
            observation = bank.observe_local_state(neighbor_defaults)
            priority = None
            if config.use_featherless and featherless_fn:
                try:
                    priority = featherless_fn(observation)
                    bank.last_priority = priority
                except Exception:
                    priority = None
            ml_action, reason = select_action(observation, priority)
            action = BankAction[ml_action.value]
            counterparty_id = _select_counterparty(bank, state.banks, action)
            market_id = random.choice(["BANK_INDEX", "FIN_SERVICES"])
            
            # Fix: If lending action but no valid counterparty (e.g., only 1 bank), switch to market action
            if action in [BankAction.INCREASE_LENDING, BankAction.DECREASE_LENDING] and counterparty_id is None:
                # Check if there are any other non-defaulted banks
                other_banks = [b for b in state.banks if b.bank_id != bank.bank_id and not b.is_defaulted]
                
                if len(other_banks) == 0:
                    # Only bank in the system or all others defaulted - can't do interbank lending
                    # Switch to market investment instead
                    action = BankAction.INVEST_MARKET if bank.balance_sheet.cash > 30 else BankAction.HOARD_CASH
                    reason = f"No lending counterparties available - switching to {action.value}"
                    counterparty_id = None
                    print(f"[SOLO BANK FIX] Bank {bank.bank_id}: No counterparties, action changed to {action.value}")
            
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
        
        # Book profits from investments (every 5 steps)
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
                "leverage": ratios.get("leverage", 0),
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
    
    config = SimulationConfig(
        num_banks=body.num_banks,
        num_steps=body.num_steps,
        use_featherless=body.use_featherless,
        verbose=False,
        lending_amount=15.0,
        investment_amount=15.0,
        connection_density=body.connection_density,
        bank_configs=bank_configs,
    )
    
    # Create new control queue
    ACTIVE_SIMULATION["control_queue"] = asyncio.Queue()
    
    featherless_fn = None
    if body.use_featherless:
        from app.routers.simulation import _get_featherless_fn
        featherless_fn = _get_featherless_fn()
    
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

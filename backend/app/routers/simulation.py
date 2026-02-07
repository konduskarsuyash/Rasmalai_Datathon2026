"""
Simulation API: run v2 simulation (core + config + ml + optional featherless).
"""
from typing import Optional
import json
import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core import run_simulation_v2, SimulationConfig, BankConfig, GLOBAL_LEDGER
from app.middleware.auth import get_optional_user
from app.schemas.simulation import SimulationRunRequest, SimulationRunResponse

router = APIRouter()


def _get_featherless_fn():
    """Return featherless priority function if API key is set, else None."""
    try:
        from app.config.settings import FEATHERLESS_API_KEY
        if not FEATHERLESS_API_KEY:
            return None
        from app.featherless.decision_engine import get_strategic_priority, create_featherless_client
        client = create_featherless_client()
        if client is None:
            return None

        def fn(observation):
            return get_strategic_priority(observation, client)

        return fn
    except Exception:
        return None


async def simulation_event_generator(config: SimulationConfig, featherless_fn):
    """Generator that yields simulation events in real-time."""
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
    
    # Send initial market states
    initial_markets = []
    for market_id, market in state.markets.markets.items():
        initial_markets.append({
            "id": market_id,
            "name": market.name,
            "price": market.price,
            "total_invested": market.total_invested,
        })
    
    # Send initial connections
    initial_connections = []
    for bank in state.banks:
        for counterparty_id, amount in bank.balance_sheet.loan_positions.items():
            initial_connections.append({
                "from": bank.bank_id,
                "to": counterparty_id,
                "amount": amount,
            })
    
    yield f"data: {json.dumps({'type': 'init', 'banks': initial_banks, 'markets': initial_markets, 'connections': initial_connections})}\n\n"
    
    # Run simulation step by step
    for t in range(config.num_steps):
        state.time_step = t
        state.defaults_this_step = []
        
        # Send step start event
        yield f"data: {json.dumps({'type': 'step_start', 'step': t})}\n\n"
        await asyncio.sleep(1.0)  # Increased pause between steps for better visualization
        
        # Process each bank
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
            
            # Get per-bank amounts if available
            if config.bank_configs and bank_idx < len(config.bank_configs):
                bank_config = config.bank_configs[bank_idx]
                lending_amt = 10.0  # Default
                investment_amt = 10.0
            else:
                lending_amt = config.lending_amount
                investment_amt = config.investment_amount
            
            amount = lending_amt if "LENDING" in action.value else investment_amt
            
            # Execute action
            bank.execute_action(
                action=action,
                time_step=t,
                counterparty_id=counterparty_id,
                market_id=market_id,
                amount=amount,
                reason=reason,
            )
            
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
            }
            yield f"data: {json.dumps(transaction_event)}\n\n"
            await asyncio.sleep(0.3)  # Increased pause between transactions for visibility
        
        # Check for defaults
        new_defaults = []
        for bank in state.banks:
            if not bank.is_defaulted and bank.check_default():
                new_defaults.append(bank.bank_id)
                state.defaults_this_step.append(bank.bank_id)
                
                # Send default event
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
        
        # Send step summary with detailed bank states
        total_defaults = sum(1 for b in state.banks if b.is_defaulted)
        total_equity = sum(b.balance_sheet.equity for b in state.banks if not b.is_defaulted)
        
        # Include detailed state for each bank for dashboard visualization
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
        
        # Include market states
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
        
        if total_defaults >= config.num_banks:
            break
    
    # Send completion event
    final_summary = {
        "type": "complete",
        "total_steps": t + 1,
        "total_defaults": sum(1 for b in state.banks if b.is_defaulted),
        "surviving_banks": sum(1 for b in state.banks if not b.is_defaulted),
    }
    yield f"data: {json.dumps(final_summary)}\n\n"


@router.post("/run/stream")
async def run_simulation_stream(
    body: SimulationRunRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Run simulation with real-time streaming of transactions and events.
    Uses Server-Sent Events (SSE) to stream simulation progress.
    """
    # Convert node parameters to BankConfig objects if provided
    bank_configs = None
    if body.node_parameters:
        bank_configs = [
            BankConfig(
                initial_capital=node.initial_capital,
                target_leverage=node.target_leverage,
                risk_factor=node.risk_factor,
            )
            for node in body.node_parameters
        ]
    
    config = SimulationConfig(
        num_banks=body.num_banks,
        num_steps=body.num_steps,
        use_featherless=body.use_featherless,
        use_game_theory=body.use_game_theory,
        verbose=body.verbose,
        lending_amount=body.lending_amount,
        investment_amount=body.investment_amount,
        connection_density=body.connection_density,
        bank_configs=bank_configs,
    )
    
    featherless_fn = _get_featherless_fn() if body.use_featherless else None
    
    return StreamingResponse(
        simulation_event_generator(config, featherless_fn),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/run", response_model=SimulationRunResponse)
async def run_simulation(
    body: SimulationRunRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """
    Run financial network simulation v2 (balance-sheet, ML policy, optional Featherless).
    Supports per-node parameters (capital, target leverage, risk factor) for customized simulations.
    """
    # Convert node parameters to BankConfig objects if provided
    bank_configs = None
    if body.node_parameters:
        bank_configs = [
            BankConfig(
                initial_capital=node.initial_capital,
                target_leverage=node.target_leverage,
                risk_factor=node.risk_factor,
            )
            for node in body.node_parameters
        ]
    
    config = SimulationConfig(
        num_banks=body.num_banks,
        num_steps=body.num_steps,
        use_featherless=body.use_featherless,
        use_game_theory=body.use_game_theory,
        verbose=body.verbose,
        lending_amount=body.lending_amount,
        investment_amount=body.investment_amount,
        connection_density=body.connection_density,
        bank_configs=bank_configs,
    )
    featherless_fn = _get_featherless_fn() if body.use_featherless else None
    history = run_simulation_v2(config, featherless_fn=featherless_fn)
    return SimulationRunResponse(
        summary=history["summary"],
        steps_count=len(history["steps"]),
        defaults_over_time=history["defaults_over_time"],
        total_equity_over_time=history["total_equity_over_time"],
        market_prices=history["market_prices"],
        cascade_events=history["cascade_events"],
        system_logs=history["system_logs"],
        bank_logs=history.get("bank_logs") if body.verbose else None,
    )

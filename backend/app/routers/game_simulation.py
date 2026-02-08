"""
Game-Theoretic Simulation API Router
Implements full step-based simulation lifecycle with all control endpoints
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from app.core.stateful_simulation import (
    get_simulation,
    destroy_simulation,
    StatefulSimulation,
    BankObjective,
    ActionType
)

router = APIRouter()


# ============ Request/Response Models ============

class NetworkConfig(BaseModel):
    num_banks: int = Field(20, description="Number of banks in network")
    connection_density: float = Field(0.2, description="Network connection density")


class SimulationConfig(BaseModel):
    steps: int = Field(30, description="Total simulation steps")
    use_featherless: bool = Field(False, description="Use AI strategy engine")
    verbose_logging: bool = Field(False, description="Enable verbose logs")


class MarketConfig(BaseModel):
    price_sensitivity: float = Field(0.002, description="Market price sensitivity")
    volatility: float = Field(0.03, description="Market volatility")
    momentum: float = Field(0.1, description="Price momentum factor")


class InitRequest(BaseModel):
    network: NetworkConfig
    simulation: SimulationConfig
    market: MarketConfig


class BankCreateRequest(BaseModel):
    capital: float = Field(100_000_000, description="Initial capital")
    target_leverage: float = Field(3.0, description="Target leverage ratio")
    risk_factor: float = Field(0.2, description="Risk appetite")
    interbank_rate: float = Field(0.025, description="Interbank lending rate")
    collateral_haircut: float = Field(0.15, description="Collateral haircut")
    reserve_requirement: float = Field(0.10, description="Reserve requirement")
    objective: str = Field("SURVIVAL", description="Bank objective: SURVIVAL, GROWTH, AGGRESSIVE")
    info_visibility: float = Field(0.6, description="Information visibility (0-1)")


class BankUpdateRequest(BaseModel):
    risk_factor: Optional[float] = None
    target_leverage: Optional[float] = None
    objective: Optional[str] = None


class ConnectionCreateRequest(BaseModel):
    from_bank: str = Field(..., description="Source bank ID")
    to_bank: str = Field(..., description="Target bank ID")
    type: str = Field("credit", description="Connection type: credit, lending, exposure")
    exposure: float = Field(..., description="Exposure amount")


class ActionExecuteRequest(BaseModel):
    bank_id: str
    action: str = Field(..., description="Action: INVEST_MARKET, DIVEST_MARKET, HOARD_CASH, REDUCE_LEVERAGE, LEND_INTERBANK, BORROW_INTERBANK")


class MarginCheckRequest(BaseModel):
    bank_id: str
    market_price_change: float


class CapitalInjectionRequest(BaseModel):
    bank_id: str
    amount: float


class StrategyEvaluateRequest(BaseModel):
    bank_id: str
    observed_state: Dict[str, Any]


# Global session tracking
_current_session_id: Optional[str] = None


def get_current_simulation() -> StatefulSimulation:
    """Get current active simulation or raise error"""
    global _current_session_id
    if _current_session_id is None:
        raise HTTPException(status_code=400, detail="No active simulation. Call POST /api/simulation/init first")
    return get_simulation(_current_session_id)


# ============ Simulation Control Endpoints ============

@router.post("/simulation/init")
async def initialize_simulation(req: InitRequest):
    """
    Initialize simulation context.
    Creates empty state, allocates resources, does NOT start execution.
    """
    global _current_session_id
    
    # Create new simulation
    sim = get_simulation(None)  # Creates new instance
    _current_session_id = sim.session_id
    
    # Initialize
    result = sim.initialize(
        network_config=req.network.dict(),
        simulation_config=req.simulation.dict(),
        market_config=req.market.dict()
    )
    
    return result


@router.post("/simulation/start")
async def start_simulation():
    """
    Start simulation execution.
    Locks inputs and moves state to RUNNING.
    """
    sim = get_current_simulation()
    result = sim.start()
    return result


@router.post("/simulation/pause")
async def pause_simulation():
    """Pause simulation execution"""
    sim = get_current_simulation()
    result = sim.pause()
    return result


@router.post("/simulation/resume")
async def resume_simulation():
    """Resume paused simulation"""
    sim = get_current_simulation()
    result = sim.resume()
    return result


@router.post("/simulation/stop")
async def stop_simulation():
    """
    Stop simulation and finalize metrics.
    Unlocks state.
    """
    sim = get_current_simulation()
    result = sim.stop()
    return result


@router.post("/simulation/step")
async def execute_step():
    """
    Execute single simulation step with 9-phase lifecycle.
    
    Lifecycle:
    1. step_start
    2. information_update
    3. strategy_selection
    4. action_execution
    5. margin_and_constraints
    6. settlement_and_clearing
    7. market_update
    8. contagion_check
    9. step_end
    """
    sim = get_current_simulation()
    
    try:
        result = sim.execute_step()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/simulation/destroy")
async def destroy_current_simulation():
    """Destroy current simulation session"""
    global _current_session_id
    if _current_session_id:
        destroy_simulation(_current_session_id)
        _current_session_id = None
    return {"status": "destroyed"}


# ============ Bank (Node) APIs ============

@router.post("/banks")
async def create_bank(req: BankCreateRequest):
    """Create new bank node in network"""
    sim = get_current_simulation()
    
    try:
        bank_state = sim.create_bank(
            capital=req.capital,
            target_leverage=req.target_leverage,
            risk_factor=req.risk_factor,
            interbank_rate=req.interbank_rate,
            collateral_haircut=req.collateral_haircut,
            reserve_requirement=req.reserve_requirement,
            objective=req.objective,
            info_visibility=req.info_visibility
        )
        
        return {
            "bank_id": bank_state.bank_id,
            "capital": bank_state.capital,
            "cash": bank_state.cash,
            "borrowed": bank_state.borrowed,
            "equity": bank_state.equity,
            "leverage": bank_state.leverage,
            "liquidity_ratio": bank_state.liquidity_ratio
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/banks/{bank_id}")
async def update_bank(bank_id: str, req: BankUpdateRequest):
    """Update bank parameters (runtime safe fields only)"""
    sim = get_current_simulation()
    
    try:
        updates = req.dict(exclude_none=True)
        bank_state = sim.update_bank(bank_id, **updates)
        
        return {
            "bank_id": bank_state.bank_id,
            "risk_factor": bank_state.risk_factor,
            "target_leverage": bank_state.target_leverage,
            "objective": bank_state.objective.value
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/banks/{bank_id}")
async def get_bank_state(bank_id: str):
    """Get full bank state including balance sheet"""
    sim = get_current_simulation()
    
    try:
        bank_state = sim.get_bank(bank_id)
        
        return {
            "bank_id": bank_state.bank_id,
            "capital": bank_state.capital,
            "cash": bank_state.cash,
            "investments": bank_state.investments,
            "loans_given": bank_state.loans_given,
            "borrowed": bank_state.borrowed,
            "equity": bank_state.equity,
            "leverage": bank_state.leverage,
            "liquidity_ratio": bank_state.liquidity_ratio,
            "market_exposure": bank_state.market_exposure,
            "target_leverage": bank_state.target_leverage,
            "risk_factor": bank_state.risk_factor,
            "objective": bank_state.objective.value,
            "is_defaulted": bank_state.is_defaulted,
            "default_step": bank_state.default_step
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/banks")
async def list_banks():
    """List all banks in simulation"""
    sim = get_current_simulation()
    
    return {
        "banks": [
            {
                "bank_id": bs.bank_id,
                "equity": bs.equity,
                "leverage": bs.leverage,
                "liquidity_ratio": bs.liquidity_ratio,
                "is_defaulted": bs.is_defaulted
            }
            for bs in sim.banks.values()
        ]
    }


# ============ Connection (Edge) APIs ============

@router.post("/connections")
async def create_connection(req: ConnectionCreateRequest):
    """Create network connection between banks"""
    sim = get_current_simulation()
    
    try:
        connection = sim.create_connection(
            from_bank=req.from_bank,
            to_bank=req.to_bank,
            connection_type=req.type,
            exposure=req.exposure
        )
        
        return {
            "connection_id": connection.connection_id,
            "from_bank": connection.from_bank,
            "to_bank": connection.to_bank,
            "type": connection.type,
            "exposure": connection.exposure,
            "weight": connection.weight
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/network")
async def get_network():
    """Get complete network state (nodes + edges)"""
    sim = get_current_simulation()
    return sim.get_network()


# ============ Strategy & Game Theory APIs ============

@router.post("/strategy/evaluate")
async def evaluate_strategy(req: StrategyEvaluateRequest):
    """
    Evaluate strategy for a bank based on observed state.
    Typically used for AI/Featherless testing, not during normal simulation.
    """
    sim = get_current_simulation()
    
    try:
        bank_state = sim.get_bank(req.bank_id)
        
        # Use internal strategy selection
        action = sim._select_bank_action(bank_state)
        
        return {
            "bank_id": req.bank_id,
            "chosen_action": action.value,
            "confidence": 0.75,  # Placeholder for AI confidence
            "observed_state": req.observed_state
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Action Execution APIs ============

@router.post("/actions/execute")
async def execute_action(req: ActionExecuteRequest):
    """Execute bank action manually"""
    sim = get_current_simulation()
    
    try:
        result = sim.execute_action(req.bank_id, req.action)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Margin & Clearing APIs ============

@router.post("/margin/check")
async def check_margin(req: MarginCheckRequest):
    """Check margin requirements for bank"""
    sim = get_current_simulation()
    
    try:
        bank_state = sim.get_bank(req.bank_id)
        
        variation_margin = bank_state.market_exposure * abs(req.market_price_change)
        
        return {
            "bank_id": req.bank_id,
            "market_exposure": bank_state.market_exposure,
            "price_change": req.market_price_change,
            "variation_margin": variation_margin,
            "available_cash": bank_state.cash,
            "margin_met": bank_state.cash >= variation_margin
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/margin/call")
async def issue_margin_call(bank_id: str = Body(..., embed=True)):
    """Issue margin call to bank"""
    sim = get_current_simulation()
    
    try:
        bank_state = sim.get_bank(bank_id)
        
        # Calculate required margin
        market_price_change = sum(m.momentum for m in sim.markets.values()) / len(sim.markets) if sim.markets else 0
        margin_required = bank_state.market_exposure * abs(market_price_change) * 1.1  # 10% buffer
        
        status = "PAID" if bank_state.cash >= margin_required else "UNPAID"
        
        return {
            "bank_id": bank_id,
            "margin_required": margin_required,
            "available_cash": bank_state.cash,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/liquidation/force")
async def force_liquidation(bank_id: str = Body(..., embed=True)):
    """Force liquidation of bank assets"""
    sim = get_current_simulation()
    
    try:
        bank_state = sim.get_bank(bank_id)
        
        # Force liquidate 50% of investments
        liquidation_amount = bank_state.investments * 0.5
        
        events = []
        if liquidation_amount > 0:
            sim._force_liquidation(bank_id, liquidation_amount, events)
        
        return {
            "bank_id": bank_id,
            "liquidation_amount": liquidation_amount,
            "fire_sale_discount": 0.15,
            "market_impact": -liquidation_amount * 0.0001,
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Market APIs ============

@router.get("/market")
async def get_market_state():
    """Get current market state"""
    sim = get_current_simulation()
    
    return {
        market_id: {
            "price": market.price,
            "volatility": market.volatility,
            "momentum": market.momentum,
            "net_flow": market.net_flow
        }
        for market_id, market in sim.markets.items()
    }


@router.post("/market/update")
async def update_market():
    """Manually trigger market update (internal use)"""
    sim = get_current_simulation()
    
    if sim.market_system:
        sim.market_system.daily_update()
    
    return {"status": "updated", "markets": await get_market_state()}


# ============ Default & Contagion APIs ============

@router.post("/defaults/check")
async def check_defaults():
    """Check all banks for default conditions"""
    sim = get_current_simulation()
    
    defaults = []
    for bank_id, bank_state in sim.banks.items():
        if not bank_state.is_defaulted:
            if bank_state.equity <= 0 or bank_state.liquidity_ratio < 0.05:
                defaults.append({
                    "bank_id": bank_id,
                    "equity": bank_state.equity,
                    "liquidity_ratio": bank_state.liquidity_ratio,
                    "reason": "equity_depleted" if bank_state.equity <= 0 else "liquidity_crisis"
                })
    
    return {"defaults_detected": len(defaults), "defaults": defaults}


@router.post("/cascade/propagate")
async def propagate_cascade(bank_id: str = Body(..., embed=True)):
    """Propagate default cascade from specified bank"""
    sim = get_current_simulation()
    
    try:
        events = []
        sim._propagate_cascade(bank_id, events)
        
        return {
            "source_bank": bank_id,
            "cascade_events": len(events),
            "affected_banks": [e["to_bank"] for e in events if e["type"] == "cascade"],
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Intervention APIs ============

@router.post("/intervention/add_capital")
async def add_capital_injection(req: CapitalInjectionRequest):
    """Inject capital into bank (regulatory intervention)"""
    sim = get_current_simulation()
    
    try:
        sim.add_capital_injection(req.bank_id, req.amount)
        
        bank_state = sim.get_bank(req.bank_id)
        
        return {
            "bank_id": req.bank_id,
            "injected_amount": req.amount,
            "new_capital": bank_state.capital,
            "new_equity": bank_state.equity,
            "new_cash": bank_state.cash
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/intervention/financial_crisis")
async def trigger_financial_crisis():
    """Trigger system-wide financial crisis"""
    sim = get_current_simulation()
    
    sim.trigger_financial_crisis()
    
    return {
        "status": "crisis_triggered",
        "price_shock": -0.15,
        "liquidity_drain": -0.30,
        "risk_multiplier": 1.5,
        "affected_banks": len(sim.banks)
    }


# ============ Observability APIs ============

@router.get("/events")
async def get_events():
    """Get all simulation events"""
    sim = get_current_simulation()
    return {"events": sim.get_events()}


@router.get("/metrics")
async def get_metrics():
    """Get simulation metrics summary"""
    sim = get_current_simulation()
    return sim.get_metrics()


@router.get("/simulation/status")
async def get_simulation_status():
    """Get current simulation status"""
    try:
        sim = get_current_simulation()
        return {
            "session_id": sim.session_id,
            "state": sim.state.value,
            "current_step": sim.current_step,
            "total_steps": sim.total_steps,
            "banks_count": len(sim.banks),
            "connections_count": len(sim.connections),
            "defaults": sim.metrics.get("total_defaults", 0),
            "surviving_banks": sim.metrics.get("surviving_banks", 0)
        }
    except HTTPException:
        return {
            "session_id": None,
            "state": "UNINITIALIZED",
            "message": "No active simulation"
        }

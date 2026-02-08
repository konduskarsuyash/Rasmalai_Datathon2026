"""
Layered simulation router - adds architecture visibility to existing simulation
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from app.layers.orchestration import run_layered_simulation


router = APIRouter()


class BankConfigInput(BaseModel):
    """Bank configuration"""
    initial_capital: float = Field(default=100.0, ge=10.0)
    target_leverage: float = Field(default=3.0, ge=1.0)
    risk_factor: float = Field(default=0.3, ge=0.0, le=1.0)


class LayeredSimulationRequest(BaseModel):
    """Request for simulation with layered architecture tracking"""
    num_banks: int = Field(default=20, ge=2, le=50)
    num_steps: int = Field(default=30, ge=5, le=200)
    bank_configs: Optional[List[BankConfigInput]] = None
    connection_density: float = Field(default=0.2, ge=0.0, le=1.0)
    use_featherless: bool = Field(default=False)
    shock_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    verbose: bool = Field(default=True)


@router.post("/run")
async def run_simulation_with_layers(request: LayeredSimulationRequest):
    """
    Run simulation with layered architecture visibility.
    Same simulation as /api/simulation/run but with layer execution tracking.
    """
    
    # Convert configs
    bank_configs = None
    if request.bank_configs:
        bank_configs = [bc.dict() for bc in request.bank_configs]
    
    # Run simulation
    result = run_layered_simulation(
        num_banks=request.num_banks,
        num_steps=request.num_steps,
        bank_configs=bank_configs,
        connection_density=request.connection_density,
        use_featherless=request.use_featherless,
        shock_probability=request.shock_probability,
        verbose=request.verbose
    )
    
    return {
        "success": True,
        "enhanced_with": "layered_architecture_tracking",
        **result
    }


@router.get("/architecture")
async def get_architecture_info():
    """Get information about the layered architecture"""
    return {
        "architecture": "6-Layer Financial Network Simulation",
        "description": "Modular architecture with clear separation of concerns",
        "layers": [
            {
                "id": 1,
                "name": "User / Control Layer",
                "icon": "🧍‍♂️",
                "responsibilities": [
                    "Parameter inputs (bank config, network density, volatility)",
                    "Scenario triggers (crisis, liquidity shock)",
                    "Live commands (pause, inject capital)"
                ]
            },
            {
                "id": 2,
                "name": "Simulation Orchestrator",
                "icon": "🧠",
                "responsibilities": [
                    "Advances simulation steps",
                    "Coordinates subsystem execution",
                    "Manages step lifecycle"
                ],
                "note": "Does NOT decide behavior, only coordinates"
            },
            {
                "id": 3,
                "name": "Strategy & Game Theory Engine",
                "icon": "🎯",
                "responsibilities": [
                    "Objective functions per bank",
                    "Incomplete information modeling",
                    "Belief updates and risk-adjusted payoffs",
                    "Strategic action selection"
                ],
                "highlight": "USP Layer - Competitive Advantage"
            },
            {
                "id": 4,
                "name": "Financial Network & Market Core",
                "icon": "🌐",
                "responsibilities": [
                    "Interbank network (nodes, edges, exposures)",
                    "Balance sheet engine (assets, liabilities, leverage)",
                    "Market engine (pricing, impact, volatility)"
                ],
                "flow": "Bank Actions → Cash/Loans/Investments → Market Prices"
            },
            {
                "id": 5,
                "name": "Clearing, Margin & Regulatory",
                "icon": "🏛️",
                "responsibilities": [
                    "Central Counterparty (CCP) operations",
                    "Margin calls and forced liquidation",
                    "Regulatory oversight and intervention"
                ],
                "critical_loop": "Price drop → Margin call → Asset sale → Price drop → CONTAGION"
            },
            {
                "id": 6,
                "name": "Output, Metrics & Visualization",
                "icon": "📊",
                "responsibilities": [
                    "Real-time event stream",
                    "Aggregate metrics (default rate, equity, risk)",
                    "Cascade detection",
                    "Visualization data preparation"
                ]
            }
        ],
        "feedback_arrows": [
            {"from": "Market (4)", "to": "Strategy (3)", "type": "Price signals affect decisions"},
            {"from": "Clearing (5)", "to": "Market (4)", "type": "Fire sales impact prices"},
            {"from": "Defaults (4)", "to": "Network (4)", "type": "Contagion through exposures"}
        ]
    }

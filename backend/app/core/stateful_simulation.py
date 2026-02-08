"""
Stateful Game-Theoretic Financial Simulation Manager
Implements step-by-step execution with full lifecycle control
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import random

from app.core.bank import Bank
from app.core.market import MarketSystem
from app.core.balance_sheet import BalanceSheet, GLOBAL_LEDGER


class SimulationState(str, Enum):
    """Simulation lifecycle states"""
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"


class BankObjective(str, Enum):
    """Bank decision-making objectives"""
    SURVIVAL = "SURVIVAL"
    GROWTH = "GROWTH"
    AGGRESSIVE = "AGGRESSIVE"


class ActionType(str, Enum):
    """Bank action types"""
    INVEST_MARKET = "INVEST_MARKET"
    DIVEST_MARKET = "DIVEST_MARKET"
    LEND_INTERBANK = "LEND_INTERBANK"
    BORROW_INTERBANK = "BORROW_INTERBANK"
    HOARD_CASH = "HOARD_CASH"
    REDUCE_LEVERAGE = "REDUCE_LEVERAGE"


@dataclass
class BankState:
    """Extended bank state with game-theoretic parameters"""
    bank_id: str
    capital: float
    target_leverage: float
    risk_factor: float
    
    # Extended parameters
    interbank_rate: float = 0.025
    collateral_haircut: float = 0.15
    reserve_requirement: float = 0.10
    objective: BankObjective = BankObjective.SURVIVAL
    info_visibility: float = 0.6
    
    # Calculated state
    cash: float = 0.0
    investments: float = 0.0
    loans_given: float = 0.0
    borrowed: float = 0.0
    equity: float = 0.0
    leverage: float = 0.0
    liquidity_ratio: float = 0.0
    market_exposure: float = 0.0
    
    # Status
    is_defaulted: bool = False
    default_step: Optional[int] = None
    
    # Bank instance reference
    bank: Optional[Bank] = None


@dataclass
class Connection:
    """Network connection (edge) between banks"""
    connection_id: str
    from_bank: str
    to_bank: str
    type: str  # "credit", "lending", "exposure"
    exposure: float
    weight: float = 1.0


@dataclass
class SimulationEvent:
    """Event tracking for observability"""
    step: int
    event_type: str
    bank_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketState:
    """Market state tracking"""
    market_id: str
    price: float
    volatility: float
    momentum: float
    net_flow: float = 0.0


class StatefulSimulation:
    """
    Stateful simulation manager with step-by-step execution.
    Implements the full game-theoretic financial simulation lifecycle.
    """
    
    def __init__(self):
        self.session_id: str = str(uuid.uuid4())
        self.state: SimulationState = SimulationState.UNINITIALIZED
        
        # Configuration
        self.config: Dict[str, Any] = {}
        
        # Network state
        self.banks: Dict[str, BankState] = {}
        self.connections: Dict[str, Connection] = {}
        
        # Market system
        self.markets: Dict[str, MarketState] = {}
        self.market_system: Optional[MarketSystem] = None
        
        # Simulation progress
        self.current_step: int = 0
        self.total_steps: int = 0
        
        # Event tracking
        self.events: List[SimulationEvent] = []
        
        # Metrics
        self.metrics: Dict[str, Any] = {
            "total_defaults": 0,
            "default_rate": 0.0,
            "surviving_banks": 0,
            "total_equity": 0.0,
            "cascade_events": 0,
            "system_collapsed": False
        }
    
    def initialize(self, network_config: Dict, simulation_config: Dict, market_config: Dict):
        """
        Initialize simulation context without starting execution.
        Creates empty state and allocates resources.
        """
        if self.state != SimulationState.UNINITIALIZED:
            raise ValueError(f"Cannot initialize from state {self.state}")
        
        self.config = {
            "network": network_config,
            "simulation": simulation_config,
            "market": market_config
        }
        
        # Store configuration
        self.total_steps = simulation_config.get("steps", 30)
        
        # Initialize market system
        price_sensitivity = market_config.get("price_sensitivity", 0.002)
        volatility = market_config.get("volatility", 0.03)
        momentum = market_config.get("momentum", 0.1)
        
        self.market_system = MarketSystem(
            price_sensitivity=price_sensitivity,
            volatility=volatility,
            momentum=momentum
        )
        
        # Initialize market states
        for market_id in ["BANK_INDEX", "FIN_SERVICES", "EQUITY_MARKET"]:
            self.markets[market_id] = MarketState(
                market_id=market_id,
                price=100.0,
                volatility=volatility,
                momentum=0.0
            )
        
        # Reset step counter
        self.current_step = 0
        
        # Add initialization event
        self.events.append(SimulationEvent(
            step=0,
            event_type="init",
            data={"session_id": self.session_id}
        ))
        
        self.state = SimulationState.INITIALIZED
        
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "total_steps": self.total_steps,
            "banks_count": len(self.banks)
        }
    
    def create_bank(self, capital: float, target_leverage: float, risk_factor: float,
                   interbank_rate: float = 0.025, collateral_haircut: float = 0.15,
                   reserve_requirement: float = 0.10, objective: str = "SURVIVAL",
                   info_visibility: float = 0.6) -> BankState:
        """Create a new bank node"""
        if self.state == SimulationState.RUNNING:
            raise ValueError("Cannot add banks while simulation is running")
        
        bank_id = f"BANK_{len(self.banks) + 1}"
        
        # Calculate initial balance sheet
        borrowed = capital * target_leverage
        cash = capital + borrowed * 0.5
        
        # Create Bank instance
        bank = Bank(
            bank_id=bank_id,
            initial_capital=capital,
            target_leverage=target_leverage,
            risk_factor=risk_factor,
            market_system=self.market_system
        )
        
        bank_state = BankState(
            bank_id=bank_id,
            capital=capital,
            target_leverage=target_leverage,
            risk_factor=risk_factor,
            interbank_rate=interbank_rate,
            collateral_haircut=collateral_haircut,
            reserve_requirement=reserve_requirement,
            objective=BankObjective(objective),
            info_visibility=info_visibility,
            cash=cash,
            investments=0.0,
            loans_given=0.0,
            borrowed=borrowed,
            equity=capital,
            leverage=target_leverage,
            liquidity_ratio=cash / (cash + borrowed) if (cash + borrowed) > 0 else 0.0,
            market_exposure=0.0,
            bank=bank
        )
        
        self.banks[bank_id] = bank_state
        
        return bank_state
    
    def update_bank(self, bank_id: str, **kwargs) -> BankState:
        """Update bank parameters (runtime safe fields only)"""
        if bank_id not in self.banks:
            raise ValueError(f"Bank {bank_id} not found")
        
        bank_state = self.banks[bank_id]
        
        # Only allow safe updates
        allowed_fields = {"risk_factor", "target_leverage", "objective"}
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == "objective":
                    setattr(bank_state, key, BankObjective(value))
                else:
                    setattr(bank_state, key, value)
        
        return bank_state
    
    def get_bank(self, bank_id: str) -> BankState:
        """Get full bank state"""
        if bank_id not in self.banks:
            raise ValueError(f"Bank {bank_id} not found")
        return self.banks[bank_id]
    
    def create_connection(self, from_bank: str, to_bank: str, 
                         connection_type: str, exposure: float) -> Connection:
        """Create network connection between banks"""
        if from_bank not in self.banks or to_bank not in self.banks:
            raise ValueError("Both banks must exist")
        
        connection_id = f"CONN_{from_bank}_{to_bank}"
        
        # Calculate weight based on exposure and risk
        from_risk = self.banks[from_bank].risk_factor
        weight = exposure * (1 + from_risk)
        
        connection = Connection(
            connection_id=connection_id,
            from_bank=from_bank,
            to_bank=to_bank,
            type=connection_type,
            exposure=exposure,
            weight=weight
        )
        
        self.connections[connection_id] = connection
        
        return connection
    
    def get_network(self) -> Dict[str, Any]:
        """Get complete network state"""
        return {
            "nodes": [
                {
                    "id": bs.bank_id,
                    "capital": bs.capital,
                    "equity": bs.equity,
                    "leverage": bs.leverage,
                    "liquidity_ratio": bs.liquidity_ratio,
                    "is_defaulted": bs.is_defaulted
                }
                for bs in self.banks.values()
            ],
            "edges": [
                {
                    "id": c.connection_id,
                    "from": c.from_bank,
                    "to": c.to_bank,
                    "type": c.type,
                    "exposure": c.exposure,
                    "weight": c.weight
                }
                for c in self.connections.values()
            ]
        }
    
    def start(self):
        """Start simulation - locks inputs and begins execution"""
        if self.state != SimulationState.INITIALIZED:
            raise ValueError(f"Cannot start from state {self.state}")
        
        self.state = SimulationState.RUNNING
        
        self.events.append(SimulationEvent(
            step=self.current_step,
            event_type="start",
            data={"banks_count": len(self.banks)}
        ))
        
        return {"state": self.state.value, "current_step": self.current_step}
    
    def pause(self):
        """Pause execution"""
        if self.state != SimulationState.RUNNING:
            raise ValueError(f"Cannot pause from state {self.state}")
        
        self.state = SimulationState.PAUSED
        return {"state": self.state.value, "current_step": self.current_step}
    
    def resume(self):
        """Resume execution"""
        if self.state != SimulationState.PAUSED:
            raise ValueError(f"Cannot resume from state {self.state}")
        
        self.state = SimulationState.RUNNING
        return {"state": self.state.value, "current_step": self.current_step}
    
    def stop(self):
        """Stop and finalize simulation"""
        if self.state not in [SimulationState.RUNNING, SimulationState.PAUSED]:
            raise ValueError(f"Cannot stop from state {self.state}")
        
        self.state = SimulationState.STOPPED
        self._finalize_metrics()
        
        return {
            "state": self.state.value,
            "total_steps_executed": self.current_step,
            "metrics": self.metrics
        }
    
    def execute_step(self) -> Dict[str, Any]:
        """
        Execute single simulation step with full 9-phase lifecycle.
        
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
        if self.state != SimulationState.RUNNING:
            raise ValueError(f"Cannot execute step from state {self.state}")
        
        if self.current_step >= self.total_steps:
            self.state = SimulationState.COMPLETED
            return {"status": "completed", "step": self.current_step}
        
        self.current_step += 1
        step_events = []
        defaults_this_step = []
        
        # Phase 1: step_start
        self._phase_step_start(step_events)
        
        # Phase 2: information_update
        self._phase_information_update(step_events)
        
        # Phase 3: strategy_selection
        strategies = self._phase_strategy_selection(step_events)
        
        # Phase 4: action_execution
        self._phase_action_execution(strategies, step_events)
        
        # Phase 5: margin_and_constraints
        margin_calls = self._phase_margin_and_constraints(step_events)
        
        # Phase 6: settlement_and_clearing
        self._phase_settlement_and_clearing(margin_calls, step_events)
        
        # Phase 7: market_update
        self._phase_market_update(step_events)
        
        # Phase 8: contagion_check
        defaults_this_step = self._phase_contagion_check(step_events)
        
        # Phase 9: step_end
        self._phase_step_end(step_events)
        
        # Calculate system liquidity
        system_liquidity = self._calculate_system_liquidity()
        
        return {
            "step": self.current_step,
            "events": [e["type"] for e in step_events],
            "defaults": defaults_this_step,
            "system_liquidity": system_liquidity,
            "state": self.state.value
        }
    
    # Step lifecycle phases
    
    def _phase_step_start(self, events: List):
        """Phase 1: Initialize step"""
        events.append({"type": "step_start", "step": self.current_step})
    
    def _phase_information_update(self, events: List):
        """Phase 2: Update visible information for all banks"""
        for bank_state in self.banks.values():
            if bank_state.is_defaulted:
                continue
            
            # Update bank's view of network state
            # Based on info_visibility parameter
            pass
    
    def _phase_strategy_selection(self, events: List) -> Dict[str, ActionType]:
        """Phase 3: Each bank selects strategy"""
        strategies = {}
        
        for bank_id, bank_state in self.banks.items():
            if bank_state.is_defaulted:
                continue
            
            # Select action based on objective and observed state
            action = self._select_bank_action(bank_state)
            strategies[bank_id] = action
        
        return strategies
    
    def _phase_action_execution(self, strategies: Dict[str, ActionType], events: List):
        """Phase 4: Execute selected actions"""
        for bank_id, action in strategies.items():
            bank_state = self.banks[bank_id]
            
            result = self.execute_action(bank_id, action.value)
            
            events.append({
                "type": "action_execution",
                "bank_id": bank_id,
                "action": action.value,
                "amount": result.get("amount", 0)
            })
    
    def _phase_margin_and_constraints(self, events: List) -> List[Dict]:
        """Phase 5: Check margin requirements and constraints"""
        margin_calls = []
        
        for bank_id, bank_state in self.banks.items():
            if bank_state.is_defaulted:
                continue
            
            # Check if bank meets margin requirements
            if bank_state.market_exposure > 0:
                # Calculate required margin
                market_price_change = sum(m.momentum for m in self.markets.values()) / len(self.markets)
                variation_margin = bank_state.market_exposure * abs(market_price_change)
                
                if variation_margin > bank_state.cash * 0.1:
                    margin_calls.append({
                        "bank_id": bank_id,
                        "margin_required": variation_margin,
                        "status": "UNPAID"
                    })
                    
                    events.append({
                        "type": "margin_call",
                        "bank_id": bank_id,
                        "amount": variation_margin
                    })
        
        return margin_calls
    
    def _phase_settlement_and_clearing(self, margin_calls: List[Dict], events: List):
        """Phase 6: Settle transactions and clear margin calls"""
        for margin_call in margin_calls:
            bank_id = margin_call["bank_id"]
            bank_state = self.banks[bank_id]
            margin_required = margin_call["margin_required"]
            
            if bank_state.cash < margin_required:
                # Forced liquidation
                liquidation_amount = min(bank_state.investments, margin_required * 1.2)
                
                if liquidation_amount > 0:
                    self._force_liquidation(bank_id, liquidation_amount, events)
    
    def _phase_market_update(self, events: List):
        """Phase 7: Update market prices based on flows"""
        if self.market_system:
            # Calculate net market flow
            net_flow = sum(
                bs.market_exposure * (1 if not bs.is_defaulted else -1)
                for bs in self.banks.values()
            )
            
            # Update prices
            self.market_system.daily_update()
            
            for market_id, market_state in self.markets.items():
                market_state.net_flow = net_flow
                market_state.momentum = self.market_system.momentum
    
    def _phase_contagion_check(self, events: List) -> List[str]:
        """Phase 8: Check for defaults and propagate contagion"""
        defaults = []
        
        for bank_id, bank_state in self.banks.items():
            if bank_state.is_defaulted:
                continue
            
            # Check default condition
            if bank_state.equity <= 0 or bank_state.liquidity_ratio < 0.05:
                bank_state.is_defaulted = True
                bank_state.default_step = self.current_step
                defaults.append(bank_id)
                
                self.metrics["total_defaults"] += 1
                
                events.append({
                    "type": "default",
                    "bank_id": bank_id,
                    "equity": bank_state.equity,
                    "liquidity": bank_state.liquidity_ratio
                })
                
                # Propagate contagion
                self._propagate_cascade(bank_id, events)
        
        return defaults
    
    def _phase_step_end(self, events: List):
        """Phase 9: Finalize step and update metrics"""
        # Update metrics
        surviving_banks = sum(1 for bs in self.banks.values() if not bs.is_defaulted)
        total_equity = sum(bs.equity for bs in self.banks.values() if not bs.is_defaulted)
        
        self.metrics["surviving_banks"] = surviving_banks
        self.metrics["total_equity"] = total_equity
        self.metrics["default_rate"] = self.metrics["total_defaults"] / len(self.banks) if self.banks else 0.0
        
        if surviving_banks < len(self.banks) * 0.3:
            self.metrics["system_collapsed"] = True
        
        events.append({"type": "step_end", "step": self.current_step})
    
    # Helper methods
    
    def _select_bank_action(self, bank_state: BankState) -> ActionType:
        """Select action based on bank objective and state"""
        if bank_state.liquidity_ratio < 0.2:
            return ActionType.HOARD_CASH
        elif bank_state.objective == BankObjective.SURVIVAL:
            if bank_state.leverage > bank_state.target_leverage * 1.1:
                return ActionType.REDUCE_LEVERAGE
            else:
                return ActionType.HOARD_CASH
        elif bank_state.objective == BankObjective.GROWTH:
            return ActionType.INVEST_MARKET if random.random() > 0.5 else ActionType.LEND_INTERBANK
        elif bank_state.objective == BankObjective.AGGRESSIVE:
            return ActionType.INVEST_MARKET
        else:
            return ActionType.HOARD_CASH
    
    def execute_action(self, bank_id: str, action: str) -> Dict[str, Any]:
        """Execute bank action"""
        bank_state = self.banks[bank_id]
        
        if action == "INVEST_MARKET":
            amount = bank_state.cash * 0.096 * (1 + bank_state.risk_factor)
            amount = min(amount, bank_state.cash)
            
            if amount > 0:
                bank_state.cash -= amount
                bank_state.investments += amount
                bank_state.market_exposure += amount
                
                # Update bank instance
                if bank_state.bank and self.market_system:
                    bank_state.bank.invest_in_market(amount, self.market_system)
            
            return {"amount": amount, "new_cash": bank_state.cash}
        
        elif action == "DIVEST_MARKET":
            amount = bank_state.investments * 0.1
            amount = min(amount, bank_state.investments)
            
            if amount > 0:
                bank_state.investments -= amount
                bank_state.cash += amount * 0.98  # 2% slippage
                bank_state.market_exposure -= amount
            
            return {"amount": amount, "new_cash": bank_state.cash}
        
        elif action == "HOARD_CASH":
            # Do nothing, preserve liquidity
            return {"amount": 0, "new_cash": bank_state.cash}
        
        elif action == "REDUCE_LEVERAGE":
            # Pay down debt
            paydown = min(bank_state.cash * 0.1, bank_state.borrowed * 0.05)
            if paydown > 0:
                bank_state.cash -= paydown
                bank_state.borrowed -= paydown
                bank_state.leverage = bank_state.borrowed / bank_state.equity if bank_state.equity > 0 else 0
            
            return {"amount": paydown, "new_cash": bank_state.cash}
        
        else:
            return {"amount": 0, "new_cash": bank_state.cash}
    
    def _force_liquidation(self, bank_id: str, amount: float, events: List):
        """Force liquidation of bank assets"""
        bank_state = self.banks[bank_id]
        
        liquidated = min(amount, bank_state.investments)
        
        if liquidated > 0:
            bank_state.investments -= liquidated
            bank_state.cash += liquidated * 0.85  # 15% fire sale discount
            bank_state.market_exposure -= liquidated
            
            # Market impact
            if self.market_system:
                impact = -liquidated * 0.0001
                self.market_system.momentum += impact
            
            events.append({
                "type": "forced_liquidation",
                "bank_id": bank_id,
                "amount": liquidated
            })
            
            self.metrics["cascade_events"] += 1
    
    def _propagate_cascade(self, defaulted_bank_id: str, events: List):
        """Propagate default contagion through network"""
        # Find connections where defaulted bank is lender
        for conn in self.connections.values():
            if conn.from_bank == defaulted_bank_id:
                # Reduce counterparty liquidity
                target_bank = self.banks[conn.to_bank]
                if not target_bank.is_defaulted:
                    liquidity_hit = conn.exposure * 0.5
                    target_bank.cash -= min(liquidity_hit, target_bank.cash * 0.3)
                    target_bank.liquidity_ratio = target_bank.cash / (target_bank.cash + target_bank.borrowed) if (target_bank.cash + target_bank.borrowed) > 0 else 0
                    
                    events.append({
                        "type": "cascade",
                        "from_bank": defaulted_bank_id,
                        "to_bank": target_bank.bank_id,
                        "impact": liquidity_hit
                    })
    
    def _calculate_system_liquidity(self) -> float:
        """Calculate aggregate system liquidity"""
        if not self.banks:
            return 0.0
        
        total_liquid = sum(bs.cash for bs in self.banks.values() if not bs.is_defaulted)
        total_assets = sum(bs.cash + bs.investments for bs in self.banks.values() if not bs.is_defaulted)
        
        return total_liquid / total_assets if total_assets > 0 else 0.0
    
    def _finalize_metrics(self):
        """Finalize simulation metrics"""
        self.metrics["surviving_banks"] = sum(1 for bs in self.banks.values() if not bs.is_defaulted)
        self.metrics["total_equity"] = sum(bs.equity for bs in self.banks.values() if not bs.is_defaulted)
        self.metrics["default_rate"] = self.metrics["total_defaults"] / len(self.banks) if self.banks else 0.0
    
    def add_capital_injection(self, bank_id: str, amount: float):
        """Inject capital into bank (intervention)"""
        if bank_id not in self.banks:
            raise ValueError(f"Bank {bank_id} not found")
        
        bank_state = self.banks[bank_id]
        bank_state.cash += amount
        bank_state.equity += amount
        bank_state.capital += amount
        
        self.events.append(SimulationEvent(
            step=self.current_step,
            event_type="capital_injection",
            bank_id=bank_id,
            data={"amount": amount}
        ))
    
    def trigger_financial_crisis(self):
        """Trigger system-wide financial crisis"""
        # Price shock
        if self.market_system:
            self.market_system.momentum -= 0.15
        
        for market in self.markets.values():
            market.price *= 0.85
            market.momentum -= 0.15
        
        # Liquidity drain
        for bank_state in self.banks.values():
            if not bank_state.is_defaulted:
                bank_state.cash *= 0.7
                bank_state.risk_factor *= 1.5
        
        self.events.append(SimulationEvent(
            step=self.current_step,
            event_type="financial_crisis",
            data={"trigger": "manual"}
        ))
    
    def get_events(self) -> List[Dict]:
        """Get all simulation events"""
        return [
            {
                "step": e.step,
                "type": e.event_type,
                "bank_id": e.bank_id,
                "data": e.data,
                "timestamp": e.timestamp.isoformat()
            }
            for e in self.events
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get simulation metrics"""
        return self.metrics


# Global simulation instance manager
_simulation_instances: Dict[str, StatefulSimulation] = {}


def get_simulation(session_id: Optional[str] = None) -> StatefulSimulation:
    """Get or create simulation instance"""
    if session_id is None:
        # Create new simulation
        sim = StatefulSimulation()
        _simulation_instances[sim.session_id] = sim
        return sim
    
    if session_id not in _simulation_instances:
        raise ValueError(f"Simulation session {session_id} not found")
    
    return _simulation_instances[session_id]


def destroy_simulation(session_id: str):
    """Destroy simulation instance"""
    if session_id in _simulation_instances:
        del _simulation_instances[session_id]

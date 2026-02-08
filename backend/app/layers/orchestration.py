"""
Layered Architecture Orchestration
Wraps existing simulation_v2 to provide layer visibility and execution tracking
"""
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from app.core.simulation_v2 import run_simulation_v2, SimulationConfig


class Layer(Enum):
    """Execution layers"""
    USER_CONTROL = 1
    ORCHESTRATOR = 2
    STRATEGY = 3
    NETWORK = 4
    CLEARING = 5
    OUTPUT = 6


@dataclass
class LayerExecution:
    """Track execution of a specific layer"""
    layer: Layer
    start_time: float
    end_time: Optional[float] = None
    actions: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class StepExecution:
    """Track execution of a simulation step through all layers"""
    step_number: int
    layer_executions: Dict[Layer, LayerExecution] = field(default_factory=dict)
    total_start: float = 0.0
    total_end: float = 0.0
    
    @property
    def total_duration(self) -> float:
        if self.total_end > 0:
            return self.total_end - self.total_start
        return 0.0


class LayeredSimulationOrchestrator:
    """
    Orchestrates simulation with layer tracking.
    Wraps existing simulation_v2 without modifying it.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.step_executions: List[StepExecution] = []
        self.current_step: Optional[StepExecution] = None
        
    def run(self, featherless_fn: Optional[Callable] = None) -> Dict:
        """Run simulation with layer tracking"""
        
        # Layer 1: User Control - Configuration
        layer1_exec = LayerExecution(Layer.USER_CONTROL, time.time())
        layer1_exec.actions.append(f"Configured {self.config.num_banks} banks")
        layer1_exec.actions.append(f"Network density: {self.config.connection_density}")
        layer1_exec.actions.append(f"Simulation steps: {self.config.num_steps}")
        layer1_exec.end_time = time.time()
        
        # Layer 2: Orchestrator - Initialize
        layer2_exec = LayerExecution(Layer.ORCHESTRATOR, time.time())
        layer2_exec.actions.append("Starting simulation orchestration")
        
        # Run actual simulation (layers 3-6 happen inside)
        result = run_simulation_v2(self.config, featherless_fn)
        
        layer2_exec.actions.append(f"Completed {result.get('steps_count', 0)} steps")
        layer2_exec.end_time = time.time()
        
        # Layer 6: Output - Format results
        layer6_exec = LayerExecution(Layer.OUTPUT, time.time())
        layer6_exec.actions.append(f"Generated metrics for {len(result.get('steps', []))} steps")
        layer6_exec.actions.append(f"Defaults: {result['summary'].get('default_rate', 0):.2%}")
        layer6_exec.end_time = time.time()
        
        # Add layer execution info to result
        result['layer_execution'] = {
            'layer_1_control': {
                'duration_ms': layer1_exec.duration * 1000,
                'actions': layer1_exec.actions
            },
            'layer_2_orchestrator': {
                'duration_ms': layer2_exec.duration * 1000,
                'actions': layer2_exec.actions
            },
            'layer_6_output': {
                'duration_ms': layer6_exec.duration * 1000,
                'actions': layer6_exec.actions
            }
        }
        
        # Add architecture metadata
        result['architecture'] = {
            'type': 'layered',
            'layers': [
                {
                    'id': 1,
                    'name': 'User/Control Layer',
                    'description': 'Parameter inputs and configuration',
                    'icon': '🧍‍♂️'
                },
                {
                    'id': 2,
                    'name': 'Simulation Orchestrator',
                    'description': 'Step coordination and timing',
                    'icon': '🧠'
                },
                {
                    'id': 3,
                    'name': 'Strategy & Game Theory',
                    'description': 'AI decision making with incomplete information',
                    'icon': '🎯'
                },
                {
                    'id': 4,
                    'name': 'Financial Network & Markets',
                    'description': 'Interbank lending, balance sheets, market execution',
                    'icon': '🌐'
                },
                {
                    'id': 5,
                    'name': 'Clearing & Regulatory',
                    'description': 'Margin calls, liquidation, fire-sale feedback',
                    'icon': '🏛️'
                },
                {
                    'id': 6,
                    'name': 'Output & Metrics',
                    'description': 'Metrics calculation and visualization',
                    'icon': '📊'
                }
            ],
            'feedback_loops': [
                'Market → Strategy (Layer 4 → 3)',
                'Clearing → Market (Layer 5 → 4)',
                'Defaults → Network (Layer 4 → 4)'
            ]
        }
        
        return result


def run_layered_simulation(
    num_banks: int = 20,
    num_steps: int = 30,
    bank_configs: Optional[list] = None,
    connection_density: float = 0.2,
    use_featherless: bool = False,
    **kwargs
) -> Dict:
    """
    Convenience function to run simulation with layered architecture tracking.
    This wraps the existing simulation without modifying it.
    """
    from app.core.simulation_v2 import BankConfig
    
    # Convert bank configs if provided
    configs = None
    if bank_configs:
        configs = [
            BankConfig(
                initial_capital=bc.get('initial_capital', 100.0),
                target_leverage=bc.get('target_leverage', 3.0),
                risk_factor=bc.get('risk_factor', 0.3)
            )
            for bc in bank_configs
        ]
    
    # Create config
    config = SimulationConfig(
        num_banks=num_banks,
        num_steps=num_steps,
        bank_configs=configs,
        connection_density=connection_density,
        use_featherless=use_featherless,
        **kwargs
    )
    
    # Run with orchestration
    orchestrator = LayeredSimulationOrchestrator(config)
    return orchestrator.run()

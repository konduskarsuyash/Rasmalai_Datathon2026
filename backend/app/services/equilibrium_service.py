"""
Equilibrium Engine: Nash via fictitious play using core_implementation.GameEngine, FinancialAgent.
"""
from core_implementation import (
    FinancialNetwork,
    FinancialAgent,
    GameEngine,
    ContagionEngine,
)

from .network_service import NetworkService


class EquilibriumService:
    @staticmethod
    def compute_equilibrium(
        network_id: str,
        max_iterations: int = 1000,
        convergence_threshold: float = 1e-3,
        analyze_stability: bool = True,
    ) -> dict:
        net = NetworkService.get_network(network_id)
        if net is None:
            raise ValueError(f"Network not found: {network_id}")

        agents = [
            FinancialAgent(inst, net)
            for inst in net.institutions.values()
        ]
        engine = GameEngine(net, agents)

        equilibrium = engine.find_nash_equilibrium_fictitious_play(
            max_iterations=max_iterations,
            convergence_threshold=convergence_threshold,
        )

        # Serialize strategies for JSON
        equilibrium_serialized = {}
        for agent_id, strategy in equilibrium.items():
            equilibrium_serialized[agent_id] = {
                "lending_limits": strategy.lending_limits,
                "margin_requirements": strategy.margin_requirements,
                "interest_rates": strategy.interest_rates,
            }

        out = {
            "converged": True,
            "equilibrium": equilibrium_serialized,
        }

        if analyze_stability:
            stability = engine.analyze_equilibrium_stability(equilibrium)
            # Ensure JSON-serializable (e.g. numpy floats -> Python float)
            dev = stability["deviation_impacts"]
            out["stability"] = {
                "is_stable": bool(stability["is_stable"]),
                "deviation_impacts": {k: float(v) for k, v in dev.items()},
            }

        return out

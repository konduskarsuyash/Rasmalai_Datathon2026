"""
Contagion Engine: DebtRank and threshold cascade using core_implementation.ContagionEngine.
"""
from core_implementation import ContagionEngine

from .network_service import NetworkService


class ContagionService:
    @staticmethod
    def run_debtrank(network_id: str, initial_shock: dict | None, max_iterations: int) -> dict:
        net = NetworkService.get_network(network_id)
        if net is None:
            raise ValueError(f"Network not found: {network_id}")
        engine = ContagionEngine(net)
        debtrank = engine.compute_debtrank(
            initial_shock=initial_shock or None,
            max_iterations=max_iterations,
        )
        dr_values = list(debtrank.values())
        return {
            "debtrank": debtrank,
            "max_debtrank": max(dr_values) if dr_values else 0.0,
            "systemic_risk": sum(dr_values),
        }

    @staticmethod
    def run_threshold_cascade(
        network_id: str,
        initial_defaults: list[str],
        threshold: float,
    ) -> dict:
        net = NetworkService.get_network(network_id)
        if net is None:
            raise ValueError(f"Network not found: {network_id}")
        engine = ContagionEngine(net)
        return engine.simulate_threshold_contagion(
            initial_defaults=initial_defaults,
            threshold=threshold,
        )

    @staticmethod
    def run_stress_test(network_id: str, scenarios: list[dict]) -> list[dict]:
        net = NetworkService.get_network(network_id)
        if net is None:
            raise ValueError(f"Network not found: {network_id}")
        engine = ContagionEngine(net)
        return engine.stress_test(scenarios)

"""
Experiment runner for the financial network simulation.
Runs various scenarios to analyze system behavior.
"""
import copy
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.network import create_financial_network, get_network_stats, identify_systemically_important
from core.agent import FinancialAgent
from core.simulation import run_simulation, run_comparative_simulation
from core.shock import targeted_attack, compute_systemic_risk_contribution
from utils.metrics import compute_all_metrics, compute_risk_indicators, generate_report, plot_simulation_results
from config.settings import NUM_AGENTS, TIME_STEPS, FEATHERLESS_AGENT_RATIO


def run_experiment_suite(
    llm_decision_fn=None,
    output_dir: str = "experiment_results",
    verbose: bool = True
) -> Dict:
    """
    Run a comprehensive suite of experiments.
    
    Experiments:
    1. Baseline simulation with and without LLM
    2. Varying LLM agent ratios
    3. Targeted attack resilience
    4. Network size sensitivity
    
    Args:
        llm_decision_fn: Function to make LLM decisions
        output_dir: Directory to save results
        verbose: Whether to print progress
        
    Returns:
        Dictionary with all experiment results
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "experiments": {}
    }
    
    if verbose:
        print("=" * 60)
        print("🔬 FINANCIAL NETWORK EXPERIMENT SUITE")
        print("=" * 60)
    
    # Experiment 1: Baseline comparison
    if verbose:
        print("\n📊 Experiment 1: Baseline LLM vs Rule-Based Comparison")
        print("-" * 40)
    
    results["experiments"]["baseline"] = run_baseline_experiment(
        llm_decision_fn, verbose
    )
    
    # Experiment 2: LLM ratio sensitivity
    if verbose:
        print("\n📊 Experiment 2: LLM Agent Ratio Sensitivity")
        print("-" * 40)
    
    results["experiments"]["llm_ratio"] = run_llm_ratio_experiment(
        llm_decision_fn, verbose
    )
    
    # Experiment 3: Targeted attack resilience
    if verbose:
        print("\n📊 Experiment 3: Targeted Attack Resilience")
        print("-" * 40)
    
    results["experiments"]["attack_resilience"] = run_attack_experiment(
        llm_decision_fn, verbose
    )
    
    # Experiment 4: Network topology analysis
    if verbose:
        print("\n📊 Experiment 4: Network Topology Analysis")
        print("-" * 40)
    
    results["experiments"]["topology"] = run_topology_experiment(verbose)
    
    # Save results
    results_file = output_path / "experiment_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    if verbose:
        print(f"\n✅ Results saved to {results_file}")
    
    return results


def run_baseline_experiment(llm_decision_fn=None, verbose=True) -> Dict:
    """
    Run baseline comparison between LLM and rule-based agents.
    """
    G = create_financial_network(NUM_AGENTS)
    
    # Create agents with LLM capability
    agents = [
        FinancialAgent(i, use_llm=(i < NUM_AGENTS * FEATHERLESS_AGENT_RATIO))
        for i in G.nodes
    ]
    
    # Run with LLM (if available)
    G_llm = copy.deepcopy(G)
    history_llm = run_simulation(
        G_llm, agents, llm_decision_fn, TIME_STEPS,
        enable_shocks=True
    )
    
    # Run without LLM
    for agent in agents:
        agent.credit_strategy = "MEDIUM"
        agent.margin_strategy = "NORMAL"
    
    G_rule = copy.deepcopy(G)
    history_rule = run_simulation(
        G_rule, agents, None, TIME_STEPS,
        enable_shocks=True
    )
    
    metrics_llm = compute_all_metrics(G_llm, history_llm)
    metrics_rule = compute_all_metrics(G_rule, history_rule)
    
    if verbose:
        print(f"  With LLM:    {metrics_llm['total_defaults']} defaults, "
              f"utility={metrics_llm.get('final_systemic_utility', 0):.2f}")
        print(f"  Rule-based:  {metrics_rule['total_defaults']} defaults, "
              f"utility={metrics_rule.get('final_systemic_utility', 0):.2f}")
    
    return {
        "with_llm": {
            "history_summary": history_llm["summary"],
            "metrics": metrics_llm
        },
        "without_llm": {
            "history_summary": history_rule["summary"],
            "metrics": metrics_rule
        }
    }


def run_llm_ratio_experiment(llm_decision_fn=None, verbose=True) -> Dict:
    """
    Analyze how varying the proportion of LLM agents affects outcomes.
    """
    ratios = [0.0, 0.25, 0.50, 0.75, 1.0]
    results = []
    
    for ratio in ratios:
        G = create_financial_network(NUM_AGENTS)
        agents = [
            FinancialAgent(i, use_llm=(i < NUM_AGENTS * ratio))
            for i in G.nodes
        ]
        
        history = run_simulation(
            G, agents, llm_decision_fn, TIME_STEPS,
            enable_shocks=True
        )
        
        metrics = compute_all_metrics(G, history)
        
        result = {
            "ratio": ratio,
            "defaults": metrics["total_defaults"],
            "utility": metrics.get("final_systemic_utility", 0),
            "cascade_depth": metrics.get("max_cascade_depth", 0)
        }
        results.append(result)
        
        if verbose:
            print(f"  Ratio {ratio:.0%}: {result['defaults']} defaults")
    
    return {"ratio_analysis": results}


def run_attack_experiment(llm_decision_fn=None, verbose=True) -> Dict:
    """
    Test network resilience to targeted attacks.
    """
    attack_types = ["degree", "betweenness", "random"]
    results = []
    
    for attack_type in attack_types:
        G = create_financial_network(NUM_AGENTS)
        agents = [
            FinancialAgent(i, use_llm=(i < NUM_AGENTS * FEATHERLESS_AGENT_RATIO))
            for i in G.nodes
        ]
        
        # Apply targeted attack
        targets, attack_details = targeted_attack(G, attack_type, num_targets=3)
        
        # Run simulation after attack
        history = run_simulation(
            G, agents, llm_decision_fn, TIME_STEPS,
            enable_shocks=False  # Only the initial attack, no random shocks
        )
        
        metrics = compute_all_metrics(G, history)
        
        result = {
            "attack_type": attack_type,
            "targets": targets,
            "final_defaults": metrics["total_defaults"],
            "cascade_depth": metrics.get("max_cascade_depth", 0),
            "system_collapsed": history["summary"]["system_collapsed"]
        }
        results.append(result)
        
        if verbose:
            print(f"  {attack_type.capitalize()} attack: {result['final_defaults']} defaults"
                  f" (collapsed: {result['system_collapsed']})")
    
    return {"attack_analysis": results}


def run_topology_experiment(verbose=True) -> Dict:
    """
    Analyze network topology characteristics.
    """
    G = create_financial_network(NUM_AGENTS)
    
    stats = get_network_stats(G)
    sifis = identify_systemically_important(G, top_n=5)
    
    # Compute systemic risk contribution for top nodes
    risk_contributions = {}
    for node in sifis[:3]:  # Top 3 for speed
        risk = compute_systemic_risk_contribution(G.copy(), node)
        risk_contributions[node] = risk
    
    if verbose:
        print(f"  Network nodes: {stats['num_nodes']}, edges: {stats['num_edges']}")
        print(f"  Average degree: {stats['avg_degree']:.2f}")
        print(f"  Systemically important: {sifis[:3]}")
    
    return {
        "network_stats": stats,
        "systemically_important": sifis,
        "risk_contributions": risk_contributions
    }


def run_single_simulation(
    num_agents: int = NUM_AGENTS,
    time_steps: int = TIME_STEPS,
    llm_ratio: float = FEATHERLESS_AGENT_RATIO,
    llm_decision_fn=None,
    enable_shocks: bool = True,
    verbose: bool = True
) -> Dict:
    """
    Run a single simulation with specified parameters.
    Useful for quick experiments and debugging.
    
    Args:
        num_agents: Number of financial institutions
        time_steps: Simulation duration
        llm_ratio: Proportion of agents using LLM
        llm_decision_fn: LLM decision function
        enable_shocks: Whether to apply random shocks
        verbose: Print progress
        
    Returns:
        Complete simulation results
    """
    G = create_financial_network(num_agents)
    
    agents = [
        FinancialAgent(i, use_llm=(i < num_agents * llm_ratio))
        for i in G.nodes
    ]
    
    if verbose:
        print(f"Created network with {num_agents} agents "
              f"({int(num_agents * llm_ratio)} LLM-enabled)")
    
    history = run_simulation(
        G, agents, llm_decision_fn, time_steps,
        enable_shocks=enable_shocks
    )
    
    metrics = compute_all_metrics(G, history)
    risk_indicators = compute_risk_indicators(G)
    
    if verbose:
        report = generate_report(metrics, risk_indicators, history)
        print(report)
    
    return {
        "network": G,
        "agents": agents,
        "history": history,
        "metrics": metrics,
        "risk_indicators": risk_indicators
    }


if __name__ == "__main__":
    # Run experiment suite without LLM for testing
    print("Running experiments without LLM (for testing)...\n")
    run_experiment_suite(llm_decision_fn=None, verbose=True)

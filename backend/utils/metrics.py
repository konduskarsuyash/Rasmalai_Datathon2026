"""
Metrics and visualization utilities for the financial network simulation.
Provides system-level risk metrics and plotting functions.
"""
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Any
from pathlib import Path


def compute_all_metrics(G: nx.DiGraph, history: Dict) -> Dict:
    """
    Compute comprehensive system-level metrics.
    
    Args:
        G: The financial network graph (final state)
        history: Simulation history dictionary
        
    Returns:
        Dictionary of all computed metrics
    """
    metrics = {}
    
    # Default metrics
    defaults_over_time = history.get("defaults_over_time", [])
    metrics["total_defaults"] = defaults_over_time[-1] if defaults_over_time else 0
    metrics["default_rate"] = metrics["total_defaults"] / G.number_of_nodes()
    metrics["max_defaults_in_step"] = max(
        [defaults_over_time[i] - defaults_over_time[i-1] 
         for i in range(1, len(defaults_over_time))], 
        default=0
    )
    
    # Cascade metrics
    cascade_events = history.get("cascade_events", [])
    metrics["num_cascade_events"] = len(cascade_events)
    metrics["max_cascade_depth"] = max(
        [c["cascade"]["cascade_depth"] for c in cascade_events], 
        default=0
    )
    
    # Liquidity metrics
    liquidity_over_time = history.get("liquidity_over_time", [])
    if liquidity_over_time:
        metrics["final_liquidity"] = liquidity_over_time[-1]
        metrics["liquidity_drop"] = liquidity_over_time[0] - liquidity_over_time[-1]
        metrics["min_liquidity"] = min(liquidity_over_time)
    
    # Systemic risk metrics
    defaults_over_time = history.get("defaults_over_time", [])
    if len(defaults_over_time) > 1:
        # Contagion velocity: average defaults per step when cascading
        non_zero_changes = [
            defaults_over_time[i] - defaults_over_time[i-1]
            for i in range(1, len(defaults_over_time))
            if defaults_over_time[i] > defaults_over_time[i-1]
        ]
        metrics["avg_contagion_velocity"] = np.mean(non_zero_changes) if non_zero_changes else 0
    else:
        metrics["avg_contagion_velocity"] = 0
    
    # Network structure metrics (final state)
    surviving_nodes = [n for n in G.nodes if not G.nodes[n]["defaulted"]]
    if surviving_nodes:
        subgraph = G.subgraph(surviving_nodes)
        metrics["surviving_nodes"] = len(surviving_nodes)
        metrics["surviving_edges"] = subgraph.number_of_edges()
        metrics["surviving_connectivity"] = nx.density(subgraph) if len(surviving_nodes) > 1 else 0
    else:
        metrics["surviving_nodes"] = 0
        metrics["surviving_edges"] = 0
        metrics["surviving_connectivity"] = 0
    
    # LLM usage metrics
    llm_decisions = history.get("llm_decisions", [])
    metrics["total_llm_decisions"] = len(llm_decisions)
    if llm_decisions:
        llm_agents = set(d["agent_id"] for d in llm_decisions)
        llm_defaulted = sum(1 for a in llm_agents if G.nodes[a]["defaulted"])
        metrics["llm_agent_default_rate"] = llm_defaulted / len(llm_agents)
    else:
        metrics["llm_agent_default_rate"] = None
    
    # Utility metrics
    utility_over_time = history.get("systemic_utility_over_time", [])
    if utility_over_time:
        metrics["final_systemic_utility"] = utility_over_time[-1]
        metrics["utility_change"] = utility_over_time[-1] - utility_over_time[0]
        metrics["min_utility"] = min(utility_over_time)
    
    # Shock impact metrics
    shock_events = history.get("shock_events", [])
    metrics["total_shocks"] = len(shock_events)
    if shock_events:
        metrics["avg_shock_nodes"] = np.mean([
            len(s["details"]["shocked_nodes"]) for s in shock_events
        ])
    else:
        metrics["avg_shock_nodes"] = 0
    
    return metrics


def compute_risk_indicators(G: nx.DiGraph) -> Dict:
    """
    Compute systemic risk indicators for regulatory analysis.
    
    Args:
        G: The financial network graph
        
    Returns:
        Dictionary of risk indicators
    """
    indicators = {}
    
    # Concentration risk: Herfindahl-Hirschman Index of exposures
    total_exposure = sum(G.edges[e]["exposure"] for e in G.edges)
    if total_exposure > 0:
        node_exposures = {}
        for n in G.nodes:
            exposure = sum(G.edges[n, v]["exposure"] for _, v in G.out_edges(n))
            node_exposures[n] = exposure / total_exposure
        indicators["hhi_exposure"] = sum(s**2 for s in node_exposures.values()) * 10000
    else:
        indicators["hhi_exposure"] = 0
    
    # Interconnectedness
    indicators["avg_degree"] = np.mean([d for n, d in G.degree()])
    indicators["max_degree"] = max([d for n, d in G.degree()])
    
    # Capital adequacy distribution
    capitals = [G.nodes[n]["capital"] for n in G.nodes if not G.nodes[n]["defaulted"]]
    if capitals:
        indicators["avg_capital"] = np.mean(capitals)
        indicators["min_capital"] = min(capitals)
        indicators["capital_std"] = np.std(capitals)
        indicators["nodes_near_threshold"] = sum(1 for c in capitals if c < 30)
    else:
        indicators["avg_capital"] = 0
        indicators["min_capital"] = 0
        indicators["capital_std"] = 0
        indicators["nodes_near_threshold"] = 0
    
    # Liquidity stress
    liquidities = [G.nodes[n]["liquidity"] for n in G.nodes if not G.nodes[n]["defaulted"]]
    if liquidities:
        indicators["avg_liquidity"] = np.mean(liquidities)
        indicators["liquidity_stress_nodes"] = sum(1 for l in liquidities if l < 20)
    else:
        indicators["avg_liquidity"] = 0
        indicators["liquidity_stress_nodes"] = 0
    
    return indicators


def plot_simulation_results(history: Dict, save_path: str = None) -> None:
    """
    Create visualization plots for simulation results.
    
    Args:
        history: Simulation history dictionary
        save_path: Optional path to save the figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Financial Network Simulation Results", fontsize=14, fontweight='bold')
    
    steps = range(len(history.get("defaults_over_time", [])))
    
    # Plot 1: Defaults over time
    ax1 = axes[0, 0]
    defaults = history.get("defaults_over_time", [])
    ax1.plot(steps, defaults, 'r-', linewidth=2, marker='o', markersize=4)
    ax1.fill_between(steps, defaults, alpha=0.3, color='red')
    ax1.set_xlabel("Time Step")
    ax1.set_ylabel("Cumulative Defaults")
    ax1.set_title("Default Propagation")
    ax1.grid(True, alpha=0.3)
    
    # Mark cascade events
    for event in history.get("cascade_events", []):
        ax1.axvline(x=event["time"], color='orange', linestyle='--', alpha=0.7)
    
    # Plot 2: Liquidity over time
    ax2 = axes[0, 1]
    liquidity = history.get("liquidity_over_time", [])
    ax2.plot(steps, liquidity, 'b-', linewidth=2)
    ax2.fill_between(steps, liquidity, alpha=0.3, color='blue')
    ax2.set_xlabel("Time Step")
    ax2.set_ylabel("Total System Liquidity")
    ax2.set_title("Liquidity Dynamics")
    ax2.grid(True, alpha=0.3)
    
    # Mark shock events
    for event in history.get("shock_events", []):
        ax2.axvline(x=event["time"], color='red', linestyle=':', alpha=0.7, label='Shock')
    
    # Plot 3: Systemic Utility
    ax3 = axes[1, 0]
    utility = history.get("systemic_utility_over_time", [])
    ax3.plot(steps, utility, 'g-', linewidth=2)
    ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_xlabel("Time Step")
    ax3.set_ylabel("Systemic Utility")
    ax3.set_title("System-wide Payoff")
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Total Exposure
    ax4 = axes[1, 1]
    exposure = history.get("total_exposure_over_time", [])
    ax4.plot(steps, exposure, 'm-', linewidth=2)
    ax4.set_xlabel("Time Step")
    ax4.set_ylabel("Total Network Exposure")
    ax4.set_title("Credit Exposure Dynamics")
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    
    plt.show()


def plot_network_state(G: nx.DiGraph, title: str = "Financial Network", 
                       save_path: str = None) -> None:
    """
    Visualize the current state of the financial network.
    
    Args:
        G: The financial network graph
        title: Plot title
        save_path: Optional path to save the figure
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Node colors based on status
    node_colors = []
    for n in G.nodes:
        if G.nodes[n]["defaulted"]:
            node_colors.append('red')
        elif G.nodes[n]["capital"] < 30:
            node_colors.append('orange')
        else:
            node_colors.append('green')
    
    # Node sizes based on capital
    node_sizes = [max(50, G.nodes[n]["capital"] * 5) for n in G.nodes]
    
    # Edge widths based on exposure
    edge_widths = [G.edges[e]["exposure"] / 5 for e in G.edges]
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Draw
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=edge_widths, edge_color='gray', ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                           alpha=0.8, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)
    
    ax.set_title(title)
    ax.axis('off')
    
    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Healthy'),
        Patch(facecolor='orange', label='Stressed'),
        Patch(facecolor='red', label='Defaulted')
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Network plot saved to {save_path}")
    
    plt.show()


def generate_report(metrics: Dict, risk_indicators: Dict, 
                    history: Dict) -> str:
    """
    Generate a text report of simulation results.
    
    Args:
        metrics: Computed metrics dictionary
        risk_indicators: Risk indicators dictionary
        history: Simulation history
        
    Returns:
        Formatted report string
    """
    summary = history.get("summary", {})
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║        FINANCIAL NETWORK SIMULATION REPORT                   ║
╚══════════════════════════════════════════════════════════════╝

📊 SIMULATION SUMMARY
────────────────────────────────────────────────────────────────
  Total Steps Completed:     {summary.get('total_steps', 'N/A')}
  System Collapsed:          {'YES ⚠️' if summary.get('system_collapsed') else 'NO ✓'}
  
🏦 DEFAULT ANALYSIS
────────────────────────────────────────────────────────────────
  Final Defaults:            {metrics.get('total_defaults', 0)} / {metrics.get('total_defaults', 0) + metrics.get('surviving_nodes', 0)} institutions
  Default Rate:              {metrics.get('default_rate', 0):.1%}
  Cascade Events:            {metrics.get('num_cascade_events', 0)}
  Max Cascade Depth:         {metrics.get('max_cascade_depth', 0)} rounds
  Avg Contagion Velocity:    {metrics.get('avg_contagion_velocity', 0):.2f} defaults/step

💰 LIQUIDITY & CAPITAL
────────────────────────────────────────────────────────────────
  Final System Liquidity:    ${metrics.get('final_liquidity', 0):,.2f}
  Liquidity Drain:           ${metrics.get('liquidity_drop', 0):,.2f}
  Avg Institution Capital:   ${risk_indicators.get('avg_capital', 0):,.2f}
  Near-Threshold Nodes:      {risk_indicators.get('nodes_near_threshold', 0)}

🔗 NETWORK RESILIENCE
────────────────────────────────────────────────────────────────
  Surviving Nodes:           {metrics.get('surviving_nodes', 0)}
  Surviving Connections:     {metrics.get('surviving_edges', 0)}
  Network Connectivity:      {metrics.get('surviving_connectivity', 0):.3f}
  
⚡ SHOCK ANALYSIS
────────────────────────────────────────────────────────────────
  Total Shocks:              {metrics.get('total_shocks', 0)}
  Avg Nodes per Shock:       {metrics.get('avg_shock_nodes', 0):.1f}
  
🤖 LLM AGENT PERFORMANCE
────────────────────────────────────────────────────────────────
  LLM Decisions Made:        {metrics.get('total_llm_decisions', 0)}
  LLM Agent Default Rate:    {f"{metrics.get('llm_agent_default_rate', 0):.1%}" if metrics.get('llm_agent_default_rate') is not None else 'N/A'}

📈 UTILITY ANALYSIS
────────────────────────────────────────────────────────────────
  Final Systemic Utility:    {metrics.get('final_systemic_utility', 0):,.2f}
  Utility Change:            {metrics.get('utility_change', 0):,.2f}

⚠️  RISK INDICATORS
────────────────────────────────────────────────────────────────
  Exposure Concentration:    {risk_indicators.get('hhi_exposure', 0):,.0f} (HHI)
  Avg Degree:                {risk_indicators.get('avg_degree', 0):.2f}
  Liquidity Stress Nodes:    {risk_indicators.get('liquidity_stress_nodes', 0)}
  
══════════════════════════════════════════════════════════════
"""
    return report

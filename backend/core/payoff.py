"""
Payoff and utility functions for financial agents.
Implements game-theoretic utility calculations.
"""
import networkx as nx
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import FinancialAgent


def compute_utility(agent: "FinancialAgent", G: nx.DiGraph) -> float:
    """
    Compute the utility (payoff) for a financial agent.
    
    Utility = Profit from exposures - Liquidity penalty - Default losses
    
    This is the core game-theoretic component where agents maximize
    expected utility given their local information.
    
    Args:
        agent: The financial agent
        G: The financial network graph
        
    Returns:
        Float utility value
    """
    node_data = G.nodes[agent.id]
    
    # Profit from credit exposures (revenue from lending/trading)
    profit = sum(
        G.edges[agent.id, v]["exposure"] * 0.05  # 5% return on exposure
        for _, v in G.out_edges(agent.id)
        if not G.nodes[v]["defaulted"]  # Only count non-defaulted counterparties
    )
    
    # Liquidity penalty (cost of illiquidity)
    liquidity = node_data["liquidity"]
    liquidity_penalty = max(0, 30 - liquidity) * 0.5
    
    # Default loss (catastrophic penalty for defaulting)
    default_loss = 100 if node_data["defaulted"] else 0
    
    # Counterparty default losses
    counterparty_loss = sum(
        G.edges[agent.id, v]["exposure"] - G.edges[agent.id, v]["margin_held"]
        for _, v in G.out_edges(agent.id)
        if G.nodes[v]["defaulted"]
    )
    counterparty_loss = max(0, counterparty_loss)
    
    # Margin opportunity cost (capital tied up in margins)
    margin_cost = sum(
        G.edges[agent.id, v]["margin_held"] * 0.02
        for _, v in G.out_edges(agent.id)
    )
    
    return profit - liquidity_penalty - default_loss - counterparty_loss - margin_cost


def compute_systemic_utility(agents: list, G: nx.DiGraph) -> float:
    """
    Compute aggregate systemic utility across all agents.
    Measures overall financial system health.
    
    Args:
        agents: List of all financial agents
        G: The financial network graph
        
    Returns:
        Float systemic utility value
    """
    return sum(compute_utility(agent, G) for agent in agents)


def compute_expected_utility(agent: "FinancialAgent", G: nx.DiGraph, 
                             strategies: dict, 
                             num_simulations: int = 10) -> float:
    """
    Compute expected utility under uncertainty using Monte Carlo.
    
    This simulates the incomplete information aspect where agents
    don't know future states with certainty.
    
    Args:
        agent: The financial agent
        G: The financial network graph
        strategies: Dictionary of {strategy_name: (credit, margin)}
        num_simulations: Number of Monte Carlo samples
        
    Returns:
        Expected utility value
    """
    import numpy as np
    
    utilities = []
    for _ in range(num_simulations):
        # Simulate potential future state
        G_sim = G.copy()
        
        # Add noise to neighbor states
        for node in G_sim.nodes:
            if node != agent.id:
                noise = np.random.normal(0, 5)
                G_sim.nodes[node]["capital"] += noise
        
        utilities.append(compute_utility(agent, G_sim))
    
    return np.mean(utilities)


def emergent_equilibrium_check(agents: list, G: nx.DiGraph) -> dict:
    """
    Check if current strategies show emergent equilibrium behavior.
    
    Under repeated strategic interaction, agents may converge to
    a stable strategy profile where no agent has incentive to deviate.
    This is an emergent phenomenon, not a computed Nash solution.
    
    Args:
        agents: List of financial agents
        G: The financial network graph
        
    Returns:
        Dictionary with stability analysis
    """
    deviators = []
    
    for agent in agents:
        current_utility = compute_utility(agent, G)
        original_credit = agent.credit_strategy
        original_margin = agent.margin_strategy
        
        # Check if any deviation improves utility
        best_deviation_gain = 0
        for credit in ["LOW", "MEDIUM", "HIGH"]:
            for margin in ["TIGHT", "NORMAL", "LOOSE"]:
                if credit == original_credit and margin == original_margin:
                    continue
                
                # Temporarily apply deviation
                agent.credit_strategy = credit
                agent.margin_strategy = margin
                agent.apply_strategy(G)
                
                deviation_utility = compute_utility(agent, G)
                gain = deviation_utility - current_utility
                
                if gain > best_deviation_gain:
                    best_deviation_gain = gain
                    deviators.append({
                        "agent_id": agent.id,
                        "from": (original_credit, original_margin),
                        "to": (credit, margin),
                        "gain": gain
                    })
        
        # Restore original strategy
        agent.credit_strategy = original_credit
        agent.margin_strategy = original_margin
        agent.apply_strategy(G)
    
    return {
        "is_stable": len(deviators) == 0,
        "num_potential_deviators": len(deviators),
        "top_deviations": sorted(deviators, key=lambda x: x["gain"], reverse=True)[:5]
    }

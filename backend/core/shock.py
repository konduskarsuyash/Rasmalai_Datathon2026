"""
Shock propagation and cascading failure logic.
Models how localized disturbances propagate through the financial network.
"""
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple
from config.settings import DEFAULT_THRESHOLD, SHOCK_MAGNITUDE


def apply_shock(G: nx.DiGraph, shocked_nodes: List[int], 
                magnitude: float = SHOCK_MAGNITUDE) -> Dict:
    """
    Apply an exogenous shock to specified nodes.
    
    Shocks represent external events like market crashes,
    sudden liquidity drains, or counterparty failures.
    
    Args:
        G: The financial network graph
        shocked_nodes: List of node IDs to shock
        magnitude: Capital reduction amount
        
    Returns:
        Dictionary with shock details
    """
    shock_details = {
        "shocked_nodes": shocked_nodes,
        "magnitude": magnitude,
        "capital_before": {},
        "capital_after": {}
    }
    
    for node in shocked_nodes:
        shock_details["capital_before"][node] = G.nodes[node]["capital"]
        G.nodes[node]["capital"] -= magnitude
        shock_details["capital_after"][node] = G.nodes[node]["capital"]
    
    return shock_details


def propagate_defaults(G: nx.DiGraph, threshold: float = DEFAULT_THRESHOLD,
                       max_iterations: int = 100) -> Dict:
    """
    Propagate defaults through the network in cascading fashion.
    
    When a node defaults:
    1. Its capital falls below threshold
    2. Creditors (predecessors) lose exposure minus margin held
    3. This may trigger further defaults
    
    Args:
        G: The financial network graph (modified in place)
        threshold: Capital level below which an institution defaults
        max_iterations: Maximum cascade rounds to prevent infinite loops
        
    Returns:
        Dictionary with cascade details
    """
    cascade_log = {
        "rounds": [],
        "total_defaults": 0,
        "cascade_depth": 0,
        "contagion_paths": []
    }
    
    for iteration in range(max_iterations):
        new_defaults = []
        
        for node in G.nodes:
            # Skip already defaulted nodes
            if G.nodes[node]["defaulted"]:
                continue
            
            # Check if node should default
            if G.nodes[node]["capital"] < threshold:
                G.nodes[node]["defaulted"] = True
                new_defaults.append(node)
                
                # Propagate losses to creditors (nodes with outgoing edges to this node)
                for u, _ in G.in_edges(node):
                    if not G.nodes[u]["defaulted"]:
                        # Loss = exposure - margin held
                        exposure = G.edges[u, node]["exposure"]
                        margin = G.edges[u, node]["margin_held"]
                        loss = max(0, exposure - margin)
                        
                        G.nodes[u]["capital"] -= loss
                        
                        # Also drain some liquidity
                        G.nodes[u]["liquidity"] -= loss * 0.3
                        G.nodes[u]["liquidity"] = max(0, G.nodes[u]["liquidity"])
                        
                        cascade_log["contagion_paths"].append({
                            "from": node,
                            "to": u,
                            "loss": loss,
                            "round": iteration
                        })
        
        if not new_defaults:
            break
        
        cascade_log["rounds"].append({
            "round": iteration,
            "new_defaults": new_defaults,
            "count": len(new_defaults)
        })
        cascade_log["cascade_depth"] = iteration + 1
    
    cascade_log["total_defaults"] = sum(
        1 for n in G.nodes if G.nodes[n]["defaulted"]
    )
    
    return cascade_log


def generate_random_shock(G: nx.DiGraph, probability: float = 0.1,
                          target_type: str = None) -> Tuple[List[int], Dict]:
    """
    Generate a random shock affecting nodes with given probability.
    
    Args:
        G: The financial network graph
        probability: Probability each node is shocked
        target_type: If specified, only shock nodes of this type
        
    Returns:
        Tuple of (shocked_nodes, shock_details)
    """
    candidates = [
        n for n in G.nodes 
        if not G.nodes[n]["defaulted"] and
        (target_type is None or G.nodes[n]["type"] == target_type)
    ]
    
    shocked = [n for n in candidates if np.random.random() < probability]
    
    if shocked:
        details = apply_shock(G, shocked)
    else:
        details = {"shocked_nodes": [], "magnitude": 0}
    
    return shocked, details


def targeted_attack(G: nx.DiGraph, attack_strategy: str = "degree",
                    num_targets: int = 3) -> Tuple[List[int], Dict]:
    """
    Simulate a targeted attack on systemically important nodes.
    
    Args:
        G: The financial network graph
        attack_strategy: 'degree' (hub attack), 'betweenness', or 'random'
        num_targets: Number of nodes to attack
        
    Returns:
        Tuple of (attacked_nodes, attack_details)
    """
    non_defaulted = [n for n in G.nodes if not G.nodes[n]["defaulted"]]
    
    if attack_strategy == "degree":
        sorted_nodes = sorted(non_defaulted, 
                             key=lambda x: G.degree(x), 
                             reverse=True)
    elif attack_strategy == "betweenness":
        betweenness = nx.betweenness_centrality(G)
        sorted_nodes = sorted(non_defaulted, 
                             key=lambda x: betweenness[x], 
                             reverse=True)
    else:  # random
        sorted_nodes = list(np.random.permutation(non_defaulted))
    
    targets = sorted_nodes[:num_targets]
    details = apply_shock(G, targets, magnitude=SHOCK_MAGNITUDE * 1.5)
    
    return targets, details


def compute_systemic_risk_contribution(G: nx.DiGraph, node: int,
                                       threshold: float = DEFAULT_THRESHOLD) -> float:
    """
    Compute a node's contribution to systemic risk.
    
    Measures how much defaults would increase if this node fails.
    
    Args:
        G: The financial network graph
        node: Node ID to analyze
        threshold: Default threshold
        
    Returns:
        Systemic risk score (0-1)
    """
    # Create copy to simulate
    G_sim = G.copy()
    
    # Count current defaults
    initial_defaults = sum(1 for n in G.nodes if G.nodes[n]["defaulted"])
    
    # Force this node to default
    G_sim.nodes[node]["defaulted"] = True
    G_sim.nodes[node]["capital"] = 0
    
    # Propagate
    cascade = propagate_defaults(G_sim, threshold)
    final_defaults = cascade["total_defaults"]
    
    # Risk contribution = additional defaults caused
    additional_defaults = final_defaults - initial_defaults - 1  # -1 for the node itself
    max_possible = G.number_of_nodes() - initial_defaults - 1
    
    if max_possible <= 0:
        return 0.0
    
    return additional_defaults / max_possible

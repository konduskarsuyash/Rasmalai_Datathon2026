"""
Network construction for the financial infrastructure simulation.
Uses Barabási-Albert model to generate scale-free networks that mimic
real-world financial networks with hub institutions.
"""
import networkx as nx
import numpy as np
from config.settings import MIN_EXPOSURE, MAX_EXPOSURE


def create_financial_network(num_agents: int, m: int = 3) -> nx.DiGraph:
    """
    Create a directed financial network with realistic properties.
    
    Args:
        num_agents: Number of financial institutions (nodes)
        m: Number of edges to attach from new node to existing nodes
        
    Returns:
        DiGraph with node and edge attributes
    """
    # Create scale-free network (power-law degree distribution)
    G = nx.barabasi_albert_graph(num_agents, m)
    G = G.to_directed()
    
    # Initialize node attributes (financial institutions)
    for node in G.nodes:
        G.nodes[node]["capital"] = np.random.uniform(80, 120)
        G.nodes[node]["liquidity"] = np.random.uniform(40, 60)
        G.nodes[node]["defaulted"] = False
        G.nodes[node]["type"] = np.random.choice(
            ["bank", "exchange", "clearing_house"],
            p=[0.6, 0.25, 0.15]
        )
    
    # Initialize edge attributes (credit exposures and settlement obligations)
    for u, v in G.edges:
        G.edges[u, v]["exposure"] = np.random.uniform(MIN_EXPOSURE, MAX_EXPOSURE)
        G.edges[u, v]["settlement_obligation"] = np.random.uniform(2, 10)
        G.edges[u, v]["margin_held"] = np.random.uniform(1, 5)
    
    return G


def get_network_stats(G: nx.DiGraph) -> dict:
    """
    Calculate key network statistics for analysis.
    
    Args:
        G: The financial network graph
        
    Returns:
        Dictionary of network metrics
    """
    return {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "avg_degree": np.mean([d for n, d in G.degree()]),
        "density": nx.density(G),
        "avg_clustering": nx.average_clustering(G.to_undirected()),
        "num_weakly_connected": nx.number_weakly_connected_components(G),
        "total_exposure": sum(G.edges[e]["exposure"] for e in G.edges),
        "total_capital": sum(G.nodes[n]["capital"] for n in G.nodes),
    }


def identify_systemically_important(G: nx.DiGraph, top_n: int = 5) -> list:
    """
    Identify systemically important financial institutions (SIFIs).
    Based on PageRank centrality and total exposure.
    
    Args:
        G: The financial network graph
        top_n: Number of top institutions to identify
        
    Returns:
        List of node IDs ranked by systemic importance
    """
    pagerank = nx.pagerank(G)
    
    # Combine PageRank with exposure centrality
    importance = {}
    for node in G.nodes:
        out_exposure = sum(G.edges[node, v]["exposure"] for _, v in G.out_edges(node))
        in_exposure = sum(G.edges[u, node]["exposure"] for u, _ in G.in_edges(node))
        importance[node] = pagerank[node] * (1 + out_exposure + in_exposure)
    
    sorted_nodes = sorted(importance.keys(), key=lambda x: importance[x], reverse=True)
    return sorted_nodes[:top_n]


def add_new_institution(
    G: nx.DiGraph,
    agent_id: int,
    capital: float = 100.0,
    liquidity: float = 50.0,
    institution_type: str = "bank",
    connect_strategy: str = "preferential",
    num_connections: int = 3,
    target_stressed: bool = False
) -> dict:
    """
    Dynamically add a new financial institution to the network.
    
    Models real-world scenarios:
    - New market entrant (bank/exchange)
    - Regulator liquidity injection vehicle
    - Clearing house / stabilizing intermediary
    
    Args:
        G: The financial network graph
        agent_id: Unique ID for new node
        capital: Initial capital of institution
        liquidity: Initial liquidity
        institution_type: "bank", "exchange", "clearing_house", or "stabilizer"
        connect_strategy: "preferential" (hub-focused), "random", or "targeted" (stressed nodes)
        num_connections: Number of bidirectional connections to form
        target_stressed: If True, connect to nodes near default threshold
        
    Returns:
        Dictionary with entry metadata for logging
    """
    import random
    
    existing_nodes = list(G.nodes())
    if not existing_nodes:
        raise ValueError("Cannot add institution to empty network")
    
    # Add the new node
    G.add_node(agent_id)
    G.nodes[agent_id]["capital"] = capital
    G.nodes[agent_id]["liquidity"] = liquidity
    G.nodes[agent_id]["defaulted"] = False
    G.nodes[agent_id]["type"] = institution_type
    G.nodes[agent_id]["entry_time"] = True  # Mark as dynamic entrant
    
    # Filter out defaulted nodes for connections
    active_nodes = [n for n in existing_nodes if not G.nodes[n]["defaulted"]]
    num_connections = min(num_connections, len(active_nodes))
    
    # Select target nodes based on strategy
    if connect_strategy == "preferential":
        # Connect to high-degree nodes (hub attachment - realistic)
        targets = sorted(
            active_nodes,
            key=lambda n: G.degree(n),
            reverse=True
        )[:num_connections]
    elif connect_strategy == "targeted" or target_stressed:
        # Connect to stressed nodes (stabilizer intervention)
        from config.settings import DEFAULT_THRESHOLD
        stressed = sorted(
            active_nodes,
            key=lambda n: G.nodes[n]["capital"] - DEFAULT_THRESHOLD
        )[:num_connections]
        targets = stressed if stressed else random.sample(active_nodes, num_connections)
    else:  # random
        targets = random.sample(active_nodes, num_connections)
    
    # Create bidirectional edges
    connected_to = []
    for t in targets:
        # Exposure from new institution to target
        G.add_edge(agent_id, t, 
                   exposure=np.random.uniform(MIN_EXPOSURE, MAX_EXPOSURE),
                   settlement_obligation=np.random.uniform(2, 10),
                   margin_held=np.random.uniform(1, 5))
        # Exposure from target to new institution
        G.add_edge(t, agent_id,
                   exposure=np.random.uniform(MIN_EXPOSURE, MAX_EXPOSURE),
                   settlement_obligation=np.random.uniform(2, 10),
                   margin_held=np.random.uniform(1, 5))
        connected_to.append(t)
    
    return {
        "agent_id": agent_id,
        "capital": capital,
        "liquidity": liquidity,
        "type": institution_type,
        "strategy": connect_strategy,
        "connected_to": connected_to,
        "num_edges_created": len(connected_to) * 2
    }

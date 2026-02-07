"""
Main simulation loop for the financial network game.
Orchestrates agent decisions, strategy application, and cascade propagation.
"""
import networkx as nx
import numpy as np
from typing import List, Dict, Optional, Callable
from .agent import FinancialAgent
from .payoff import compute_utility, compute_systemic_utility
from .shock import propagate_defaults, generate_random_shock
from config.settings import TIME_STEPS, DEFAULT_THRESHOLD, SHOCK_PROBABILITY, VERBOSE


def run_simulation(
    G: nx.DiGraph,
    agents: List[FinancialAgent],
    llm_decision_fn: Optional[Callable] = None,
    steps: int = TIME_STEPS,
    threshold: float = DEFAULT_THRESHOLD,
    shock_probability: float = SHOCK_PROBABILITY,
    enable_shocks: bool = True
) -> Dict:
    """
    Run the full financial network simulation.
    
    Each time step:
    1. Agents observe local network state
    2. Agents make strategic decisions (LLM or rule-based)
    3. Agents apply strategies to the network
    4. Random shocks may occur
    5. Defaults propagate through the network
    6. Metrics are recorded
    
    Args:
        G: The financial network graph
        agents: List of FinancialAgent objects
        llm_decision_fn: Function to call Featherless API (optional)
        steps: Number of simulation time steps
        threshold: Capital threshold for default
        shock_probability: Probability of random shock per step
        enable_shocks: Whether to apply random shocks
        
    Returns:
        Dictionary with simulation history and results
    """
    history = {
        "steps": [],
        "defaults_over_time": [],
        "liquidity_over_time": [],
        "total_exposure_over_time": [],
        "systemic_utility_over_time": [],
        "llm_decisions": [],
        "cascade_events": [],
        "shock_events": []
    }
    
    # Map agent IDs to agents for quick lookup
    agent_map = {agent.id: agent for agent in agents}
    
    for t in range(steps):
        step_log = {
            "time": t,
            "decisions": [],
            "defaults_before": sum(1 for n in G.nodes if G.nodes[n]["defaulted"]),
            "defaults_after": 0,
            "cascade": None,
            "shock": None
        }
        
        if VERBOSE:
            print(f"\n=== Time Step {t} ===")
        
        # Phase 1: Agent observations and decisions
        for agent in agents:
            if G.nodes[agent.id]["defaulted"]:
                continue  # Skip defaulted agents
            
            observation = agent.observe(G)
            
            if agent.use_llm and llm_decision_fn is not None:
                try:
                    decision = llm_decision_fn(observation)
                    history["llm_decisions"].append({
                        "time": t,
                        "agent_id": agent.id,
                        "observation": observation,
                        "decision": decision
                    })
                    if VERBOSE:
                        print(f"  Agent {agent.id} (LLM): {decision}")
                except Exception as e:
                    if VERBOSE:
                        print(f"  Agent {agent.id} LLM failed: {e}, using rule-based")
                    decision = agent.make_rule_based_decision(observation)
            else:
                decision = agent.make_rule_based_decision(observation)
            
            agent.update_strategy(decision)
            step_log["decisions"].append({
                "agent_id": agent.id,
                "decision": decision,
                "used_llm": agent.use_llm and llm_decision_fn is not None
            })
        
        # Phase 2: Apply strategies
        for agent in agents:
            if not G.nodes[agent.id]["defaulted"]:
                agent.apply_strategy(G)
        
        # Phase 3: Random shock (if enabled)
        if enable_shocks and np.random.random() < shock_probability:
            shocked_nodes, shock_details = generate_random_shock(G, probability=0.15)
            if shocked_nodes:
                step_log["shock"] = shock_details
                history["shock_events"].append({
                    "time": t,
                    "details": shock_details
                })
                if VERBOSE:
                    print(f"  SHOCK! Affected nodes: {shocked_nodes}")
        
        # Phase 4: Propagate defaults
        cascade = propagate_defaults(G, threshold)
        step_log["cascade"] = cascade
        step_log["defaults_after"] = cascade["total_defaults"]
        
        if cascade["total_defaults"] > step_log["defaults_before"]:
            history["cascade_events"].append({
                "time": t,
                "cascade": cascade
            })
            if VERBOSE:
                print(f"  CASCADE: {cascade['total_defaults'] - step_log['defaults_before']} new defaults")
        
        # Phase 5: Record metrics
        total_defaults = sum(1 for n in G.nodes if G.nodes[n]["defaulted"])
        total_liquidity = sum(G.nodes[n]["liquidity"] for n in G.nodes)
        total_exposure = sum(G.edges[e]["exposure"] for e in G.edges)
        systemic_utility = compute_systemic_utility(agents, G)
        
        history["defaults_over_time"].append(total_defaults)
        history["liquidity_over_time"].append(total_liquidity)
        history["total_exposure_over_time"].append(total_exposure)
        history["systemic_utility_over_time"].append(systemic_utility)
        history["steps"].append(step_log)
        
        if VERBOSE:
            print(f"  Defaults: {total_defaults}, Liquidity: {total_liquidity:.2f}, Utility: {systemic_utility:.2f}")
        
        # Early termination if all agents defaulted
        if total_defaults >= len(agents):
            if VERBOSE:
                print("\n!!! TOTAL SYSTEM COLLAPSE !!!")
            break
    
    # Final summary
    history["summary"] = {
        "total_steps": len(history["steps"]),
        "final_defaults": history["defaults_over_time"][-1] if history["defaults_over_time"] else 0,
        "max_defaults": max(history["defaults_over_time"]) if history["defaults_over_time"] else 0,
        "total_cascade_events": len(history["cascade_events"]),
        "total_shock_events": len(history["shock_events"]),
        "llm_decisions_made": len(history["llm_decisions"]),
        "final_systemic_utility": history["systemic_utility_over_time"][-1] if history["systemic_utility_over_time"] else 0,
        "system_collapsed": history["defaults_over_time"][-1] >= len(agents) if history["defaults_over_time"] else False
    }
    
    return history


def run_comparative_simulation(
    G: nx.DiGraph,
    agents: List[FinancialAgent],
    llm_decision_fn: Optional[Callable] = None,
    steps: int = TIME_STEPS,
    num_runs: int = 5
) -> Dict:
    """
    Run multiple simulations to compare LLM vs rule-based strategies.
    
    Args:
        G: Base network (will be copied for each run)
        agents: List of agents (will be reset for each run)
        llm_decision_fn: LLM decision function
        steps: Steps per simulation
        num_runs: Number of simulation runs
        
    Returns:
        Comparative analysis results
    """
    import copy
    
    results = {
        "with_llm": [],
        "without_llm": []
    }
    
    for run in range(num_runs):
        # Run with LLM
        G_llm = copy.deepcopy(G)
        for agent in agents:
            agent.credit_strategy = "MEDIUM"
            agent.margin_strategy = "NORMAL"
        
        history_llm = run_simulation(
            G_llm, agents, llm_decision_fn, steps,
            enable_shocks=True
        )
        results["with_llm"].append(history_llm["summary"])
        
        # Run without LLM (rule-based only)
        G_rule = copy.deepcopy(G)
        for agent in agents:
            agent.credit_strategy = "MEDIUM"
            agent.margin_strategy = "NORMAL"
        
        history_rule = run_simulation(
            G_rule, agents, None, steps,
            enable_shocks=True
        )
        results["without_llm"].append(history_rule["summary"])
    
    # Aggregate results
    results["comparison"] = {
        "avg_defaults_with_llm": np.mean([r["final_defaults"] for r in results["with_llm"]]),
        "avg_defaults_without_llm": np.mean([r["final_defaults"] for r in results["without_llm"]]),
        "avg_utility_with_llm": np.mean([r["final_systemic_utility"] for r in results["with_llm"]]),
        "avg_utility_without_llm": np.mean([r["final_systemic_utility"] for r in results["without_llm"]]),
        "collapse_rate_with_llm": np.mean([r["system_collapsed"] for r in results["with_llm"]]),
        "collapse_rate_without_llm": np.mean([r["system_collapsed"] for r in results["without_llm"]]),
    }
    
    return results


def run_dynamic_entry_simulation(
    G: nx.DiGraph,
    agents: List[FinancialAgent],
    llm_decision_fn: Optional[Callable] = None,
    steps: int = TIME_STEPS,
    entry_time: int = None,
    entry_config: Dict = None,
    threshold: float = DEFAULT_THRESHOLD,
    enable_shocks: bool = True
) -> Dict:
    """
    Run simulation with dynamic institution entry at a specified time.
    
    This models real-world scenarios:
    - New market entrant (bank/exchange)
    - Regulator liquidity injection vehicle
    - Stabilizing intermediary intervention
    
    Args:
        G: The financial network graph
        agents: List of starting agents
        llm_decision_fn: LLM decision function
        steps: Total simulation steps
        entry_time: Time step when new institution enters (default: mid-simulation)
        entry_config: Config dict for the new institution:
            - capital: Initial capital (default 150)
            - liquidity: Initial liquidity (default 75)
            - risk_profile: "conservative", "balanced", "aggressive", "stabilizer"
            - connect_strategy: "preferential", "random", "targeted"
            - use_llm: Whether new agent uses LLM
        threshold: Default threshold
        enable_shocks: Whether to enable shocks
        
    Returns:
        Simulation history with entry event tracked
    """
    from .network import add_new_institution
    
    # Default entry at mid-simulation
    if entry_time is None:
        entry_time = steps // 2
    
    # Default entry configuration
    if entry_config is None:
        entry_config = {
            "capital": 150.0,
            "liquidity": 75.0,
            "risk_profile": "balanced",
            "connect_strategy": "preferential",
            "use_llm": False,
            "institution_type": "bank"
        }
    
    history = {
        "steps": [],
        "defaults_over_time": [],
        "liquidity_over_time": [],
        "total_exposure_over_time": [],
        "systemic_utility_over_time": [],
        "llm_decisions": [],
        "cascade_events": [],
        "shock_events": [],
        "entry_events": []
    }
    
    agent_map = {agent.id: agent for agent in agents}
    agent_list = list(agents)  # Mutable copy
    
    for t in range(steps):
        step_log = {
            "time": t,
            "decisions": [],
            "defaults_before": sum(1 for n in G.nodes if G.nodes[n]["defaulted"]),
            "defaults_after": 0,
            "cascade": None,
            "shock": None,
            "entry": None
        }
        
        if VERBOSE:
            print(f"\n=== Time Step {t} ===")
        
        # DYNAMIC ENTRY: Add new institution at entry_time
        if t == entry_time:
            new_id = max(G.nodes()) + 1
            
            entry_result = add_new_institution(
                G,
                agent_id=new_id,
                capital=entry_config.get("capital", 150.0),
                liquidity=entry_config.get("liquidity", 75.0),
                institution_type=entry_config.get("institution_type", "bank"),
                connect_strategy=entry_config.get("connect_strategy", "preferential"),
                num_connections=entry_config.get("num_connections", 3),
                target_stressed=entry_config.get("connect_strategy") == "targeted"
            )
            
            # Create agent for new institution
            new_agent = FinancialAgent(
                agent_id=new_id,
                use_llm=entry_config.get("use_llm", False),
                risk_profile=entry_config.get("risk_profile", "balanced")
            )
            new_agent.is_dynamic_entrant = True
            agent_list.append(new_agent)
            agent_map[new_id] = new_agent
            
            step_log["entry"] = entry_result
            history["entry_events"].append({
                "time": t,
                "details": entry_result,
                "risk_profile": entry_config.get("risk_profile", "balanced")
            })
            
            if VERBOSE:
                print(f"  🏦 NEW ENTRANT: Node {new_id} ({entry_config.get('risk_profile', 'balanced')}) connected to {entry_result['connected_to']}")
        
        # Phase 1: Agent observations and decisions
        for agent in agent_list:
            if G.nodes[agent.id]["defaulted"]:
                continue
            
            observation = agent.observe(G)
            
            # Add network change awareness for LLM agents
            if agent.use_llm and llm_decision_fn is not None:
                # Enhance observation with network change info
                if t == entry_time and agent.id != new_id:
                    observation["network_changed"] = True
                    observation["new_entrant_connected"] = agent.id in entry_result.get("connected_to", [])
                
                try:
                    decision = llm_decision_fn(observation)
                    history["llm_decisions"].append({
                        "time": t,
                        "agent_id": agent.id,
                        "observation": observation,
                        "decision": decision
                    })
                    if VERBOSE:
                        print(f"  Agent {agent.id} (LLM): {decision}")
                except Exception as e:
                    if VERBOSE:
                        print(f"  Agent {agent.id} LLM failed: {e}")
                    decision = agent.make_rule_based_decision(observation)
            else:
                decision = agent.make_rule_based_decision(observation)
            
            agent.update_strategy(decision)
            step_log["decisions"].append({
                "agent_id": agent.id,
                "decision": decision,
                "used_llm": agent.use_llm and llm_decision_fn is not None
            })
        
        # Phase 2: Apply strategies
        for agent in agent_list:
            if not G.nodes[agent.id]["defaulted"]:
                agent.apply_strategy(G)
        
        # Phase 3: Random shock
        if enable_shocks and np.random.random() < SHOCK_PROBABILITY:
            from .shock import generate_random_shock
            shocked_nodes, shock_details = generate_random_shock(G, probability=0.15)
            if shocked_nodes:
                step_log["shock"] = shock_details
                history["shock_events"].append({"time": t, "details": shock_details})
                if VERBOSE:
                    print(f"  SHOCK! Affected nodes: {shocked_nodes}")
        
        # Phase 4: Propagate defaults
        cascade = propagate_defaults(G, threshold)
        step_log["cascade"] = cascade
        step_log["defaults_after"] = cascade["total_defaults"]
        
        if cascade["total_defaults"] > step_log["defaults_before"]:
            history["cascade_events"].append({"time": t, "cascade": cascade})
            if VERBOSE:
                print(f"  CASCADE: {cascade['total_defaults'] - step_log['defaults_before']} new defaults")
        
        # Phase 5: Record metrics
        total_defaults = sum(1 for n in G.nodes if G.nodes[n]["defaulted"])
        total_liquidity = sum(G.nodes[n]["liquidity"] for n in G.nodes)
        total_exposure = sum(G.edges[e]["exposure"] for e in G.edges)
        systemic_utility = compute_systemic_utility(agent_list, G)
        
        history["defaults_over_time"].append(total_defaults)
        history["liquidity_over_time"].append(total_liquidity)
        history["total_exposure_over_time"].append(total_exposure)
        history["systemic_utility_over_time"].append(systemic_utility)
        history["steps"].append(step_log)
        
        if VERBOSE:
            print(f"  Defaults: {total_defaults}, Liquidity: {total_liquidity:.2f}, Utility: {systemic_utility:.2f}")
        
        if total_defaults >= len(agent_list):
            if VERBOSE:
                print("\n!!! TOTAL SYSTEM COLLAPSE !!!")
            break
    
    history["summary"] = {
        "total_steps": len(history["steps"]),
        "final_defaults": history["defaults_over_time"][-1] if history["defaults_over_time"] else 0,
        "max_defaults": max(history["defaults_over_time"]) if history["defaults_over_time"] else 0,
        "total_cascade_events": len(history["cascade_events"]),
        "total_shock_events": len(history["shock_events"]),
        "llm_decisions_made": len(history["llm_decisions"]),
        "final_systemic_utility": history["systemic_utility_over_time"][-1] if history["systemic_utility_over_time"] else 0,
        "system_collapsed": history["defaults_over_time"][-1] >= len(agent_list) if history["defaults_over_time"] else False,
        "dynamic_entries": len(history["entry_events"]),
        "final_node_count": G.number_of_nodes()
    }
    
    return history

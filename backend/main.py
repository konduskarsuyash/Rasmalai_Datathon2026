"""
Financial Network Game-Theoretic Simulation MVP
================================================

Main entry point for the hackathon project.

This simulation models strategic interactions among financial institutions
(banks, exchanges, clearing houses) using game theory and network analysis.
Featherless.ai is integrated for decision-making under incomplete information.

Usage:
    python main.py                    # Run v1 with default settings
    python main.py --v2               # Run v2 with balance sheets
    python main.py --v2 --banks 30    # v2 with 30 banks
    python main.py --no-llm           # Run without LLM (rule-based only)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import (
    NUM_AGENTS, TIME_STEPS, FEATHERLESS_AGENT_RATIO,
    FEATHERLESS_API_KEY, VERBOSE
)
from core.network import create_financial_network, get_network_stats, identify_systemically_important
from core.agent import FinancialAgent
from core.simulation import run_simulation, run_dynamic_entry_simulation
from core.shock import targeted_attack
from utils.metrics import (
    compute_all_metrics, compute_risk_indicators, 
    generate_report, plot_simulation_results, plot_network_state
)
from experiments.run_experiments import run_experiment_suite, run_single_simulation


def create_llm_decision_function():
    """
    Create the LLM decision function using Featherless.ai.
    Returns None if API key is not configured.
    """
    if not FEATHERLESS_API_KEY:
        print("⚠️  FEATHERLESS_API_KEY not set. Running in rule-based mode.")
        print("   Set your API key in .env file to enable LLM decisions.\n")
        return None
    
    try:
        from featherless.decision_engine import featherless_decision, create_featherless_client
        client = create_featherless_client()
        
        def llm_decision(observation):
            return featherless_decision(observation, client)
        
        print("✅ Featherless.ai client initialized successfully.\n")
        return llm_decision
    except Exception as e:
        print(f"⚠️  Failed to initialize Featherless.ai: {e}")
        print("   Falling back to rule-based mode.\n")
        return None


def main():
    """Main entry point for the financial network simulation."""
    parser = argparse.ArgumentParser(
        description="Financial Network Game-Theoretic Simulation"
    )
    parser.add_argument(
        "--agents", type=int, default=NUM_AGENTS,
        help=f"Number of financial institutions (default: {NUM_AGENTS})"
    )
    parser.add_argument(
        "--steps", type=int, default=TIME_STEPS,
        help=f"Number of simulation time steps (default: {TIME_STEPS})"
    )
    parser.add_argument(
        "--llm-ratio", type=float, default=FEATHERLESS_AGENT_RATIO,
        help=f"Ratio of agents using LLM (default: {FEATHERLESS_AGENT_RATIO})"
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Disable LLM and use only rule-based decisions"
    )
    parser.add_argument(
        "--no-shocks", action="store_true",
        help="Disable random shocks during simulation"
    )
    parser.add_argument(
        "--experiments", action="store_true",
        help="Run full experiment suite"
    )
    parser.add_argument(
        "--plot", action="store_true",
        help="Generate visualization plots"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--attack", type=str, choices=["degree", "betweenness", "random"],
        help="Apply targeted attack before simulation"
    )
    # Dynamic Entry Arguments
    parser.add_argument(
        "--dynamic-entry", action="store_true",
        help="Enable dynamic institution entry during simulation"
    )
    parser.add_argument(
        "--entry-time", type=int, default=None,
        help="Time step when new institution enters (default: mid-simulation)"
    )
    parser.add_argument(
        "--entry-profile", type=str, default="balanced",
        choices=["conservative", "balanced", "aggressive", "stabilizer"],
        help="Risk profile of new entrant (default: balanced)"
    )
    parser.add_argument(
        "--entry-capital", type=float, default=150.0,
        help="Capital of new entrant (default: 150)"
    )
    parser.add_argument(
        "--entry-strategy", type=str, default="preferential",
        choices=["preferential", "random", "targeted"],
        help="Connection strategy for new entrant (default: preferential)"
    )
    # V2 Mode Arguments
    parser.add_argument(
        "--v2", action="store_true",
        help="Run v2 simulation with balance sheets and transaction ledger"
    )
    parser.add_argument(
        "--banks", type=int, default=20,
        help="Number of banks for v2 mode (default: 20)"
    )
    
    args = parser.parse_args()
    
    # ============================================================
    # V2 MODE: Balance Sheet-Based Simulation
    # ============================================================
    if args.v2:
        return run_v2_mode(args)
    
    # ============================================================
    # V1 MODE: Original Network Simulation
    # ============================================================
    print("=" * 60)
    print("🏦 FINANCIAL NETWORK GAME-THEORETIC SIMULATION (v1)")
    print("   Network-Based Modeling of Financial Infrastructure")
    print("=" * 60)
    print()
    
    # Initialize LLM decision function
    llm_decision_fn = None
    if not args.no_llm:
        llm_decision_fn = create_llm_decision_function()
    else:
        print("ℹ️  Running in rule-based mode (--no-llm flag set)\n")
    
    # Run experiment suite if requested
    if args.experiments:
        print("🔬 Running Experiment Suite...")
        print("-" * 40)
        results = run_experiment_suite(
            llm_decision_fn=llm_decision_fn,
            verbose=not args.quiet
        )
        print("\n✅ Experiments complete. Results saved to experiment_results/")
        return
    
    # Create financial network
    print(f"📊 Creating financial network with {args.agents} institutions...")
    G = create_financial_network(args.agents)
    
    # Print network statistics
    stats = get_network_stats(G)
    print(f"   Nodes: {stats['num_nodes']}, Edges: {stats['num_edges']}")
    print(f"   Average degree: {stats['avg_degree']:.2f}")
    print(f"   Total capital: ${stats['total_capital']:,.2f}")
    print(f"   Total exposure: ${stats['total_exposure']:,.2f}")
    
    # Identify systemically important institutions
    sifis = identify_systemically_important(G, top_n=5)
    print(f"   Systemically important nodes: {sifis}")
    print()
    
    # Create agents
    print(f"🤖 Creating agents ({args.llm_ratio:.0%} LLM-enabled)...")
    agents = [
        FinancialAgent(i, use_llm=(i < args.agents * args.llm_ratio))
        for i in G.nodes
    ]
    llm_agents = sum(1 for a in agents if a.use_llm)
    print(f"   {llm_agents} LLM agents, {len(agents) - llm_agents} rule-based agents")
    print()
    
    # Apply targeted attack if specified
    if args.attack:
        print(f"⚡ Applying {args.attack} targeted attack...")
        targets, attack_details = targeted_attack(G, args.attack, num_targets=3)
        print(f"   Attacked nodes: {targets}")
        print(f"   Capital reduced by: ${attack_details['magnitude']:.2f}")
        print()
    
    # Run simulation (standard or with dynamic entry)
    if args.dynamic_entry:
        entry_time = args.entry_time if args.entry_time else args.steps // 2
        print(f"🔄 Running simulation with DYNAMIC ENTRY at step {entry_time}...")
        print(f"   New entrant profile: {args.entry_profile}")
        print(f"   Capital: ${args.entry_capital:.2f}, Strategy: {args.entry_strategy}")
        print("-" * 40)
        
        entry_config = {
            "capital": args.entry_capital,
            "liquidity": args.entry_capital * 0.5,
            "risk_profile": args.entry_profile,
            "connect_strategy": args.entry_strategy,
            "use_llm": llm_decision_fn is not None,
            "institution_type": "stabilizer" if args.entry_profile == "stabilizer" else "bank"
        }
        
        history = run_dynamic_entry_simulation(
            G=G,
            agents=agents,
            llm_decision_fn=llm_decision_fn,
            steps=args.steps,
            entry_time=entry_time,
            entry_config=entry_config,
            enable_shocks=not args.no_shocks
        )
    else:
        print(f"🔄 Running simulation for {args.steps} time steps...")
        print("-" * 40)
        
        history = run_simulation(
            G=G,
            agents=agents,
            llm_decision_fn=llm_decision_fn,
            steps=args.steps,
            enable_shocks=not args.no_shocks
        )
    
    print("-" * 40)
    
    # Compute and display metrics
    metrics = compute_all_metrics(G, history)
    risk_indicators = compute_risk_indicators(G)
    
    report = generate_report(metrics, risk_indicators, history)
    print(report)
    
    # Generate plots if requested
    if args.plot:
        print("📈 Generating plots...")
        try:
            plot_simulation_results(history, save_path="simulation_results.png")
            plot_network_state(G, save_path="network_state.png")
        except Exception as e:
            print(f"   Warning: Could not generate plots: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if history["summary"]["system_collapsed"]:
        print("💥 RESULT: SYSTEM COLLAPSE - All institutions defaulted!")
    else:
        print(f"✅ RESULT: System survived with {metrics['surviving_nodes']} institutions")
    print("=" * 60)
    
    return history


def run_v2_mode(args):
    """
    Run v2 simulation with balance sheets and transaction ledger.
    """
    from core.simulation_v2 import run_simulation_v2, SimulationConfig
    from featherless.decision_engine import get_strategic_priority, create_featherless_client
    
    # Create Featherless priority function
    featherless_fn = None
    if not args.no_llm:
        try:
            client = create_featherless_client()
            def featherless_fn(observation):
                return get_strategic_priority(observation, client)
            print("✅ Featherless.ai client initialized for v2.\n")
        except Exception as e:
            print(f"⚠️  Featherless unavailable: {e}")
            print("   Using rule-based priorities.\n")
    
    # Configure simulation
    config = SimulationConfig(
        num_banks=args.banks,
        num_steps=args.steps,
        use_featherless=featherless_fn is not None,
        verbose=not args.quiet if hasattr(args, 'quiet') else True
    )
    
    # Run v2 simulation
    history = run_simulation_v2(config, featherless_fn)
    
    return history


if __name__ == "__main__":
    main()

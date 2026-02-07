"""
Financial Agent definition with strategic decision-making capabilities.
Agents represent banks, exchanges, and clearing houses.
"""
import numpy as np
from typing import Dict, Any, Optional
import networkx as nx


class FinancialAgent:
    """
    Represents a financial institution making strategic decisions.
    
    Strategies:
        - Credit: LOW (conservative), MEDIUM (balanced), HIGH (aggressive)
        - Margin: TIGHT (high requirements), NORMAL, LOOSE (low requirements)
    
    Risk Profiles:
        - conservative: Low credit, tight margins (new cautious entrant)
        - balanced: Medium credit, normal margins (default)
        - aggressive: High credit, loose margins (market disruptor)
        - stabilizer: Medium credit, tight margins (regulatory vehicle)
    """
    
    CREDIT_MULTIPLIERS = {"LOW": 0.7, "MEDIUM": 1.0, "HIGH": 1.4}
    MARGIN_MULTIPLIERS = {"TIGHT": 1.3, "NORMAL": 1.0, "LOOSE": 0.7}
    
    # Risk profile presets for dynamic entrants
    RISK_PROFILES = {
        "conservative": {"credit": "LOW", "margin": "TIGHT"},
        "balanced": {"credit": "MEDIUM", "margin": "NORMAL"},
        "aggressive": {"credit": "HIGH", "margin": "LOOSE"},
        "stabilizer": {"credit": "MEDIUM", "margin": "TIGHT"},
    }
    
    def __init__(self, agent_id: int, use_llm: bool = False, risk_profile: str = "balanced"):
        """
        Initialize a financial agent.
        
        Args:
            agent_id: Unique identifier matching graph node ID
            use_llm: Whether to use Featherless.ai for decision-making
            risk_profile: Initial behavior preset ("conservative", "balanced", "aggressive", "stabilizer")
        """
        self.id = agent_id
        self.use_llm = use_llm
        self.risk_profile = risk_profile
        self.is_dynamic_entrant = False  # Set True for mid-simulation entrants
        
        # Initialize strategy based on risk profile
        profile = self.RISK_PROFILES.get(risk_profile, self.RISK_PROFILES["balanced"])
        self.credit_strategy = profile["credit"]
        self.margin_strategy = profile["margin"]
        self.decision_history = []
        
    def observe(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Observe local network state under incomplete information.
        Agent can only see immediate neighbors, not global state.
        
        Args:
            G: The financial network graph
            
        Returns:
            Dictionary of observable state variables
        """
        neighbors = list(G.neighbors(self.id))
        predecessors = list(G.predecessors(self.id))
        
        # Calculate neighbor default rate (visible information)
        neighbor_default_rate = np.mean(
            [G.nodes[n]["defaulted"] for n in neighbors]
        ) if neighbors else 0.0
        
        # Calculate exposure at risk
        exposure_at_risk = sum(
            G.edges[self.id, v]["exposure"] 
            for _, v in G.out_edges(self.id)
            if G.nodes[v]["defaulted"]
        )
        
        # Incoming obligations
        incoming_obligations = sum(
            G.edges[u, self.id]["exposure"]
            for u, _ in G.in_edges(self.id)
        )
        
        return {
            "agent_id": self.id,
            "capital": G.nodes[self.id]["capital"],
            "liquidity": G.nodes[self.id]["liquidity"],
            "type": G.nodes[self.id]["type"],
            "neighbor_default_rate": round(neighbor_default_rate, 3),
            "num_neighbors": len(neighbors),
            "num_predecessors": len(predecessors),
            "exposure_at_risk": round(exposure_at_risk, 2),
            "incoming_obligations": round(incoming_obligations, 2),
            "current_credit_strategy": self.credit_strategy,
            "current_margin_strategy": self.margin_strategy,
        }
    
    def make_rule_based_decision(self, observation: Dict[str, Any]) -> Dict[str, str]:
        """
        Make a strategic decision using rule-based logic.
        Used when LLM is not available or for baseline comparison.
        
        Args:
            observation: Current observable state
            
        Returns:
            Dictionary with credit and margin strategy
        """
        capital = observation["capital"]
        liquidity = observation["liquidity"]
        default_rate = observation["neighbor_default_rate"]
        exposure_at_risk = observation["exposure_at_risk"]
        
        # Credit strategy based on risk assessment
        if default_rate > 0.3 or capital < 50:
            credit = "LOW"
        elif default_rate < 0.1 and capital > 80 and liquidity > 40:
            credit = "HIGH"
        else:
            credit = "MEDIUM"
        
        # Margin strategy based on liquidity and network stress
        if liquidity < 30 or exposure_at_risk > 20:
            margin = "TIGHT"
        elif liquidity > 50 and default_rate < 0.1:
            margin = "LOOSE"
        else:
            margin = "NORMAL"
            
        return {"credit": credit, "margin": margin}
    
    def update_strategy(self, decision: Dict[str, str]):
        """
        Update agent's strategy based on decision.
        
        Args:
            decision: Dictionary with 'credit' and 'margin' keys
        """
        if decision.get("credit") in self.CREDIT_MULTIPLIERS:
            self.credit_strategy = decision["credit"]
        if decision.get("margin") in self.MARGIN_MULTIPLIERS:
            self.margin_strategy = decision["margin"]
        
        self.decision_history.append(decision)
    
    def apply_strategy(self, G: nx.DiGraph):
        """
        Apply current strategy to modify network exposures and margins.
        
        Args:
            G: The financial network graph (modified in place)
        """
        credit_mult = self.CREDIT_MULTIPLIERS[self.credit_strategy]
        margin_mult = self.MARGIN_MULTIPLIERS[self.margin_strategy]
        
        for _, v in G.out_edges(self.id):
            # Adjust credit exposure based on strategy
            base_exposure = G.edges[self.id, v].get("base_exposure")
            if base_exposure is None:
                base_exposure = G.edges[self.id, v]["exposure"]
                G.edges[self.id, v]["base_exposure"] = base_exposure
            
            G.edges[self.id, v]["exposure"] = base_exposure * credit_mult
            
            # Adjust margin requirements
            base_margin = G.edges[self.id, v].get("base_margin")
            if base_margin is None:
                base_margin = G.edges[self.id, v]["margin_held"]
                G.edges[self.id, v]["base_margin"] = base_margin
                
            G.edges[self.id, v]["margin_held"] = base_margin * margin_mult
    
    def __repr__(self):
        return f"FinancialAgent(id={self.id}, llm={self.use_llm}, credit={self.credit_strategy}, margin={self.margin_strategy})"

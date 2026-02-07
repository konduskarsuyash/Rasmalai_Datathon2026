"""
Training Data Collection System
Collects decision points, outcomes, and features for ML training
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import csv
from pathlib import Path
from datetime import datetime
import os


@dataclass
class LendingDecisionPoint:
    """Single lending decision observation"""
    # Timestamp
    timestamp: str
    simulation_id: str
    step: int
    
    # Decision
    lender_id: int
    borrower_id: int
    decision: str  # LEND, REJECT, REDUCE, EXTEND
    amount: float
    
    # Borrower features (financial health)
    borrower_capital_ratio: float
    borrower_leverage: float
    borrower_liquidity_ratio: float
    borrower_equity: float
    borrower_cash: float
    borrower_market_exposure: float
    borrower_past_defaults: int
    borrower_risk_appetite: float
    
    # Network features
    borrower_centrality: float
    borrower_degree: int
    borrower_upstream_exposure: float
    borrower_downstream_exposure: float
    borrower_clustering: float
    
    # Market features
    market_stress: float
    market_volatility: float
    market_liquidity: float
    
    # Lender context
    lender_capital_ratio: float
    lender_equity: float
    lender_cash: float
    
    # Exposure context
    exposure_ratio: float  # amount / lender_equity
    
    # Outcome (filled later)
    borrower_defaulted_t5: Optional[int] = None  # Default within 5 steps
    borrower_defaulted_t10: Optional[int] = None  # Default within 10 steps
    cascade_triggered: Optional[int] = None
    cascade_size: Optional[int] = None
    system_stress_increase: Optional[float] = None


@dataclass
class SimulationOutcome:
    """Overall simulation outcomes"""
    simulation_id: str
    num_banks: int
    num_steps: int
    total_defaults: int
    cascade_events: int
    max_cascade_size: int
    final_system_stress: float
    use_game_theory: bool
    use_featherless: bool


class TrainingDataCollector:
    """
    Collects training data from simulations
    Stores decision points and outcomes for ML training
    """
    
    def __init__(self, output_dir: str = "training_data"):
        """
        Initialize data collector
        
        Args:
            output_dir: Directory to save training data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.decision_points: List[LendingDecisionPoint] = []
        self.simulation_outcomes: List[SimulationOutcome] = []
        
        self.current_simulation_id = None
        self.enabled = False
    
    def start_collection(self, simulation_id: Optional[str] = None):
        """Start collecting data for a new simulation"""
        if simulation_id is None:
            simulation_id = f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_simulation_id = simulation_id
        self.enabled = True
        print(f"📊 Data collection started: {simulation_id}")
    
    def stop_collection(self):
        """Stop collecting data"""
        self.enabled = False
        print(f"📊 Data collection stopped")
    
    def record_lending_decision(
        self,
        step: int,
        lender_state: Dict,
        borrower_state: Dict,
        network_metrics: Dict,
        market_state: Dict,
        decision: str,
        amount: float
    ):
        """
        Record a lending decision point
        
        Args:
            step: Current simulation step
            lender_state: Lender bank's state
            borrower_state: Borrower bank's state
            network_metrics: Network connectivity metrics
            market_state: Market conditions
            decision: Decision made (LEND, REJECT, etc.)
            amount: Lending amount
        """
        if not self.enabled:
            return
        
        lender_equity = lender_state.get('equity', 100)
        exposure_ratio = amount / lender_equity if lender_equity > 0 else 0.0
        
        decision_point = LendingDecisionPoint(
            timestamp=datetime.now().isoformat(),
            simulation_id=self.current_simulation_id,
            step=step,
            
            lender_id=lender_state.get('bank_id', 0),
            borrower_id=borrower_state.get('bank_id', 0),
            decision=decision,
            amount=amount,
            
            # Borrower features
            borrower_capital_ratio=borrower_state.get('capital_ratio', 0.08),
            borrower_leverage=borrower_state.get('leverage', 1.0),
            borrower_liquidity_ratio=borrower_state.get('liquidity_ratio', 0.5),
            borrower_equity=borrower_state.get('equity', 50),
            borrower_cash=borrower_state.get('cash', 100),
            borrower_market_exposure=borrower_state.get('market_exposure', 0.0),
            borrower_past_defaults=borrower_state.get('past_defaults', 0),
            borrower_risk_appetite=borrower_state.get('risk_appetite', 0.5),
            
            # Network features
            borrower_centrality=network_metrics.get('centrality', 0.0),
            borrower_degree=network_metrics.get('degree', 0),
            borrower_upstream_exposure=network_metrics.get('upstream_exposure', 0.0),
            borrower_downstream_exposure=network_metrics.get('downstream_exposure', 0.0),
            borrower_clustering=network_metrics.get('clustering_coefficient', 0.0),
            
            # Market features
            market_stress=market_state.get('stress', 0.0),
            market_volatility=market_state.get('volatility', 0.0),
            market_liquidity=market_state.get('liquidity_available', 1000.0),
            
            # Lender context
            lender_capital_ratio=lender_state.get('capital_ratio', 0.08),
            lender_equity=lender_equity,
            lender_cash=lender_state.get('cash', 100),
            
            # Exposure
            exposure_ratio=exposure_ratio,
        )
        
        self.decision_points.append(decision_point)
    
    def record_outcome(
        self,
        borrower_id: int,
        defaulted: bool,
        steps_until_default: Optional[int],
        cascade_triggered: bool,
        cascade_size: int
    ):
        """
        Record outcome for borrower after decision
        
        Args:
            borrower_id: ID of borrower
            defaulted: Whether borrower defaulted
            steps_until_default: Steps until default (if defaulted)
            cascade_triggered: Whether cascade was triggered
            cascade_size: Size of cascade
        """
        if not self.enabled:
            return
        
        # Update decision points for this borrower
        for dp in reversed(self.decision_points):
            if dp.borrower_id == borrower_id and dp.simulation_id == self.current_simulation_id:
                steps_since_decision = steps_until_default if steps_until_default else 999
                
                if steps_since_decision <= 5:
                    dp.borrower_defaulted_t5 = 1 if defaulted else 0
                if steps_since_decision <= 10:
                    dp.borrower_defaulted_t10 = 1 if defaulted else 0
                
                dp.cascade_triggered = 1 if cascade_triggered else 0
                dp.cascade_size = cascade_size
    
    def record_simulation_outcome(
        self,
        num_banks: int,
        num_steps: int,
        total_defaults: int,
        cascade_events: int,
        max_cascade_size: int,
        final_system_stress: float,
        use_game_theory: bool,
        use_featherless: bool
    ):
        """Record overall simulation outcome"""
        if not self.enabled:
            return
        
        outcome = SimulationOutcome(
            simulation_id=self.current_simulation_id,
            num_banks=num_banks,
            num_steps=num_steps,
            total_defaults=total_defaults,
            cascade_events=cascade_events,
            max_cascade_size=max_cascade_size,
            final_system_stress=final_system_stress,
            use_game_theory=use_game_theory,
            use_featherless=use_featherless
        )
        
        self.simulation_outcomes.append(outcome)
    
    def save_to_csv(self, filename: Optional[str] = None):
        """
        Save collected data to CSV file
        
        Args:
            filename: Output filename (default: training_data_YYYYMMDD.csv)
        """
        if not self.decision_points:
            print("⚠️ No data to save")
            return
        
        if filename is None:
            filename = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        # Write decision points
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LendingDecisionPoint.__annotations__.keys())
            writer.writeheader()
            
            for dp in self.decision_points:
                writer.writerow(asdict(dp))
        
        print(f"✓ Saved {len(self.decision_points)} decision points to {filepath}")
        
        # Write simulation outcomes
        outcomes_file = self.output_dir / f"outcomes_{filename}"
        with open(outcomes_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=SimulationOutcome.__annotations__.keys())
            writer.writeheader()
            
            for outcome in self.simulation_outcomes:
                writer.writerow(asdict(outcome))
        
        print(f"✓ Saved {len(self.simulation_outcomes)} simulation outcomes to {outcomes_file}")
        
        return filepath
    
    def save_to_json(self, filename: Optional[str] = None):
        """Save collected data to JSON file"""
        if not self.decision_points:
            print("⚠️ No data to save")
            return
        
        if filename is None:
            filename = f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        data = {
            'decision_points': [asdict(dp) for dp in self.decision_points],
            'simulation_outcomes': [asdict(outcome) for outcome in self.simulation_outcomes],
            'metadata': {
                'num_decision_points': len(self.decision_points),
                'num_simulations': len(self.simulation_outcomes),
                'collection_date': datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Saved training data to {filepath}")
        return filepath
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of collected data"""
        if not self.decision_points:
            return {}
        
        total_points = len(self.decision_points)
        
        # Count decisions
        decisions = {}
        for dp in self.decision_points:
            decisions[dp.decision] = decisions.get(dp.decision, 0) + 1
        
        # Count defaults
        defaults_t5 = sum(1 for dp in self.decision_points if dp.borrower_defaulted_t5 == 1)
        defaults_t10 = sum(1 for dp in self.decision_points if dp.borrower_defaulted_t10 == 1)
        
        # Count cascades
        cascades = sum(1 for dp in self.decision_points if dp.cascade_triggered == 1)
        
        return {
            'total_decision_points': total_points,
            'total_simulations': len(self.simulation_outcomes),
            'decisions': decisions,
            'defaults_within_5_steps': defaults_t5,
            'defaults_within_10_steps': defaults_t10,
            'cascades_triggered': cascades,
            'default_rate_t5': defaults_t5 / total_points if total_points > 0 else 0,
            'default_rate_t10': defaults_t10 / total_points if total_points > 0 else 0,
            'cascade_rate': cascades / total_points if total_points > 0 else 0,
        }
    
    def clear(self):
        """Clear collected data"""
        self.decision_points.clear()
        self.simulation_outcomes.clear()
        self.current_simulation_id = None
        print("📊 Data collector cleared")


# Global collector instance
_global_collector = None


def get_data_collector(output_dir: str = "training_data") -> TrainingDataCollector:
    """Get global data collector instance"""
    global _global_collector
    
    if _global_collector is None:
        _global_collector = TrainingDataCollector(output_dir)
    
    return _global_collector


def enable_data_collection(simulation_id: Optional[str] = None):
    """Enable data collection globally"""
    collector = get_data_collector()
    collector.start_collection(simulation_id)


def disable_data_collection():
    """Disable data collection globally"""
    collector = get_data_collector()
    collector.stop_collection()

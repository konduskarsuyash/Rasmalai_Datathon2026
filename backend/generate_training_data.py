"""
Generate meaningful training data for ML risk model by running diverse simulations.

This script runs multiple simulations with varying parameters to create a rich
dataset covering different market conditions, network structures, and stress scenarios.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json
import random

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.simulation_v2 import run_simulation_v2, SimulationConfig, BankConfig
from app.ml.data_collector import TrainingDataCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generate diverse training data from multiple simulation scenarios."""
    
    def __init__(self, output_dir: str = "training_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.collector = TrainingDataCollector()
        
    def create_bank_configs(
        self,
        num_banks: int,
        capital_range: tuple = (80, 150),
        risk_range: tuple = (0.2, 0.6),
        leverage_range: tuple = (2.0, 4.0)
    ) -> List[BankConfig]:
        """Create diverse bank configurations."""
        configs = []
        for i in range(num_banks):
            config = BankConfig(
                initial_capital=random.uniform(*capital_range),
                target_leverage=random.uniform(*leverage_range),
                risk_factor=random.uniform(*risk_range)
            )
            configs.append(config)
        return configs
    
    def run_scenario(
        self,
        scenario_name: str,
        num_banks: int,
        num_steps: int,
        connection_density: float,
        shock_probability: float,
        capital_range: tuple = (80, 150),
        use_game_theory: bool = True
    ) -> Dict[str, Any]:
        """Run a single simulation scenario."""
        
        logger.info(f"Running scenario: {scenario_name}")
        logger.info(f"  Banks: {num_banks}, Steps: {num_steps}, Density: {connection_density:.2f}")
        
        # Create bank configurations
        bank_configs = self.create_bank_configs(num_banks, capital_range)
        
        # Create simulation config
        config = SimulationConfig(
            num_banks=num_banks,
            num_steps=num_steps,
            use_featherless=True,
            use_game_theory=use_game_theory,
            shock_probability=shock_probability,
            verbose=False,
            connection_density=connection_density,
            bank_configs=bank_configs
        )
        
        # Run simulation
        try:
            result = run_simulation_v2(config)
            
            # Extract statistics
            num_defaults = len([b for b in result.get('final_banks', []) if b.get('is_defaulted', False)])
            total_equity = sum(b.get('equity', 0) for b in result.get('final_banks', []))
            
            scenario_result = {
                'scenario': scenario_name,
                'num_banks': num_banks,
                'num_steps': num_steps,
                'connection_density': connection_density,
                'num_defaults': num_defaults,
                'total_equity': total_equity,
                'shock_probability': shock_probability
            }
            
            logger.info(f"  Completed: {num_defaults} defaults, equity: ${total_equity:.1f}M")
            
            return scenario_result
            
        except Exception as e:
            logger.error(f"  Error in scenario {scenario_name}: {e}")
            import traceback
            traceback.print_exc()
            return {'scenario': scenario_name, 'error': str(e)}
    
    def generate_all_scenarios(self):
        """Generate training data from diverse scenarios."""
        
        logger.info("=" * 60)
        logger.info("GENERATING TRAINING DATA FOR ML RISK MODEL")
        logger.info("=" * 60)
        
        scenarios = []
        
        # Scenario Set 1: Healthy market, low stress (15 runs)
        logger.info("\n[SET 1] Healthy Market - Low Stress")
        for i in range(15):
            scenario = self.run_scenario(
                scenario_name=f"healthy_low_stress_{i}",
                num_banks=random.randint(8, 12),
                num_steps=30,
                connection_density=random.uniform(0.15, 0.35),
                shock_probability=0.05,
                capital_range=(100, 150)
            )
            scenarios.append(scenario)
        
        # Scenario Set 2: Moderate stress (15 runs)
        logger.info("\n[SET 2] Moderate Stress")
        for i in range(15):
            scenario = self.run_scenario(
                scenario_name=f"moderate_stress_{i}",
                num_banks=random.randint(10, 15),
                num_steps=35,
                connection_density=random.uniform(0.2, 0.4),
                shock_probability=0.15,
                capital_range=(80, 120)
            )
            scenarios.append(scenario)
        
        # Scenario Set 3: High stress (15 runs)
        logger.info("\n[SET 3] High Stress")
        for i in range(15):
            scenario = self.run_scenario(
                scenario_name=f"high_stress_{i}",
                num_banks=random.randint(12, 18),
                num_steps=40,
                connection_density=random.uniform(0.3, 0.5),
                shock_probability=0.25,
                capital_range=(60, 100)
            )
            scenarios.append(scenario)
        
        # Scenario Set 4: Dense networks (10 runs)
        logger.info("\n[SET 4] Dense Networks")
        for i in range(10):
            scenario = self.run_scenario(
                scenario_name=f"dense_network_{i}",
                num_banks=random.randint(10, 15),
                num_steps=35,
                connection_density=random.uniform(0.5, 0.7),
                shock_probability=0.15,
                capital_range=(80, 130)
            )
            scenarios.append(scenario)
        
        # Scenario Set 5: Sparse networks (10 runs)
        logger.info("\n[SET 5] Sparse Networks")
        for i in range(10):
            scenario = self.run_scenario(
                scenario_name=f"sparse_network_{i}",
                num_banks=random.randint(15, 20),
                num_steps=30,
                connection_density=random.uniform(0.1, 0.2),
                shock_probability=0.1,
                capital_range=(90, 140)
            )
            scenarios.append(scenario)
        
        # Scenario Set 6: Low capital banks (10 runs)
        logger.info("\n[SET 6] Low Capital Banks")
        for i in range(10):
            scenario = self.run_scenario(
                scenario_name=f"low_capital_{i}",
                num_banks=random.randint(10, 15),
                num_steps=35,
                connection_density=random.uniform(0.25, 0.4),
                shock_probability=0.2,
                capital_range=(50, 80)
            )
            scenarios.append(scenario)
        
        # Scenario Set 7: High capital banks (10 runs)
        logger.info("\n[SET 7] High Capital Banks")
        for i in range(10):
            scenario = self.run_scenario(
                scenario_name=f"high_capital_{i}",
                num_banks=random.randint(8, 12),
                num_steps=30,
                connection_density=random.uniform(0.2, 0.35),
                shock_probability=0.1,
                capital_range=(150, 200)
            )
            scenarios.append(scenario)
        
        # Scenario Set 8: Extended simulations (5 runs)
        logger.info("\n[SET 8] Extended Duration")
        for i in range(5):
            scenario = self.run_scenario(
                scenario_name=f"extended_{i}",
                num_banks=random.randint(12, 16),
                num_steps=50,
                connection_density=random.uniform(0.25, 0.4),
                shock_probability=0.15,
                capital_range=(80, 130)
            )
            scenarios.append(scenario)
        
        # Scenario Set 9: No game theory (10 runs) - for comparison
        logger.info("\n[SET 9] Heuristic Decision Making")
        for i in range(10):
            scenario = self.run_scenario(
                scenario_name=f"heuristic_{i}",
                num_banks=random.randint(10, 14),
                num_steps=30,
                connection_density=random.uniform(0.2, 0.4),
                shock_probability=0.15,
                capital_range=(80, 130),
                use_game_theory=False
            )
            scenarios.append(scenario)
        
        logger.info("\n" + "=" * 60)
        logger.info("SCENARIO GENERATION COMPLETE")
        logger.info("=" * 60)
        
        return scenarios
    
    def save_data_and_report(self, scenarios: List[Dict[str, Any]]):
        """Save collected data and generate report."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save training data
        csv_path = self.output_dir / f"training_data_{timestamp}.csv"
        self.collector.save_to_csv(str(csv_path))
        logger.info(f"\n✅ Training data saved: {csv_path}")
        
        # Save JSON format too
        json_path = self.output_dir / f"training_data_{timestamp}.json"
        self.collector.save_to_json(str(json_path))
        logger.info(f"✅ JSON data saved: {json_path}")
        
        # Get statistics
        stats = self.collector.get_summary_stats()
        
        # Save comprehensive report
        report = {
            'timestamp': timestamp,
            'scenarios_run': len(scenarios),
            'data_statistics': stats,
            'scenario_results': scenarios
        }
        
        report_path = self.output_dir / f"data_generation_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Report saved: {report_path}")
        logger.info("\n" + "=" * 60)
        logger.info("DATA GENERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Scenarios: {len(scenarios)}")
        logger.info(f"Total Decisions: {stats['total_decisions']}")
        logger.info(f"Defaults (5 steps): {stats['default_5_steps']}")
        logger.info(f"Defaults (10 steps): {stats['default_10_steps']}")
        logger.info(f"Cascades Triggered: {stats['cascade_triggered']}")
        logger.info(f"Default Rate: {stats['default_rate_5_steps']:.2%}")
        logger.info("=" * 60)
        
        return csv_path


def main():
    """Main entry point."""
    
    generator = TrainingDataGenerator()
    
    # Generate all scenarios
    scenarios = generator.generate_all_scenarios()
    
    # Save data and create report
    csv_path = generator.save_data_and_report(scenarios)
    
    logger.info(f"\n✅ READY FOR TRAINING!")
    logger.info(f"   Run: python train_risk_model.py {csv_path} models/risk_model.pkl")


if __name__ == "__main__":
    main()


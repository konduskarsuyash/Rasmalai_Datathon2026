"""
Generate synthetic training data for ML risk model.

Creates realistic lending scenarios with known outcomes based on financial theory
and empirical relationships from banking literature.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic but realistic training data for credit risk."""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        self.data = []
        
    def generate_borrower_features(self, num_samples, risk_profile='mixed'):
        """Generate borrower financial features."""
        
        if risk_profile == 'healthy':
            capital_ratio_mean, capital_ratio_std = 0.12, 0.03
            leverage_mean, leverage_std = 8.0, 2.0
            liquidity_mean, liquidity_std = 0.3, 0.08
        elif risk_profile == 'stressed':
            capital_ratio_mean, capital_ratio_std = 0.08, 0.02
            leverage_mean, leverage_std = 12.0, 3.0
            liquidity_mean, liquidity_std = 0.15, 0.05
        elif risk_profile == 'distressed':
            capital_ratio_mean, capital_ratio_std = 0.05, 0.015
            leverage_mean, leverage_std = 18.0, 5.0
            liquidity_mean, liquidity_std = 0.08, 0.03
        else:  # mixed
            # Mix of all profiles
            profiles = self.generate_borrower_features(num_samples // 3, 'healthy')
            profiles = pd.concat([profiles, self.generate_borrower_features(num_samples // 3, 'stressed')])
            profiles = pd.concat([profiles, self.generate_borrower_features(num_samples - 2*(num_samples//3), 'distressed')])
            return profiles.sample(frac=1).reset_index(drop=True)
        
        features = {
            'capital_ratio': np.clip(np.random.normal(capital_ratio_mean, capital_ratio_std, num_samples), 0.01, 0.3),
            'leverage': np.clip(np.random.normal(leverage_mean, leverage_std, num_samples), 1.0, 30.0),
            'liquidity_ratio': np.clip(np.random.normal(liquidity_mean, liquidity_std, num_samples), 0.01, 0.6),
            'roa': np.clip(np.random.normal(0.01, 0.008, num_samples), -0.05, 0.05),
            'asset_quality': np.clip(np.random.beta(8, 2, num_samples), 0.5, 1.0),
        }
        
        return pd.DataFrame(features)
    
    def generate_network_features(self, num_samples):
        """Generate network position features."""
        
        features = {
            'network_centrality': np.random.beta(2, 5, num_samples),  # Most banks not central
            'num_connections': np.random.poisson(5, num_samples),
            'total_exposure': np.random.gamma(2, 20, num_samples),
            'max_single_exposure': np.random.gamma(1.5, 8, num_samples),
            'exposure_concentration': np.random.beta(3, 7, num_samples),
        }
        
        return pd.DataFrame(features)
    
    def generate_market_features(self, num_samples, market_condition='normal'):
        """Generate market condition features."""
        
        if market_condition == 'bull':
            stress_mean, stress_std = 0.15, 0.05
            volatility_mean, volatility_std = 0.015, 0.005
        elif market_condition == 'bear':
            stress_mean, stress_std = 0.75, 0.15
            volatility_mean, volatility_std = 0.045, 0.015
        elif market_condition == 'crisis':
            stress_mean, stress_std = 0.95, 0.03
            volatility_mean, volatility_std = 0.08, 0.02
        else:  # normal
            stress_mean, stress_std = 0.35, 0.15
            volatility_mean, volatility_std = 0.025, 0.008
        
        features = {
            'market_stress_index': np.clip(np.random.normal(stress_mean, stress_std, num_samples), 0, 1),
            'interest_rate': np.clip(np.random.normal(0.05, 0.02, num_samples), 0.01, 0.15),
            'market_volatility': np.clip(np.random.normal(volatility_mean, volatility_std, num_samples), 0.005, 0.15),
        }
        
        return pd.DataFrame(features)
    
    def generate_behavior_features(self, num_samples):
        """Generate behavioral features."""
        
        features = {
            'past_defaults': np.random.choice([0, 0, 0, 1, 2], size=num_samples, p=[0.7, 0.15, 0.1, 0.04, 0.01]),
            'risk_appetite': np.random.beta(5, 5, num_samples),
            'investment_volatility': np.random.beta(2, 8, num_samples),
        }
        
        return pd.DataFrame(features)
    
    def generate_lender_features(self, num_samples):
        """Generate lender-specific features."""
        
        features = {
            'lender_capital_ratio': np.clip(np.random.normal(0.12, 0.03, num_samples), 0.05, 0.25),
            'lender_risk_appetite': np.random.beta(5, 5, num_samples),
        }
        
        return pd.DataFrame(features)
    
    def calculate_default_probability(self, df):
        """Calculate default probability based on features using financial theory."""
        
        # Feature contributions (negative = reduces default risk)
        # Scaled to produce realistic default rates (5-20%)
        capital_effect = -8 * (df['capital_ratio'] - 0.08)
        leverage_effect = 0.15 * (df['leverage'] - 10)
        liquidity_effect = -4 * (df['liquidity_ratio'] - 0.15)
        roa_effect = -30 * df['roa']
        asset_quality_effect = -2 * (df['asset_quality'] - 0.7)
        
        # Network effects
        centrality_effect = 0.8 * df['network_centrality']
        exposure_effect = 0.01 * df['total_exposure']
        concentration_effect = 1.0 * df['exposure_concentration']
        
        # Market effects
        market_stress_effect = 2.5 * df['market_stress_index']
        volatility_effect = 12 * df['market_volatility']
        rate_effect = 5 * (df['interest_rate'] - 0.05)
        
        # Behavioral effects
        past_defaults_effect = 1.2 * df['past_defaults']
        risk_appetite_effect = 1.0 * (df['risk_appetite'] - 0.5)
        inv_volatility_effect = 1.5 * df['investment_volatility']
        
        # Lender effects
        lender_effect = 0.5 * (df['lender_risk_appetite'] - 0.5)
        
        # Combine all effects with proper baseline
        log_odds = (
            -4.2 +  # Baseline log-odds (gives ~1.5% base rate)
            capital_effect + leverage_effect + liquidity_effect + roa_effect + asset_quality_effect +
            centrality_effect + exposure_effect + concentration_effect +
            market_stress_effect + volatility_effect + rate_effect +
            past_defaults_effect + risk_appetite_effect + inv_volatility_effect +
            lender_effect
        )
        
        # Convert to probability using logistic function
        probability = 1 / (1 + np.exp(-log_odds))
        
        return np.clip(probability, 0.001, 0.999)
    
    def calculate_cascade_risk(self, df, default_prob):
        """Calculate cascade risk."""
        
        # Cascade more likely if:
        # - Borrower is central
        # - High total exposure
        # - Market is stressed
        # - Already likely to default
        
        cascade_score = (
            2.0 * df['network_centrality'] +
            0.03 * df['total_exposure'] +
            1.5 * df['market_stress_index'] +
            2.0 * default_prob
        )
        
        cascade_prob = 1 / (1 + np.exp(-cascade_score + 3))
        return np.clip(cascade_prob, 0.001, 0.999)
    
    def generate_dataset(
        self,
        num_samples=10000,
        market_distribution={'normal': 0.5, 'bull': 0.2, 'bear': 0.2, 'crisis': 0.1},
        borrower_distribution={'healthy': 0.5, 'stressed': 0.3, 'distressed': 0.2}
    ):
        """Generate complete dataset with all features and labels."""
        
        logger.info(f"Generating {num_samples} synthetic training samples...")
        
        # Calculate samples per market condition
        market_samples = {
            condition: int(num_samples * prob)
            for condition, prob in market_distribution.items()
        }
        
        all_data = []
        
        for market_condition, n_samples in market_samples.items():
            if n_samples == 0:
                continue
                
            logger.info(f"  Generating {n_samples} samples for {market_condition} market...")
            
            # Generate features
            borrower_df = self.generate_borrower_features(n_samples, 'mixed')
            network_df = self.generate_network_features(n_samples)
            market_df = self.generate_market_features(n_samples, market_condition)
            behavior_df = self.generate_behavior_features(n_samples)
            lender_df = self.generate_lender_features(n_samples)
            
            # Combine all features
            df = pd.concat([borrower_df, network_df, market_df, behavior_df, lender_df], axis=1)
            
            # Add loan amount
            df['loan_amount'] = np.random.gamma(3, 5, n_samples)
            
            # Calculate target variables (before renaming)
            df['default_prob'] = self.calculate_default_probability(df)
            df['cascade_risk'] = self.calculate_cascade_risk(df, df['default_prob'])
            
            # Rename columns to match training script expectations
            df.rename(columns={
                'capital_ratio': 'borrower_capital_ratio',
                'leverage': 'borrower_leverage',
                'liquidity_ratio': 'borrower_liquidity_ratio',
                'roa': 'borrower_roa',
                'asset_quality': 'borrower_asset_quality',
                'network_centrality': 'borrower_network_centrality',
                'num_connections': 'loan_network_degree',
                'total_exposure': 'loan_total_interbank_exposure',
                'max_single_exposure': 'loan_max_single_counterparty_exposure',
                'exposure_concentration': 'loan_exposure_concentration',
                'risk_appetite': 'borrower_risk_appetite',
                'investment_volatility': 'borrower_investment_volatility',
                'past_defaults': 'borrower_past_defaults'
            }, inplace=True)
            
            # Add borrower equity (derived from capital ratio)
            df['borrower_equity'] = df['borrower_capital_ratio'] * 100  # Assuming ~100M assets
            
            # Generate binary outcomes (for classification) with corrected names
            df['borrower_defaulted_t5'] = (np.random.random(n_samples) < df['default_prob']).astype(int)
            df['borrower_defaulted_t10'] = (np.random.random(n_samples) < df['default_prob'] * 1.3).astype(int)
            df['cascade_triggered'] = (np.random.random(n_samples) < df['cascade_risk']).astype(int)
            
            all_data.append(df)
        
        # Combine all market conditions
        full_df = pd.concat(all_data, ignore_index=True)
        
        # Shuffle
        full_df = full_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        logger.info(f"✅ Generated {len(full_df)} samples")
        logger.info(f"   Default rate (5 steps): {full_df['borrower_defaulted_t5'].mean():.2%}")
        logger.info(f"   Default rate (10 steps): {full_df['borrower_defaulted_t10'].mean():.2%}")
        logger.info(f"   Cascade rate: {full_df['cascade_triggered'].mean():.2%}")
        
        return full_df
    
    def save_dataset(self, df, output_dir='training_data'):
        """Save the generated dataset."""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_path / f"synthetic_training_data_{timestamp}.csv"
        
        df.to_csv(csv_path, index=False)
        logger.info(f"💾 Dataset saved to: {csv_path}")
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'num_samples': len(df),
            'features': list(df.columns),
            'default_rate_5': float(df['borrower_defaulted_t5'].mean()),
            'default_rate_10': float(df['borrower_defaulted_t10'].mean()),
            'cascade_rate': float(df['cascade_triggered'].mean()),
            'feature_stats': df.describe().to_dict()
        }
        
        import json
        metadata_path = output_path / f"synthetic_metadata_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"📋 Metadata saved to: {metadata_path}")
        
        return csv_path


def main():
    """Generate synthetic training data."""
    
    logger.info("=" * 60)
    logger.info("SYNTHETIC TRAINING DATA GENERATION")
    logger.info("=" * 60)
    
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate 10,000 training samples
    df = generator.generate_dataset(
        num_samples=10000,
        market_distribution={
            'normal': 0.50,  # 50% normal market
            'bull': 0.20,    # 20% bull market
            'bear': 0.20,    # 20% bear market
            'crisis': 0.10   # 10% crisis
        }
    )
    
    # Save dataset
    csv_path = generator.save_dataset(df)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ DATA GENERATION COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"\n📊 Next step: Train the model")
    logger.info(f"   python train_risk_model.py {csv_path} models/risk_model.pkl")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

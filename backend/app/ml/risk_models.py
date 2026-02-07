"""
ML-Based Credit Risk Assessment System
Implements supervised learning for predicting default probabilities and systemic risk.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import math
import os
import pickle
from pathlib import Path
# Default path to trained XGBoost model
DEFAULT_MODEL_PATH = "models/risk_model.pkl"

class RiskLevel(Enum):
    """Risk level classification"""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


@dataclass
class RiskPrediction:
    """Risk prediction output"""
    default_probability: float  # 0.0 to 1.0
    expected_loss: float  # Dollar amount
    systemic_impact: float  # 0.0 to 1.0
    cascade_risk: float  # 0.0 to 1.0
    risk_level: RiskLevel
    recommendation: str  # EXTEND_CREDIT, HOLD, REDUCE_EXPOSURE, REJECT
    confidence: float  # Model confidence
    reasons: List[str]  # Human-readable reasons


class SimpleRiskScorer:
    """
    Rule-based risk scorer (no ML training needed)
    Uses domain knowledge weighted factors
    Serves as baseline and fallback when ML model unavailable
    """
    
    def __init__(self):
        """Initialize with calibrated weights"""
        self.weights = {
            'financial_health': 0.35,
            'network_position': 0.25,
            'behavior_pattern': 0.20,
            'market_conditions': 0.15,
            'exposure_concentration': 0.05
        }
    
    def calculate_risk_score(
        self,
        borrower_state: Dict,
        lender_state: Dict,
        network_metrics: Dict,
        market_state: Dict,
        exposure_amount: float = 0.0
    ) -> RiskPrediction:
        """
        Calculate comprehensive risk score
        
        Args:
            borrower_state: Borrower bank's financial state
            lender_state: Lender bank's state
            network_metrics: Network connectivity metrics
            market_state: Market conditions
            exposure_amount: Proposed lending amount
            
        Returns:
            RiskPrediction with score and recommendations
        """
        risk_components = {}
        reasons = []
        
        # 1. Financial Health Score (35% weight)
        financial_risk = self._score_financial_health(borrower_state, reasons)
        risk_components['financial'] = financial_risk * self.weights['financial_health']
        
        # 2. Network Position Score (25% weight)
        network_risk = self._score_network_position(borrower_state, network_metrics, reasons)
        risk_components['network'] = network_risk * self.weights['network_position']
        
        # 3. Behavior Pattern Score (20% weight)
        behavior_risk = self._score_behavior(borrower_state, reasons)
        risk_components['behavior'] = behavior_risk * self.weights['behavior_pattern']
        
        # 4. Market Conditions Score (15% weight)
        market_risk = self._score_market_conditions(market_state, reasons)
        risk_components['market'] = market_risk * self.weights['market_conditions']
        
        # 5. Exposure Concentration Score (5% weight)
        concentration_risk = self._score_exposure_concentration(
            lender_state, borrower_state, exposure_amount, reasons
        )
        risk_components['concentration'] = concentration_risk * self.weights['exposure_concentration']
        
        # Total risk score
        total_risk = sum(risk_components.values())
        total_risk = min(max(total_risk, 0.0), 1.0)  # Clamp to [0, 1]
        
        # Calculate derived metrics
        borrower_equity = borrower_state.get('equity', 50)
        expected_loss = total_risk * exposure_amount if exposure_amount > 0 else total_risk * borrower_equity * 0.1
        
        # Systemic impact based on network centrality
        centrality = network_metrics.get('centrality', 0.0)
        systemic_impact = total_risk * (0.5 + 0.5 * centrality)  # Higher for central nodes
        
        # Cascade risk (probability of triggering cascade)
        cascade_risk = self._calculate_cascade_risk(total_risk, network_metrics, borrower_state)
        
        # Risk level classification
        risk_level = self._classify_risk_level(total_risk)
        
        # Recommendation
        recommendation = self._generate_recommendation(total_risk, systemic_impact, cascade_risk)
        
        # Confidence (high for rule-based)
        confidence = 0.75
        
        return RiskPrediction(
            default_probability=total_risk,
            expected_loss=expected_loss,
            systemic_impact=systemic_impact,
            cascade_risk=cascade_risk,
            risk_level=risk_level,
            recommendation=recommendation,
            confidence=confidence,
            reasons=reasons
        )
    
    def _score_financial_health(self, borrower_state: Dict, reasons: List[str]) -> float:
        """Score based on capital adequacy, leverage, liquidity"""
        risk = 0.0
        
        capital_ratio = borrower_state.get('capital_ratio', 0.08)
        leverage = borrower_state.get('leverage', 1.0)
        liquidity_ratio = borrower_state.get('liquidity_ratio', 0.5)
        equity = borrower_state.get('equity', 50)
        
        # Capital adequacy (weight: 40%)
        if capital_ratio < 0.06:
            risk += 0.4
            reasons.append(f"⚠️ Low capital ratio: {capital_ratio:.1%}")
        elif capital_ratio < 0.08:
            risk += 0.25
            reasons.append(f"⚠️ Marginal capital: {capital_ratio:.1%}")
        elif capital_ratio < 0.10:
            risk += 0.1
        
        # Leverage (weight: 30%)
        if leverage > 15:
            risk += 0.3
            reasons.append(f"⚠️ High leverage: {leverage:.1f}x")
        elif leverage > 10:
            risk += 0.2
            reasons.append(f"⚠️ Elevated leverage: {leverage:.1f}x")
        elif leverage > 7:
            risk += 0.1
        
        # Liquidity (weight: 20%)
        if liquidity_ratio < 0.15:
            risk += 0.2
            reasons.append(f"⚠️ Liquidity stress: {liquidity_ratio:.1%}")
        elif liquidity_ratio < 0.25:
            risk += 0.1
        
        # Equity cushion (weight: 10%)
        if equity < 20:
            risk += 0.1
            reasons.append(f"⚠️ Low equity: ${equity:.0f}M")
        elif equity < 30:
            risk += 0.05
        
        return min(risk, 1.0)
    
    def _score_network_position(self, borrower_state: Dict, network_metrics: Dict, reasons: List[str]) -> float:
        """Score based on network centrality and exposures"""
        risk = 0.0
        
        centrality = network_metrics.get('centrality', 0.0)
        degree = network_metrics.get('degree', 0)
        upstream_exposure = network_metrics.get('upstream_exposure', 0)
        downstream_exposure = network_metrics.get('downstream_exposure', 0)
        
        # High centrality = systemic importance = higher risk
        if centrality > 0.7:
            risk += 0.4
            reasons.append(f"🕸️ Systemically important (centrality: {centrality:.2f})")
        elif centrality > 0.5:
            risk += 0.25
        elif centrality > 0.3:
            risk += 0.1
        
        # High degree = many connections = contagion risk
        if degree > 8:
            risk += 0.3
            reasons.append(f"🕸️ Highly connected: {degree} counterparties")
        elif degree > 5:
            risk += 0.15
        
        # Upstream exposure (how much it owes)
        equity = borrower_state.get('equity', 50)
        if equity > 0:
            upstream_ratio = upstream_exposure / equity
            if upstream_ratio > 3.0:
                risk += 0.2
                reasons.append(f"💰 Heavy debt burden: {upstream_ratio:.1f}x equity")
            elif upstream_ratio > 2.0:
                risk += 0.1
        
        return min(risk, 1.0)
    
    def _score_behavior(self, borrower_state: Dict, reasons: List[str]) -> float:
        """Score based on past behavior and risk-taking"""
        risk = 0.0
        
        past_defaults = borrower_state.get('past_defaults', 0)
        market_exposure = borrower_state.get('market_exposure', 0.0)
        investment_volatility = borrower_state.get('investment_volatility', 0.0)
        risk_appetite = borrower_state.get('risk_appetite', 0.5)
        
        # Default history
        if past_defaults > 2:
            risk += 0.5
            reasons.append(f"📉 Multiple defaults: {past_defaults}")
        elif past_defaults > 0:
            risk += 0.25
            reasons.append(f"📉 Past default: {past_defaults}")
        
        # Market exposure
        if market_exposure > 0.25:
            risk += 0.3
            reasons.append(f"📊 High market exposure: {market_exposure:.1%}")
        elif market_exposure > 0.15:
            risk += 0.15
        
        # Investment volatility
        if investment_volatility > 0.7:
            risk += 0.2
            reasons.append(f"📈 Volatile investments: {investment_volatility:.2f}")
        
        return min(risk, 1.0)
    
    def _score_market_conditions(self, market_state: Dict, reasons: List[str]) -> float:
        """Score based on overall market stress"""
        risk = 0.0
        
        market_stress = market_state.get('stress', 0.0)
        volatility = market_state.get('volatility', 0.0)
        liquidity_available = market_state.get('liquidity_available', 1000)
        
        # Market stress
        if market_stress > 0.6:
            risk += 0.6
            reasons.append(f"🌪️ High market stress: {market_stress:.1%}")
        elif market_stress > 0.4:
            risk += 0.4
            reasons.append(f"🌪️ Elevated stress: {market_stress:.1%}")
        elif market_stress > 0.2:
            risk += 0.2
        
        # Volatility
        if volatility > 0.5:
            risk += 0.3
        elif volatility > 0.3:
            risk += 0.15
        
        # Liquidity crunch
        if liquidity_available < 200:
            risk += 0.1
        
        return min(risk, 1.0)
    
    def _score_exposure_concentration(
        self, lender_state: Dict, borrower_state: Dict, exposure_amount: float, reasons: List[str]
    ) -> float:
        """Score based on concentration of exposure"""
        risk = 0.0
        
        lender_equity = lender_state.get('equity', 100)
        
        if exposure_amount > 0 and lender_equity > 0:
            concentration = exposure_amount / lender_equity
            
            if concentration > 0.5:
                risk += 0.8
                reasons.append(f"⚠️ Concentrated exposure: {concentration:.1%} of equity")
            elif concentration > 0.3:
                risk += 0.5
            elif concentration > 0.2:
                risk += 0.3
        
        return min(risk, 1.0)
    
    def _calculate_cascade_risk(self, base_risk: float, network_metrics: Dict, borrower_state: Dict) -> float:
        """Calculate probability of triggering cascade"""
        centrality = network_metrics.get('centrality', 0.0)
        degree = network_metrics.get('degree', 0)
        
        # Cascade risk = base risk × network amplification
        network_amplification = 1.0 + centrality * 0.5 + min(degree / 10, 0.5)
        cascade_risk = base_risk * network_amplification
        
        return min(cascade_risk, 1.0)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk into levels"""
        if risk_score < 0.15:
            return RiskLevel.VERY_LOW
        elif risk_score < 0.30:
            return RiskLevel.LOW
        elif risk_score < 0.50:
            return RiskLevel.MEDIUM
        elif risk_score < 0.70:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_recommendation(self, risk_score: float, systemic_impact: float, cascade_risk: float) -> str:
        """Generate lending recommendation"""
        if risk_score > 0.7 or systemic_impact > 0.7:
            return "REJECT"
        elif risk_score > 0.5 or cascade_risk > 0.6:
            return "REDUCE_EXPOSURE"
        elif risk_score > 0.3:
            return "HOLD"
        elif risk_score < 0.2:
            return "EXTEND_CREDIT"
        else:
            return "HOLD"


class MLRiskPredictor:
    """
    Machine Learning-based risk predictor using XGBoost
    Trained on simulation data to predict default probabilities
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML predictor
        
        Args:
            model_path: Path to trained model file
        """
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def extract_features(
        self,
        borrower_state: Dict,
        lender_state: Dict,
        network_metrics: Dict,
        market_state: Dict
    ) -> np.ndarray:
        """
        Extract feature vector for ML model
        Matches the 8 features used in training:
        1. borrower_capital_ratio
        2. borrower_leverage
        3. borrower_liquidity_ratio
        4. borrower_equity
        5. borrower_past_defaults
        6. borrower_risk_appetite
        7. market_volatility
        8. lender_capital_ratio
        
        Returns:
            numpy array of features
        """
        features = [
            borrower_state.get('capital_ratio', 0.08),
            borrower_state.get('leverage', 10.0),
            borrower_state.get('liquidity_ratio', 0.2),
            borrower_state.get('equity', 100.0),
            float(borrower_state.get('past_defaults', 0)),
            borrower_state.get('risk_appetite', 0.5),
            market_state.get('volatility', 0.02),
            lender_state.get('capital_ratio', 0.10),
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(
        self,
        borrower_state: Dict,
        lender_state: Dict,
        network_metrics: Dict,
        market_state: Dict,
        exposure_amount: float = 0.0
    ) -> RiskPrediction:
        """
        Predict risk using trained ML model
        
        Returns:
            RiskPrediction with ML-based estimates
        """
        if not self.is_trained:
            # Fall back to simple scorer
            simple_scorer = SimpleRiskScorer()
            return simple_scorer.calculate_risk_score(
                borrower_state, lender_state, network_metrics, market_state, exposure_amount
            )
        
        # Extract features
        features = self.extract_features(borrower_state, lender_state, network_metrics, market_state)
        
        # Predict default probability
        default_prob = self.model.predict_proba(features)[0][1]
        
        # Calculate derived metrics
        borrower_equity = borrower_state.get('equity', 50)
        expected_loss = default_prob * (exposure_amount if exposure_amount > 0 else borrower_equity * 0.1)
        
        centrality = network_metrics.get('centrality', 0.0)
        systemic_impact = default_prob * (0.5 + 0.5 * centrality)
        
        cascade_risk = self._calculate_ml_cascade_risk(default_prob, network_metrics)
        
        risk_level = self._classify_risk_level(default_prob)
        recommendation = self._generate_recommendation(default_prob, systemic_impact, cascade_risk)
        
        reasons = self._generate_ml_reasons(default_prob, features[0], borrower_state, network_metrics)
        
        return RiskPrediction(
            default_probability=default_prob,
            expected_loss=expected_loss,
            systemic_impact=systemic_impact,
            cascade_risk=cascade_risk,
            risk_level=risk_level,
            recommendation=recommendation,
            confidence=0.85,  # ML models have higher confidence
            reasons=reasons
        )
    
    def _calculate_ml_cascade_risk(self, default_prob: float, network_metrics: Dict) -> float:
        """Calculate cascade risk from ML prediction"""
        centrality = network_metrics.get('centrality', 0.0)
        degree = network_metrics.get('degree', 0)
        
        network_amplification = 1.0 + centrality * 0.6 + min(degree / 10, 0.4)
        cascade_risk = default_prob * network_amplification
        
        return min(cascade_risk, 1.0)
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify risk level"""
        if risk_score < 0.15:
            return RiskLevel.VERY_LOW
        elif risk_score < 0.30:
            return RiskLevel.LOW
        elif risk_score < 0.50:
            return RiskLevel.MEDIUM
        elif risk_score < 0.70:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _generate_recommendation(self, risk_score: float, systemic_impact: float, cascade_risk: float) -> str:
        """Generate recommendation"""
        if risk_score > 0.7 or systemic_impact > 0.7:
            return "REJECT"
        elif risk_score > 0.5 or cascade_risk > 0.6:
            return "REDUCE_EXPOSURE"
        elif risk_score > 0.3:
            return "HOLD"
        elif risk_score < 0.2:
            return "EXTEND_CREDIT"
        else:
            return "HOLD"
    
    def _generate_ml_reasons(
        self, default_prob: float, features: np.ndarray, borrower_state: Dict, network_metrics: Dict
    ) -> List[str]:
        """Generate human-readable reasons from ML prediction"""
        reasons = [f"🤖 ML Model: {default_prob:.1%} default probability"]
        
        if features[1] > 10:  # Leverage
            reasons.append(f"⚠️ High leverage: {features[1]:.1f}x")
        
        if features[0] < 0.08:  # Capital ratio
            reasons.append(f"⚠️ Low capital: {features[0]:.1%}")
        
        if network_metrics.get('centrality', 0) > 0.6:
            reasons.append(f"🕸️ Systemic importance (centrality: {network_metrics['centrality']:.2f})")
        
        if borrower_state.get('past_defaults', 0) > 0:
            reasons.append(f"📉 Default history: {borrower_state['past_defaults']}")
        
        return reasons
    
    def load_model(self, model_path: str):
        """Load trained model from disk"""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            self.is_trained = True
            
            print(f"✓ Loaded ML risk model from {model_path}")
        except Exception as e:
            print(f"⚠️ Failed to load model: {e}")
            self.is_trained = False
    
    def save_model(self, model_path: str):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Saved ML risk model to {model_path}")


# Global risk predictor instance
_risk_predictor = None


def get_risk_predictor(use_ml: bool = True, model_path: Optional[str] = None) -> SimpleRiskScorer:
    """
    Get risk predictor instance
    
    Args:
        use_ml: Use ML model if available (default: True)
        model_path: Path to ML model (default: models/risk_model.pkl)
        
    Returns:
        Risk predictor (ML or Simple)
    """
    global _risk_predictor
    
    # Auto-detect trained model if not specified
    if use_ml and model_path is None:
        if os.path.exists(DEFAULT_MODEL_PATH):
            model_path = DEFAULT_MODEL_PATH
    
    if use_ml and model_path and os.path.exists(model_path):
        if _risk_predictor is None or not isinstance(_risk_predictor, MLRiskPredictor):
            _risk_predictor = MLRiskPredictor(model_path)
        return _risk_predictor
    else:
        # Fall back to simple scorer
        if _risk_predictor is None or not isinstance(_risk_predictor, SimpleRiskScorer):
            _risk_predictor = SimpleRiskScorer()
        return _risk_predictor


def assess_lending_risk(
    borrower_state: Dict,
    lender_state: Dict,
    network_metrics: Dict,
    market_state: Dict,
    exposure_amount: float = 0.0,
    use_ml: bool = True
) -> RiskPrediction:
    """
    Main entry point for risk assessment
    
    Args:
        borrower_state: Borrower bank state
        lender_state: Lender bank state
        network_metrics: Network connectivity metrics
        market_state: Market conditions
        exposure_amount: Proposed lending amount
        use_ml: Use ML model if available (default: True)
        
    Returns:
        RiskPrediction with comprehensive assessment
    """
    predictor = get_risk_predictor(use_ml=use_ml)
    
    # Call appropriate method based on predictor type
    if isinstance(predictor, MLRiskPredictor):
        return predictor.predict(
            borrower_state=borrower_state,
            lender_state=lender_state,
            network_metrics=network_metrics,
            market_state=market_state,
            exposure_amount=exposure_amount
        )
    else:
        return predictor.calculate_risk_score(
            borrower_state=borrower_state,
            lender_state=lender_state,
            network_metrics=network_metrics,
            market_state=market_state,
            exposure_amount=exposure_amount
        )

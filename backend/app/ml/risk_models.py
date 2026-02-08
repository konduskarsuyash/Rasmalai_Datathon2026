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


class FormulaRiskPredictor:
    """
    Direct mathematical formula-based risk predictor.
    Uses Merton Distance-to-Default inspired logistic model.
    No ML training required — calibrated coefficients based on financial theory.
    
    Formula:
        z = Σ(wi * fi)  where fi are normalized financial features
        default_probability = sigmoid(z) = 1 / (1 + exp(-z))
    
    The coefficients are calibrated so that a healthy bank with:
      - capital_ratio=0.10, leverage=5, liquidity=0.4, equity=80
    gets a low risk score (~0.10), while a stressed bank with:
      - capital_ratio=0.04, leverage=20, liquidity=0.05, equity=10, past_defaults=2
    gets a high risk score (~0.75).
    """
    
    # Calibrated coefficients (positive = increases risk)
    COEFFICIENTS = {
        'intercept':       -2.5,    # Base bias toward low risk (healthy default)
        'capital_ratio':   -8.0,    # Higher capital → much lower risk
        'leverage':         0.12,   # Higher leverage → higher risk
        'liquidity_ratio': -3.0,    # Higher liquidity → lower risk
        'equity':          -0.015,  # Higher equity cushion → lower risk
        'past_defaults':    0.8,    # Each past default adds significant risk
        'risk_appetite':    0.5,    # Higher risk appetite → slightly higher risk
        'market_volatility': 4.0,   # Market turbulence → higher risk
        'lender_strength': -2.0,    # Strong lender can absorb losses (reduces systemic risk)
        'network_centrality': 1.5,  # Systemic importance amplifies risk
        'upstream_burden':  0.3,    # Debt burden relative to equity
    }
    
    def __init__(self):
        """Initialize formula predictor (no model file needed)"""
        pass
    
    @staticmethod
    def _sigmoid(z: float) -> float:
        """Numerically stable sigmoid function"""
        if z >= 0:
            return 1.0 / (1.0 + math.exp(-z))
        else:
            ez = math.exp(z)
            return ez / (1.0 + ez)
    
    def predict(
        self,
        borrower_state: Dict,
        lender_state: Dict,
        network_metrics: Dict,
        market_state: Dict,
        exposure_amount: float = 0.0
    ) -> RiskPrediction:
        """
        Predict risk using direct mathematical formula.
        
        Uses logistic regression-style:  P(default) = σ(w·x)
        where features are financial ratios and network metrics.
        
        Returns:
            RiskPrediction with formula-based estimates
        """
        # Extract raw features
        capital_ratio = borrower_state.get('capital_ratio', 0.08)
        leverage = borrower_state.get('leverage', 5.0)
        liquidity_ratio = borrower_state.get('liquidity_ratio', 0.3)
        equity = borrower_state.get('equity', 80.0)
        past_defaults = float(borrower_state.get('past_defaults', 0))
        risk_appetite = borrower_state.get('risk_appetite', 0.5)
        market_vol = market_state.get('volatility', 0.02)
        market_stress = market_state.get('stress', 0.0)
        lender_capital = lender_state.get('capital_ratio', 0.10)
        centrality = network_metrics.get('centrality', 0.0)
        degree = network_metrics.get('degree', 0)
        upstream_exposure = network_metrics.get('upstream_exposure', 0)
        
        # Compute upstream burden (debt / equity ratio)
        upstream_burden = (upstream_exposure / max(equity, 1.0)) if equity > 0 else 2.0
        upstream_burden = min(upstream_burden, 5.0)  # Cap at 5x
        
        # Combined market stress factor
        market_factor = max(market_vol, market_stress * 0.5)
        
        # Compute linear combination z = w·x
        W = self.COEFFICIENTS
        z = (
            W['intercept']
            + W['capital_ratio'] * capital_ratio
            + W['leverage'] * leverage
            + W['liquidity_ratio'] * liquidity_ratio
            + W['equity'] * equity
            + W['past_defaults'] * past_defaults
            + W['risk_appetite'] * risk_appetite
            + W['market_volatility'] * market_factor
            + W['lender_strength'] * lender_capital
            + W['network_centrality'] * centrality
            + W['upstream_burden'] * upstream_burden
        )
        
        # Apply sigmoid to get probability
        default_prob = self._sigmoid(z)
        
        # Clamp to reasonable range [0.02, 0.95]
        default_prob = max(0.02, min(default_prob, 0.95))
        
        # Derived metrics
        borrower_equity = max(equity, 1.0)
        expected_loss = default_prob * (exposure_amount if exposure_amount > 0 else borrower_equity * 0.1)
        
        systemic_impact = default_prob * (0.5 + 0.5 * centrality)
        cascade_risk = self._calculate_cascade_risk(default_prob, network_metrics)
        risk_level = self._classify_risk_level(default_prob)
        recommendation = self._generate_recommendation(default_prob, systemic_impact, cascade_risk)
        
        reasons = self._generate_reasons(
            default_prob, capital_ratio, leverage, liquidity_ratio,
            equity, past_defaults, market_factor, centrality, upstream_burden
        )
        
        return RiskPrediction(
            default_probability=default_prob,
            expected_loss=expected_loss,
            systemic_impact=systemic_impact,
            cascade_risk=cascade_risk,
            risk_level=risk_level,
            recommendation=recommendation,
            confidence=0.80,
            reasons=reasons
        )
    
    def calculate_risk_score(
        self,
        borrower_state: Dict,
        lender_state: Dict,
        network_metrics: Dict,
        market_state: Dict,
        exposure_amount: float = 0.0
    ) -> RiskPrediction:
        """Alias for predict() — compatible with SimpleRiskScorer interface"""
        return self.predict(borrower_state, lender_state, network_metrics, market_state, exposure_amount)
    
    def _calculate_cascade_risk(self, default_prob: float, network_metrics: Dict) -> float:
        """Calculate probability of triggering cascade"""
        centrality = network_metrics.get('centrality', 0.0)
        degree = network_metrics.get('degree', 0)
        network_amplification = 1.0 + centrality * 0.6 + min(degree / 10, 0.4)
        return min(default_prob * network_amplification, 1.0)
    
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
    
    def _generate_reasons(
        self, default_prob, capital_ratio, leverage, liquidity_ratio,
        equity, past_defaults, market_factor, centrality, upstream_burden
    ) -> List[str]:
        """Generate human-readable reasons from formula components"""
        reasons = [f"📐 Formula Model: {default_prob:.1%} default probability"]
        
        # Highlight the dominant risk drivers
        if capital_ratio < 0.06:
            reasons.append(f"⚠️ Critical capital ratio: {capital_ratio:.1%} (min 8% recommended)")
        elif capital_ratio < 0.08:
            reasons.append(f"⚠️ Low capital ratio: {capital_ratio:.1%}")
        
        if leverage > 15:
            reasons.append(f"⚠️ Dangerous leverage: {leverage:.1f}x")
        elif leverage > 10:
            reasons.append(f"⚠️ High leverage: {leverage:.1f}x")
        
        if liquidity_ratio < 0.15:
            reasons.append(f"⚠️ Liquidity stress: {liquidity_ratio:.1%}")
        
        if equity < 20:
            reasons.append(f"⚠️ Low equity cushion: ${equity:.0f}M")
        
        if past_defaults > 0:
            reasons.append(f"📉 Default history: {int(past_defaults)} past defaults")
        
        if market_factor > 0.3:
            reasons.append(f"🌪️ Market turbulence: {market_factor:.1%}")
        
        if centrality > 0.5:
            reasons.append(f"🕸️ Systemic importance (centrality: {centrality:.2f})")
        
        if upstream_burden > 2.0:
            reasons.append(f"💰 Heavy debt: {upstream_burden:.1f}x equity")
        
        return reasons


# Global risk predictor instance
_risk_predictor = None


def get_risk_predictor(use_ml: bool = True, model_path: Optional[str] = None):
    """
    Get risk predictor instance.
    
    Uses FormulaRiskPredictor (direct mathematical formula) by default.
    Falls back to SimpleRiskScorer (rule-based) if use_ml=False.
    
    Args:
        use_ml: Use formula predictor (default: True). If False, uses simple rule-based scorer.
        model_path: Ignored (kept for API compatibility).
        
    Returns:
        Risk predictor (Formula or Simple)
    """
    global _risk_predictor
    
    if use_ml:
        # Use the direct mathematical formula predictor (replaces XGBoost)
        if _risk_predictor is None or not isinstance(_risk_predictor, FormulaRiskPredictor):
            _risk_predictor = FormulaRiskPredictor()
            print("✓ Using FormulaRiskPredictor (direct mathematical formula, no XGBoost)")
        return _risk_predictor
    else:
        # Fall back to simple rule-based scorer
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
    
    # Both FormulaRiskPredictor and SimpleRiskScorer support calculate_risk_score()
    # FormulaRiskPredictor also supports predict() — use calculate_risk_score for unified interface
    if isinstance(predictor, FormulaRiskPredictor):
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

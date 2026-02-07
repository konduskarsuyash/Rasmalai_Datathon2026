// Real-time ML Risk Predictor Component
import { useState, useEffect } from 'react';

const MLRiskPredictor = ({ bank, marketState = {} }) => {
  const [riskPrediction, setRiskPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isLive, setIsLive] = useState(false);

  // Fetch risk prediction from ML model
  const fetchRiskPrediction = async () => {
    if (!bank) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/risk/assess', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          borrower_state: {
            capital_ratio: bank.capital_ratio || 0.08,
            leverage: bank.leverage || 10.0,
            liquidity_ratio: bank.liquidity_ratio || 0.2,
            equity: bank.capital || 100,
            cash: bank.cash || 50,
            market_exposure: bank.investments || 0,
            past_defaults: bank.past_defaults || 0,
            investment_volatility: bank.investment_volatility || 0,
            risk_appetite: bank.risk_appetite || 0.5,
          },
          lender_state: {
            capital_ratio: 0.10,
            equity: 100,
          },
          network_metrics: {
            centrality: 0.3,
            degree: 5,
            upstream_exposure: 30,
            downstream_exposure: 30,
            clustering_coefficient: 0.4,
          },
          market_state: {
            stress: marketState.stress || 0.3,
            volatility: marketState.volatility || 0.02,
            liquidity_available: 1000,
          },
          exposure_amount: 15.0,
          use_ml: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setRiskPrediction(data);
      setIsLive(true);
      
      // Flash live indicator
      setTimeout(() => setIsLive(false), 2000);
    } catch (err) {
      console.error('Risk prediction error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount and when bank changes
  useEffect(() => {
    fetchRiskPrediction();
  }, [bank?.id, bank?.capital, bank?.leverage]);

  // Get risk level color
  const getRiskColor = (level) => {
    const colors = {
      'VERY_LOW': 'bg-green-100 text-green-800 border-green-300',
      'LOW': 'bg-blue-100 text-blue-800 border-blue-300',
      'MEDIUM': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'HIGH': 'bg-orange-100 text-orange-800 border-orange-300',
      'VERY_HIGH': 'bg-red-100 text-red-800 border-red-300',
    };
    return colors[level] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  // Get recommendation color
  const getRecommendationColor = (rec) => {
    const colors = {
      'EXTEND_CREDIT': 'bg-green-500 text-white',
      'HOLD': 'bg-blue-500 text-white',
      'REDUCE_EXPOSURE': 'bg-orange-500 text-white',
      'REJECT': 'bg-red-500 text-white',
    };
    return colors[rec] || 'bg-gray-500 text-white';
  };

  if (error) {
    return (
      <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">⚠️</span>
          <h3 className="text-sm font-bold text-red-700">ML Model Error</h3>
        </div>
        <p className="text-xs text-red-600">{error}</p>
        <button
          onClick={fetchRiskPrediction}
          className="mt-2 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
<div className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 border-2 border-purple-300 rounded-xl p-4">
  
{/* Header */} 
<div className="flex items-center justify-between mb-3">
  <div className="flex items-center gap-2">
    <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2">
      <span className="text-xl">🤖</span>
      <span>AI Risk Prediction</span>
      <span className="text-xs bg-purple-600 text-white px-2 py-0.5 rounded-full">XGBoost ML</span>
    </h3>
{isLive && (
  <div className="flex items-center gap-1 bg-green-500 text-white text-xs px-2 py-1 rounded-full animate-pulse">
    <span className="w-2 h-2 bg-white rounded-full"></span>
    LIVE
  </div>
)}
  </div>
  <button
    onClick={fetchRiskPrediction}
    disabled={loading}
    className="px-2 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 disabled:opacity-50"
  >
    {loading ? '⏳' : '🔄'} Refresh
  </button>
</div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <p className="text-sm text-gray-600 mt-2">Analyzing with ML model...</p>
        </div>
      )}

      {!loading && riskPrediction && (
        <>
          {/* Main Prediction Card */}
          <div className="bg-white bg-opacity-80 backdrop-blur rounded-xl p-4 mb-3 border-2 border-purple-200 shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-xs text-gray-600 font-semibold">DEFAULT PROBABILITY</p>
                <p className="text-4xl font-bold text-purple-900">
                  {(riskPrediction.default_probability * 100).toFixed(1)}%
                </p>
              </div>
              <div className={`px-4 py-2 rounded-lg border-2 text-sm font-bold ${getRiskColor(riskPrediction.risk_level)}`}>
                {riskPrediction.risk_level.replace('_', ' ')}
              </div>
            </div>

            {/* Recommendation Badge */}
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-3 py-1.5 rounded-full ${getRecommendationColor(riskPrediction.recommendation)}`}>
                {riskPrediction.recommendation === 'EXTEND_CREDIT' ? '✅' : 
                 riskPrediction.recommendation === 'HOLD' ? '⏸️' :
                 riskPrediction.recommendation === 'REDUCE_EXPOSURE' ? '⚠️' : '🚫'} 
                {riskPrediction.recommendation.replace('_', ' ')}
              </span>
              <span className="text-xs text-gray-600">
                Confidence: {(riskPrediction.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Risk Metrics Grid */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-red-200">
              <p className="text-xs text-red-600 font-semibold mb-1">💸 Expected Loss</p>
              <p className="text-lg font-bold text-red-900">
                ${riskPrediction.expected_loss.toFixed(1)}M
              </p>
            </div>
            <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-orange-200">
              <p className="text-xs text-orange-600 font-semibold mb-1">⚡ Systemic Risk</p>
              <p className="text-lg font-bold text-orange-900">
                {(riskPrediction.systemic_impact * 100).toFixed(0)}%
              </p>
            </div>
            <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-purple-200">
              <p className="text-xs text-purple-600 font-semibold mb-1">🌊 Cascade Risk</p>
              <p className="text-lg font-bold text-purple-900">
                {(riskPrediction.cascade_risk * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          {/* AI Reasoning */}
          {riskPrediction.reasons && riskPrediction.reasons.length > 0 && (
            <div className="bg-white bg-opacity-50 rounded-lg p-3 border border-purple-200">
              <p className="text-xs font-bold text-gray-700 mb-2">🧠 AI Analysis:</p>
              <div className="space-y-1">
                {riskPrediction.reasons.slice(0, 5).map((reason, idx) => (
                  <p key={idx} className="text-xs text-gray-700 flex items-start gap-1">
                    <span className="text-purple-600 font-bold">•</span>
                    <span>{reason}</span>
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Model Info Footer */}
          <div className="mt-3 text-center">
            <p className="text-xs text-gray-500">
              Powered by <strong>XGBoost v1.0</strong> • Trained on 10,000 scenarios • 
              <span className="text-purple-600 font-semibold"> 83% AUC-ROC</span>
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default MLRiskPredictor;

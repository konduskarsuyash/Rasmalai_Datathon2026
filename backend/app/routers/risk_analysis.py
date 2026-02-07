"""
Risk Analysis API Endpoints
Provides ML-based credit risk assessment for lending decisions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import numpy as np

from app.ml.risk_models import (
    assess_lending_risk,
    RiskPrediction,
    RiskLevel,
    get_risk_predictor
)
from app.ml.data_collector import get_data_collector


router = APIRouter(prefix="/api/risk", tags=["risk"])


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment"""
    borrower_state: Dict
    lender_state: Dict
    network_metrics: Dict = Field(default_factory=dict)
    market_state: Dict = Field(default_factory=dict)
    exposure_amount: float = 0.0
    use_ml: bool = False


class RiskAssessmentResponse(BaseModel):
    """Response with risk prediction"""
    default_probability: float
    expected_loss: float
    systemic_impact: float
    cascade_risk: float
    risk_level: str
    recommendation: str
    confidence: float
    reasons: List[str]


class DataCollectionControlRequest(BaseModel):
    """Control data collection"""
    enabled: bool
    simulation_id: Optional[str] = None


@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk(request: RiskAssessmentRequest):
    """
    Assess credit risk for a lending decision
    
    Returns ML-based risk prediction with recommendations
    """
    try:
        # Ensure default values for network metrics
        network_metrics = request.network_metrics or {
            'centrality': 0.0,
            'degree': 0,
            'upstream_exposure': 0.0,
            'downstream_exposure': 0.0,
            'clustering_coefficient': 0.0
        }
        
        # Ensure default values for market state
        market_state = request.market_state or {
            'stress': 0.0,
            'volatility': 0.0,
            'liquidity_available': 1000.0
        }
        
        # Perform risk assessment
        prediction = assess_lending_risk(
            borrower_state=request.borrower_state,
            lender_state=request.lender_state,
            network_metrics=network_metrics,
            market_state=market_state,
            exposure_amount=request.exposure_amount,
            use_ml=request.use_ml
        )
        
        return RiskAssessmentResponse(
            default_probability=prediction.default_probability,
            expected_loss=prediction.expected_loss,
            systemic_impact=prediction.systemic_impact,
            cascade_risk=prediction.cascade_risk,
            risk_level=prediction.risk_level.value,
            recommendation=prediction.recommendation,
            confidence=prediction.confidence,
            reasons=prediction.reasons
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.post("/batch-assess", response_model=List[RiskAssessmentResponse])
async def batch_assess_risk(requests: List[RiskAssessmentRequest]):
    """
    Assess risk for multiple lending decisions in batch
    
    Useful for network-wide risk analysis
    """
    results = []
    
    for request in requests:
        try:
            network_metrics = request.network_metrics or {}
            market_state = request.market_state or {}
            
            prediction = assess_lending_risk(
                borrower_state=request.borrower_state,
                lender_state=request.lender_state,
                network_metrics=network_metrics,
                market_state=market_state,
                exposure_amount=request.exposure_amount,
                use_ml=request.use_ml
            )
            
            results.append(RiskAssessmentResponse(
                default_probability=prediction.default_probability,
                expected_loss=prediction.expected_loss,
                systemic_impact=prediction.systemic_impact,
                cascade_risk=prediction.cascade_risk,
                risk_level=prediction.risk_level.value,
                recommendation=prediction.recommendation,
                confidence=prediction.confidence,
                reasons=prediction.reasons
            ))
        except Exception as e:
            # Add error result
            results.append(RiskAssessmentResponse(
                default_probability=0.5,
                expected_loss=0.0,
                systemic_impact=0.0,
                cascade_risk=0.0,
                risk_level="MEDIUM",
                recommendation="HOLD",
                confidence=0.0,
                reasons=[f"Error: {str(e)}"]
            ))
    
    return results


@router.post("/data-collection/control")
async def control_data_collection(request: DataCollectionControlRequest):
    """
    Enable or disable training data collection
    
    When enabled, simulations will record decision points for ML training
    """
    collector = get_data_collector()
    
    if request.enabled:
        collector.start_collection(request.simulation_id)
        return {
            "status": "enabled",
            "simulation_id": collector.current_simulation_id,
            "message": "Data collection started"
        }
    else:
        collector.stop_collection()
        return {
            "status": "disabled",
            "message": "Data collection stopped"
        }


@router.get("/data-collection/status")
async def get_data_collection_status():
    """Get current data collection status"""
    collector = get_data_collector()
    
    stats = collector.get_summary_stats() if collector.decision_points else {}
    
    return {
        "enabled": collector.enabled,
        "simulation_id": collector.current_simulation_id,
        "decision_points_collected": len(collector.decision_points),
        "simulations_completed": len(collector.simulation_outcomes),
        "statistics": stats
    }


@router.post("/data-collection/save")
async def save_training_data(format: str = "csv"):
    """
    Save collected training data to file
    
    Args:
        format: 'csv' or 'json'
    """
    collector = get_data_collector()
    
    if not collector.decision_points:
        raise HTTPException(status_code=400, detail="No data collected yet")
    
    try:
        if format == "csv":
            filepath = collector.save_to_csv()
        elif format == "json":
            filepath = collector.save_to_json()
        else:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
        
        return {
            "success": True,
            "filepath": str(filepath),
            "num_decision_points": len(collector.decision_points),
            "num_simulations": len(collector.simulation_outcomes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")


@router.get("/model/info")
async def get_model_info():
    """Get information about the loaded risk assessment model"""
    predictor = get_risk_predictor()
    
    info = {
        "predictor_type": type(predictor).__name__,
        "ml_enabled": hasattr(predictor, 'is_trained') and predictor.is_trained,
    }
    
    if hasattr(predictor, 'model') and predictor.model:
        info.update({
            "model_type": type(predictor.model).__name__,
            "features": predictor.feature_names if hasattr(predictor, 'feature_names') else [],
            "num_features": len(predictor.feature_names) if hasattr(predictor, 'feature_names') else 0
        })
    
    return info

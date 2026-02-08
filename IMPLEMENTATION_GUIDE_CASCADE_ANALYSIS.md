# 🔥 IMPLEMENTATION GUIDE: Advanced Cascade Analysis System

**Priority:** CRITICAL - Feature #1  
**Timeline:** 2-3 weeks  
**Business Impact:** Directly addresses core project objective

---

## 📋 OVERVIEW

Implement a comprehensive cascade analysis system that identifies, tracks, and visualizes how defaults propagate through the financial network, enabling regulators to:
- Identify systemically important institutions
- Map contagion pathways
- Predict cascade probability
- Measure network resilience

---

## 🏗️ ARCHITECTURE

```
backend/app/analytics/
├── __init__.py
├── cascade_analyzer.py      # Core cascade analysis logic
├── network_metrics.py        # Graph-based metrics
├── risk_scorer.py            # Risk assessment algorithms
└── visualization_data.py     # Data prep for frontend

frontend/src/components/
├── CascadeAnalysisDashboard.jsx    # Main dashboard
├── CascadePathwayMap.jsx           # Visual pathway display
├── CriticalNodesPanel.jsx          # Too-big-to-fail list
└── RiskHeatmap.jsx                 # Network-wide risk view
```

---

## 🔨 BACKEND IMPLEMENTATION

### Step 1: Create Cascade Analyzer (`backend/app/analytics/cascade_analyzer.py`)

```python
"""
Cascade Analysis System for Financial Network
Identifies contagion pathways and systemic risk nodes
"""
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
import networkx as nx
from collections import defaultdict

from app.core.bank import Bank
from app.core.simulation_v2 import SimulationState


@dataclass
class CascadeEvent:
    """Single cascade event in propagation chain"""
    time_step: int
    trigger_bank_id: int
    affected_bank_id: int
    exposure_amount: float
    cascade_depth: int
    pathway: List[int] = field(default_factory=list)


@dataclass
class CascadeAnalysis:
    """Complete cascade analysis results"""
    cascade_events: List[CascadeEvent]
    cascade_depth: int
    total_affected_banks: int
    contagion_pathways: List[List[int]]
    critical_nodes: List[Dict]
    systemic_importance_scores: Dict[int, float]
    cascade_probability: float
    network_resilience_score: float


class CascadeAnalyzer:
    """Analyzes cascade propagation in financial networks"""
    
    def __init__(self, state: SimulationState):
        self.state = state
        self.graph = self._build_network_graph()
        
    def _build_network_graph(self) -> nx.DiGraph:
        """Build directed graph from interbank exposures"""
        G = nx.DiGraph()
        
        # Add nodes
        for bank in self.state.banks:
            G.add_node(
                bank.bank_id,
                capital=bank.balance_sheet.equity,
                cash=bank.balance_sheet.cash,
                is_defaulted=bank.is_defaulted
            )
        
        # Add edges (loan exposures)
        for bank in self.state.banks:
            for counterparty_id, amount in bank.balance_sheet.loan_positions.items():
                G.add_edge(
                    bank.bank_id,
                    counterparty_id,
                    weight=amount,
                    type='loan'
                )
        
        return G
    
    def analyze_cascade(self, initial_defaults: List[int]) -> CascadeAnalysis:
        """
        Simulate cascade from initial defaults
        
        Args:
            initial_defaults: List of bank IDs that initially default
            
        Returns:
            Complete cascade analysis
        """
        cascade_events = []
        affected_banks = set(initial_defaults)
        cascade_depth = 0
        contagion_pathways = []
        
        # Track cascade propagation
        current_wave = initial_defaults.copy()
        depth_map = {bank_id: 0 for bank_id in initial_defaults}
        
        while current_wave:
            cascade_depth += 1
            next_wave = []
            
            for defaulted_id in current_wave:
                # Find all banks exposed to this defaulted bank
                exposed_banks = self._get_exposed_banks(defaulted_id)
                
                for exposed_bank_id, exposure in exposed_banks:
                    if exposed_bank_id in affected_banks:
                        continue
                    
                    # Check if exposure causes default
                    if self._would_cause_default(exposed_bank_id, exposure):
                        next_wave.append(exposed_bank_id)
                        affected_banks.add(exposed_bank_id)
                        depth_map[exposed_bank_id] = cascade_depth
                        
                        # Record cascade event
                        pathway = self._trace_cascade_path(defaulted_id, depth_map)
                        event = CascadeEvent(
                            time_step=self.state.time_step,
                            trigger_bank_id=defaulted_id,
                            affected_bank_id=exposed_bank_id,
                            exposure_amount=exposure,
                            cascade_depth=cascade_depth,
                            pathway=pathway
                        )
                        cascade_events.append(event)
                        
                        if pathway not in contagion_pathways:
                            contagion_pathways.append(pathway)
            
            current_wave = next_wave
            
            # Safety limit
            if cascade_depth > 10:
                break
        
        # Calculate systemic importance
        systemic_scores = self._calculate_systemic_importance()
        
        # Identify critical nodes
        critical_nodes = self._identify_critical_nodes(systemic_scores)
        
        # Calculate cascade probability
        cascade_prob = self._estimate_cascade_probability()
        
        # Calculate network resilience
        resilience = self._calculate_network_resilience()
        
        return CascadeAnalysis(
            cascade_events=cascade_events,
            cascade_depth=cascade_depth,
            total_affected_banks=len(affected_banks),
            contagion_pathways=contagion_pathways,
            critical_nodes=critical_nodes,
            systemic_importance_scores=systemic_scores,
            cascade_probability=cascade_prob,
            network_resilience_score=resilience
        )
    
    def _get_exposed_banks(self, defaulted_bank_id: int) -> List[Tuple[int, float]]:
        """Get all banks with exposure to defaulted bank"""
        exposed = []
        for bank in self.state.banks:
            if bank.bank_id == defaulted_bank_id or bank.is_defaulted:
                continue
            exposure = bank.balance_sheet.loan_positions.get(defaulted_bank_id, 0)
            if exposure > 0:
                exposed.append((bank.bank_id, exposure))
        return exposed
    
    def _would_cause_default(self, bank_id: int, loss_amount: float) -> bool:
        """Check if loss would cause bank default"""
        bank = next((b for b in self.state.banks if b.bank_id == bank_id), None)
        if not bank:
            return False
        
        # Simplified default check
        remaining_capital = bank.balance_sheet.equity - loss_amount
        return remaining_capital < bank.balance_sheet.default_threshold
    
    def _trace_cascade_path(self, bank_id: int, depth_map: Dict[int, int]) -> List[int]:
        """Trace back the cascade pathway to this bank"""
        # Simplified - in reality would track full tree
        return [bid for bid, depth in sorted(depth_map.items(), key=lambda x: x[1]) 
                if depth <= depth_map[bank_id]]
    
    def _calculate_systemic_importance(self) -> Dict[int, float]:
        """
        Calculate systemic importance score for each bank
        Based on: network centrality, capital size, interconnectedness
        """
        scores = {}
        
        # Centrality measures
        betweenness = nx.betweenness_centrality(self.graph, weight='weight')
        eigenvector = nx.eigenvector_centrality(self.graph, weight='weight', max_iter=1000)
        
        for bank in self.state.banks:
            bank_id = bank.bank_id
            
            # Component scores
            capital_score = bank.balance_sheet.equity / 1000  # Normalized
            centrality_score = betweenness.get(bank_id, 0) + eigenvector.get(bank_id, 0)
            exposure_score = len(bank.balance_sheet.loan_positions) / len(self.state.banks)
            
            # Combined systemic importance
            scores[bank_id] = (
                0.4 * capital_score + 
                0.4 * centrality_score + 
                0.2 * exposure_score
            )
        
        return scores
    
    def _identify_critical_nodes(self, systemic_scores: Dict[int, float]) -> List[Dict]:
        """
        Identify too-big-to-fail institutions
        Returns top 20% by systemic importance
        """
        threshold = sorted(systemic_scores.values(), reverse=True)[len(systemic_scores) // 5]
        
        critical = []
        for bank_id, score in systemic_scores.items():
            if score >= threshold:
                bank = next((b for b in self.state.banks if b.bank_id == bank_id), None)
                if bank:
                    critical.append({
                        'bank_id': bank_id,
                        'name': bank.name,
                        'systemic_importance': score,
                        'capital': bank.balance_sheet.equity,
                        'connections': len(bank.balance_sheet.loan_positions),
                        'classification': 'SYSTEMICALLY_IMPORTANT'
                    })
        
        return sorted(critical, key=lambda x: x['systemic_importance'], reverse=True)
    
    def _estimate_cascade_probability(self) -> float:
        """
        Estimate probability of cascade given current network state
        Based on: network density, capital buffers, concentration
        """
        # Average capital buffer
        avg_buffer = sum(b.balance_sheet.equity for b in self.state.banks) / len(self.state.banks)
        buffer_score = max(0, min(1, avg_buffer / 100))
        
        # Network density (more connections = higher cascade risk)
        density = nx.density(self.graph)
        
        # Concentration (more concentrated = higher risk)
        capitals = [b.balance_sheet.equity for b in self.state.banks]
        concentration = max(capitals) / sum(capitals) if sum(capitals) > 0 else 0
        
        # Combined probability (inverse of stability)
        probability = (
            0.4 * (1 - buffer_score) +
            0.3 * density +
            0.3 * concentration
        )
        
        return min(1.0, max(0.0, probability))
    
    def _calculate_network_resilience(self) -> float:
        """
        Calculate overall network resilience score (0-1)
        Higher = more resilient
        """
        # Factor 1: Average capital adequacy
        avg_capital = sum(b.balance_sheet.equity for b in self.state.banks 
                         if not b.is_defaulted) / len(self.state.banks)
        capital_score = min(1.0, avg_capital / 100)
        
        # Factor 2: Network connectivity (moderate is best)
        density = nx.density(self.graph)
        connectivity_score = 1 - abs(0.3 - density)  # Optimal around 0.3
        
        # Factor 3: Absence of super-hubs
        degree_centrality = nx.degree_centrality(self.graph)
        max_centrality = max(degree_centrality.values()) if degree_centrality else 0
        hub_score = 1 - max_centrality
        
        # Combined resilience
        resilience = (
            0.5 * capital_score +
            0.3 * connectivity_score +
            0.2 * hub_score
        )
        
        return resilience


# Utility function for API
def analyze_simulation_cascades(state: SimulationState, 
                               initial_defaults: List[int]) -> Dict:
    """
    Main function to analyze cascades for API endpoint
    
    Args:
        state: Current simulation state
        initial_defaults: Banks that have defaulted
        
    Returns:
        JSON-serializable analysis results
    """
    analyzer = CascadeAnalyzer(state)
    analysis = analyzer.analyze_cascade(initial_defaults)
    
    return {
        'cascade_depth': analysis.cascade_depth,
        'total_affected': analysis.total_affected_banks,
        'cascade_probability': round(analysis.cascade_probability, 3),
        'network_resilience': round(analysis.network_resilience_score, 3),
        'critical_nodes': analysis.critical_nodes,
        'systemic_importance_scores': {
            k: round(v, 3) for k, v in analysis.systemic_importance_scores.items()
        },
        'cascade_events': [
            {
                'time': e.time_step,
                'trigger': e.trigger_bank_id,
                'affected': e.affected_bank_id,
                'exposure': round(e.exposure_amount, 2),
                'depth': e.cascade_depth,
                'pathway': e.pathway
            }
            for e in analysis.cascade_events
        ],
        'contagion_pathways': analysis.contagion_pathways
    }
```

### Step 2: Add API Endpoint (`backend/app/routers/analytics.py`)

```python
"""
Analytics API Router
Provides cascade analysis and network metrics
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from app.middleware.auth import get_optional_user
from app.analytics.cascade_analyzer import analyze_simulation_cascades

router = APIRouter()


class CascadeAnalysisRequest(BaseModel):
    """Request for cascade analysis"""
    simulation_id: str
    initial_defaults: List[int]


@router.post("/cascade-analysis")
async def run_cascade_analysis(
    request: CascadeAnalysisRequest,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Analyze cascade propagation from initial defaults
    
    Returns comprehensive cascade analysis including:
    - Cascade depth and affected banks
    - Contagion pathways
    - Critical nodes (too-big-to-fail)
    - Systemic importance scores
    - Network resilience metrics
    """
    # In real implementation, fetch simulation state from DB
    # For now, use global state
    from app.routers.interactive_simulation import ACTIVE_SIMULATION
    
    state = ACTIVE_SIMULATION.get("state")
    if not state:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    analysis = analyze_simulation_cascades(state, request.initial_defaults)
    
    return {
        "status": "success",
        "analysis": analysis
    }


@router.get("/network-metrics")
async def get_network_metrics(
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get current network topology metrics
    """
    from app.routers.interactive_simulation import ACTIVE_SIMULATION
    
    state = ACTIVE_SIMULATION.get("state")
    if not state:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    # Calculate basic network metrics
    # (extend with more sophisticated analysis)
    
    return {
        "num_banks": len(state.banks),
        "num_defaults": sum(1 for b in state.banks if b.is_defaulted),
        "total_capital": sum(b.balance_sheet.equity for b in state.banks),
        # Add more metrics
    }
```

### Step 3: Register Router (`backend/app/main.py`)

```python
# Add to imports
from .routers import simulation, config_router, network, interactive_simulation, analytics

# Add to routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
```

### Step 4: Install Dependencies

```bash
cd backend
pip install networkx
# Add to requirements.txt:
# networkx>=3.0
```

---

## 🎨 FRONTEND IMPLEMENTATION

### Step 1: Create Cascade Dashboard Component

```jsx
// frontend/src/components/CascadeAnalysisDashboard.jsx
import { useState, useEffect } from 'react';
import { AlertTriangle, Network, Shield } from 'lucide-react';
import CascadePathwayMap from './CascadePathwayMap';
import CriticalNodesPanel from './CriticalNodesPanel';
import RiskHeatmap from './RiskHeatmap';

const CascadeAnalysisDashboard = ({ simulationId, defaultedBanks }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (defaultedBanks && defaultedBanks.length > 0) {
      analyzeCascade();
    }
  }, [defaultedBanks]);

  const analyzeCascade = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${baseUrl}/api/analytics/cascade-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          simulation_id: simulationId,
          initial_defaults: defaultedBanks
        })
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data.analysis);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
        <p className="text-red-800">Analysis Error: {error}</p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-6 text-center">
        <Network className="mx-auto mb-3 text-gray-400" size={48} />
        <p className="text-gray-600">No cascade analysis available</p>
        <p className="text-sm text-gray-500 mt-1">
          Analysis will appear when banks default
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-red-600" size={20} />
            <span className="text-xs font-bold text-red-900 uppercase">
              Cascade Depth
            </span>
          </div>
          <p className="text-3xl font-bold text-red-600">
            {analysis.cascade_depth}
          </p>
        </div>

        <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Network className="text-orange-600" size={20} />
            <span className="text-xs font-bold text-orange-900 uppercase">
              Affected Banks
            </span>
          </div>
          <p className="text-3xl font-bold text-orange-600">
            {analysis.total_affected}
          </p>
        </div>

        <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <span className="text-xs font-bold text-yellow-900 uppercase">
              Cascade Risk
            </span>
          </div>
          <p className="text-3xl font-bold text-yellow-600">
            {(analysis.cascade_probability * 100).toFixed(0)}%
          </p>
        </div>

        <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="text-green-600" size={20} />
            <span className="text-xs font-bold text-green-900 uppercase">
              Resilience
            </span>
          </div>
          <p className="text-3xl font-bold text-green-600">
            {(analysis.network_resilience * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Cascade Pathway Visualization */}
      <CascadePathwayMap
        events={analysis.cascade_events}
        pathways={analysis.contagion_pathways}
      />

      {/* Critical Nodes Panel */}
      <CriticalNodesPanel
        criticalNodes={analysis.critical_nodes}
        systemicScores={analysis.systemic_importance_scores}
      />

      {/* Risk Heatmap */}
      <RiskHeatmap
        systemicScores={analysis.systemic_importance_scores}
      />
    </div>
  );
};

export default CascadeAnalysisDashboard;
```

### Step 2: Integrate into Main Playground

```jsx
// In FinancialNetworkPlayground.jsx

import CascadeAnalysisDashboard from './CascadeAnalysisDashboard';

// Add state
const [showCascadeAnalysis, setShowCascadeAnalysis] = useState(false);
const [defaultedBanks, setDefaultedBanks] = useState([]);

// Track defaults
const handleDefaultEvent = (event) => {
  if (event.bank_id && !defaultedBanks.includes(event.bank_id)) {
    setDefaultedBanks([...defaultedBanks, event.bank_id]);
    setShowCascadeAnalysis(true);
  }
};

// Add tab/panel
{showCascadeAnalysis && (
  <div className="mt-6">
    <CascadeAnalysisDashboard
      simulationId="current"
      defaultedBanks={defaultedBanks}
    />
  </div>
)}
```

---

## 📊 EXPECTED OUTCOMES

After implementation, users will see:

1. **Real-Time Cascade Tracking**
   - As banks default, cascade depth counter updates
   - Affected banks highlighted on network graph
   - Contagion pathways drawn in real-time

2. **Critical Node Identification**
   - "Too-Big-To-Fail" banks clearly marked
   - Systemic importance scores displayed
   - Prioritized list for regulatory focus

3. **Risk Metrics Dashboard**
   - Network resilience score (0-100%)
   - Cascade probability estimation
   - Early warning indicators

4. **Policy Insights**
   - Which banks need higher capital requirements
   - Where to place circuit breakers
   - Network restructuring suggestions

---

## 🧪 TESTING

```python
# tests/test_cascade_analyzer.py
import pytest
from app.analytics.cascade_analyzer import CascadeAnalyzer
from app.core.simulation_v2 import SimulationState, create_banks

def test_cascade_analysis():
    """Test basic cascade analysis"""
    state = SimulationState()
    state.banks = create_banks(10)
    
    analyzer = CascadeAnalyzer(state)
    analysis = analyzer.analyze_cascade([0])  # Bank 0 defaults
    
    assert analysis.cascade_depth >= 0
    assert analysis.total_affected_banks >= 1
    assert 0 <= analysis.cascade_probability <= 1
    assert 0 <= analysis.network_resilience_score <= 1

def test_critical_nodes():
    """Test critical node identification"""
    # ... test implementation
```

---

## 📈 SUCCESS METRICS

- ✅ Cascade analysis completes in < 2 seconds for 40-bank network
- ✅ Correctly identifies systemically important banks
- ✅ Visualizes contagion pathways intuitively
- ✅ Provides actionable regulatory insights

---

## 🚀 DEPLOYMENT

1. **Backend:**
   ```bash
   pip install -r requirements.txt
   # Includes: networkx>=3.0
   ```

2. **Database:** 
   - No new tables needed initially (uses in-memory state)
   - Future: Store analysis results for historical comparison

3. **Frontend:**
   ```bash
   npm install
   # No new dependencies (uses existing React)
   ```

---

## 📚 NEXT STEPS AFTER THIS FEATURE

1. **Historical Cascade Comparison**
   - Store past analyses
   - Compare network evolution
   - Trend analysis

2. **Predictive Cascade Alerts**
   - ML model predicting cascade risk
   - Alert when threshold exceeded
   - Preventive action suggestions

3. **Interactive "What-If" Scenarios**
   - Click bank to simulate its default
   - See cascade propagation in real-time
   - Compare intervention strategies

---

**Ready to implement? Start with Step 1 of Backend Implementation!**

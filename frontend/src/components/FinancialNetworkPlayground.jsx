// components/FinancialNetworkPlayground.jsx
import { useState, useEffect, useRef } from 'react';
import NetworkCanvas from './NetworkCanvas';
import ControlPanel from './ControlPanel';
import InstitutionPanel from './InstitutionPanel';
import MetricsPanel from './MetricsPanel';
import SimulationControls from './SimulationControls';
import ScenarioPanel from './ScenarioPanel';

const FinancialNetworkPlayground = () => {
  // Network state
  const [institutions, setInstitutions] = useState([
    { id: 'bank1', type: 'bank', name: 'Central Bank A', position: { x: 200, y: 150 }, capital: 1000, liquidity: 500, risk: 0.2, strategy: 'conservative' },
    { id: 'bank2', type: 'bank', name: 'Commercial Bank B', position: { x: 400, y: 150 }, capital: 800, liquidity: 400, risk: 0.3, strategy: 'balanced' },
    { id: 'exchange1', type: 'exchange', name: 'Stock Exchange X', position: { x: 300, y: 300 }, capital: 1200, liquidity: 600, risk: 0.25, strategy: 'aggressive' },
    { id: 'clearing1', type: 'clearinghouse', name: 'Clearing House C', position: { x: 500, y: 300 }, capital: 900, liquidity: 450, risk: 0.15, strategy: 'conservative' },
  ]);

  const [connections, setConnections] = useState([
    { id: 'conn1', source: 'bank1', target: 'bank2', type: 'credit', exposure: 300, weight: 0.7 },
    { id: 'conn2', source: 'bank1', target: 'exchange1', type: 'settlement', exposure: 200, weight: 0.5 },
    { id: 'conn3', source: 'bank2', target: 'clearing1', type: 'margin', exposure: 150, weight: 0.6 },
    { id: 'conn4', source: 'exchange1', target: 'clearing1', type: 'settlement', exposure: 400, weight: 0.8 },
  ]);

  // Simulation state
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1);
  const [currentStep, setCurrentStep] = useState(0);
  const [maxSteps, setMaxSteps] = useState(100);

  // System metrics
  const [metrics, setMetrics] = useState({
    systemicRisk: 0.2,
    liquidityFlow: 0.75,
    networkCongestion: 0.3,
    stabilityIndex: 0.85,
    cascadeRisk: 0.15,
    interconnectedness: 0.6
  });

  // Simulation parameters
  const [parameters, setParameters] = useState({
    shockMagnitude: 0.3,
    shockType: 'liquidity',
    contagionThreshold: 0.5,
    recoveryRate: 0.1,
    informationAsymmetry: 0.3,
    regulatoryIntervention: false
  });

  // Selected institution for details
  const [selectedInstitution, setSelectedInstitution] = useState(null);
  const [selectedConnection, setSelectedConnection] = useState(null);

  // Simulation history for analysis
  const [simulationHistory, setSimulationHistory] = useState([]);

  // Alerts and events
  const [alerts, setAlerts] = useState([]);

  // Simulation engine
  const simulationInterval = useRef(null);

  useEffect(() => {
    if (isSimulating) {
      simulationInterval.current = setInterval(() => {
        runSimulationStep();
      }, 1000 / simulationSpeed);
    } else {
      if (simulationInterval.current) {
        clearInterval(simulationInterval.current);
      }
    }

    return () => {
      if (simulationInterval.current) {
        clearInterval(simulationInterval.current);
      }
    };
  }, [isSimulating, simulationSpeed, currentStep]);

  const runSimulationStep = () => {
    if (currentStep >= maxSteps) {
      setIsSimulating(false);
      return;
    }

    // Update institutions based on game-theoretic decisions
    setInstitutions(prevInstitutions => {
      return prevInstitutions.map(inst => {
        // Calculate strategic response
        const neighbors = connections.filter(c => c.source === inst.id || c.target === inst.id);
        const totalExposure = neighbors.reduce((sum, c) => sum + c.exposure, 0);
        
        // Apply shock if applicable
        let newCapital = inst.capital;
        let newLiquidity = inst.liquidity;
        let newRisk = inst.risk;

        // Strategic decision making
        if (inst.strategy === 'conservative') {
          newLiquidity *= 1.005; // Accumulate liquidity
          newRisk *= 0.995; // Reduce risk
        } else if (inst.strategy === 'aggressive') {
          newCapital *= 1.01; // Grow capital
          newRisk *= 1.02; // Increase risk
        }

        // Apply contagion effects
        const exposedConnections = neighbors.filter(c => {
          const partnerId = c.source === inst.id ? c.target : c.source;
          const partner = prevInstitutions.find(i => i.id === partnerId);
          return partner && partner.risk > parameters.contagionThreshold;
        });

        if (exposedConnections.length > 0) {
          newRisk *= 1.1; // Risk contagion
          newLiquidity *= 0.95; // Liquidity drain
          
          addAlert({
            type: 'warning',
            institution: inst.name,
            message: 'Exposed to high-risk counterparty',
            severity: 'medium'
          });
        }

        // Capital depletion check
        if (newCapital < 300) {
          addAlert({
            type: 'critical',
            institution: inst.name,
            message: 'Critical capital shortage detected',
            severity: 'high'
          });
        }

        return {
          ...inst,
          capital: Math.max(0, newCapital),
          liquidity: Math.max(0, newLiquidity),
          risk: Math.min(1, Math.max(0, newRisk))
        };
      });
    });

    // Update system metrics
    updateMetrics();

    // Record history
    setSimulationHistory(prev => [...prev, {
      step: currentStep,
      institutions: [...institutions],
      metrics: { ...metrics }
    }]);

    setCurrentStep(prev => prev + 1);
  };

  const updateMetrics = () => {
    const avgRisk = institutions.reduce((sum, i) => sum + i.risk, 0) / institutions.length;
    const avgLiquidity = institutions.reduce((sum, i) => sum + i.liquidity, 0) / institutions.length;
    const totalCapital = institutions.reduce((sum, i) => sum + i.capital, 0);
    
    const networkDensity = connections.length / (institutions.length * (institutions.length - 1) / 2);
    const totalExposure = connections.reduce((sum, c) => sum + c.exposure, 0);

    setMetrics({
      systemicRisk: avgRisk,
      liquidityFlow: avgLiquidity / 1000,
      networkCongestion: Math.min(1, totalExposure / totalCapital),
      stabilityIndex: Math.max(0, 1 - avgRisk),
      cascadeRisk: avgRisk * networkDensity,
      interconnectedness: networkDensity
    });
  };

  const addAlert = (alert) => {
    setAlerts(prev => [...prev, { ...alert, timestamp: Date.now(), id: Math.random() }]);
  };

  const handleAddInstitution = (type) => {
    const newId = `${type}${institutions.length + 1}`;
    const newInst = {
      id: newId,
      type,
      name: `New ${type.charAt(0).toUpperCase() + type.slice(1)} ${institutions.length + 1}`,
      position: { x: Math.random() * 600 + 50, y: Math.random() * 400 + 50 },
      capital: 500,
      liquidity: 250,
      risk: 0.2,
      strategy: 'balanced'
    };
    setInstitutions(prev => [...prev, newInst]);
  };

  const handleAddConnection = (source, target, type, exposure) => {
    const newConn = {
      id: `conn${connections.length + 1}`,
      source,
      target,
      type,
      exposure,
      weight: exposure / 500
    };
    setConnections(prev => [...prev, newConn]);
  };

  const handleRemoveInstitution = (id) => {
    setInstitutions(prev => prev.filter(i => i.id !== id));
    setConnections(prev => prev.filter(c => c.source !== id && c.target !== id));
    if (selectedInstitution?.id === id) setSelectedInstitution(null);
  };

  const handleRemoveConnection = (id) => {
    setConnections(prev => prev.filter(c => c.id !== id));
    if (selectedConnection?.id === id) setSelectedConnection(null);
  };

  const handleUpdateInstitution = (id, updates) => {
    setInstitutions(prev => prev.map(i => i.id === id ? { ...i, ...updates } : i));
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setCurrentStep(0);
    setSimulationHistory([]);
    setAlerts([]);
    updateMetrics();
  };

  const applyScenario = (scenario) => {
    switch (scenario) {
      case 'financial_crisis':
        setParameters(prev => ({ ...prev, shockMagnitude: 0.7, shockType: 'liquidity' }));
        setInstitutions(prev => prev.map(i => ({ ...i, risk: i.risk * 1.5, liquidity: i.liquidity * 0.5 })));
        addAlert({ type: 'critical', institution: 'System', message: 'Financial crisis scenario applied', severity: 'high' });
        break;
      case 'credit_crunch':
        setConnections(prev => prev.map(c => c.type === 'credit' ? { ...c, exposure: c.exposure * 0.5 } : c));
        addAlert({ type: 'warning', institution: 'System', message: 'Credit crunch scenario applied', severity: 'medium' });
        break;
      case 'regulatory_stress':
        setParameters(prev => ({ ...prev, contagionThreshold: 0.3, regulatoryIntervention: true }));
        addAlert({ type: 'info', institution: 'System', message: 'Regulatory stress test initiated', severity: 'low' });
        break;
      case 'network_failure':
        const randomInst = institutions[Math.floor(Math.random() * institutions.length)];
        handleUpdateInstitution(randomInst.id, { capital: randomInst.capital * 0.2, risk: 0.9 });
        addAlert({ type: 'critical', institution: randomInst.name, message: 'Institution failure simulated', severity: 'high' });
        break;
    }
  };

  return (
    <div className="w-full h-screen bg-gray-900 text-white overflow-hidden flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blue-400">Financial Infrastructure Simulator</h1>
          <p className="text-sm text-gray-400">Network-Based Game-Theoretic Modeling Platform</p>
        </div>
        <SimulationControls 
          isSimulating={isSimulating}
          onToggleSimulation={() => setIsSimulating(!isSimulating)}
          onReset={resetSimulation}
          simulationSpeed={simulationSpeed}
          onSpeedChange={setSimulationSpeed}
          currentStep={currentStep}
          maxSteps={maxSteps}
        />
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Controls */}
        <div className="w-80 bg-gray-800 border-r border-gray-700 overflow-y-auto">
          <ControlPanel 
            parameters={parameters}
            onParametersChange={setParameters}
            onAddInstitution={handleAddInstitution}
            onAddConnection={handleAddConnection}
            institutions={institutions}
          />
          <ScenarioPanel onApplyScenario={applyScenario} />
        </div>

        {/* Center - Network Visualization */}
        <div className="flex-1 bg-gray-900 relative">
          <NetworkCanvas 
            institutions={institutions}
            connections={connections}
            onSelectInstitution={setSelectedInstitution}
            onSelectConnection={setSelectedConnection}
            onUpdateInstitution={handleUpdateInstitution}
            selectedInstitution={selectedInstitution}
            selectedConnection={selectedConnection}
            isSimulating={isSimulating}
          />
          
          {/* Alerts Overlay */}
          <div className="absolute top-4 right-4 w-80 max-h-96 overflow-y-auto space-y-2">
            {alerts.slice(-5).reverse().map(alert => (
              <div 
                key={alert.id} 
                className={`p-3 rounded-lg shadow-lg ${
                  alert.severity === 'high' ? 'bg-red-900 border border-red-600' :
                  alert.severity === 'medium' ? 'bg-yellow-900 border border-yellow-600' :
                  'bg-blue-900 border border-blue-600'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-sm">{alert.institution}</p>
                    <p className="text-xs text-gray-300 mt-1">{alert.message}</p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Sidebar - Metrics & Details */}
        <div className="w-96 bg-gray-800 border-l border-gray-700 overflow-y-auto">
          <MetricsPanel metrics={metrics} />
          {selectedInstitution && (
            <InstitutionPanel 
              institution={selectedInstitution}
              onUpdate={handleUpdateInstitution}
              onRemove={handleRemoveInstitution}
              connections={connections.filter(c => 
                c.source === selectedInstitution.id || c.target === selectedInstitution.id
              )}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default FinancialNetworkPlayground;
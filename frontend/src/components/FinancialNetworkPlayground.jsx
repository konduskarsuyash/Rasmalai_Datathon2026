// components/FinancialNetworkPlayground.jsx
import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useUser, SignOutButton } from "@clerk/clerk-react";
import {
  ChevronLeft,
  ChevronRight,
  Layers,
  Settings,
  TrendingUp,
  LogOut,
} from "lucide-react";
import NetworkCanvas from "./NetworkCanvas";
import ControlPanel from "./ControlPanel";
import InstitutionPanel from "./InstitutionPanel";
import MetricsPanel from "./MetricsPanel";
import CanvasToolbar from "./CanvasToolbar";
import ScenarioPanel from "./ScenarioPanel";

const FinancialNetworkPlayground = () => {
  const { user } = useUser();

  // Network state
  const [institutions, setInstitutions] = useState([
    {
      id: "bank1",
      type: "bank",
      name: "Central Bank A",
      position: { x: 200, y: 150 },
      capital: 1000,
      liquidity: 500,
      risk: 0.2,
      strategy: "conservative",
    },
    {
      id: "bank2",
      type: "bank",
      name: "Commercial Bank B",
      position: { x: 400, y: 150 },
      capital: 800,
      liquidity: 400,
      risk: 0.3,
      strategy: "balanced",
    },
    {
      id: "exchange1",
      type: "exchange",
      name: "Stock Exchange X",
      position: { x: 300, y: 300 },
      capital: 1200,
      liquidity: 600,
      risk: 0.25,
      strategy: "aggressive",
    },
    {
      id: "clearing1",
      type: "clearinghouse",
      name: "Clearing House C",
      position: { x: 500, y: 300 },
      capital: 900,
      liquidity: 450,
      risk: 0.15,
      strategy: "conservative",
    },
  ]);

  const [connections, setConnections] = useState([
    {
      id: "conn1",
      source: "bank1",
      target: "bank2",
      type: "credit",
      exposure: 300,
      weight: 0.7,
    },
    {
      id: "conn2",
      source: "bank1",
      target: "exchange1",
      type: "settlement",
      exposure: 200,
      weight: 0.5,
    },
    {
      id: "conn3",
      source: "bank2",
      target: "clearing1",
      type: "margin",
      exposure: 150,
      weight: 0.6,
    },
    {
      id: "conn4",
      source: "exchange1",
      target: "clearing1",
      type: "settlement",
      exposure: 400,
      weight: 0.8,
    },
  ]);

  // Simulation state
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(1);
  const [currentStep, setCurrentStep] = useState(0);
  const [maxSteps, setMaxSteps] = useState(100);

  // UI state
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [tool, setTool] = useState("select");

  // System metrics
  const [metrics, setMetrics] = useState({
    systemicRisk: 0.2,
    liquidityFlow: 0.75,
    networkCongestion: 0.3,
    stabilityIndex: 0.85,
    cascadeRisk: 0.15,
    interconnectedness: 0.6,
  });

  // Simulation parameters
  const [parameters, setParameters] = useState({
    shockMagnitude: 0.3,
    shockType: "liquidity",
    contagionThreshold: 0.5,
    recoveryRate: 0.1,
    informationAsymmetry: 0.3,
    regulatoryIntervention: false,
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
    setInstitutions((prevInstitutions) => {
      return prevInstitutions.map((inst) => {
        // Calculate strategic response
        const neighbors = connections.filter(
          (c) => c.source === inst.id || c.target === inst.id,
        );
        const totalExposure = neighbors.reduce((sum, c) => sum + c.exposure, 0);

        // Apply shock if applicable
        let newCapital = inst.capital;
        let newLiquidity = inst.liquidity;
        let newRisk = inst.risk;

        // Strategic decision making
        if (inst.strategy === "conservative") {
          newLiquidity *= 1.005; // Accumulate liquidity
          newRisk *= 0.995; // Reduce risk
        } else if (inst.strategy === "aggressive") {
          newCapital *= 1.01; // Grow capital
          newRisk *= 1.02; // Increase risk
        }

        // Apply contagion effects
        const exposedConnections = neighbors.filter((c) => {
          const partnerId = c.source === inst.id ? c.target : c.source;
          const partner = prevInstitutions.find((i) => i.id === partnerId);
          return partner && partner.risk > parameters.contagionThreshold;
        });

        if (exposedConnections.length > 0) {
          newRisk *= 1.1; // Risk contagion
          newLiquidity *= 0.95; // Liquidity drain

          addAlert({
            type: "warning",
            institution: inst.name,
            message: "Exposed to high-risk counterparty",
            severity: "medium",
          });
        }

        // Capital depletion check
        if (newCapital < 300) {
          addAlert({
            type: "critical",
            institution: inst.name,
            message: "Critical capital shortage detected",
            severity: "high",
          });
        }

        return {
          ...inst,
          capital: Math.max(0, newCapital),
          liquidity: Math.max(0, newLiquidity),
          risk: Math.min(1, Math.max(0, newRisk)),
        };
      });
    });

    // Update system metrics
    updateMetrics();

    // Record history
    setSimulationHistory((prev) => [
      ...prev,
      {
        step: currentStep,
        institutions: [...institutions],
        metrics: { ...metrics },
      },
    ]);

    setCurrentStep((prev) => prev + 1);
  };

  const updateMetrics = () => {
    const avgRisk =
      institutions.reduce((sum, i) => sum + i.risk, 0) / institutions.length;
    const avgLiquidity =
      institutions.reduce((sum, i) => sum + i.liquidity, 0) /
      institutions.length;
    const totalCapital = institutions.reduce((sum, i) => sum + i.capital, 0);

    const networkDensity =
      connections.length /
      ((institutions.length * (institutions.length - 1)) / 2);
    const totalExposure = connections.reduce((sum, c) => sum + c.exposure, 0);

    setMetrics({
      systemicRisk: avgRisk,
      liquidityFlow: avgLiquidity / 1000,
      networkCongestion: Math.min(1, totalExposure / totalCapital),
      stabilityIndex: Math.max(0, 1 - avgRisk),
      cascadeRisk: avgRisk * networkDensity,
      interconnectedness: networkDensity,
    });
  };

  const addAlert = (alert) => {
    setAlerts((prev) => [
      ...prev,
      { ...alert, timestamp: Date.now(), id: Math.random() },
    ]);
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
      strategy: "balanced",
    };
    setInstitutions((prev) => [...prev, newInst]);
  };

  const handleAddConnection = (source, target, type, exposure) => {
    const newConn = {
      id: `conn${connections.length + 1}`,
      source,
      target,
      type,
      exposure,
      weight: exposure / 500,
    };
    setConnections((prev) => [...prev, newConn]);
  };

  const handleRemoveInstitution = (id) => {
    setInstitutions((prev) => prev.filter((i) => i.id !== id));
    setConnections((prev) =>
      prev.filter((c) => c.source !== id && c.target !== id),
    );
    if (selectedInstitution?.id === id) setSelectedInstitution(null);
  };

  const handleRemoveConnection = (id) => {
    setConnections((prev) => prev.filter((c) => c.id !== id));
    if (selectedConnection?.id === id) setSelectedConnection(null);
  };

  const handleUpdateInstitution = (id, updates) => {
    setInstitutions((prev) =>
      prev.map((i) => (i.id === id ? { ...i, ...updates } : i)),
    );
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
      case "financial_crisis":
        setParameters((prev) => ({
          ...prev,
          shockMagnitude: 0.7,
          shockType: "liquidity",
        }));
        setInstitutions((prev) =>
          prev.map((i) => ({
            ...i,
            risk: i.risk * 1.5,
            liquidity: i.liquidity * 0.5,
          })),
        );
        addAlert({
          type: "critical",
          institution: "System",
          message: "Financial crisis scenario applied",
          severity: "high",
        });
        break;
      case "credit_crunch":
        setConnections((prev) =>
          prev.map((c) =>
            c.type === "credit" ? { ...c, exposure: c.exposure * 0.5 } : c,
          ),
        );
        addAlert({
          type: "warning",
          institution: "System",
          message: "Credit crunch scenario applied",
          severity: "medium",
        });
        break;
      case "regulatory_stress":
        setParameters((prev) => ({
          ...prev,
          contagionThreshold: 0.3,
          regulatoryIntervention: true,
        }));
        addAlert({
          type: "info",
          institution: "System",
          message: "Regulatory stress test initiated",
          severity: "low",
        });
        break;
      case "network_failure":
        const randomInst =
          institutions[Math.floor(Math.random() * institutions.length)];
        handleUpdateInstitution(randomInst.id, {
          capital: randomInst.capital * 0.2,
          risk: 0.9,
        });
        addAlert({
          type: "critical",
          institution: randomInst.name,
          message: "Institution failure simulated",
          severity: "high",
        });
        break;
    }
  };

  return (
    <div className="w-full h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 text-gray-900 overflow-hidden flex flex-col relative">
      {/* Minimal Top Bar */}
      <div className="h-14 bg-white/90 backdrop-blur-xl border-b border-gray-200 flex items-center justify-between px-6 relative z-50 shadow-sm">
        <Link
          to="/"
          className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent hover:from-blue-300 hover:to-purple-400 transition flex items-center space-x-2"
        >
          <Layers className="w-5 h-5 text-blue-400" />
          <span>FinNet</span>
        </Link>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4" />
            <span>
              {user?.fullName || user?.primaryEmailAddress?.emailAddress}
            </span>
          </span>
          <SignOutButton>
            <button className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-all duration-200 flex items-center space-x-2 border border-gray-300">
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </SignOutButton>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Left Panel - Collapsible */}
        <div
          className={`${leftPanelOpen ? "w-80" : "w-0"} transition-all duration-300 bg-white/80 backdrop-blur-xl border-r border-gray-200 overflow-hidden relative z-40 shadow-lg`}
        >
          <div className="h-full overflow-y-auto scrollbar-hide p-4 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center space-x-2">
                <Settings className="w-5 h-5" />
                <span>Controls</span>
              </h2>
            </div>
            <ControlPanel
              parameters={parameters}
              onParametersChange={setParameters}
              onAddInstitution={handleAddInstitution}
              onAddConnection={handleAddConnection}
              institutions={institutions}
            />
            <ScenarioPanel onApplyScenario={applyScenario} />
          </div>
        </div>

        {/* Toggle Left Panel Button */}
        <button
          onClick={() => setLeftPanelOpen(!leftPanelOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-50 bg-white/90 backdrop-blur-xl border border-gray-300 rounded-r-lg p-2 hover:bg-gray-50 transition-all duration-200 shadow-lg text-gray-700"
          style={{ left: leftPanelOpen ? "20rem" : "0" }}
        >
          {leftPanelOpen ?
            <ChevronLeft className="w-5 h-5" />
          : <ChevronRight className="w-5 h-5" />}
        </button>

        {/* Center Canvas Area */}
        <div className="flex-1 relative">
          {/* Floating Toolbar */}
          <div className="absolute top-6 left-1/2 -translate-x-1/2 z-40">
            <CanvasToolbar
              tool={tool}
              onToolChange={setTool}
              isSimulating={isSimulating}
              onToggleSimulation={() => setIsSimulating(!isSimulating)}
              onReset={resetSimulation}
              zoomLevel={zoomLevel}
              onZoomIn={() => setZoomLevel(Math.min(zoomLevel + 0.1, 2))}
              onZoomOut={() => setZoomLevel(Math.max(zoomLevel - 0.1, 0.5))}
              currentStep={currentStep}
              maxSteps={maxSteps}
            />
          </div>

          {/* Network Canvas */}
          <NetworkCanvas
            institutions={institutions}
            connections={connections}
            onSelectInstitution={setSelectedInstitution}
            onSelectConnection={setSelectedConnection}
            onUpdateInstitution={handleUpdateInstitution}
            onAddConnection={handleAddConnection}
            selectedInstitution={selectedInstitution}
            selectedConnection={selectedConnection}
            isSimulating={isSimulating}
            zoomLevel={zoomLevel}
            tool={tool}
          />

          {/* Connection Hint - Bottom Left */}
          <div className="absolute bottom-6 left-6 px-4 py-2 bg-white/90 backdrop-blur-xl border border-gray-300 rounded-xl text-sm text-gray-700 shadow-lg">
            <span className="font-semibold text-blue-600">Tip:</span> Hold{" "}
            <kbd className="px-2 py-1 bg-gray-100 border border-gray-400 rounded text-xs text-gray-800">
              Ctrl
            </kbd>{" "}
            + drag to connect nodes
          </div>

          {/* Alerts - Bottom Left (Above Hint) */}
          <div className="absolute bottom-20 left-6 w-72 max-h-64 overflow-y-auto space-y-2 scrollbar-hide">
            {alerts
              .slice(-3)
              .reverse()
              .map((alert) => (
                <div
                  key={alert.id}
                  className={`p-2.5 rounded-lg backdrop-blur-xl shadow-lg border transition-all duration-300 text-xs ${
                    alert.severity === "high" ?
                      "bg-red-50/90 border-red-300 text-red-900"
                    : alert.severity === "medium" ?
                      "bg-yellow-50/90 border-yellow-300 text-yellow-900"
                    : "bg-blue-50/90 border-blue-300 text-blue-900"
                  }`}
                >
                  <p className="font-semibold">{alert.institution}</p>
                  <p className="mt-0.5 opacity-90">{alert.message}</p>
                </div>
              ))}
          </div>
        </div>

        {/* Right Panel - Collapsible */}
        <div
          className={`${rightPanelOpen ? "w-96" : "w-0"} transition-all duration-300 bg-white/80 backdrop-blur-xl border-l border-gray-200 overflow-hidden relative z-40 shadow-lg`}
        >
          <div className="h-full overflow-y-auto scrollbar-hide p-4 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center space-x-2">
                <TrendingUp className="w-5 h-5" />
                <span>Metrics</span>
              </h2>
            </div>
            <MetricsPanel metrics={metrics} />
            {selectedInstitution && (
              <InstitutionPanel
                institution={selectedInstitution}
                onUpdate={handleUpdateInstitution}
                onRemove={handleRemoveInstitution}
                connections={connections.filter(
                  (c) =>
                    c.source === selectedInstitution.id ||
                    c.target === selectedInstitution.id,
                )}
              />
            )}
          </div>
        </div>

        {/* Toggle Right Panel Button */}
        <button
          onClick={() => setRightPanelOpen(!rightPanelOpen)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-50 bg-white/90 backdrop-blur-xl border border-gray-300 rounded-l-lg p-2 hover:bg-gray-50 transition-all duration-200 shadow-lg text-gray-700"
          style={{ right: rightPanelOpen ? "24rem" : "0" }}
        >
          {rightPanelOpen ?
            <ChevronRight className="w-5 h-5" />
          : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );
};

export default FinancialNetworkPlayground;

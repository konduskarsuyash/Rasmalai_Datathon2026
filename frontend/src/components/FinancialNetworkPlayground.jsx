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
import BackendSimulationPanel from "./BackendSimulationPanel";
import SimulationResultCard from "./SimulationResultCard";
import BankDashboard from "./BankDashboard";
import MarketDashboard from "./MarketDashboard";
import LiveActivityFeed from "./LiveActivityFeed";

const FinancialNetworkPlayground = () => {
  const { user } = useUser();

  // Network state
  const [institutions, setInstitutions] = useState([
    {
      id: "bank1",
      type: "bank",
      name: "Central Bank A",
      position: { x: 150, y: 150 },
      capital: 1000,
      target: 2.5,
      risk: 0.2,
    },
    {
      id: "bank2",
      type: "bank",
      name: "Commercial Bank B",
      position: { x: 350, y: 150 },
      capital: 800,
      target: 3.5,
      risk: 0.3,
    },
    {
      id: "bank3",
      type: "bank",
      name: "Investment Bank C",
      position: { x: 550, y: 150 },
      capital: 1200,
      target: 4.0,
      risk: 0.25,
    },
    // Market nodes
    {
      id: "BANK_INDEX",
      type: "market",
      name: "Bank Index Fund",
      position: { x: 250, y: 350 },
      capital: 0,
      target: 1.0,
      risk: 0.0,
      isMarket: true,
    },
    {
      id: "FIN_SERVICES",
      type: "market",
      name: "Financial Services",
      position: { x: 450, y: 350 },
      capital: 0,
      target: 1.0,
      risk: 0.0,
      isMarket: true,
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

  // Backend simulation result (from POST /api/simulation/run)
  const [backendResult, setBackendResult] = useState(null);

  // Real-time simulation state
  const [activeTransactions, setActiveTransactions] = useState([]);
  const [realtimeConnections, setRealtimeConnections] = useState([]);

  // Dashboard state
  const [historicalData, setHistoricalData] = useState([]);
  const [allTransactions, setAllTransactions] = useState([]);
  const [activeDashboard, setActiveDashboard] = useState(null); // { type: 'bank' | 'market', id: string }
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);
  const [currentSimulationStep, setCurrentSimulationStep] = useState(0);

  // Derive metrics from backend result when present (so MetricsPanel reflects last run)
  const effectiveMetrics = backendResult?.summary
    ? {
        systemicRisk: backendResult.summary.default_rate ?? metrics.systemicRisk,
        liquidityFlow: Math.min(
          1,
          (backendResult.summary.final_total_equity ?? 0) / 1000
        ) || metrics.liquidityFlow,
        networkCongestion: (backendResult.summary.transactions_logged ?? 0) / 500 || metrics.networkCongestion,
        stabilityIndex: backendResult.summary.surviving_banks != null
          ? Math.min(1, backendResult.summary.surviving_banks / 20)
          : metrics.stabilityIndex,
        cascadeRisk: (backendResult.summary.total_cascade_events ?? 0) / 10 || metrics.cascadeRisk,
        interconnectedness: backendResult.summary.system_collapsed ? 0.9 : 0.6,
      }
    : metrics;

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
      target: 3.0,
      risk: 0.2,
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
            capital: i.capital * 0.5,
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

  const handleTransactionEvent = (event) => {
    if (event.type === 'init') {
      // Initialize connections from backend
      setRealtimeConnections(event.connections);
      // Reset historical data when simulation starts
      setHistoricalData([]);
      setAllTransactions([]);
      setCurrentSimulationStep(0);
      setIsSimulationRunning(true);
    } else if (event.type === 'step_start') {
      // Update current step
      setCurrentSimulationStep(event.step);
    } else if (event.type === 'transaction') {
      // Store transaction for dashboard
      setAllTransactions((prev) => [
        ...prev,
        {
          step: event.step,
          from_bank: event.from_bank,
          to_bank: event.to_bank,
          market_id: event.market_id,
          action: event.action,
          amount: event.amount,
          reason: event.reason,
        },
      ]);
      
      // Determine target based on action type
      let targetId = null;
      let targetType = 'bank';
      
      if (event.action === 'INVEST_MARKET' || event.action === 'DIVEST_MARKET') {
        // Market transaction - use market_id as target
        targetId = event.market_id || 'BANK_INDEX';
        targetType = 'market';
      } else if (event.action === 'INCREASE_LENDING' || event.action === 'DECREASE_LENDING') {
        // Bank-to-bank transaction
        targetId = event.to_bank;
        targetType = 'bank';
      }
      
      // Add active transaction for visualization
      const txId = `tx-${event.step}-${event.from_bank}-${Date.now()}`;
      setActiveTransactions((prev) => [
        ...prev,
        {
          id: txId,
          from: event.from_bank,
          to: targetId,
          targetType: targetType,
          amount: event.amount,
          action: event.action,
          market_id: event.market_id,
        },
      ]);

      // Remove after animation duration
      setTimeout(() => {
        setActiveTransactions((prev) => prev.filter((tx) => tx.id !== txId));
      }, 3000);

      // Update/create connections based on action type
      if (event.action === 'INCREASE_LENDING' && targetId !== null) {
        // Bank-to-bank lending connection
        setRealtimeConnections((prev) => {
          const existing = prev.find(
            (c) => c.from === event.from_bank && c.to === targetId && c.type === 'lending'
          );
          if (existing) {
            return prev.map((c) =>
              c.from === event.from_bank && c.to === targetId && c.type === 'lending'
                ? { ...c, amount: c.amount + event.amount }
                : c
            );
          } else {
            return [
              ...prev,
              {
                from: event.from_bank,
                to: targetId,
                amount: event.amount,
                type: 'lending',
              },
            ];
          }
        });
      } else if (event.action === 'INVEST_MARKET') {
        // Bank-to-market investment connection
        setRealtimeConnections((prev) => {
          const existing = prev.find(
            (c) => c.from === event.from_bank && c.to === targetId && c.type === 'investment'
          );
          if (existing) {
            return prev.map((c) =>
              c.from === event.from_bank && c.to === targetId && c.type === 'investment'
                ? { ...c, amount: c.amount + event.amount }
                : c
            );
          } else {
            return [
              ...prev,
              {
                from: event.from_bank,
                to: targetId,
                amount: event.amount,
                type: 'investment',
              },
            ];
          }
        });
      } else if (event.action === 'DIVEST_MARKET') {
        // Reduce market investment
        setRealtimeConnections((prev) => 
          prev.map((c) =>
            c.from === event.from_bank && c.to === targetId && c.type === 'investment'
              ? { ...c, amount: Math.max(0, c.amount - event.amount) }
              : c
          ).filter((c) => c.amount > 0.1) // Remove connections with negligible amounts
        );
      }
    } else if (event.type === 'step_end') {
      // Store step data for historical analysis
      setHistoricalData((prev) => [
        ...prev,
        {
          step: event.step,
          total_defaults: event.total_defaults,
          total_equity: event.total_equity,
          bank_states: event.bank_states,
          market_states: event.market_states,
        },
      ]);
    } else if (event.type === 'complete') {
      setIsSimulationRunning(false);
    }
  };

  const handleDefaultEvent = (event) => {
    // Mark institution as defaulted
    addAlert({
      type: "critical",
      institution: `Bank ${event.bank_id}`,
      message: `Bank has defaulted (equity: $${event.equity.toFixed(2)}M)`,
      severity: "high",
    });
  };

  const handleInstitutionClickDuringSimulation = (institution) => {
    // Only show dashboard if simulation has data
    if (historicalData.length === 0 && !isSimulationRunning) {
      // No simulation data yet, just select normally
      setSelectedInstitution(institution);
      return;
    }

    // Show dashboard for banks or markets
    if (institution.isMarket || institution.type === 'market') {
      setActiveDashboard({ type: 'market', id: institution.id });
    } else if (institution.type === 'bank') {
      setActiveDashboard({ type: 'bank', id: institution.id });
    }
  };

  const closeDashboard = () => {
    setActiveDashboard(null);
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
              onAddInstitution={handleAddInstitution}
              institutions={institutions}
              onClearAll={() => {
                setInstitutions([
                  {
                    id: "BANK_INDEX",
                    type: "market",
                    name: "Bank Index Fund",
                    position: { x: 250, y: 350 },
                    capital: 0,
                    target: 1.0,
                    risk: 0.0,
                    isMarket: true,
                  },
                  {
                    id: "FIN_SERVICES",
                    type: "market",
                    name: "Financial Services",
                    position: { x: 450, y: 350 },
                    capital: 0,
                    target: 1.0,
                    risk: 0.0,
                    isMarket: true,
                  },
                ]);
                setConnections([]);
                setRealtimeConnections([]);
                setActiveTransactions([]);
                setSelectedInstitution(null);
              }}
            />
            <BackendSimulationPanel
              institutions={institutions}
              connections={connections}
              onTransactionEvent={handleTransactionEvent}
            />
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
            onSelectInstitution={
              isSimulationRunning || historicalData.length > 0
                ? handleInstitutionClickDuringSimulation
                : setSelectedInstitution
            }
            onSelectConnection={setSelectedConnection}
            onUpdateInstitution={handleUpdateInstitution}
            onAddConnection={handleAddConnection}
            selectedInstitution={selectedInstitution}
            selectedConnection={selectedConnection}
            isSimulating={isSimulating}
            zoomLevel={zoomLevel}
            tool={tool}
            activeTransactions={activeTransactions}
            realtimeConnections={realtimeConnections}
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
          
          {/* Live Activity Feed - Show during simulation */}
          {isSimulationRunning && (
            <LiveActivityFeed 
              transactions={allTransactions}
              currentStep={currentSimulationStep}
            />
          )}
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
            {backendResult && (
              <div className="mb-4">
                <SimulationResultCard result={backendResult} />
              </div>
            )}
            <MetricsPanel metrics={effectiveMetrics} />
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

      {/* Dashboards (rendered as modals) */}
      {activeDashboard && activeDashboard.type === 'bank' && (() => {
        // Find bank by either string ID or numeric ID
        const bank = institutions.find(i => {
          if (i.id === activeDashboard.id) return true;
          // Handle case where backend sends numeric ID but frontend has string IDs
          const numericId = typeof activeDashboard.id === 'number' ? activeDashboard.id : null;
          if (numericId !== null && i.id === `bank${numericId + 1}`) return true;
          return false;
        });
        
        return bank ? (
          <BankDashboard
            bank={bank}
            historicalData={historicalData}
            transactions={allTransactions}
            onClose={closeDashboard}
          />
        ) : null;
      })()}
      
      {activeDashboard && activeDashboard.type === 'market' && (
        <MarketDashboard
          market={institutions.find(i => i.id === activeDashboard.id)}
          historicalData={historicalData}
          transactions={allTransactions}
          onClose={closeDashboard}
        />
      )}
    </div>
  );
};

export default FinancialNetworkPlayground;

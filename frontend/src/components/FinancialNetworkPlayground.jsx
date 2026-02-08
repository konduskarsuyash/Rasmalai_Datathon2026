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
import CascadeVisualization from "./CascadeVisualization";
import CascadePlayer from "./CascadePlayer";
import HistoricalTrendsChart from "./HistoricalTrendsChart";

const FinancialNetworkPlayground = () => {
  const { user } = useUser();

  // Network state - Start completely empty
  const [institutions, setInstitutions] = useState([]);

  const [connections, setConnections] = useState([]);

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

  // System metrics - Initialize to 0 until simulation runs
  const [metrics, setMetrics] = useState({
    systemicRisk: 0,
    liquidityFlow: 0,
    networkCongestion: 0,
    stabilityIndex: 0,
    cascadeRisk: 0,
    interconnectedness: 0,
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
  const effectiveMetrics =
    backendResult?.summary ?
      {
        systemicRisk:
          backendResult.summary.default_rate ?? metrics.systemicRisk,
        liquidityFlow:
          Math.min(1, (backendResult.summary.final_total_equity ?? 0) / 1000) ||
          metrics.liquidityFlow,
        networkCongestion:
          (backendResult.summary.transactions_logged ?? 0) / 500 ||
          metrics.networkCongestion,
        stabilityIndex:
          backendResult.summary.surviving_banks != null ?
            Math.min(1, backendResult.summary.surviving_banks / 20)
          : metrics.stabilityIndex,
        cascadeRisk:
          (backendResult.summary.total_cascade_events ?? 0) / 10 ||
          metrics.cascadeRisk,
        interconnectedness: backendResult.summary.system_collapsed ? 0.9 : 0.6,
      }
    : metrics;

  // Update market nodes with real-time data from simulation
  useEffect(() => {
    if (historicalData.length > 0) {
      const latestData = historicalData[historicalData.length - 1];
      if (latestData.market_states) {
        setInstitutions((prev) =>
          prev.map((inst) => {
            if (inst.type === "market" || inst.isMarket) {
              const marketState = latestData.market_states.find(
                (m) => m.market_id === inst.id,
              );
              if (marketState) {
                return {
                  ...inst,
                  price: marketState.price,
                  total_invested: marketState.total_invested,
                  return: marketState.return,
                };
              }
            }
            return inst;
          }),
        );
      }
    }
  }, [historicalData]);

  // Alerts and events
  const [alerts, setAlerts] = useState([]);

  // Cascade state
  const [cascadeEvents, setCascadeEvents] = useState([]);
  const [cascadingBanks, setCascadingBanks] = useState([]);
  const [cascadeTrigger, setCascadeTrigger] = useState(null);
  const [cascadePlayerActive, setCascadePlayerActive] = useState(false);
  const [showCascadePanel, setShowCascadePanel] = useState(false);

  // Historical trends state
  const [showTrendsPanel, setShowTrendsPanel] = useState(false);
  const [selectedBanksForComparison, setSelectedBanksForComparison] = useState([]);

  // Simulation engine
  const simulationInterval = useRef(null);

  // Trigger a bank default for cascade testing
  const triggerBankDefault = async (bankId) => {
    try {
      const response = await fetch('http://localhost:8000/api/interactive/trigger_default', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bank_id: bankId }),
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Default triggered:', result);
        
        // Add cascade event to history
        const cascadeEvent = {
          time_step: currentSimulationStep || 0,
          cascade_count: result.cascade_count,
          cascade_depth: result.cascade_depth,
          affected_banks: result.affected_banks,
        };
        
        setCascadeEvents(prev => [...prev, cascadeEvent]);
        setCascadingBanks(result.affected_banks || []);
        setCascadeTrigger(bankId);
        setShowCascadePanel(true);
        
        // Clear cascade animation after 5 seconds
        setTimeout(() => {
          setCascadingBanks([]);
          setCascadeTrigger(null);
        }, 5000);
        
        return result;
      } else {
        console.error('Failed to trigger default:', await response.text());
      }
    } catch (error) {
      console.error('Error triggering default:', error);
    }
  };

  // Cascade player step change handler
  const handleCascadeStepChange = (step) => {
    // Update visualization based on cascade playback step
    const selectedCascade = cascadeEvents[cascadeEvents.length - 1];
    if (selectedCascade && selectedCascade.affected_banks) {
      setCascadingBanks(selectedCascade.affected_banks.slice(0, step));
      if (step > 0) {
        setCascadeTrigger(selectedCascade.affected_banks[0]);
      } else {
        setCascadeTrigger(null);
      }
    }
  };

  // Replay cascade animation
  const handleReplayCascade = (cascade) => {
    setCascadePlayerActive(true);
    setCascadingBanks([]);
    setCascadeTrigger(null);
  };

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
    if (institutions.length === 0) return;
    const avgRisk =
      institutions.reduce((sum, i) => sum + (i.risk || 0), 0) / institutions.length;
    const avgLiquidity =
      institutions.reduce((sum, i) => sum + (i.liquidity || 0), 0) /
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
    if (type === 'market') {
      // Add a market node
      const marketCount = institutions.filter(i => i.type === 'market' || i.isMarket).length;
      const marketNames = ['Bank Index Fund', 'Financial Services', 'Tech Sector', 'Real Estate', 'Commodities', 'Bond Market'];
      const marketIds = ['BANK_INDEX', 'FIN_SERVICES', 'TECH_SECTOR', 'REAL_ESTATE', 'COMMODITIES', 'BOND_MARKET'];
      const idx = marketCount % marketIds.length;
      // Avoid duplicate market IDs
      let marketId = marketIds[idx];
      let marketName = marketNames[idx];
      if (institutions.find(i => i.id === marketId)) {
        marketId = `MARKET_${Date.now()}`;
        marketName = `Market ${marketCount + 1}`;
      }
      const newMarket = {
        id: marketId,
        type: 'market',
        name: marketName,
        position: { x: Math.random() * 600 + 50, y: Math.random() * 400 + 50 },
        capital: 0,
        target: 1.0,
        risk: 0.0,
        isMarket: true,
      };
      setInstitutions((prev) => [...prev, newMarket]);
      setSelectedInstitution(newMarket);
    } else {
      // Add a bank node
      const bankCount = institutions.filter(i => i.type === 'bank' && !i.isMarket).length;
      const newId = `bank${bankCount + 1}`;
      // Ensure unique ID
      let finalId = newId;
      if (institutions.find(i => i.id === finalId)) {
        finalId = `bank${Date.now()}`;
      }
      const newInst = {
        id: finalId,
        type,
        name: `Bank ${bankCount + 1}`,
        position: { x: Math.random() * 600 + 50, y: Math.random() * 400 + 50 },
        capital: 100,
        target: 3.0,
        risk: 0.3,
        // Interbank parameters
        interbankRate: 2.5,
        haircut: 15,
        reserveRatio: 10,
      };
      setInstitutions((prev) => [...prev, newInst]);
      setSelectedInstitution(newInst);
    }
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
    // Also update selected institution if it's the one being updated
    if (selectedInstitution?.id === id) {
      setSelectedInstitution((prev) => (prev ? { ...prev, ...updates } : null));
    }
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
    try {
    if (!event || !event.type) {
      console.warn("[FinancialNetworkPlayground] Received invalid event:", event);
      return;
    }
    console.log("[FinancialNetworkPlayground] Received event:", event.type);

    if (event.type === "init") {
      // Initialize connections from backend
      setRealtimeConnections(event.connections || []);
      // Reset historical data when simulation starts
      setHistoricalData([]);
      setAllTransactions([]);
      setCurrentSimulationStep(0);
      setIsSimulationRunning(true);

      // Add backend-created market nodes to the canvas if they don't exist yet
      if (event.markets && event.markets.length > 0) {
        setInstitutions(prev => {
          const existingIds = new Set(prev.map(i => i.id));
          const newMarkets = event.markets
            .filter(m => !existingIds.has(m.id))
            .map((m, idx) => ({
              id: m.id,
              type: 'market',
              name: m.name || m.id,
              position: { x: 450 + idx * 150, y: 80 + idx * 60 },
              capital: 0,
              target: 1.0,
              risk: 0.0,
              isMarket: true,
              price: m.price || 100,
              totalInvested: m.total_invested || 0,
            }));
          if (newMarkets.length > 0) {
            console.log('[FinancialNetworkPlayground] Adding', newMarkets.length, 'backend-created markets to canvas:', newMarkets.map(m => m.id));
            return [...prev, ...newMarkets];
          }
          return prev;
        });
      }

      // Store initial state with market data
      if (event.markets && event.markets.length > 0) {
        const initialState = {
          step: 0,
          total_defaults: 0,
          total_equity:
            event.banks?.reduce((sum, b) => sum + b.capital, 0) || 0,
          bank_states:
            event.banks?.map((b) => ({
              bank_id: b.id,
              name: b.name,
              capital: b.capital,
              cash: b.cash,
              is_defaulted: b.is_defaulted || false,
            })) || [],
          market_states: event.markets.map((m) => ({
            market_id: m.id,
            name: m.name,
            price: m.price || 100,
            total_invested: m.total_invested || 0,
            return: 0,
          })),
        };
        setHistoricalData([initialState]);
        console.log(
          "[FinancialNetworkPlayground] Stored initial state with",
          event.markets.length,
          "markets",
        );
      }

      console.log("[FinancialNetworkPlayground] Simulation initialized");
    } else if (event.type === "restart") {
      // Reset all simulation state
      setHistoricalData([]);
      setAllTransactions([]);
      setCurrentSimulationStep(0);
      setIsSimulationRunning(false);
      setActiveTransactions([]);
      setRealtimeConnections([]);
      setActiveDashboard(null);
      console.log("[FinancialNetworkPlayground] Simulation restarted");
    } else if (event.type === "financial_crisis") {
      // Show crisis alert
      addAlert({
        type: "critical",
        institution: "GLOBAL MARKETS",
        message:
          "💥 FINANCIAL CRISIS! Markets crashed 50%, banks facing liquidity crisis",
        severity: "high",
      });
      console.log("[FinancialNetworkPlayground] Financial crisis triggered");
    } else if (event.type === "step_start") {
      // Update current step
      setCurrentSimulationStep(event.step);
      console.log("[FinancialNetworkPlayground] Step started:", event.step);
    } else if (event.type === "transaction") {
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

      // Log varying amounts to show dynamic behavior
      if (event.step < 2) {
        console.log(
          `[Transaction] Bank ${event.from_bank}: ${event.action} $${(event.amount ?? 0).toFixed(1)}M`,
        );
      }

      // Determine target based on action type
      let targetId = null;
      let targetType = "bank";

      if (
        event.action === "INVEST_MARKET" ||
        event.action === "DIVEST_MARKET"
      ) {
        // Market transaction - use market_id as target
        targetId = event.market_id || "BANK_INDEX";
        targetType = "market";
      } else if (
        event.action === "INCREASE_LENDING" ||
        event.action === "DECREASE_LENDING"
      ) {
        // Bank-to-bank transaction
        targetId = event.to_bank;
        targetType = "bank";
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
      if (event.action === "INCREASE_LENDING" && targetId !== null) {
        // Bank-to-bank lending connection
        setRealtimeConnections((prev) => {
          const existing = prev.find(
            (c) =>
              c.from === event.from_bank &&
              c.to === targetId &&
              c.type === "lending",
          );
          if (existing) {
            return prev.map((c) =>
              (
                c.from === event.from_bank &&
                c.to === targetId &&
                c.type === "lending"
              ) ?
                { ...c, amount: c.amount + event.amount }
              : c,
            );
          } else {
            return [
              ...prev,
              {
                from: event.from_bank,
                to: targetId,
                amount: event.amount,
                type: "lending",
              },
            ];
          }
        });
      } else if (event.action === "INVEST_MARKET") {
        // Bank-to-market investment connection
        setRealtimeConnections((prev) => {
          const existing = prev.find(
            (c) =>
              c.from === event.from_bank &&
              c.to === targetId &&
              c.type === "investment",
          );
          if (existing) {
            return prev.map((c) =>
              (
                c.from === event.from_bank &&
                c.to === targetId &&
                c.type === "investment"
              ) ?
                { ...c, amount: c.amount + event.amount }
              : c,
            );
          } else {
            return [
              ...prev,
              {
                from: event.from_bank,
                to: targetId,
                amount: event.amount,
                type: "investment",
              },
            ];
          }
        });
      } else if (event.action === "DIVEST_MARKET") {
        // Reduce market investment
        setRealtimeConnections(
          (prev) =>
            prev
              .map((c) =>
                (
                  c.from === event.from_bank &&
                  c.to === targetId &&
                  c.type === "investment"
                ) ?
                  { ...c, amount: Math.max(0, c.amount - event.amount) }
                : c,
              )
              .filter((c) => c.amount > 0.1), // Remove connections with negligible amounts
        );
      }
    } else if (event.type === "step_end") {
      // Store step data for historical analysis
      console.log(
        "[FinancialNetworkPlayground] Step ended:",
        event.step,
        "Bank states:",
        event.bank_states?.length,
      );
      setHistoricalData((prev) => {
        const updated = [
          ...prev,
          {
            step: event.step,
            total_defaults: event.total_defaults,
            total_equity: event.total_equity,
            bank_states: event.bank_states,
            market_states: event.market_states,
          },
        ];
        console.log(
          "[FinancialNetworkPlayground] Historical data updated, total steps:",
          updated.length,
        );
        return updated;
      });
    } else if (event.type === "market_gain") {
      // Bank realized gain/loss from market divestment
      const realizedGain = event.realized_gain ?? 0;
      const marketReturn = event.market_return ?? 0;
      const gainLoss = realizedGain >= 0 ? "gain" : "loss";
      const absGain = Math.abs(realizedGain);

      addAlert({
        type: realizedGain >= 0 ? "success" : "warning",
        institution: `Bank ${event.bank_id}`,
        message: `Realized ${realizedGain >= 0 ? "📈" : "📉"} $${absGain.toFixed(1)}M ${gainLoss} (${marketReturn.toFixed(1)}% return) from ${event.market_id}`,
        severity: absGain > 10 ? "high" : "medium",
      });

      console.log(
        `[Market Gain] Bank ${event.bank_id}: $${realizedGain.toFixed(1)}M ${gainLoss} from ${event.market_id}`,
      );
    } else if (event.type === "profit_booking") {
      // Bank booked profit from market investments (mark-to-market)
      const profit = event.profit ?? 0;
      const bankId = event.bank_id;
      const isGain = profit >= 0;
      const absProfit = Math.abs(profit);
      
      // Add to allTransactions for activity feed
      setAllTransactions((prev) => [
        ...prev,
        {
          step: event.step,
          from_bank: bankId,
          to_bank: null,
          market_id: null,
          action: "BOOK_PROFIT",
          amount: absProfit,
          reason: `${isGain ? 'Profit' : 'Loss'}: $${absProfit.toFixed(1)}M from investments`,
        },
      ]);
      
      // Add active transaction for canvas visualization (pulsing effect at bank)
      const txId = `profit-${event.step}-${bankId}-${Date.now()}`;
      setActiveTransactions((prev) => [
        ...prev,
        {
          id: txId,
          from: bankId,
          to: null,          // No target — shows pulsing at source
          targetType: "self",
          amount: absProfit,
          action: "BOOK_PROFIT",
          profit: profit,
        },
      ]);
      
      // Remove after animation
      setTimeout(() => {
        setActiveTransactions((prev) => prev.filter((tx) => tx.id !== txId));
      }, 3500);
      
      // Show alert for significant profit bookings
      if (absProfit > 1.0) {
        addAlert({
          type: isGain ? "success" : "warning",
          institution: `Bank ${bankId}`,
          message: `${isGain ? '💰' : '📉'} Booked $${absProfit.toFixed(1)}M ${isGain ? 'profit' : 'loss'} from investments`,
          severity: absProfit > 5 ? "high" : "medium",
        });
      }
      
      console.log(
        `[Profit Booking] Bank ${bankId}: ${isGain ? '+' : '-'}$${absProfit.toFixed(1)}M`,
      );
    } else if (event.type === "market_movement") {
      // Market price fluctuation
      const changePct = event.change_pct ?? 0;
      const direction = changePct >= 0 ? "⬆️" : "⬇️";

      addAlert({
        type: changePct >= 0 ? "success" : "warning",
        institution: event.market_id,
        message: `${direction} Price moved ${changePct >= 0 ? "+" : ""}${changePct.toFixed(1)}%: $${event.old_price ?? '?'} → $${event.new_price ?? '?'}`,
        severity: Math.abs(changePct) > 5 ? "high" : "medium",
      });

      console.log(
        `[Market Movement] ${event.market_id}: ${(event.change_pct ?? 0).toFixed(1)}% ($${event.old_price ?? '?'} → $${event.new_price ?? '?'})`,
      );
    } else if (event.type === "complete") {
      setIsSimulationRunning(false);
      console.log("[FinancialNetworkPlayground] Simulation completed");
    }
    } catch (err) {
      console.error('[FinancialNetworkPlayground] Error handling event:', event?.type, err);
    }
  };

  const handleDefaultEvent = (event) => {
    // Mark institution as defaulted
    addAlert({
      type: "critical",
      institution: `Bank ${event.bank_id}`,
      message: `Bank has defaulted (equity: $${(event.equity ?? 0).toFixed(2)}M)`,
      severity: "high",
    });
  };

  const handleInstitutionClickDuringSimulation = (institution) => {
    console.log(
      "[FinancialNetworkPlayground] Institution clicked:",
      institution.name,
      "Historical data points:",
      historicalData.length,
    );

    // Only show dashboard if simulation has data
    if (historicalData.length === 0 && !isSimulationRunning) {
      // No simulation data yet, just select normally
      setSelectedInstitution(institution);
      console.log(
        "[FinancialNetworkPlayground] No historical data, selecting institution normally",
      );
      return;
    }

    // Show dashboard for banks or markets
    if (institution.isMarket || institution.type === "market") {
      console.log(
        "[FinancialNetworkPlayground] Opening market dashboard for:",
        institution.id,
      );
      setActiveDashboard({ type: "market", id: institution.id });
    } else if (institution.type === "bank") {
      console.log(
        "[FinancialNetworkPlayground] Opening bank dashboard for:",
        institution.id,
      );
      setActiveDashboard({ type: "bank", id: institution.id });
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
                setInstitutions([]);
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
              isSimulationRunning || historicalData.length > 0 ?
                handleInstitutionClickDuringSimulation
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
            cascadingBanks={cascadingBanks}
            cascadeTrigger={cascadeTrigger}
          />

          {/* Connection Hint - Bottom Left */}
          <div className="absolute bottom-6 left-6 px-4 py-2 bg-white/90 backdrop-blur-xl border border-gray-300 rounded-xl text-sm text-gray-700 shadow-lg">
            <span className="font-semibold text-blue-600">Tip:</span> Hold{" "}
            <kbd className="px-2 py-1 bg-gray-100 border border-gray-400 rounded text-xs text-gray-800">
              Ctrl
            </kbd>{" "}
            + drag to connect nodes
          </div>

          {/* Historical Trends Button - Top Right */}
          {historicalData.length > 0 && (
            <div className="absolute top-24 right-96 z-40">
              <button
                onClick={() => setShowTrendsPanel(!showTrendsPanel)}
                className={`px-4 py-2 rounded-lg shadow-lg font-semibold transition-all duration-200 flex items-center gap-2 ${
                  showTrendsPanel
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white'
                    : 'bg-white/90 text-gray-700 border-2 border-gray-300 hover:bg-gray-50'
                }`}
                title="Show historical trends"
              >
                <span>📊</span>
                <span>Trends</span>
              </button>
            </div>
          )}

          {/* Historical Trends Panel - Full Right Side Overlay */}
          {showTrendsPanel && historicalData.length > 0 && (
            <div className="absolute top-0 right-0 bottom-0 w-[500px] bg-white/95 backdrop-blur-xl border-l-2 border-gray-300 shadow-2xl overflow-y-auto z-50">
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    <span>📈</span>
                    <span>Historical Analytics</span>
                  </h2>
                  <button
                    onClick={() => setShowTrendsPanel(false)}
                    className="bg-gray-200 hover:bg-gray-300 rounded-full p-2 transition-all"
                    title="Close trends panel"
                  >
                    <span className="text-gray-600 font-bold text-lg leading-none">×</span>
                  </button>
                </div>
                
                {/* Bank Selection for Comparison */}
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h3 className="text-xs font-bold text-gray-700 mb-2">Select Banks to Compare:</h3>
                  <div className="grid grid-cols-4 gap-2">
                    {institutions
                      .filter(i => i.type === 'bank')
                      .slice(0, 8)
                      .map(bank => {
                        const bankId = parseInt(bank.id.replace('bank', '')) - 1;
                        const isSelected = selectedBanksForComparison.includes(bankId);
                        return (
                          <button
                            key={bank.id}
                            onClick={() => {
                              if (isSelected) {
                                setSelectedBanksForComparison(prev => prev.filter(id => id !== bankId));
                              } else if (selectedBanksForComparison.length < 6) {
                                setSelectedBanksForComparison(prev => [...prev, bankId]);
                              }
                            }}
                            className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                              isSelected
                                ? 'bg-blue-600 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                            disabled={!isSelected && selectedBanksForComparison.length >= 6}
                          >
                            B{bankId}
                          </button>
                        );
                      })}
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    {selectedBanksForComparison.length}/6 banks selected
                  </p>
                </div>

                <HistoricalTrendsChart
                  historicalData={historicalData}
                  selectedBanks={selectedBanksForComparison}
                  showSystemMetrics={true}
                />
              </div>
            </div>
          )}

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

          {/* Cascade Visualization Panel - Bottom Right */}
          {showCascadePanel && cascadeEvents.length > 0 && (
            <div className="absolute bottom-6 right-6 w-96 max-h-[600px] overflow-hidden">
              <div className="relative">
                <button
                  onClick={() => setShowCascadePanel(false)}
                  className="absolute top-4 right-4 z-10 bg-white/90 hover:bg-white rounded-full p-2 shadow-lg transition-all"
                  title="Close cascade panel"
                >
                  <span className="text-gray-600 font-bold text-lg leading-none">×</span>
                </button>
                <CascadeVisualization
                  cascadeEvents={cascadeEvents}
                  banks={institutions}
                  onReplayCascade={handleReplayCascade}
                />
                {cascadeEvents.length > 0 && (
                  <CascadePlayer
                    cascade={cascadeEvents[cascadeEvents.length - 1]}
                    onStepChange={handleCascadeStepChange}
                    isPlaying={cascadePlayerActive}
                    onPlayToggle={setCascadePlayerActive}
                  />
                )}
              </div>
            </div>
          )}

          {/* Trigger Default Button - For Testing */}
          {isSimulationRunning && selectedInstitution && selectedInstitution.type === 'bank' && (
            <div className="absolute top-24 right-6 z-50">
              <button
                onClick={() => {
                  const bankNum = parseInt(selectedInstitution.id.replace('bank', ''));
                  triggerBankDefault(bankNum);
                }}
                className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-4 py-2 rounded-lg shadow-lg font-semibold transition-all duration-200 flex items-center gap-2"
                title="Trigger default for cascade testing"
              >
                <span>💥</span>
                <span>Trigger Default</span>
              </button>
            </div>
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
              <div className="mt-2 space-y-3">
                {/* Input Features moved to right side */}
                <div className="bg-white rounded-lg border border-gray-200 p-3 space-y-2">
                  <p className="text-xs font-semibold text-gray-700">
                    Input Features for <span className="font-bold">{selectedInstitution.name || "Citigroup"}</span>
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-gray-700">
                    <div className="space-y-1">
                      <label className="block text-[11px] text-gray-600 font-medium">
                        Capital ratio (%)
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={0.1}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-[11px]"
                        value={selectedInstitution.capitalRatio ?? 8}
                        onChange={(e) => {
                          const value = Number(e.target.value) || 0;
                          handleUpdateInstitution(selectedInstitution.id, { capitalRatio: value });
                        }}
                      />
                      <p className="text-[10px] text-gray-500">Citigroup capital ratio: 8% (low)</p>
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[11px] text-gray-600 font-medium">
                        Leverage (x)
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={50}
                        step={0.1}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-[11px]"
                        value={selectedInstitution.leverage ?? 12}
                        onChange={(e) => {
                          const value = Number(e.target.value) || 0;
                          handleUpdateInstitution(selectedInstitution.id, { leverage: value });
                        }}
                      />
                      <p className="text-[10px] text-gray-500">Citigroup leverage: 12x (high)</p>
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[11px] text-gray-600 font-medium">
                        Network centrality
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={1}
                        step={0.01}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-[11px]"
                        value={selectedInstitution.networkCentrality ?? 0.78}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          handleUpdateInstitution(selectedInstitution.id, { networkCentrality: isNaN(value) ? 0 : value });
                        }}
                      />
                      <p className="text-[10px] text-gray-500">Network centrality: 0.78 (systemically important!)</p>
                    </div>
                    <div className="space-y-1">
                      <label className="block text-[11px] text-gray-600 font-medium">
                        Past defaults
                      </label>
                      <input
                        type="number"
                        min={0}
                        step={1}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-[11px]"
                        value={selectedInstitution.pastDefaults ?? 1}
                        onChange={(e) => {
                          const value = Number(e.target.value) || 0;
                          handleUpdateInstitution(selectedInstitution.id, { pastDefaults: value });
                        }}
                      />
                      <p className="text-[10px] text-gray-500">Past defaults: 1 (red flag)</p>
                    </div>
                    <div className="space-y-1 col-span-2">
                      <label className="block text-[11px] text-gray-600 font-medium">
                        Market stress (%)
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={1}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-[11px]"
                        value={selectedInstitution.marketStress ?? 45}
                        onChange={(e) => {
                          const value = Number(e.target.value) || 0;
                          handleUpdateInstitution(selectedInstitution.id, { marketStress: value });
                        }}
                      />
                      <p className="text-[10px] text-gray-500">Market stress: 45% (elevated)</p>
                    </div>
                  </div>
                </div>

                {/* Full institution editor on right */}
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
              </div>
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
      {activeDashboard &&
        activeDashboard.type === "bank" &&
        (() => {
          // Find bank by either string ID or numeric ID
          const bank = institutions.find((i) => {
            if (i.id === activeDashboard.id) return true;
            // Handle case where backend sends numeric ID but frontend has string IDs
            const numericId =
              typeof activeDashboard.id === "number" ?
                activeDashboard.id
              : null;
            if (numericId !== null && i.id === `bank${numericId + 1}`)
              return true;
            return false;
          });

          return bank ?
              <BankDashboard
                bank={bank}
                historicalData={historicalData}
                transactions={allTransactions}
                onClose={closeDashboard}
              />
            : null;
        })()}

      {activeDashboard && activeDashboard.type === "market" && (() => {
        const market = institutions.find((i) => i.id === activeDashboard.id);
        return market ? (
          <MarketDashboard
            market={market}
            historicalData={historicalData}
            transactions={allTransactions}
            onClose={closeDashboard}
          />
        ) : null;
      })()}
    </div>
  );
};

export default FinancialNetworkPlayground;

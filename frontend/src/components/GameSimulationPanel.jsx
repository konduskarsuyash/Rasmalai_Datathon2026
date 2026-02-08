// GameSimulationPanel component - Step-by-step simulation control
import { useState, useEffect } from "react";
import {
  Play,
  Pause,
  Square,
  StepForward,
  Power,
  AlertCircle,
  Activity,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import * as gameApi from "../api/gameSimulation";

const GameSimulationPanel = () => {
  const [sessionState, setSessionState] = useState("UNINITIALIZED");
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(30);
  const [isRunning, setIsRunning] = useState(false);
  const [autoStep, setAutoStep] = useState(false);
  const [banks, setBanks] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [lastStepResult, setLastStepResult] = useState(null);
  const [error, setError] = useState(null);

  // Configuration
  const [numBanks, setNumBanks] = useState(10);
  const [connectionDensity, setConnectionDensity] = useState(0.2);
  const [numSteps, setNumSteps] = useState(30);

  useEffect(() => {
    // Poll simulation status
    const interval = setInterval(async () => {
      try {
        const status = await gameApi.getSimulationStatus();
        if (status.state !== "UNINITIALIZED") {
          setSessionState(status.state);
          setCurrentStep(status.current_step || 0);
          setTotalSteps(status.total_steps || 30);
        }
      } catch (err) {
        // Simulation not initialized yet
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Auto-step mode
    if (autoStep && sessionState === "RUNNING") {
      const interval = setInterval(async () => {
        try {
          await handleStep();
        } catch (err) {
          setAutoStep(false);
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [autoStep, sessionState]);

  const handleInit = async () => {
    try {
      setError(null);
      const result = await gameApi.initSimulation({
        network: {
          num_banks: numBanks,
          connection_density: connectionDensity,
        },
        simulation: {
          steps: numSteps,
          use_featherless: false,
          verbose_logging: false,
        },
        market: {
          price_sensitivity: 0.002,
          volatility: 0.03,
          momentum: 0.1,
        },
      });

      setSessionState("INITIALIZED");
      setTotalSteps(numSteps);

      // Create banks
      const bankPromises = [];
      for (let i = 0; i < numBanks; i++) {
        bankPromises.push(
          gameApi.createBank({
            capital: 100_000_000,
            target_leverage: 2.5 + Math.random() * 1.5,
            risk_factor: 0.1 + Math.random() * 0.4,
            objective: ["SURVIVAL", "GROWTH", "AGGRESSIVE"][
              Math.floor(Math.random() * 3)
            ],
          }),
        );
      }

      const createdBanks = await Promise.all(bankPromises);
      setBanks(createdBanks);

      // Create connections
      for (let i = 0; i < createdBanks.length; i++) {
        for (let j = i + 1; j < createdBanks.length; j++) {
          if (Math.random() < connectionDensity) {
            await gameApi.createConnection({
              from_bank: createdBanks[i].bank_id,
              to_bank: createdBanks[j].bank_id,
              type: "credit",
              exposure: 10_000_000 + Math.random() * 30_000_000,
            });
          }
        }
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStart = async () => {
    try {
      setError(null);
      await gameApi.startSimulation();
      setSessionState("RUNNING");
      setIsRunning(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStep = async () => {
    try {
      setError(null);
      const result = await gameApi.executeStep();
      setLastStepResult(result);
      setCurrentStep(result.step);

      // Update metrics
      const newMetrics = await gameApi.getMetrics();
      setMetrics(newMetrics);

      if (result.state === "COMPLETED") {
        setIsRunning(false);
        setAutoStep(false);
        setSessionState("COMPLETED");
      }
    } catch (err) {
      setError(err.message);
      setAutoStep(false);
    }
  };

  const handlePause = async () => {
    try {
      setError(null);
      await gameApi.pauseSimulation();
      setSessionState("PAUSED");
      setAutoStep(false);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleResume = async () => {
    try {
      setError(null);
      await gameApi.resumeSimulation();
      setSessionState("RUNNING");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStop = async () => {
    try {
      setError(null);
      const result = await gameApi.stopSimulation();
      setSessionState("STOPPED");
      setIsRunning(false);
      setAutoStep(false);
      setMetrics(result.metrics);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCrisis = async () => {
    try {
      setError(null);
      await gameApi.triggerFinancialCrisis();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6 bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <Activity className="w-6 h-6 text-blue-400" />
          <span>Game-Theoretic Simulation</span>
        </h2>
        <div className="text-sm text-gray-400">
          State:{" "}
          <span
            className={`font-semibold ${
              sessionState === "RUNNING" ? "text-green-400"
              : sessionState === "PAUSED" ? "text-yellow-400"
              : sessionState === "STOPPED" || sessionState === "COMPLETED" ?
                "text-red-400"
              : "text-gray-400"
            }`}
          >
            {sessionState}
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-400 p-3 rounded mb-4 flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Configuration (only when UNINITIALIZED) */}
      {sessionState === "UNINITIALIZED" && (
        <div className="space-y-4 mb-6">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm text-gray-400">Banks</label>
              <input
                type="number"
                value={numBanks}
                onChange={(e) => setNumBanks(parseInt(e.target.value))}
                className="w-full bg-gray-700 text-white p-2 rounded mt-1"
                min="5"
                max="50"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">
                Connection Density
              </label>
              <input
                type="number"
                value={connectionDensity}
                onChange={(e) =>
                  setConnectionDensity(parseFloat(e.target.value))
                }
                className="w-full bg-gray-700 text-white p-2 rounded mt-1"
                min="0.1"
                max="0.9"
                step="0.1"
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">Steps</label>
              <input
                type="number"
                value={numSteps}
                onChange={(e) => setNumSteps(parseInt(e.target.value))}
                className="w-full bg-gray-700 text-white p-2 rounded mt-1"
                min="10"
                max="100"
              />
            </div>
          </div>

          <button
            onClick={handleInit}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
          >
            <Power className="w-5 h-5" />
            <span>Initialize Simulation</span>
          </button>
        </div>
      )}

      {/* Controls (after initialization) */}
      {sessionState !== "UNINITIALIZED" && (
        <>
          <div className="flex space-x-2 mb-6">
            {sessionState === "INITIALIZED" && (
              <button
                onClick={handleStart}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
              >
                <Play className="w-5 h-5" />
                <span>Start</span>
              </button>
            )}

            {sessionState === "RUNNING" && (
              <>
                <button
                  onClick={handlePause}
                  className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <Pause className="w-5 h-5" />
                  <span>Pause</span>
                </button>
                <button
                  onClick={handleStep}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <StepForward className="w-5 h-5" />
                  <span>Step</span>
                </button>
              </>
            )}

            {sessionState === "PAUSED" && (
              <>
                <button
                  onClick={handleResume}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <Play className="w-5 h-5" />
                  <span>Resume</span>
                </button>
                <button
                  onClick={handleStep}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
                >
                  <StepForward className="w-5 h-5" />
                  <span>Step</span>
                </button>
              </>
            )}

            {(sessionState === "RUNNING" || sessionState === "PAUSED") && (
              <button
                onClick={handleStop}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 rounded font-semibold transition-colors flex items-center justify-center space-x-2"
              >
                <Square className="w-5 h-5" />
                <span>Stop</span>
              </button>
            )}
          </div>

          {/* Auto-step toggle */}
          {(sessionState === "RUNNING" || sessionState === "PAUSED") && (
            <div className="flex items-center justify-between mb-4 p-3 bg-gray-700 rounded">
              <span className="text-sm text-gray-300">Auto-Step Mode</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoStep}
                  onChange={(e) => setAutoStep(e.target.checked)}
                  className="sr-only peer"
                  disabled={sessionState !== "RUNNING"}
                />
                <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          )}

          {/* Progress */}
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm text-gray-400 mb-2">
              <span>
                Step {currentStep} / {totalSteps}
              </span>
              <span>{Math.round((currentStep / totalSteps) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentStep / totalSteps) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-700 p-4 rounded">
              <div className="text-sm text-gray-400 mb-1">Total Defaults</div>
              <div className="text-2xl font-bold text-red-400">
                {metrics.total_defaults || 0}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {((metrics.default_rate || 0) * 100).toFixed(1)}% rate
              </div>
            </div>

            <div className="bg-gray-700 p-4 rounded">
              <div className="text-sm text-gray-400 mb-1">Surviving Banks</div>
              <div className="text-2xl font-bold text-green-400">
                {metrics.surviving_banks || banks.length}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {banks.length > 0 ?
                  (
                    ((metrics.surviving_banks || banks.length) / banks.length) *
                    100
                  ).toFixed(1)
                : 0}
                % survival
              </div>
            </div>

            <div className="bg-gray-700 p-4 rounded">
              <div className="text-sm text-gray-400 mb-1 flex items-center space-x-1">
                <DollarSign className="w-3 h-3" />
                <span>Total Equity</span>
              </div>
              <div className="text-xl font-bold text-blue-400">
                ${((metrics.total_equity || 0) / 1_000_000).toFixed(1)}M
              </div>
            </div>

            <div className="bg-gray-700 p-4 rounded">
              <div className="text-sm text-gray-400 mb-1">Cascade Events</div>
              <div className="text-2xl font-bold text-orange-400">
                {metrics.cascade_events || 0}
              </div>
            </div>
          </div>

          {/* Last step result */}
          {lastStepResult && (
            <div className="bg-gray-700 p-4 rounded">
              <div className="text-sm text-gray-400 mb-2">Last Step Events</div>
              <div className="flex flex-wrap gap-2">
                {lastStepResult.events.map((event, idx) => (
                  <span
                    key={idx}
                    className={`px-2 py-1 rounded text-xs font-semibold ${
                      event === "default" ? "bg-red-600 text-white"
                      : event === "margin_call" ? "bg-yellow-600 text-white"
                      : event === "cascade" ? "bg-orange-600 text-white"
                      : event === "forced_liquidation" ?
                        "bg-purple-600 text-white"
                      : "bg-blue-600 text-white"
                    }`}
                  >
                    {event}
                  </span>
                ))}
                {lastStepResult.events.length === 0 && (
                  <span className="text-gray-500 text-xs">No events</span>
                )}
              </div>

              {lastStepResult.defaults &&
                lastStepResult.defaults.length > 0 && (
                  <div className="mt-2 text-xs text-red-400">
                    Defaults: {lastStepResult.defaults.join(", ")}
                  </div>
                )}

              <div className="mt-2 text-xs text-gray-400">
                System Liquidity:{" "}
                {(lastStepResult.system_liquidity * 100).toFixed(1)}%
              </div>
            </div>
          )}

          {/* Intervention Controls */}
          {(sessionState === "RUNNING" || sessionState === "PAUSED") && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="text-sm text-gray-400 mb-2">Interventions</div>
              <button
                onClick={handleCrisis}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded font-semibold transition-colors text-sm"
              >
                Trigger Financial Crisis
              </button>
            </div>
          )}

          {/* System Collapsed Warning */}
          {metrics.system_collapsed && (
            <div className="mt-4 bg-red-600 text-white p-4 rounded-lg font-bold text-center animate-pulse">
              ⚠️ SYSTEM COLLAPSE DETECTED ⚠️
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default GameSimulationPanel;

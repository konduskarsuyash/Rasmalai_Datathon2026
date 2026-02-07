// components/RealTimeSimulationPanel.jsx
import { useState, useRef } from "react";
import { Play, Loader2, AlertCircle, CheckCircle, Zap } from "lucide-react";
import { useAuth } from "@clerk/clerk-react";

const RealTimeSimulationPanel = ({ onResult, lastResult, institutions, onTransactionEvent, onDefaultEvent }) => {
  const { getToken } = useAuth();
  const [numSteps, setNumSteps] = useState(30);
  const [useFeatherless, setUseFeatherless] = useState(false);
  const [usePlaygroundNodes, setUsePlaygroundNodes] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const eventSourceRef = useRef(null);

  const handleRun = async () => {
    setError(null);
    setIsRunning(true);
    setCurrentStep(0);
    setStats(null);

    try {
      const token = await getToken();
      
      // Build node parameters from playground institutions if enabled
      let nodeParameters = null;
      if (usePlaygroundNodes && institutions && institutions.length > 0) {
        nodeParameters = institutions.map((inst) => ({
          node_id: inst.id,
          initial_capital: inst.capital || 100.0,
          target_leverage: inst.target || 3.0,
          risk_factor: inst.risk || 0.2,
        }));
      }

      const body = {
        num_banks: usePlaygroundNodes && nodeParameters ? nodeParameters.length : 10,
        num_steps: numSteps,
        use_featherless: useFeatherless,
        verbose: false,
        node_parameters: nodeParameters,
        connection_density: 0.2,
      };

      // Use EventSource for Server-Sent Events
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const url = `${baseUrl}/api/simulation/run/stream`;
      
      // For POST with SSE, we need to use fetch with stream
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            handleEvent(data);
          }
        }
      }

      setIsRunning(false);
    } catch (e) {
      setError(e.message || "Simulation failed");
      setIsRunning(false);
    }
  };

  const handleEvent = (event) => {
    switch (event.type) {
      case 'init':
        console.log('Simulation initialized', event);
        if (onTransactionEvent) {
          onTransactionEvent({
            type: 'init',
            banks: event.banks,
            connections: event.connections,
          });
        }
        break;

      case 'step_start':
        setCurrentStep(event.step);
        break;

      case 'transaction':
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'default':
        if (onDefaultEvent) {
          onDefaultEvent(event);
        }
        break;

      case 'cascade':
        console.log('Cascade event', event);
        break;

      case 'step_end':
        setStats({
          step: event.step,
          defaults: event.total_defaults,
          equity: event.total_equity,
        });
        break;

      case 'complete':
        setStats({
          step: event.total_steps,
          defaults: event.total_defaults,
          surviving: event.surviving_banks,
        });
        if (onResult) {
          onResult({ summary: event });
        }
        setIsRunning(false);
        break;
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsRunning(false);
  };

  return (
    <div className="border-t border-gray-300 pt-4 mt-4">
      <h3 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-3 flex items-center gap-2">
        <Zap className="w-5 h-5 text-purple-600" />
        Real-Time Simulation
      </h3>
      <p className="text-xs text-gray-600 mb-3">
        Live visualization of transactions and network dynamics
      </p>

      <div className="space-y-3">
        {institutions && institutions.length > 0 && (
          <div className="flex items-center justify-between p-2 bg-purple-50 rounded-lg border border-purple-200">
            <label className="text-sm text-gray-700 font-medium">
              Use Playground Banks ({institutions.length} banks)
            </label>
            <button
              type="button"
              onClick={() => setUsePlaygroundNodes((v) => !v)}
              disabled={isRunning}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                usePlaygroundNodes
                  ? "bg-purple-500 text-white"
                  : "bg-gray-200 text-gray-800 border border-gray-300"
              } disabled:opacity-50`}
            >
              {usePlaygroundNodes ? "ON" : "OFF"}
            </button>
          </div>
        )}

        <div>
          <label className="block text-xs text-gray-600 font-medium mb-1">
            Simulation Steps
          </label>
          <input
            type="number"
            min={5}
            max={100}
            value={numSteps}
            onChange={(e) => setNumSteps(Number(e.target.value))}
            disabled={isRunning}
            className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none disabled:bg-gray-100"
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="text-sm text-gray-700 font-medium">
            AI Strategy (Featherless)
          </label>
          <button
            type="button"
            onClick={() => setUseFeatherless((v) => !v)}
            disabled={isRunning}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              useFeatherless
                ? "bg-green-500 text-white"
                : "bg-gray-200 text-gray-800 border border-gray-300"
            } disabled:opacity-50`}
          >
            {useFeatherless ? "ON" : "OFF"}
          </button>
        </div>

        {isRunning && stats && (
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-xs text-blue-900 space-y-1">
              <div className="flex justify-between">
                <span>Current Step:</span>
                <span className="font-bold">{currentStep}/{numSteps}</span>
              </div>
              <div className="flex justify-between">
                <span>Defaults:</span>
                <span className="font-bold text-red-600">{stats.defaults || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Total Equity:</span>
                <span className="font-bold text-green-600">${(stats.equity || 0).toFixed(2)}M</span>
              </div>
            </div>
          </div>
        )}

        {!isRunning ? (
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-md"
          >
            <Play className="w-4 h-4" />
            Start Real-Time Simulation
          </button>
        ) : (
          <button
            onClick={handleStop}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-md"
          >
            <Loader2 className="w-4 h-4 animate-spin" />
            Stop Simulation
          </button>
        )}

        {error && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {stats && !isRunning && stats.surviving !== undefined && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-green-50 border border-green-200 text-green-800 text-sm">
            <CheckCircle className="w-4 h-4 shrink-0" />
            Complete: {stats.surviving} survived, {stats.defaults} defaults
          </div>
        )}
      </div>
    </div>
  );
};

export default RealTimeSimulationPanel;

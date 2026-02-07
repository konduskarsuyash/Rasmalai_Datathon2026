// components/BackendSimulationPanel.jsx
import { useState } from "react";
import { Play, Loader2, AlertCircle, CheckCircle } from "lucide-react";
import { runSimulation } from "../api/client";
import { useAuth } from "@clerk/clerk-react";

const BackendSimulationPanel = ({ onResult, lastResult, institutions }) => {
  const { getToken } = useAuth();
  const [numBanks, setNumBanks] = useState(20);
  const [numSteps, setNumSteps] = useState(30);
  const [useFeatherless, setUseFeatherless] = useState(false);
  const [usePlaygroundNodes, setUsePlaygroundNodes] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setError(null);
    setLoading(true);
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
      
      const data = await runSimulation(
        {
          num_banks: usePlaygroundNodes && nodeParameters ? nodeParameters.length : numBanks,
          num_steps: numSteps,
          use_featherless: useFeatherless,
          verbose: false,
          node_parameters: nodeParameters,
          connection_density: 0.2,
        },
        token
      );
      onResult?.(data);
    } catch (e) {
      setError(e.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-t border-gray-300 pt-4 mt-4">
      <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
        Backend Simulation (v2)
      </h3>
      <p className="text-xs text-gray-600 mb-3">
        Run balance-sheet simulation on the server (config + core + ML policy).
      </p>
      <div className="space-y-3">
        {institutions && institutions.length > 0 && (
          <div className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-200">
            <label className="text-sm text-gray-700 font-medium">
              Use Playground Nodes ({institutions.length} nodes)
            </label>
            <button
              type="button"
              onClick={() => setUsePlaygroundNodes((v) => !v)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                usePlaygroundNodes
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-800 border border-gray-300"
              }`}
            >
              {usePlaygroundNodes ? "ON" : "OFF"}
            </button>
          </div>
        )}
        {!usePlaygroundNodes && (
          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">Banks</label>
            <input
              type="number"
              min={1}
              max={100}
              value={numBanks}
              onChange={(e) => setNumBanks(Number(e.target.value))}
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        )}
        <div>
          <label className="block text-xs text-gray-600 font-medium mb-1">Steps</label>
          <input
            type="number"
            min={1}
            max={200}
            value={numSteps}
            onChange={(e) => setNumSteps(Number(e.target.value))}
            className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm text-gray-700 font-medium">Featherless (LLM)</label>
          <button
            type="button"
            onClick={() => setUseFeatherless((v) => !v)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              useFeatherless
                ? "bg-green-500 text-white"
                : "bg-gray-200 text-gray-800 border border-gray-300"
            }`}
          >
            {useFeatherless ? "ON" : "OFF"}
          </button>
        </div>
        <button
          onClick={handleRun}
          disabled={loading}
          className="w-full px-4 py-2.5 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-md"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run simulation
            </>
          )}
        </button>
        {error && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}
        {lastResult && !error && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-green-50 border border-green-200 text-green-800 text-sm">
            <CheckCircle className="w-4 h-4 shrink-0" />
            Done: {lastResult.summary?.surviving_banks ?? "—"} surviving,{" "}
            {lastResult.summary?.total_defaults ?? "—"} defaults
          </div>
        )}
      </div>
    </div>
  );
};

export default BackendSimulationPanel;

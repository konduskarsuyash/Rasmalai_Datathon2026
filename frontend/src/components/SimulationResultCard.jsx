// components/SimulationResultCard.jsx
// Shows last backend simulation result (summary + time series)

const SimulationResultCard = ({ result }) => {
  if (!result?.summary) return null;

  const s = result.summary;
  const defaults = result.defaults_over_time || [];
  const equity = result.total_equity_over_time || [];

  return (
    <div className="p-4 border border-gray-200 rounded-xl bg-white/90 shadow-sm space-y-3">
      <h3 className="text-base font-bold text-gray-800 border-b border-gray-200 pb-2">
        Last backend run
      </h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Steps</span>
          <span className="font-medium">{s.total_steps}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Surviving banks</span>
          <span className="font-medium text-green-600">{s.surviving_banks}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Defaults</span>
          <span className="font-medium text-red-600">{s.total_defaults}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Default rate</span>
          <span className="font-medium">{(s.default_rate * 100).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between col-span-2">
          <span className="text-gray-600">Final equity</span>
          <span className="font-medium">${(s.final_total_equity ?? 0).toFixed(0)}</span>
        </div>
        <div className="flex justify-between col-span-2">
          <span className="text-gray-600">Cascade events</span>
          <span className="font-medium">{s.total_cascade_events ?? 0}</span>
        </div>
        <div className="flex justify-between col-span-2">
          <span className="text-gray-600">System collapsed</span>
          <span className="font-medium">{s.system_collapsed ? "Yes" : "No"}</span>
        </div>
      </div>
      {defaults.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Defaults over time (last 10 steps)</p>
          <p className="text-xs font-mono text-gray-700 truncate">
            [{defaults.slice(-10).join(", ")}]
          </p>
        </div>
      )}
      {equity.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-1">Total equity (last 10 steps)</p>
          <p className="text-xs font-mono text-gray-700 truncate">
            [{equity.slice(-10).map((e) => e.toFixed(0)).join(", ")}]
          </p>
        </div>
      )}
    </div>
  );
};

export default SimulationResultCard;

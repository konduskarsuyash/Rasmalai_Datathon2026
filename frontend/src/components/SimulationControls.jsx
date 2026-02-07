// components/SimulationControls.jsx
const SimulationControls = ({
  isSimulating,
  onToggleSimulation,
  onReset,
  simulationSpeed,
  onSpeedChange,
  currentStep,
  maxSteps,
}) => {
  return (
    <div className="flex items-center space-x-4">
      <div className="text-sm">
        <span className="text-gray-400">Step: </span>
        <span className="font-bold text-blue-400">{currentStep}</span>
        <span className="text-gray-400"> / {maxSteps}</span>
      </div>

      <div className="flex items-center space-x-2">
        <label className="text-sm text-gray-400">Speed:</label>
        <select
          value={simulationSpeed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
          className="px-3 py-1.5 bg-gray-800/90 border border-blue-500/30 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
        >
          <option value="0.5">0.5x</option>
          <option value="1">1x</option>
          <option value="2">2x</option>
          <option value="5">5x</option>
        </select>
      </div>

      <button
        onClick={onToggleSimulation}
        className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg ${
          isSimulating ?
            "bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 hover:shadow-red-500/50"
          : "bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 hover:shadow-green-500/50"
        }`}
      >
        {isSimulating ? "⏸ Pause" : "▶ Start"}
      </button>

      <button
        onClick={onReset}
        className="px-6 py-2 bg-gray-700/80 hover:bg-gray-600/80 rounded-lg font-medium transition-all duration-200 border border-gray-600"
      >
        🔄 Reset
      </button>
    </div>
  );
};

export default SimulationControls;

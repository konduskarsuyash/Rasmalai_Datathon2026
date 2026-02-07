// components/SimulationControls.jsx
const SimulationControls = ({ 
  isSimulating, 
  onToggleSimulation, 
  onReset, 
  simulationSpeed, 
  onSpeedChange, 
  currentStep, 
  maxSteps 
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
          className="px-3 py-1 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="0.5">0.5x</option>
          <option value="1">1x</option>
          <option value="2">2x</option>
          <option value="5">5x</option>
        </select>
      </div>

      <button
        onClick={onToggleSimulation}
        className={`px-6 py-2 rounded-lg font-medium transition-colors ${
          isSimulating
            ? 'bg-red-600 hover:bg-red-700'
            : 'bg-green-600 hover:bg-green-700'
        }`}
      >
        {isSimulating ? '⏸ Pause' : '▶ Start'}
      </button>

      <button
        onClick={onReset}
        className="px-6 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
      >
        🔄 Reset
      </button>
    </div>
  );
};

export default SimulationControls;
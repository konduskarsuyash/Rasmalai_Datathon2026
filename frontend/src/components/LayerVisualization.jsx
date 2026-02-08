// LayerVisualization component - Shows which layer is executing
import { useState, useEffect } from "react";

const LayerVisualization = ({ simulationRunning, currentStep, totalSteps }) => {
  const [activeLayer, setActiveLayer] = useState(null);

  const layers = [
    { id: 1, name: "User Control", icon: "🧍‍♂️", color: "blue" },
    { id: 2, name: "Orchestrator", icon: "🧠", color: "purple" },
    { id: 3, name: "Strategy/AI", icon: "🎯", color: "green" },
    { id: 4, name: "Network", icon: "🌐", color: "orange" },
    { id: 5, name: "Clearing", icon: "🏛️", color: "red" },
    { id: 6, name: "Output", icon: "📊", color: "indigo" },
  ];

  useEffect(() => {
    if (simulationRunning && currentStep > 0) {
      // Cycle through layers to show active processing
      const interval = setInterval(() => {
        setActiveLayer((prev) => {
          if (prev === null) return 2;
          if (prev >= 6) return 3;
          return prev + 1;
        });
      }, 200);
      return () => clearInterval(interval);
    } else {
      setActiveLayer(null);
    }
  }, [simulationRunning, currentStep]);

  return (
    <div className="p-4 bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-white">Layered Architecture</h3>
        {simulationRunning && (
          <div className="text-xs text-green-400 flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>
              Step {currentStep}/{totalSteps}
            </span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        {layers.map((layer) => (
          <div
            key={layer.id}
            className={`flex items-center space-x-2 p-2 rounded transition-all duration-200 ${
              activeLayer === layer.id ?
                `bg-${layer.color}-600 scale-105 shadow-lg`
              : "bg-gray-700/50"
            }`}
          >
            <span className="text-xl">{layer.icon}</span>
            <div className="flex-1">
              <div
                className={`text-xs font-medium ${
                  activeLayer === layer.id ? "text-white" : "text-gray-300"
                }`}
              >
                Layer {layer.id}
              </div>
              <div
                className={`text-xs ${
                  activeLayer === layer.id ? "text-white/90" : "text-gray-400"
                }`}
              >
                {layer.name}
              </div>
            </div>
            {activeLayer === layer.id && (
              <div className="text-white text-xs animate-pulse">▶</div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-3 p-2 bg-gray-700/30 rounded text-xs text-gray-300">
        <div className="font-semibold mb-1">Feedback Loops:</div>
        <div className="space-y-0.5 text-gray-400">
          <div>• Market → Strategy (4→3)</div>
          <div>• Clearing → Market (5→4)</div>
          <div className="text-red-400">• Fire Sale Cascade (5→4→5)</div>
        </div>
      </div>
    </div>
  );
};

export default LayerVisualization;

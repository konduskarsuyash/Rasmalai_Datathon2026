// components/CanvasToolbar.jsx
import {
  Play,
  Pause,
  RotateCcw,
  Plus,
  Minus,
  Hand,
  MousePointer2,
  Link2,
} from "lucide-react";

const CanvasToolbar = ({
  isSimulating,
  onToggleSimulation,
  onReset,
  zoomLevel,
  onZoomIn,
  onZoomOut,
  tool,
  onToolChange,
  currentStep,
  maxSteps,
}) => {
  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 flex items-center gap-2 bg-white/95 backdrop-blur-xl border border-gray-300 rounded-2xl px-4 py-2 shadow-xl">
      {/* Tool Selection */}
      <div className="flex items-center gap-1 pr-3 border-r border-gray-300">
        <button
          onClick={() => onToolChange("select")}
          className={`p-2.5 rounded-lg transition-all ${
            tool === "select" ?
              "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
            : "text-gray-700 hover:bg-gray-100"
          }`}
          title="Select & Move (V)"
        >
          <MousePointer2 size={18} />
        </button>
        <button
          onClick={() => onToolChange("pan")}
          className={`p-2.5 rounded-lg transition-all ${
            tool === "pan" ?
              "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
            : "text-gray-700 hover:bg-gray-100"
          }`}
          title="Pan (H)"
        >
          <Hand size={18} />
        </button>
        <button
          onClick={() => onToolChange("connect")}
          className={`p-2.5 rounded-lg transition-all ${
            tool === "connect" ?
              "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
            : "text-gray-700 hover:bg-gray-100"
          }`}
          title="Connect (C)"
        >
          <Link2 size={18} />
        </button>
      </div>

      {/* Simulation Controls */}
      <div className="flex items-center gap-1 px-3 border-r border-gray-300">
        <button
          onClick={onToggleSimulation}
          className={`p-2.5 rounded-lg transition-all ${
            isSimulating ?
              "bg-red-500 text-white shadow-lg shadow-red-500/30"
            : "bg-green-500 text-white shadow-lg shadow-green-500/30"
          }`}
          title={isSimulating ? "Pause" : "Play"}
        >
          {isSimulating ?
            <Pause size={18} />
          : <Play size={18} />}
        </button>
        <button
          onClick={onReset}
          className="p-2.5 rounded-lg text-gray-700 hover:bg-gray-100 transition-all"
          title="Reset"
        >
          <RotateCcw size={18} />
        </button>
        <div className="ml-2 text-sm text-gray-700 font-medium min-w-[80px]">
          {currentStep} / {maxSteps}
        </div>
      </div>

      {/* Zoom Controls */}
      <div className="flex items-center gap-1 pl-3">
        <button
          onClick={onZoomOut}
          className="p-2.5 rounded-lg text-gray-700 hover:bg-gray-100 transition-all"
          title="Zoom Out"
        >
          <Minus size={18} />
        </button>
        <div className="text-sm text-gray-700 font-medium min-w-[50px] text-center">
          {Math.round(zoomLevel * 100)}%
        </div>
        <button
          onClick={onZoomIn}
          className="p-2.5 rounded-lg text-gray-700 hover:bg-gray-100 transition-all"
          title="Zoom In"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );
};

export default CanvasToolbar;

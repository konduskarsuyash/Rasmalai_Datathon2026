import React from 'react';

/**
 * RiskLegend - Shows color scale for risk heatmap
 */
const RiskLegend = ({ showHeatmap, onToggle }) => {
  return (
    <div className="bg-white/90 backdrop-blur-xl border-2 border-gray-300 rounded-xl p-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
          <span>🌡️</span>
          <span>Risk Heatmap</span>
        </h3>
        <button
          onClick={onToggle}
          className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all duration-200 ${
            showHeatmap
              ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white shadow-md'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          {showHeatmap ? '👁️ ON' : '👁️ OFF'}
        </button>
      </div>

      {showHeatmap && (
        <>
          {/* Color Scale */}
          <div className="mb-3">
            <div className="h-8 rounded-lg overflow-hidden flex">
              <div className="flex-1 bg-gradient-to-r from-green-500 via-yellow-500 via-orange-500 to-red-600"></div>
            </div>
            <div className="flex justify-between mt-1 text-xs text-gray-600 font-medium">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Risk Levels */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 rounded-full bg-green-500 border-2 border-green-700"></div>
              <span className="font-semibold text-gray-700">Very Low</span>
              <span className="text-gray-500">(0-20%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 rounded-full bg-yellow-400 border-2 border-yellow-600"></div>
              <span className="font-semibold text-gray-700">Low</span>
              <span className="text-gray-500">(20-40%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 rounded-full bg-orange-500 border-2 border-orange-700"></div>
              <span className="font-semibold text-gray-700">Medium</span>
              <span className="text-gray-500">(40-60%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-red-700"></div>
              <span className="font-semibold text-gray-700">High</span>
              <span className="text-gray-500">(60-80%)</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <div className="w-4 h-4 rounded-full bg-red-700 border-2 border-red-900"></div>
              <span className="font-semibold text-gray-700">Very High</span>
              <span className="text-gray-500">(80-100%)</span>
            </div>
          </div>

          {/* Info */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-600 leading-relaxed">
              <span className="font-semibold">💡 How it works:</span> Risk is calculated based on leverage, capital ratio, liquidity, and network exposure. Hover over nodes to see exact scores.
            </p>
          </div>
        </>
      )}
    </div>
  );
};

export default RiskLegend;

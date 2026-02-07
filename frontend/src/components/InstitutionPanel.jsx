// components/InstitutionPanel.jsx
const InstitutionPanel = ({ institution, onUpdate, onRemove, connections }) => {
  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Bank Details
        </h3>
        <button
          onClick={() => onRemove(institution.id)}
          className="px-3 py-1.5 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md"
        >
          Remove
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs text-gray-600 font-medium mb-1">
            Bank Name
          </label>
          <input
            type="text"
            value={institution.name}
            onChange={(e) => onUpdate(institution.id, { name: e.target.value })}
            className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
        </div>

        {/* Capital Input */}
        <div className="border-2 border-blue-200 rounded-lg p-3 bg-blue-50">
          <label className="block text-sm text-blue-900 font-bold mb-2">
            💰 Capital (Million $)
          </label>
          <input
            type="number"
            min="10"
            max="1000"
            value={institution.capital}
            onChange={(e) =>
              onUpdate(institution.id, {
                capital: parseFloat(e.target.value) || 100,
              })
            }
            className="w-full px-4 py-3 bg-white border-2 border-blue-300 text-gray-800 rounded-lg text-lg font-bold focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
          <p className="text-xs text-blue-700 mt-1">
            Initial capital reserves
          </p>
        </div>

        {/* Target Input */}
        <div className="border-2 border-green-200 rounded-lg p-3 bg-green-50">
          <label className="block text-sm text-green-900 font-bold mb-2">
            🎯 Target Leverage Ratio
          </label>
          <input
            type="number"
            min="1"
            max="10"
            step="0.1"
            value={institution.target || 3.0}
            onChange={(e) =>
              onUpdate(institution.id, {
                target: parseFloat(e.target.value) || 3.0,
              })
            }
            className="w-full px-4 py-3 bg-white border-2 border-green-300 text-gray-800 rounded-lg text-lg font-bold focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all"
          />
          <p className="text-xs text-green-700 mt-1">
            Desired leverage (1-10x)
          </p>
        </div>

        {/* Risk Factor Input */}
        <div className="border-2 border-orange-200 rounded-lg p-3 bg-orange-50">
          <label className="block text-sm text-orange-900 font-bold mb-2">
            ⚠️ Risk Factor
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={institution.risk}
            onChange={(e) =>
              onUpdate(institution.id, { risk: parseFloat(e.target.value) })
            }
            className="w-full h-3 bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-lg appearance-none cursor-pointer"
            style={{
              WebkitAppearance: 'none',
            }}
          />
          <div className="flex justify-between text-xs text-orange-700 font-bold mt-2">
            <span>Conservative</span>
            <span className="text-lg px-3 py-1 bg-white rounded-lg border-2 border-orange-300">
              {(institution.risk * 100).toFixed(0)}%
            </span>
            <span>Aggressive</span>
          </div>
          <p className="text-xs text-orange-700 mt-1">
            Risk tolerance level
          </p>
        </div>

        {/* Info Display */}
        <div className="border-t border-gray-300 pt-4">
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <p className="text-xs text-gray-600">Type</p>
              <p className="text-sm font-bold text-gray-800">
                {institution.type === "bank" && "🏛️ Bank"}
                {institution.type === "exchange" && "📈 Exchange"}
                {institution.type === "clearinghouse" && "⚖️ Clearing"}
              </p>
            </div>
            <div className="p-2 bg-gray-100 rounded-lg">
              <p className="text-xs text-gray-600">Connections</p>
              <p className="text-sm font-bold text-gray-800">
                {connections.length} links
              </p>
            </div>
          </div>
          
          {connections.length > 0 && (
            <div>
              <h4 className="text-sm font-bold text-gray-800 mb-2">
                Active Connections
              </h4>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {connections.map((conn) => (
                  <div
                    key={conn.id}
                    className="p-2 bg-gray-100 border border-gray-300 rounded-lg text-xs"
                  >
                    <div className="flex justify-between">
                      <span className="font-semibold text-gray-800">
                        {conn.type === "credit" && "💰"}
                        {conn.type === "settlement" && "🔄"}
                        {conn.type === "margin" && "📋"} {conn.type}
                      </span>
                      <span className="text-gray-600">${conn.exposure}M</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstitutionPanel;

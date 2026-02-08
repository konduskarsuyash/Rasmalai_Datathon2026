// components/InstitutionPanel.jsx
const InstitutionPanel = ({ institution, onUpdate, onRemove, connections }) => {
  // Check if it's a market node
  const isMarket = institution.type === 'market' || institution.isMarket;

  if (isMarket) {
    // Market node display
    return (
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Market Details
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
              Market Name
            </label>
            <input
              type="text"
              value={institution.name}
              onChange={(e) => onUpdate(institution.id, { name: e.target.value })}
              className="w-full px-3 py-2 bg-white border-2 border-purple-300 text-purple-900 rounded-lg text-sm font-bold focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
            />
          </div>

          <div className="p-4 bg-purple-50 border-2 border-purple-300 rounded-lg">
            <p className="text-sm text-purple-900 font-bold mb-2">📊 Market Node</p>
            <p className="text-xs text-purple-700">
              This is a market/investment destination. Banks can invest in or divest from this market during simulation.
            </p>
            <p className="text-xs text-purple-700 mt-2">
              <span className="font-bold">ID:</span> {institution.id}
            </p>
          </div>

          {connections.length > 0 && (
            <div className="border-t border-gray-300 pt-4">
              <h4 className="text-sm font-bold text-gray-800 mb-2">
                Active Investments ({connections.length})
              </h4>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {connections.map((conn) => (
                  <div
                    key={conn.id}
                    className="p-2 bg-purple-50 border border-purple-300 rounded-lg text-xs"
                  >
                    <div className="flex justify-between">
                      <span className="font-semibold text-purple-800">
                        Investment
                      </span>
                      <span className="text-purple-600">${conn.exposure}M</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Regular bank node panel
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

        <div className="border-2 border-blue-200 rounded-lg p-3 bg-blue-50">
          <label className="block text-sm text-blue-900 font-bold mb-2">
            💰 Capital (Million $)
          </label>
          <input
            type="number"
            min="10"
            max="1000"
            value={institution.capital}
            onChange={(e) => {
              const newValue = parseFloat(e.target.value) || 100;
              console.log('[InstitutionPanel] Updating capital:', institution.id, 'from', institution.capital, 'to', newValue);
              onUpdate(institution.id, { capital: newValue });
            }}
            className="w-full px-4 py-3 bg-white border-2 border-blue-300 text-gray-800 rounded-lg text-lg font-bold focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          />
          <p className="text-xs text-blue-700 mt-1">
            Initial capital reserves
          </p>
        </div>

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
            onChange={(e) => {
              const newValue = parseFloat(e.target.value) || 3.0;
              console.log('[InstitutionPanel] Updating target leverage:', institution.id, 'from', institution.target, 'to', newValue);
              onUpdate(institution.id, { target: newValue });
            }}
            className="w-full px-4 py-3 bg-white border-2 border-green-300 text-gray-800 rounded-lg text-lg font-bold focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition-all"
          />
          <p className="text-xs text-green-700 mt-1">
            Desired leverage (1-10x)
          </p>
        </div>

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
            onChange={(e) => {
              const newValue = parseFloat(e.target.value);
              console.log('[InstitutionPanel] Updating risk:', institution.id, 'from', institution.risk, 'to', newValue);
              onUpdate(institution.id, { risk: newValue });
            }}
            className="w-full h-3 bg-gradient-to-r from-green-400 via-yellow-400 to-red-500 rounded-lg appearance-none cursor-pointer"
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

        {/* Interbank Transaction Parameters */}
        <div className="border-2 border-purple-200 rounded-lg p-3 bg-purple-50">
          <h4 className="text-sm text-purple-900 font-bold mb-3">
            🏦 Interbank Lending Parameters
          </h4>
          
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-purple-800 font-medium mb-1">
                Interbank Rate (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={institution.interbankRate || 2.5}
                onChange={(e) => {
                  const val = e.target.value === '' ? 2.5 : parseFloat(e.target.value);
                  onUpdate(institution.id, { interbankRate: val });
                }}
                className="w-full px-3 py-2 bg-white border-2 border-purple-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
              />
              <p className="text-xs text-purple-700 mt-1">LIBOR + Spread</p>
            </div>

            <div>
              <label className="block text-xs text-purple-800 font-medium mb-1">
                Collateral Haircut (%)
              </label>
              <input
                type="number"
                step="1"
                value={institution.haircut || 15}
                onChange={(e) => {
                  const val = e.target.value === '' ? 15 : parseFloat(e.target.value);
                  onUpdate(institution.id, { haircut: val });
                }}
                className="w-full px-3 py-2 bg-white border-2 border-purple-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
              />
              <p className="text-xs text-purple-700 mt-1">Margin on secured lending</p>
            </div>

            <div>
              <label className="block text-xs text-purple-800 font-medium mb-1">
                Reserve Requirement (%)
              </label>
              <input
                type="number"
                step="1"
                value={institution.reserveRatio || 10}
                onChange={(e) => {
                  const val = e.target.value === '' ? 10 : parseFloat(e.target.value);
                  onUpdate(institution.id, { reserveRatio: val });
                }}
                className="w-full px-3 py-2 bg-white border-2 border-purple-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
              />
              <p className="text-xs text-purple-700 mt-1">Central bank mandate</p>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-300 pt-4">
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <p className="text-xs text-gray-600">Type</p>
              <p className="text-sm font-bold text-gray-800">
                {institution.type === "bank" && "🏛️ Bank"}
                {institution.type === "exchange" && "📈 Exchange"}
                {institution.type === "clearinghouse" && "⚖️ Clearing"}
              </p>
            </div>
            <div className="p-2 bg-gray-100 rounded-lg">
              <p className="text-xs text-gray-600">Capital</p>
              <p className="text-sm font-bold text-green-600">
                ${institution.capital}M
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

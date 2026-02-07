// components/InstitutionPanel.jsx
const InstitutionPanel = ({ institution, onUpdate, onRemove, connections }) => {
  const strategyOptions = ['conservative', 'balanced', 'aggressive'];

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-blue-400">Institution Details</h3>
        <button
          onClick={() => onRemove(institution.id)}
          className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-medium transition-colors"
        >
          Remove
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Name</label>
          <input
            type="text"
            value={institution.name}
            onChange={(e) => onUpdate(institution.id, { name: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Type</label>
          <div className="px-3 py-2 bg-gray-700 rounded-lg text-sm">
            {institution.type === 'bank' && '🏦 Bank'}
            {institution.type === 'exchange' && '📊 Exchange'}
            {institution.type === 'clearinghouse' && '⚖️ Clearing House'}
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Capital (Million $)</label>
          <input
            type="number"
            value={institution.capital}
            onChange={(e) => onUpdate(institution.id, { capital: parseFloat(e.target.value) || 0 })}
            className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Liquidity (Million $)</label>
          <input
            type="number"
            value={institution.liquidity}
            onChange={(e) => onUpdate(institution.id, { liquidity: parseFloat(e.target.value) || 0 })}
            className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Risk Level</label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={institution.risk}
            onChange={(e) => onUpdate(institution.id, { risk: parseFloat(e.target.value) })}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>Low</span>
            <span className="font-bold">{(institution.risk * 100).toFixed(0)}%</span>
            <span>High</span>
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-400 mb-1">Strategy</label>
          <select
            value={institution.strategy}
            onChange={(e) => onUpdate(institution.id, { strategy: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            {strategyOptions.map(strategy => (
              <option key={strategy} value={strategy}>
                {strategy.charAt(0).toUpperCase() + strategy.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="border-t border-gray-700 pt-4">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Connections ({connections.length})</h4>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {connections.map(conn => (
              <div key={conn.id} className="p-2 bg-gray-700 rounded text-xs">
                <div className="flex justify-between">
                  <span className="font-semibold">
                    {conn.type === 'credit' && '💰'}
                    {conn.type === 'settlement' && '🔄'}
                    {conn.type === 'margin' && '📋'}
                    {' '}{conn.type}
                  </span>
                  <span className="text-gray-400">${conn.exposure}M</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InstitutionPanel;
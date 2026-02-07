// components/ControlPanel.jsx
import { useState } from 'react';

const ControlPanel = ({ parameters, onParametersChange, onAddInstitution, onAddConnection, institutions }) => {
  const [showAddConnection, setShowAddConnection] = useState(false);
  const [newConnection, setNewConnection] = useState({
    source: '',
    target: '',
    type: 'credit',
    exposure: 100
  });

  const handleAddConnection = () => {
    if (newConnection.source && newConnection.target && newConnection.source !== newConnection.target) {
      onAddConnection(
        newConnection.source,
        newConnection.target,
        newConnection.type,
        parseFloat(newConnection.exposure)
      );
      setNewConnection({ source: '', target: '', type: 'credit', exposure: 100 });
      setShowAddConnection(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-blue-400 mb-3">Add Institutions</h3>
        <div className="space-y-2">
          <button
            onClick={() => onAddInstitution('bank')}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Bank 🏦
          </button>
          <button
            onClick={() => onAddInstitution('exchange')}
            className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Exchange 📊
          </button>
          <button
            onClick={() => onAddInstitution('clearinghouse')}
            className="w-full px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg text-sm font-medium transition-colors"
          >
            + Add Clearing House ⚖️
          </button>
        </div>
      </div>

      <div className="border-t border-gray-700 pt-4">
        <h3 className="text-lg font-semibold text-blue-400 mb-3">Add Connection</h3>
        {!showAddConnection ? (
          <button
            onClick={() => setShowAddConnection(true)}
            className="w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
          >
            + Create Connection
          </button>
        ) : (
          <div className="space-y-3">
            <select
              value={newConnection.source}
              onChange={(e) => setNewConnection(prev => ({ ...prev, source: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="">Select Source</option>
              {institutions.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>

            <select
              value={newConnection.target}
              onChange={(e) => setNewConnection(prev => ({ ...prev, target: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="">Select Target</option>
              {institutions.map(inst => (
                <option key={inst.id} value={inst.id}>{inst.name}</option>
              ))}
            </select>

            <select
              value={newConnection.type}
              onChange={(e) => setNewConnection(prev => ({ ...prev, type: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="credit">Credit Exposure</option>
              <option value="settlement">Settlement Obligation</option>
              <option value="margin">Margin Requirement</option>
            </select>

            <input
              type="number"
              value={newConnection.exposure}
              onChange={(e) => setNewConnection(prev => ({ ...prev, exposure: e.target.value }))}
              placeholder="Exposure Amount (M)"
              className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />

            <div className="flex space-x-2">
              <button
                onClick={handleAddConnection}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddConnection(false)}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-sm font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-700 pt-4">
        <h3 className="text-lg font-semibold text-blue-400 mb-3">Simulation Parameters</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Shock Magnitude</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={parameters.shockMagnitude}
              onChange={(e) => onParametersChange({ ...parameters, shockMagnitude: parseFloat(e.target.value) })}
              className="w-full"
            />
            <span className="text-xs text-gray-400">{(parameters.shockMagnitude * 100).toFixed(0)}%</span>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Shock Type</label>
            <select
              value={parameters.shockType}
              onChange={(e) => onParametersChange({ ...parameters, shockType: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="liquidity">Liquidity Shock</option>
              <option value="capital">Capital Shock</option>
              <option value="operational">Operational Shock</option>
              <option value="market">Market Shock</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Contagion Threshold</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={parameters.contagionThreshold}
              onChange={(e) => onParametersChange({ ...parameters, contagionThreshold: parseFloat(e.target.value) })}
              className="w-full"
            />
            <span className="text-xs text-gray-400">{(parameters.contagionThreshold * 100).toFixed(0)}%</span>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Information Asymmetry</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={parameters.informationAsymmetry}
              onChange={(e) => onParametersChange({ ...parameters, informationAsymmetry: parseFloat(e.target.value) })}
              className="w-full"
            />
            <span className="text-xs text-gray-400">{(parameters.informationAsymmetry * 100).toFixed(0)}%</span>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Recovery Rate</label>
            <input
              type="range"
              min="0"
              max="0.5"
              step="0.05"
              value={parameters.recoveryRate}
              onChange={(e) => onParametersChange({ ...parameters, recoveryRate: parseFloat(e.target.value) })}
              className="w-full"
            />
            <span className="text-xs text-gray-400">{(parameters.recoveryRate * 100).toFixed(0)}%</span>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm text-gray-400">Regulatory Intervention</label>
            <button
              onClick={() => onParametersChange({ ...parameters, regulatoryIntervention: !parameters.regulatoryIntervention })}
              className={`px-4 py-1 rounded-lg text-sm font-medium transition-colors ${
                parameters.regulatoryIntervention
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-600 hover:bg-gray-500'
              }`}
            >
              {parameters.regulatoryIntervention ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
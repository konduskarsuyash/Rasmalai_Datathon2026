// components/ControlPanel.jsx
import { useState } from "react";

const ControlPanel = ({
  parameters,
  onParametersChange,
  onAddInstitution,
  onAddConnection,
  institutions,
}) => {
  const [showAddConnection, setShowAddConnection] = useState(false);
  const [newConnection, setNewConnection] = useState({
    source: "",
    target: "",
    type: "credit",
    exposure: 100,
  });

  const handleAddConnection = () => {
    if (
      newConnection.source &&
      newConnection.target &&
      newConnection.source !== newConnection.target
    ) {
      onAddConnection(
        newConnection.source,
        newConnection.target,
        newConnection.type,
        parseFloat(newConnection.exposure),
      );
      setNewConnection({
        source: "",
        target: "",
        type: "credit",
        exposure: 100,
      });
      setShowAddConnection(false);
    }
  };

  return (
    <div className="p-4 space-y-6">
      <div>
        <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
          Add Institutions
        </h3>
        <div className="space-y-2">
          <button
            onClick={() => onAddInstitution("bank")}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg"
          >
            + Add Bank 🏛️
          </button>
          <button
            onClick={() => onAddInstitution("exchange")}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg"
          >
            + Add Exchange 📈
          </button>
          <button
            onClick={() => onAddInstitution("clearinghouse")}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg"
          >
            + Add Clearing House ⚖️
          </button>
        </div>
      </div>

      <div className="border-t border-gray-300 pt-4">
        <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
          Add Connection
        </h3>
        {!showAddConnection ?
          <button
            onClick={() => setShowAddConnection(true)}
            className="w-full px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-sm font-medium transition-all duration-200 border border-gray-300 hover:border-gray-400"
          >
            + Create Connection
          </button>
        : <div className="space-y-3">
            <select
              value={newConnection.source}
              onChange={(e) =>
                setNewConnection((prev) => ({
                  ...prev,
                  source: e.target.value,
                }))
              }
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              <option value="">Select Source</option>
              {institutions.map((inst) => (
                <option key={inst.id} value={inst.id}>
                  {inst.name}
                </option>
              ))}
            </select>

            <select
              value={newConnection.target}
              onChange={(e) =>
                setNewConnection((prev) => ({
                  ...prev,
                  target: e.target.value,
                }))
              }
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              <option value="">Select Target</option>
              {institutions.map((inst) => (
                <option key={inst.id} value={inst.id}>
                  {inst.name}
                </option>
              ))}
            </select>

            <select
              value={newConnection.type}
              onChange={(e) =>
                setNewConnection((prev) => ({ ...prev, type: e.target.value }))
              }
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              <option value="credit">Credit Exposure</option>
              <option value="settlement">Settlement Obligation</option>
              <option value="margin">Margin Requirement</option>
            </select>

            <input
              type="number"
              value={newConnection.exposure}
              onChange={(e) =>
                setNewConnection((prev) => ({
                  ...prev,
                  exposure: e.target.value,
                }))
              }
              placeholder="Exposure Amount (M)"
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            />

            <div className="flex space-x-2">
              <button
                onClick={handleAddConnection}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md"
              >
                Add
              </button>
              <button
                onClick={() => setShowAddConnection(false)}
                className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-medium transition-all duration-200 border border-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        }
      </div>

      <div className="border-t border-gray-300 pt-4">
        <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
          Simulation Parameters
        </h3>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">
              Shock Magnitude
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={parameters.shockMagnitude}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  shockMagnitude: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <span className="text-xs text-gray-600 font-medium">
              {(parameters.shockMagnitude * 100).toFixed(0)}%
            </span>
          </div>

          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">
              Shock Type
            </label>
            <select
              value={parameters.shockType}
              onChange={(e) =>
                onParametersChange({ ...parameters, shockType: e.target.value })
              }
              className="w-full px-3 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              <option value="liquidity">Liquidity Shock</option>
              <option value="capital">Capital Shock</option>
              <option value="operational">Operational Shock</option>
              <option value="market">Market Shock</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">
              Contagion Threshold
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={parameters.contagionThreshold}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  contagionThreshold: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <span className="text-xs text-gray-600 font-medium">
              {(parameters.contagionThreshold * 100).toFixed(0)}%
            </span>
          </div>

          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">
              Information Asymmetry
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={parameters.informationAsymmetry}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  informationAsymmetry: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <span className="text-xs text-gray-600 font-medium">
              {(parameters.informationAsymmetry * 100).toFixed(0)}%
            </span>
          </div>

          <div>
            <label className="block text-xs text-gray-600 font-medium mb-1">
              Recovery Rate
            </label>
            <input
              type="range"
              min="0"
              max="0.5"
              step="0.05"
              value={parameters.recoveryRate}
              onChange={(e) =>
                onParametersChange({
                  ...parameters,
                  recoveryRate: parseFloat(e.target.value),
                })
              }
              className="w-full"
            />
            <span className="text-xs text-gray-600 font-medium">
              {(parameters.recoveryRate * 100).toFixed(0)}%
            </span>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm text-gray-700 font-medium">
              Regulatory Intervention
            </label>
            <button
              onClick={() =>
                onParametersChange({
                  ...parameters,
                  regulatoryIntervention: !parameters.regulatoryIntervention,
                })
              }
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 shadow-md ${
                parameters.regulatoryIntervention ?
                  "bg-gradient-to-r from-green-500 to-green-600 hover:from-green-400 hover:to-green-500 text-white"
                : "bg-gray-200 hover:bg-gray-300 text-gray-800 border border-gray-300"
              }`}
            >
              {parameters.regulatoryIntervention ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

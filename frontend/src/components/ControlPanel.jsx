// components/ControlPanel.jsx
const ControlPanel = ({
  onAddInstitution,
  institutions,
  onClearAll,
}) => {
  const bankCount = institutions.filter(i => i.type === 'bank' && !i.isMarket).length;

  return (
    <div className="p-4 space-y-4">
      <div>
        <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
          Network Setup
        </h3>
        <div className="space-y-2">
          <button
            onClick={() => onAddInstitution("bank")}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md hover:shadow-lg"
          >
            + Add Bank 🏛️
          </button>
          
          {bankCount === 0 && (
            <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-xs text-yellow-800 font-medium">
                👋 <span className="font-bold">Start by adding your first bank!</span>
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                Click the button above to create your financial network.
              </p>
            </div>
          )}
          
          {bankCount > 0 && (
            <div className="p-2 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-800">
                <span className="font-bold">{bankCount} banks</span> in network
              </p>
            </div>
          )}
          
          {bankCount > 0 && (
            <button
              onClick={onClearAll}
              className="w-full px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-md"
            >
              Clear All Banks
            </button>
          )}
        </div>
      </div>

      <div className="border-t border-gray-300 pt-4">
        <div className="p-3 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200">
          <p className="text-xs text-gray-700 mb-2 font-bold">
            🚀 Quick Start Guide:
          </p>
          <ol className="text-xs text-gray-600 space-y-1.5 list-decimal list-inside">
            <li>Click <span className="font-bold text-blue-600">"+ Add Bank"</span> to create 3-5 banks</li>
            <li>Click each bank node on canvas to configure parameters</li>
            <li>Set Tier 1 Capital, Leverage, Risk & Interbank rates</li>
            <li>Hold <kbd className="px-1 py-0.5 bg-gray-200 rounded text-xs font-mono">Ctrl</kbd> + drag to connect banks</li>
            <li>Run <span className="font-bold text-green-600">"Backend Simulation"</span> below to watch live transactions!</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

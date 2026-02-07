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
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-xs text-gray-600 mb-2">
            <span className="font-bold">Quick Start:</span>
          </p>
          <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
            <li>Add 3-5 banks</li>
            <li>Click each to set Capital, Target, Risk</li>
            <li>Run Real-Time Simulation below</li>
            <li>Watch transactions flow live!</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

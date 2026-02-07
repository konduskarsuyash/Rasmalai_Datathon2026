// components/ScenarioPanel.jsx
const ScenarioPanel = ({ onApplyScenario }) => {
  const scenarios = [
    {
      id: 'financial_crisis',
      name: 'Financial Crisis',
      description: 'Simulates a severe market crash with liquidity freeze',
      icon: '💥',
      severity: 'high'
    },
    {
      id: 'credit_crunch',
      name: 'Credit Crunch',
      description: 'Reduces credit availability across the network',
      icon: '📉',
      severity: 'medium'
    },
    {
      id: 'regulatory_stress',
      name: 'Regulatory Stress Test',
      description: 'Tests system resilience under stricter regulations',
      icon: '⚖️',
      severity: 'low'
    },
    {
      id: 'network_failure',
      name: 'Institution Failure',
      description: 'Random institution experiences critical failure',
      icon: '🏚️',
      severity: 'high'
    }
  ];

  return (
    <div className="p-4 border-t border-gray-700">
      <h3 className="text-lg font-semibold text-blue-400 mb-3">Stress Scenarios</h3>
      <div className="space-y-2">
        {scenarios.map(scenario => (
          <button
            key={scenario.id}
            onClick={() => onApplyScenario(scenario.id)}
            className={`w-full p-3 rounded-lg text-left transition-colors ${
              scenario.severity === 'high' 
                ? 'bg-red-900/30 hover:bg-red-900/50 border border-red-700' 
                : scenario.severity === 'medium'
                ? 'bg-yellow-900/30 hover:bg-yellow-900/50 border border-yellow-700'
                : 'bg-blue-900/30 hover:bg-blue-900/50 border border-blue-700'
            }`}
          >
            <div className="flex items-start">
              <span className="text-2xl mr-3">{scenario.icon}</span>
              <div>
                <div className="font-semibold text-sm">{scenario.name}</div>
                <div className="text-xs text-gray-400 mt-1">{scenario.description}</div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ScenarioPanel;
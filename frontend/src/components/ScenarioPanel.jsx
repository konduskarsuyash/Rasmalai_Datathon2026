// components/ScenarioPanel.jsx
const ScenarioPanel = ({ onApplyScenario }) => {
  const scenarios = [
    {
      id: "financial_crisis",
      name: "Financial Crisis",
      description: "Simulates a severe market crash with liquidity freeze",
      icon: "💥",
      severity: "high",
    },
    {
      id: "credit_crunch",
      name: "Credit Crunch",
      description: "Reduces credit availability across the network",
      icon: "📉",
      severity: "medium",
    },
    {
      id: "regulatory_stress",
      name: "Regulatory Stress Test",
      description: "Tests system resilience under stricter regulations",
      icon: "⚖️",
      severity: "low",
    },
    {
      id: "network_failure",
      name: "Institution Failure",
      description: "Random institution experiences critical failure",
      icon: "🏚️",
      severity: "high",
    },
  ];

  return (
    <div className="p-4 border-t border-gray-300">
      <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3">
        Stress Scenarios
      </h3>
      <div className="space-y-2">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            onClick={() => onApplyScenario(scenario.id)}
            className={`w-full p-3 rounded-xl text-left transition-all duration-200 shadow-md hover:shadow-lg ${
              scenario.severity === "high" ?
                "bg-red-50 hover:bg-red-100 border border-red-300 hover:border-red-400 text-gray-900"
              : scenario.severity === "medium" ?
                "bg-yellow-50 hover:bg-yellow-100 border border-yellow-300 hover:border-yellow-400 text-gray-900"
              : "bg-blue-50 hover:bg-blue-100 border border-blue-300 hover:border-blue-400 text-gray-900"
            }`}
          >
            <div className="flex items-start">
              <span className="text-2xl mr-3">{scenario.icon}</span>
              <div>
                <div className="font-semibold text-sm">{scenario.name}</div>
                <div className="text-xs text-gray-600 mt-1">
                  {scenario.description}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ScenarioPanel;

// components/MetricsPanel.jsx
const MetricsPanel = ({ metrics }) => {
  const metricConfig = [
    {
      key: "systemicRisk",
      label: "Systemic Risk",
      color: "red",
      inverse: true,
    },
    {
      key: "liquidityFlow",
      label: "Liquidity Flow",
      color: "blue",
      inverse: false,
    },
    {
      key: "networkCongestion",
      label: "Network Congestion",
      color: "yellow",
      inverse: true,
    },
    {
      key: "stabilityIndex",
      label: "Stability Index",
      color: "green",
      inverse: false,
    },
    { key: "cascadeRisk", label: "Cascade Risk", color: "red", inverse: true },
    {
      key: "interconnectedness",
      label: "Interconnectedness",
      color: "purple",
      inverse: false,
    },
  ];

  const getColorClass = (value, color, inverse) => {
    const level = inverse ? 1 - value : value;
    if (level > 0.7)
      return color === "green" || !inverse ? "text-green-400" : "text-red-400";
    if (level > 0.4) return "text-yellow-400";
    return "text-red-400";
  };

  const getBarColor = (color) => {
    const colors = {
      red: "bg-red-500",
      blue: "bg-blue-500",
      yellow: "bg-yellow-500",
      green: "bg-green-500",
      purple: "bg-purple-500",
    };
    return colors[color] || "bg-gray-500";
  };

  return (
    <div className="p-4 border-b border-gray-300">
      <h3 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
        System Metrics
      </h3>
      <div className="space-y-4">
        {metricConfig.map((metric) => (
          <div key={metric.key}>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-700 font-medium">
                {metric.label}
              </span>
              <span
                className={`text-sm font-bold ${getColorClass(metrics[metric.key], metric.color, metric.inverse)}`}
              >
                {(metrics[metric.key] * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5 border border-gray-300">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${getBarColor(metric.color)} shadow-md`}
                style={{ width: `${metrics[metric.key] * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MetricsPanel;

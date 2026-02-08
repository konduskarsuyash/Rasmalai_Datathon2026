import React from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * HistoricalTrendsChart - Shows risk and stability metrics over time
 */
const HistoricalTrendsChart = ({ historicalData, selectedBanks = [], showSystemMetrics = true }) => {
  if (!historicalData || historicalData.length === 0) {
    return (
      <div className="bg-white border-2 border-gray-300 rounded-xl p-6 text-center">
        <div className="text-4xl mb-2">📈</div>
        <h3 className="text-lg font-bold text-gray-800 mb-2">No Historical Data</h3>
        <p className="text-sm text-gray-600">Start a simulation to see risk trends over time</p>
      </div>
    );
  }

  // Process system-level metrics
  const systemData = historicalData.map((step, idx) => {
    const bankStates = step.bank_states || [];
    const totalBanks = bankStates.length;
    const defaultedBanks = bankStates.filter(b => b.is_defaulted).length;
    const avgLeverage = bankStates.reduce((sum, b) => sum + (b.leverage || 0), 0) / (totalBanks || 1);
    const avgCapitalRatio = bankStates.reduce((sum, b) => sum + (b.capital_ratio || 0), 0) / (totalBanks || 1);
    const totalEquity = bankStates.reduce((sum, b) => sum + (b.equity || 0), 0);

    return {
      step: idx,
      defaultRate: (defaultedBanks / totalBanks) * 100,
      avgLeverage: avgLeverage,
      avgCapitalRatio: avgCapitalRatio * 100,
      totalEquity: totalEquity,
      stabilityIndex: ((totalBanks - defaultedBanks) / totalBanks) * 100,
    };
  });

  // Process individual bank metrics
  const bankDataMap = {};
  selectedBanks.forEach(bankId => {
    bankDataMap[bankId] = historicalData.map((step, idx) => {
      const bankState = (step.bank_states || []).find(b => b.bank_id === bankId);
      if (!bankState) return { step: idx, leverage: 0, capitalRatio: 0, equity: 0 };
      
      return {
        step: idx,
        leverage: bankState.leverage || 0,
        capitalRatio: (bankState.capital_ratio || 0) * 100,
        equity: bankState.equity || 0,
        isDefaulted: bankState.is_defaulted,
      };
    });
  });

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-4">
      {/* System Stability Chart */}
      {showSystemMetrics && (
        <div className="bg-white border-2 border-blue-300 rounded-xl p-4">
          <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🌐</span>
            <span>System Stability Over Time</span>
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={systemData}>
              <defs>
                <linearGradient id="colorStability" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                </linearGradient>
                <linearGradient id="colorDefault" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="step" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} domain={[0, 100]} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255,255,255,0.95)', 
                  border: '2px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value) => `${value.toFixed(1)}%`}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Area 
                type="monotone" 
                dataKey="stabilityIndex" 
                stroke="#10b981" 
                fill="url(#colorStability)"
                name="Stability Index"
              />
              <Area 
                type="monotone" 
                dataKey="defaultRate" 
                stroke="#ef4444" 
                fill="url(#colorDefault)"
                name="Default Rate"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Average Leverage Chart */}
      {showSystemMetrics && (
        <div className="bg-white border-2 border-orange-300 rounded-xl p-4">
          <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>⚖️</span>
            <span>Average System Leverage</span>
          </h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={systemData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="step" stroke="#6b7280" fontSize={11} />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255,255,255,0.95)', 
                  border: '2px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value) => `${value.toFixed(2)}x`}
              />
              <Line 
                type="monotone" 
                dataKey="avgLeverage" 
                stroke="#f97316" 
                strokeWidth={2}
                dot={{ fill: '#f97316', r: 3 }}
                name="Avg Leverage"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Individual Bank Comparison */}
      {selectedBanks.length > 0 && (
        <div className="bg-white border-2 border-purple-300 rounded-xl p-4">
          <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>🏦</span>
            <span>Bank Leverage Comparison</span>
            <span className="text-xs text-gray-500 font-normal">({selectedBanks.length} banks)</span>
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="step" 
                type="number" 
                domain={[0, historicalData.length - 1]}
                stroke="#6b7280" 
                fontSize={11} 
              />
              <YAxis stroke="#6b7280" fontSize={11} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255,255,255,0.95)', 
                  border: '2px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value, name) => [`${value.toFixed(2)}x`, name]}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {selectedBanks.map((bankId, idx) => (
                <Line
                  key={bankId}
                  data={bankDataMap[bankId]}
                  type="monotone"
                  dataKey="leverage"
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`Bank ${bankId}`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Capital Ratio Comparison */}
      {selectedBanks.length > 0 && (
        <div className="bg-white border-2 border-green-300 rounded-xl p-4">
          <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
            <span>💰</span>
            <span>Capital Ratio Comparison</span>
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="step" 
                type="number" 
                domain={[0, historicalData.length - 1]}
                stroke="#6b7280" 
                fontSize={11} 
              />
              <YAxis stroke="#6b7280" fontSize={11} domain={[0, 20]} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255,255,255,0.95)', 
                  border: '2px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value, name) => [`${value.toFixed(2)}%`, name]}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              {selectedBanks.map((bankId, idx) => (
                <Line
                  key={bankId}
                  data={bankDataMap[bankId]}
                  type="monotone"
                  dataKey="capitalRatio"
                  stroke={colors[idx % colors.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`Bank ${bankId}`}
                />
              ))}
              {/* Regulatory minimum line */}
              <Line 
                data={[
                  { step: 0, min: 8 },
                  { step: historicalData.length - 1, min: 8 }
                ]}
                dataKey="min"
                stroke="#ef4444"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                name="8% Minimum"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default HistoricalTrendsChart;

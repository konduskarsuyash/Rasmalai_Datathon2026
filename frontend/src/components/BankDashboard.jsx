// components/BankDashboard.jsx
import { useEffect, useRef } from 'react';

const BankDashboard = ({ bank, historicalData, transactions, onClose }) => {
  const canvasRef = useRef(null);
  
  // Filter transactions for this specific bank
  // Handle both string IDs (like "bank1") and numeric IDs (like 0)
  const bankNumericId = typeof bank.id === 'string' 
    ? parseInt(bank.id.replace('bank', '')) - 1 
    : bank.id;
    
  const bankTransactions = transactions.filter(
    tx => tx.from_bank === bankNumericId || tx.to_bank === bankNumericId
  );
  
  // Get historical capital data for this bank
  const capitalHistory = historicalData
    .map((step, index) => {
      const bankState = step.bank_states?.find(b => b.bank_id === bankNumericId);
      return {
        step: index,
        capital: bankState?.capital || 0,
        cash: bankState?.cash || 0,
        investments: bankState?.investments || 0,
        loans_given: bankState?.loans_given || 0,
        borrowed: bankState?.borrowed || 0,
        leverage: bankState?.leverage || 0,
      };
    })
    .filter(d => d.capital !== undefined);
  
  // Draw capital chart
  useEffect(() => {
    if (!canvasRef.current || capitalHistory.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#f9fafb';
    ctx.fillRect(0, 0, width, height);
    
    // Calculate scales
    const maxCapital = Math.max(...capitalHistory.map(d => d.capital), 1);
    const minCapital = Math.min(...capitalHistory.map(d => d.capital), 0);
    const capitalRange = maxCapital - minCapital || 1;
    
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    
    const xScale = chartWidth / Math.max(capitalHistory.length - 1, 1);
    const yScale = chartHeight / capitalRange;
    
    // Draw grid lines
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight * i) / 5;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
      
      // Y-axis labels
      const value = maxCapital - (capitalRange * i) / 5;
      ctx.fillStyle = '#6b7280';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`$${value.toFixed(0)}M`, padding - 5, y + 3);
    }
    
    // Draw capital line
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    capitalHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const y = padding + chartHeight - (point.capital - minCapital) * yScale;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw points
    capitalHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const y = padding + chartHeight - (point.capital - minCapital) * yScale;
      
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
    
    // Draw X-axis labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'center';
    const labelInterval = Math.ceil(capitalHistory.length / 10);
    capitalHistory.forEach((point, i) => {
      if (i % labelInterval === 0 || i === capitalHistory.length - 1) {
        const x = padding + i * xScale;
        ctx.fillText(`T${point.step}`, x, height - padding + 15);
      }
    });
    
    // Chart title
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 14px system-ui';
    ctx.textAlign = 'left';
    ctx.fillText('Capital Over Time', padding, 25);
    
  }, [capitalHistory]);
  
  // Calculate lending/borrowing stats
  const lentAmount = bankTransactions
    .filter(tx => tx.from_bank === bankNumericId && tx.action === 'INCREASE_LENDING')
    .reduce((sum, tx) => sum + tx.amount, 0);
  
  const borrowedAmount = bankTransactions
    .filter(tx => tx.to_bank === bankNumericId && tx.action === 'INCREASE_LENDING')
    .reduce((sum, tx) => sum + tx.amount, 0);
  
  const investedAmount = bankTransactions
    .filter(tx => tx.from_bank === bankNumericId && tx.action === 'INVEST_MARKET')
    .reduce((sum, tx) => sum + tx.amount, 0);
  
  const currentState = capitalHistory[capitalHistory.length - 1] || {};
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{bank.name} Dashboard</h2>
            <p className="text-blue-100 text-sm mt-1">Real-time Performance Analytics</p>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-all"
          >
            ✕ Close
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <p className="text-xs text-blue-600 font-semibold mb-1">💰 Current Capital</p>
              <p className="text-2xl font-bold text-blue-900">${currentState.capital?.toFixed(1) || 0}M</p>
            </div>
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
              <p className="text-xs text-green-600 font-semibold mb-1">💵 Cash Reserves</p>
              <p className="text-2xl font-bold text-green-900">${currentState.cash?.toFixed(1) || 0}M</p>
            </div>
            <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
              <p className="text-xs text-purple-600 font-semibold mb-1">📊 Investments</p>
              <p className="text-2xl font-bold text-purple-900">${currentState.investments?.toFixed(1) || 0}M</p>
            </div>
            <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
              <p className="text-xs text-orange-600 font-semibold mb-1">⚖️ Leverage</p>
              <p className="text-2xl font-bold text-orange-900">{currentState.leverage?.toFixed(2) || 0}x</p>
            </div>
          </div>
          
          {/* Capital Chart */}
          <div className="bg-white border-2 border-gray-200 rounded-xl p-4">
            <canvas
              ref={canvasRef}
              width={800}
              height={300}
              className="w-full"
            />
          </div>
          
          {/* Transaction Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded-lg p-4">
              <p className="text-sm text-green-700 font-bold mb-2">🏦 Total Lent</p>
              <p className="text-3xl font-bold text-green-900">${lentAmount.toFixed(1)}M</p>
              <p className="text-xs text-green-600 mt-1">{bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'INCREASE_LENDING').length} transactions</p>
            </div>
            <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 rounded-lg p-4">
              <p className="text-sm text-red-700 font-bold mb-2">💸 Total Borrowed</p>
              <p className="text-3xl font-bold text-red-900">${borrowedAmount.toFixed(1)}M</p>
              <p className="text-xs text-red-600 mt-1">{bankTransactions.filter(tx => tx.to_bank === bankNumericId && tx.action === 'INCREASE_LENDING').length} transactions</p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-300 rounded-lg p-4">
              <p className="text-sm text-purple-700 font-bold mb-2">📈 Market Investments</p>
              <p className="text-3xl font-bold text-purple-900">${investedAmount.toFixed(1)}M</p>
              <p className="text-xs text-purple-600 mt-1">{bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'INVEST_MARKET').length} transactions</p>
            </div>
          </div>
          
          {/* Recent Transactions Log */}
          <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-4">
            <h3 className="text-lg font-bold text-gray-800 mb-3">📋 Transaction Log</h3>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {bankTransactions.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-4">No transactions yet</p>
              ) : (
                bankTransactions.slice(-20).reverse().map((tx, idx) => {
                  const isOutgoing = tx.from_bank === bankNumericId;
                  const actionColors = {
                    'INCREASE_LENDING': 'bg-green-100 border-green-300 text-green-800',
                    'DECREASE_LENDING': 'bg-orange-100 border-orange-300 text-orange-800',
                    'INVEST_MARKET': 'bg-purple-100 border-purple-300 text-purple-800',
                    'DIVEST_MARKET': 'bg-pink-100 border-pink-300 text-pink-800',
                    'HOARD_CASH': 'bg-blue-100 border-blue-300 text-blue-800',
                  };
                  const colorClass = actionColors[tx.action] || 'bg-gray-100 border-gray-300 text-gray-800';
                  
                  return (
                    <div
                      key={idx}
                      className={`p-3 border-2 rounded-lg ${colorClass} flex justify-between items-center text-sm`}
                    >
                      <div className="flex-1">
                        <p className="font-bold">
                          {isOutgoing ? '→' : '←'} {tx.action.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs opacity-80">
                          {tx.market_id ? `Market: ${tx.market_id}` : tx.to_bank !== null ? `Bank ${tx.to_bank}` : 'Internal'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">${tx.amount.toFixed(1)}M</p>
                        <p className="text-xs opacity-80">Step {tx.step}</p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BankDashboard;

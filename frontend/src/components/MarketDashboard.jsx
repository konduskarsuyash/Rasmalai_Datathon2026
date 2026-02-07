// components/MarketDashboard.jsx
import { useEffect, useRef } from 'react';

const MarketDashboard = ({ market, historicalData, transactions, onClose }) => {
  const canvasRef = useRef(null);
  
  // Get historical market data
  const marketHistory = historicalData
    .map((step, index) => {
      const marketState = step.market_states?.find(m => m.market_id === market.id);
      return {
        step: index,
        price: marketState?.price || market.capital || 100,
        total_invested: marketState?.total_invested || 0,
        return: marketState?.return || 0,
      };
    })
    .filter(d => d.price !== undefined);
  
  // Filter transactions for this market
  const marketTransactions = transactions.filter(
    tx => tx.market_id === market.id
  );
  
  // Draw price chart
  useEffect(() => {
    if (!canvasRef.current || marketHistory.length === 0) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#faf5ff';
    ctx.fillRect(0, 0, width, height);
    
    // Calculate scales
    const maxPrice = Math.max(...marketHistory.map(d => d.price), 100);
    const minPrice = Math.min(...marketHistory.map(d => d.price), 100);
    const priceRange = maxPrice - minPrice || 1;
    
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    
    const xScale = chartWidth / Math.max(marketHistory.length - 1, 1);
    const yScale = chartHeight / priceRange;
    
    // Draw grid lines
    ctx.strokeStyle = '#e9d5ff';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight * i) / 5;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
      
      // Y-axis labels
      const value = maxPrice - (priceRange * i) / 5;
      ctx.fillStyle = '#6b7280';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`${value.toFixed(1)}`, padding - 5, y + 3);
    }
    
    // Draw baseline at 100
    const baselineY = padding + chartHeight - (100 - minPrice) * yScale;
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding, baselineY);
    ctx.lineTo(width - padding, baselineY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw price line
    ctx.strokeStyle = '#9333ea';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    marketHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const y = padding + chartHeight - (point.price - minPrice) * yScale;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw points
    marketHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const y = padding + chartHeight - (point.price - minPrice) * yScale;
      
      ctx.fillStyle = '#9333ea';
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
    const labelInterval = Math.ceil(marketHistory.length / 10);
    marketHistory.forEach((point, i) => {
      if (i % labelInterval === 0 || i === marketHistory.length - 1) {
        const x = padding + i * xScale;
        ctx.fillText(`T${point.step}`, x, height - padding + 15);
      }
    });
    
    // Chart title
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 14px system-ui';
    ctx.textAlign = 'left';
    ctx.fillText('Index Price Over Time', padding, 25);
    
  }, [marketHistory]);
  
  // Calculate investment stats
  const totalInvestments = marketTransactions
    .filter(tx => tx.action === 'INVEST_MARKET')
    .reduce((sum, tx) => sum + tx.amount, 0);
  
  const totalDivestments = marketTransactions
    .filter(tx => tx.action === 'DIVEST_MARKET')
    .reduce((sum, tx) => sum + tx.amount, 0);
  
  const netFlow = totalInvestments - totalDivestments;
  
  const currentState = marketHistory[marketHistory.length - 1] || { price: 100, return: 0 };
  
  // Market sector information
  const sectorInfo = {
    'BANK_INDEX': {
      icon: '🏦',
      fullName: 'Banking Sector Index',
      description: 'Tracks major commercial banks, investment banks, and financial institutions',
      sectors: ['Commercial Banking', 'Investment Banking', 'Retail Banking', 'Asset Management'],
    },
    'FIN_SERVICES': {
      icon: '💼',
      fullName: 'Financial Services Index',
      description: 'Comprehensive index of fintech, insurance, payments, and financial technology companies',
      sectors: ['Fintech', 'Insurance', 'Payment Systems', 'Digital Banking'],
    },
  };
  
  const info = sectorInfo[market.id] || {
    icon: '📊',
    fullName: market.name,
    description: 'Market index tracking financial instruments',
    sectors: ['Financial Services'],
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-pink-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{info.icon} {info.fullName}</h2>
            <p className="text-purple-100 text-sm mt-1">{info.description}</p>
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
            <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
              <p className="text-xs text-purple-600 font-semibold mb-1">📊 Index Price</p>
              <p className="text-2xl font-bold text-purple-900">{currentState.price.toFixed(2)}</p>
            </div>
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
              <p className="text-xs text-green-600 font-semibold mb-1">📈 Return</p>
              <p className={`text-2xl font-bold ${currentState.return >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                {currentState.return >= 0 ? '+' : ''}{(currentState.return * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <p className="text-xs text-blue-600 font-semibold mb-1">💰 Total Invested</p>
              <p className="text-2xl font-bold text-blue-900">${currentState.total_invested.toFixed(1)}M</p>
            </div>
            <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
              <p className="text-xs text-orange-600 font-semibold mb-1">🔄 Net Flow</p>
              <p className={`text-2xl font-bold ${netFlow >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                {netFlow >= 0 ? '+' : ''}{netFlow.toFixed(1)}M
              </p>
            </div>
          </div>
          
          {/* Price Chart */}
          <div className="bg-white border-2 border-purple-200 rounded-xl p-4">
            <canvas
              ref={canvasRef}
              width={800}
              height={300}
              className="w-full"
            />
          </div>
          
          {/* Sector Composition */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-200 rounded-xl p-6">
            <h3 className="text-lg font-bold text-purple-900 mb-4">🎯 Sector Composition</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {info.sectors.map((sector, idx) => (
                <div key={idx} className="bg-white rounded-lg p-3 text-center shadow-sm">
                  <p className="text-sm font-bold text-purple-900">{sector}</p>
                  <div className="mt-2 h-2 bg-purple-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                      style={{ width: `${75 + Math.random() * 25}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Investment Activity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded-lg p-4">
              <p className="text-sm text-green-700 font-bold mb-2">💵 Total Investments</p>
              <p className="text-3xl font-bold text-green-900">${totalInvestments.toFixed(1)}M</p>
              <p className="text-xs text-green-600 mt-1">{marketTransactions.filter(tx => tx.action === 'INVEST_MARKET').length} investment transactions</p>
            </div>
            <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 rounded-lg p-4">
              <p className="text-sm text-red-700 font-bold mb-2">💸 Total Divestments</p>
              <p className="text-3xl font-bold text-red-900">${totalDivestments.toFixed(1)}M</p>
              <p className="text-xs text-red-600 mt-1">{marketTransactions.filter(tx => tx.action === 'DIVEST_MARKET').length} divestment transactions</p>
            </div>
          </div>
          
          {/* Recent Transactions Log */}
          <div className="bg-gray-50 border-2 border-gray-200 rounded-xl p-4">
            <h3 className="text-lg font-bold text-gray-800 mb-3">📋 Market Activity Log</h3>
            <div className="max-h-64 overflow-y-auto space-y-2">
              {marketTransactions.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-4">No transactions yet</p>
              ) : (
                marketTransactions.slice(-20).reverse().map((tx, idx) => {
                  const isInvestment = tx.action === 'INVEST_MARKET';
                  
                  return (
                    <div
                      key={idx}
                      className={`p-3 border-2 rounded-lg flex justify-between items-center text-sm ${
                        isInvestment
                          ? 'bg-purple-100 border-purple-300 text-purple-800'
                          : 'bg-pink-100 border-pink-300 text-pink-800'
                      }`}
                    >
                      <div className="flex-1">
                        <p className="font-bold">
                          {isInvestment ? '📈 Investment' : '📉 Divestment'}
                        </p>
                        <p className="text-xs opacity-80">
                          From Bank {tx.from_bank}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg">
                          {isInvestment ? '+' : '-'}${tx.amount.toFixed(1)}M
                        </p>
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

export default MarketDashboard;

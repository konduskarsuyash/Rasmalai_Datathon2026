// components/BankDashboard.jsx
import { useEffect, useRef } from 'react';
import MLRiskPredictor from './MLRiskPredictor';

const BankDashboard = ({ bank, historicalData, transactions, onClose }) => {
  const canvasRef = useRef(null);
  const balanceSheetCanvasRef = useRef(null);
  
  // Debug logging
  console.log('BankDashboard opened for:', bank.name, 'ID:', bank.id);
  console.log('Historical data points:', historicalData.length);
  console.log('Transactions count:', transactions.length);
  
  // Filter transactions for this specific bank
  // Handle both string IDs (like "bank1") and numeric IDs (like 0)
  const bankNumericId = typeof bank.id === 'string' 
    ? parseInt(bank.id.replace('bank', '')) - 1 
    : bank.id;
  
  console.log('Bank numeric ID calculated:', bankNumericId, 'from original ID:', bank.id);
  
  // Debug: Log first historical data point
  if (historicalData.length > 0) {
    console.log('First historical data point:', historicalData[0]);
    console.log('Bank states in first point:', historicalData[0].bank_states);
  }
    
  const bankTransactions = transactions.filter(
    tx => tx.from_bank === bankNumericId || tx.to_bank === bankNumericId
  );
  
  console.log('Filtered bank transactions:', bankTransactions.length);
  
  // Get historical capital data for this bank
  const capitalHistory = historicalData
    .map((step, index) => {
      const bankState = step.bank_states?.find(b => b.bank_id === bankNumericId);
      
      // Debug first few steps
      if (index < 3) {
        console.log(`Step ${index}: Looking for bank_id ${bankNumericId}, found:`, bankState);
      }
      
      return {
        step: index,
        capital: bankState?.capital || 0,
        cash: bankState?.cash || 0,
        investments: bankState?.investments || 0,
        loans_given: bankState?.loans_given || 0,
        borrowed: bankState?.borrowed || 0,
        leverage: bankState?.leverage || 0,
        found: !!bankState,
      };
    })
    .filter(d => d.capital !== undefined);
  
  console.log('Capital history generated:', capitalHistory.length, 'points');
  console.log('First capital point:', capitalHistory[0]);
  console.log('Last capital point:', capitalHistory[capitalHistory.length - 1]);
  
  // Get current state (either from latest historical data or from bank object)
  const currentState = capitalHistory.length > 0
    ? capitalHistory[capitalHistory.length - 1]
    : {
        capital: bank.capital || 0,
        cash: 0,
        investments: 0,
        loans_given: 0,
        borrowed: 0,
        leverage: bank.target || 0,
      };
  
  // Draw capital chart
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#f9fafb';
    ctx.fillRect(0, 0, width, height);
    
    // If no data yet, show placeholder
    if (capitalHistory.length === 0) {
      ctx.fillStyle = '#9ca3af';
      ctx.font = '14px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Waiting for simulation data...', width / 2, height / 2 - 10);
      ctx.font = '12px system-ui';
      ctx.fillText('Run a simulation to see historical data', width / 2, height / 2 + 10);
      ctx.fillStyle = '#6b7280';
      ctx.font = '11px system-ui';
      ctx.fillText(`(Historical data points: ${historicalData.length})`, width / 2, height / 2 + 30);
      return;
    }
    
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
    
  }, [capitalHistory, historicalData]);
  
  // Draw balance sheet composition chart (stacked area showing asset breakdown)
  useEffect(() => {
    if (!balanceSheetCanvasRef.current || capitalHistory.length === 0) return;
    
    const canvas = balanceSheetCanvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#f9fafb';
    ctx.fillRect(0, 0, width, height);
    
    const padding = 40;
    const chartWidth = width - 2 * padding;
    const chartHeight = height - 2 * padding;
    
    // Calculate max total assets for scaling
    const maxTotal = Math.max(...capitalHistory.map(d => 
      (d.cash || 0) + (d.investments || 0) + (d.loans_given || 0)
    ), 1);
    
    const xScale = chartWidth / Math.max(capitalHistory.length - 1, 1);
    const yScale = chartHeight / maxTotal;
    
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
      const value = maxTotal - (maxTotal * i) / 5;
      ctx.fillStyle = '#6b7280';
      ctx.font = '10px system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(`$${value.toFixed(0)}M`, padding - 5, y + 3);
    }
    
    // Draw stacked areas (loans_given + investments + cash)
    // 1. Loans (bottom layer)
    ctx.fillStyle = 'rgba(251, 146, 60, 0.5)'; // Orange
    ctx.beginPath();
    ctx.moveTo(padding, padding + chartHeight);
    capitalHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const loansHeight = (point.loans_given || 0) * yScale;
      const y = padding + chartHeight - loansHeight;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(padding + (capitalHistory.length - 1) * xScale, padding + chartHeight);
    ctx.closePath();
    ctx.fill();
    
    // 2. Investments (middle layer)
    ctx.fillStyle = 'rgba(168, 85, 247, 0.5)'; // Purple
    ctx.beginPath();
    ctx.moveTo(padding, padding + chartHeight);
    capitalHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const loansHeight = (point.loans_given || 0) * yScale;
      const investmentsHeight = loansHeight + ((point.investments || 0) * yScale);
      const y = padding + chartHeight - investmentsHeight;
      ctx.lineTo(x, y);
    });
    // Draw back to baseline through loans
    for (let i = capitalHistory.length - 1; i >= 0; i--) {
      const x = padding + i * xScale;
      const loansHeight = (capitalHistory[i].loans_given || 0) * yScale;
      const y = padding + chartHeight - loansHeight;
      ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 3. Cash (top layer)
    ctx.fillStyle = 'rgba(34, 197, 94, 0.5)'; // Green
    ctx.beginPath();
    ctx.moveTo(padding, padding + chartHeight);
    capitalHistory.forEach((point, i) => {
      const x = padding + i * xScale;
      const totalHeight = ((point.loans_given || 0) + (point.investments || 0) + (point.cash || 0)) * yScale;
      const y = padding + chartHeight - totalHeight;
      ctx.lineTo(x, y);
    });
    // Draw back to baseline through investments and loans
    for (let i = capitalHistory.length - 1; i >= 0; i--) {
      const x = padding + i * xScale;
      const loansInvestHeight = ((capitalHistory[i].loans_given || 0) + (capitalHistory[i].investments || 0)) * yScale;
      const y = padding + chartHeight - loansInvestHeight;
      ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
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
    ctx.fillText('Asset Composition Over Time', padding, 25);
    
    // Legend
    ctx.font = '11px system-ui';
    const legendY = 25;
    
    ctx.fillStyle = 'rgba(34, 197, 94, 0.7)';
    ctx.fillRect(width - 200, legendY - 10, 15, 15);
    ctx.fillStyle = '#111827';
    ctx.textAlign = 'left';
    ctx.fillText('Cash', width - 180, legendY);
    
    ctx.fillStyle = 'rgba(168, 85, 247, 0.7)';
    ctx.fillRect(width - 120, legendY - 10, 15, 15);
    ctx.fillStyle = '#111827';
    ctx.fillText('Investments', width - 100, legendY);
    
    ctx.fillStyle = 'rgba(251, 146, 60, 0.7)';
    ctx.fillRect(width - 320, legendY - 10, 15, 15);
    ctx.fillStyle = '#111827';
    ctx.fillText('Loans Given', width - 300, legendY);
    
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
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
<div className="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-y-auto scrollbar-hide">

        {/* Header */}
        <div className="sticky top-0 z-20 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-2xl flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold z-10">{bank.name} Dashboard</h2>
            <p className="text-blue-100 text-sm mt-1">Real-time Performance Analytics</p>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2  bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-all text-3xl"
          >
            ✕
          </button>
        </div>
        
        {/* Content */}
<div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Status Banner if no data */}
          {historicalData.length === 0 && (
            <div className="bg-yellow-50 border-2 border-yellow-300 rounded-xl p-4 text-center">
              <p className="text-yellow-800 font-semibold mb-1">⚠️ No Simulation Data Yet</p>
              <p className="text-yellow-700 text-sm">Start a simulation and wait for it to complete some steps to see live data here.</p>
            </div>
          )}
          
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <p className="text-xs text-blue-600 font-semibold mb-1">💰 Equity (Capital)</p>
              <p className="text-2xl font-bold text-blue-900">${currentState.capital?.toFixed(1) || 0}M</p>
              <p className="text-xs text-blue-600 mt-1">Assets - Liabilities</p>
            </div>
            <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
              <p className="text-xs text-green-600 font-semibold mb-1">💵 Cash</p>
              <p className="text-2xl font-bold text-green-900">${currentState.cash?.toFixed(1) || 0}M</p>
              <p className="text-xs text-green-600 mt-1">Liquid reserves</p>
            </div>
            <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
              <p className="text-xs text-purple-600 font-semibold mb-1">📊 Investments</p>
              <p className="text-2xl font-bold text-purple-900">${currentState.investments?.toFixed(1) || 0}M</p>
              <p className="text-xs text-purple-600 mt-1">Market exposure</p>
            </div>
            <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-4">
              <p className="text-xs text-orange-600 font-semibold mb-1">🏦 Loans Given</p>
              <p className="text-2xl font-bold text-orange-900">${currentState.loans_given?.toFixed(1) || 0}M</p>
              <p className="text-xs text-orange-600 mt-1">Lending portfolio</p>
            </div>
          </div>
          
          {/* Additional Balance Sheet Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
              <p className="text-xs text-red-600 font-semibold mb-1">💳 Debt</p>
              <p className="text-2xl font-bold text-red-900">${currentState.borrowed?.toFixed(1) || 0}M</p>
              <p className="text-xs text-red-600 mt-1">Borrowed funds</p>
            </div>
            <div className="bg-indigo-50 border-2 border-indigo-200 rounded-lg p-4">
              <p className="text-xs text-indigo-600 font-semibold mb-1">📈 Total Assets</p>
              <p className="text-2xl font-bold text-indigo-900">
                ${((currentState.cash || 0) + (currentState.investments || 0) + (currentState.loans_given || 0)).toFixed(1)}M
              </p>
              <p className="text-xs text-indigo-600 mt-1">Cash + Investments + Loans</p>
            </div>
            <div className="bg-amber-50 border-2 border-amber-200 rounded-lg p-4">
              <p className="text-xs text-amber-600 font-semibold mb-1">⚖️ Leverage</p>
              <p className="text-2xl font-bold text-amber-900">{currentState.leverage?.toFixed(2) || 0}x</p>
              <p className="text-xs text-amber-600 mt-1">Assets / Equity</p>
            </div>
          </div>
          
          {/* ML Risk Assessment Section */}
          {bank.past_defaults !== undefined && (
            <div className="bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 rounded-xl p-4">
              <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                <span>🤖</span>
                <span>ML-Based Risk Assessment</span>
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-red-200">
                  <p className="text-xs text-red-600 font-semibold mb-1">📉 Default History</p>
                  <p className="text-xl font-bold text-red-900">{bank.past_defaults || 0}</p>
                  <p className="text-xs text-red-600 mt-1">
                    {bank.past_defaults === 0 ? '✅ Clean' : '⚠️ Elevated risk'}
                  </p>
                </div>
                <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-orange-200">
                  <p className="text-xs text-orange-600 font-semibold mb-1">🎯 Risk Appetite</p>
                  <p className="text-xl font-bold text-orange-900">
                    {((bank.risk_appetite || 0.5) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-orange-600 mt-1">
                    {bank.risk_appetite < 0.3 ? '🛡️ Conservative' : bank.risk_appetite > 0.7 ? '🚀 Aggressive' : '⚖️ Balanced'}
                  </p>
                </div>
                <div className="bg-white bg-opacity-70 rounded-lg p-3 border border-yellow-200">
                  <p className="text-xs text-yellow-600 font-semibold mb-1">📊 Volatility</p>
                  <p className="text-xl font-bold text-yellow-900">
                    {((bank.investment_volatility || 0) * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-yellow-600 mt-1">
                    {bank.investment_volatility < 0.3 ? '✅ Stable' : bank.investment_volatility > 0.7 ? '⚠️ High' : '🟡 Moderate'}
                  </p>
                </div>
              </div>
              <div className="mt-3 text-xs text-gray-600 bg-white bg-opacity-50 rounded-lg p-2">
                <p className="font-semibold mb-1">📖 What these metrics mean:</p>
                <p>• <strong>Default History:</strong> Number of times this bank failed to meet obligations (0 = best)</p>
                <p>• <strong>Risk Appetite:</strong> How aggressively the bank takes risk (0% = very conservative, 100% = very aggressive)</p>
                <p>• <strong>Volatility:</strong> Variability in investment returns (lower = more predictable)</p>
              </div>
            </div>
          )}
          
          {/* LIVE ML Risk Prediction - Real-time AI Model */}
          <MLRiskPredictor 
            bank={{
              ...bank,
              capital_ratio: currentState.leverage ? 1 / currentState.leverage : 0.1,
              leverage: currentState.leverage || 10,
              liquidity_ratio: currentState.cash / (currentState.capital || 100) || 0.2,
              capital: currentState.capital,
              cash: currentState.cash,
              investments: currentState.investments,
              past_defaults: bank.past_defaults || 0,
              investment_volatility: bank.investment_volatility || 0,
              risk_appetite: bank.risk_appetite || 0.5,
            }}
            marketState={{
              stress: 0.3,
              volatility: 0.02,
            }}
          />
          
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-xl p-4">
            <h3 className="text-sm font-bold text-gray-700 mb-2">📚 Understanding the Balance Sheet:</h3>
            <div className="text-xs text-gray-600 space-y-1">
              <p>• <strong>Equity (Capital)</strong> = Total Assets - Total Liabilities</p>
              <p>• When you <strong>lend or invest</strong>, cash decreases but loans/investments increase → <strong>equity stays the same</strong> (just converting one asset to another)</p>
              <p>• Equity only changes when: you earn returns, suffer losses, take on debt, or default on obligations</p>
              <p>• Watch the <strong>Asset Composition chart</strong> below to see how your cash converts to other assets!</p>
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
          
          {/* Balance Sheet Composition Chart */}
          {capitalHistory.length > 0 && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-4">
              <canvas
                ref={balanceSheetCanvasRef}
                width={800}
                height={250}
                className="w-full"
              />
              <p className="text-xs text-gray-500 text-center mt-2">
                💡 This shows how your assets are allocated. When you lend or invest, cash converts to other assets.
              </p>
            </div>
          )}
          
          {/* Transaction Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Interbank Lending Section */}
            <div className="bg-gradient-to-br from-cyan-50 to-blue-50 border-2 border-cyan-300 rounded-xl p-4">
              <h4 className="text-sm font-bold text-cyan-800 mb-3">🏦 Interbank Activity</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-green-700">Total Lent:</span>
                  <span className="font-bold text-green-900">${lentAmount.toFixed(1)}M</span>
                </div>
                <div className="text-xs text-green-600">
                  {bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'INCREASE_LENDING').length} lending transactions
                </div>
                <div className="flex justify-between items-center mt-2 pt-2 border-t border-cyan-200">
                  <span className="text-xs text-red-700">Total Borrowed:</span>
                  <span className="font-bold text-red-900">${borrowedAmount.toFixed(1)}M</span>
                </div>
                <div className="text-xs text-red-600">
                  {bankTransactions.filter(tx => tx.to_bank === bankNumericId && tx.action === 'INCREASE_LENDING').length} borrowing transactions
                </div>
              </div>
            </div>
            
            {/* Market Activity Section */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 border-2 border-purple-300 rounded-xl p-4">
              <h4 className="text-sm font-bold text-purple-800 mb-3">📊 Market Activity</h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-purple-700">Total Invested:</span>
                  <span className="font-bold text-purple-900">${investedAmount.toFixed(1)}M</span>
                </div>
                <div className="text-xs text-purple-600">
                  {bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'INVEST_MARKET').length} investment transactions
                </div>
                <div className="flex justify-between items-center mt-2 pt-2 border-t border-purple-200">
                  <span className="text-xs text-pink-700">Total Divested:</span>
                  <span className="font-bold text-pink-900">
                    ${bankTransactions
                      .filter(tx => tx.from_bank === bankNumericId && tx.action === 'DIVEST_MARKET')
                      .reduce((sum, tx) => sum + tx.amount, 0)
                      .toFixed(1)}M
                  </span>
                </div>
                <div className="text-xs text-pink-600">
                  {bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'DIVEST_MARKET').length} divestment transactions
                </div>
                <div className="mt-2 pt-2 border-t border-purple-200 text-xs">
                  <span className="text-gray-600">Net Market Position: </span>
                  <span className={`font-bold ${(investedAmount - bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'DIVEST_MARKET').reduce((sum, tx) => sum + tx.amount, 0)) >= 0 ? 'text-purple-900' : 'text-pink-900'}`}>
                    ${(investedAmount - bankTransactions.filter(tx => tx.from_bank === bankNumericId && tx.action === 'DIVEST_MARKET').reduce((sum, tx) => sum + tx.amount, 0)).toFixed(1)}M
                  </span>
                </div>
              </div>
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

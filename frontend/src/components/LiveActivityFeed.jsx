// components/LiveActivityFeed.jsx
import { useEffect, useRef } from 'react';

const LiveActivityFeed = ({ transactions, currentStep }) => {
  const feedRef = useRef(null);
  
  // Auto-scroll to bottom when new transactions arrive
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [transactions.length]);
  
  // Get last 10 transactions
  const recentTransactions = transactions.slice(-10);
  
  // Action styling
  const getActionStyle = (action) => {
    const styles = {
      'INCREASE_LENDING': {
        bg: 'bg-green-100',
        border: 'border-green-400',
        text: 'text-green-800',
        icon: '💰',
        label: 'LEND'
      },
      'DECREASE_LENDING': {
        bg: 'bg-orange-100',
        border: 'border-orange-400',
        text: 'text-orange-800',
        icon: '💸',
        label: 'REPAY'
      },
      'INVEST_MARKET': {
        bg: 'bg-purple-100',
        border: 'border-purple-400',
        text: 'text-purple-800',
        icon: '📈',
        label: 'INVEST'
      },
      'DIVEST_MARKET': {
        bg: 'bg-pink-100',
        border: 'border-pink-400',
        text: 'text-pink-800',
        icon: '📉',
        label: 'DIVEST'
      },
      'HOARD_CASH': {
        bg: 'bg-blue-100',
        border: 'border-blue-400',
        text: 'text-blue-800',
        icon: '💵',
        label: 'HOLD'
      },
    };
    return styles[action] || {
      bg: 'bg-gray-100',
      border: 'border-gray-400',
      text: 'text-gray-800',
      icon: '🏦',
      label: action
    };
  };
  
  return (
    <div className="absolute bottom-6 right-6 w-80 bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl border-2 border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-3">
        <h3 className="text-sm font-bold flex items-center justify-between">
          <span>📊 Live Activity Feed</span>
          <span className="text-xs bg-white/20 px-2 py-1 rounded">
            Step {currentStep}
          </span>
        </h3>
      </div>
      
      {/* Feed */}
      <div 
        ref={feedRef}
        className="h-64 overflow-y-auto p-3 space-y-2"
      >
        {recentTransactions.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            Waiting for simulation...
          </div>
        ) : (
          recentTransactions.map((tx, idx) => {
            const style = getActionStyle(tx.action);
            const target = tx.market_id 
              ? tx.market_id 
              : tx.to_bank !== null 
                ? `Bank ${tx.to_bank}` 
                : 'Internal';
            
            return (
              <div
                key={`${tx.step}-${tx.from_bank}-${idx}`}
                className={`p-2 border-2 ${style.border} ${style.bg} rounded-lg text-xs animate-fadeIn`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-bold ${style.text}`}>
                    {style.icon} Bank {tx.from_bank}
                  </span>
                  <span className="text-xs text-gray-600">
                    T{tx.step}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className={`text-xs ${style.text}`}>
                    {style.label} → {target}
                  </span>
                  <span className={`font-bold ${style.text}`}>
                    ${tx.amount.toFixed(1)}M
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
      
      {/* Footer stats */}
      <div className="bg-gray-50 border-t-2 border-gray-200 p-2 flex justify-between text-xs">
        <span className="text-gray-600">
          Total Actions: <span className="font-bold text-gray-900">{transactions.length}</span>
        </span>
        <span className="text-gray-600">
          Active Banks: <span className="font-bold text-gray-900">{new Set(transactions.map(t => t.from_bank)).size}</span>
        </span>
      </div>
    </div>
  );
};

export default LiveActivityFeed;

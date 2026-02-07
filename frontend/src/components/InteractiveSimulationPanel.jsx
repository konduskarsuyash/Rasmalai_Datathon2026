// components/InteractiveSimulationPanel.jsx
import { useState, useEffect, useRef } from 'react';
import { LocalSimulationEngine } from '../utils/localSimulationEngine';

const InteractiveSimulationPanel = ({ 
  institutions, 
  connections,
  onTransactionEvent, 
  onDefaultEvent,
  onBankUpdate
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [stats, setStats] = useState({ defaults: 0, totalCapital: 0 });
  const [showModifyPanel, setShowModifyPanel] = useState(false);
  
  const engineRef = useRef(null);
  
  // Initialize or update engine when institutions/connections change
  useEffect(() => {
    if (institutions.length > 0 && !isRunning) {
      engineRef.current = new LocalSimulationEngine(institutions, connections, {
        interestRate: 0.05,
        loanRepaymentRate: 0.1,
        marketVolatility: 0.02
      });
      
      // Set up callbacks
      engineRef.current.onStepComplete = (state) => {
        setCurrentStep(state.step);
        setStats({
          defaults: state.banks.filter(b => b.isDefaulted).length,
          totalCapital: state.banks.reduce((sum, b) => sum + b.capital, 0)
        });
        
        // Send state to parent for visualization
        if (onTransactionEvent) {
          onTransactionEvent({
            type: 'step_end',
            step: state.step,
            bank_states: state.banks.map(b => ({
              bank_id: b.id,
              capital: b.capital,
              cash: b.cash,
              investments: Object.values(b.investments).reduce((a, b) => a + b, 0),
              loans_given: Object.values(b.loansGiven).reduce((a, b) => a + b, 0),
              borrowed: Object.values(b.loansTaken).reduce((a, b) => a + b, 0),
              leverage: b.capital > 0 ? b.cash / b.capital : 0,
              is_defaulted: b.isDefaulted
            })),
            market_states: state.markets ? Object.entries(state.markets).map(([id, m]) => ({
              market_id: id,
              name: id,
              price: m.price,
              total_invested: m.totalInvested,
              return: (m.price - 100) / 100
            })) : []
          });
        }
      };
      
      engineRef.current.onTransaction = (tx) => {
        if (onTransactionEvent) {
          onTransactionEvent({
            type: 'transaction',
            step: tx.step,
            from_bank: tx.from,
            to_bank: tx.to,
            market_id: tx.market_id,
            action: tx.type,
            amount: tx.amount,
            reason: ''
          });
        }
      };
      
      engineRef.current.onBankDefault = (bank) => {
        if (onDefaultEvent) {
          onDefaultEvent({
            bank_id: bank.id,
            equity: bank.capital
          });
        }
      };
    }
  }, [institutions, connections]);
  
  const handleStart = () => {
    if (!engineRef.current) return;
    
    // Send init event
    if (onTransactionEvent) {
      onTransactionEvent({
        type: 'init',
        banks: institutions.filter(i => i.type === 'bank').map(b => ({
          id: parseInt(b.id.replace('bank', '')) - 1,
          name: b.name,
          capital: b.capital
        })),
        connections: []
      });
    }
    
    setIsRunning(true);
    setIsPaused(false);
    engineRef.current.start();
  };
  
  const handlePause = () => {
    if (!engineRef.current) return;
    engineRef.current.pause();
    setIsPaused(true);
    setShowModifyPanel(true);
  };
  
  const handleResume = () => {
    if (!engineRef.current) return;
    engineRef.current.resume();
    setIsPaused(false);
    setShowModifyPanel(false);
  };
  
  const handleStop = () => {
    if (!engineRef.current) return;
    engineRef.current.stop();
    setIsRunning(false);
    setIsPaused(false);
    setShowModifyPanel(false);
    
    if (onTransactionEvent) {
      onTransactionEvent({ type: 'complete' });
    }
  };
  
  // Modification actions
  const handleAddCapital = (bankId, amount) => {
    if (!engineRef.current || !isPaused) return;
    engineRef.current.addCapitalToBank(bankId, amount);
    
    // Update parent component
    if (onBankUpdate) {
      const bank = engineRef.current.banks.find(b => b.id === bankId);
      if (bank) {
        onBankUpdate(`bank${bankId + 1}`, { capital: bank.capital });
      }
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Control Panel */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-4 text-white shadow-lg">
        <h3 className="text-lg font-bold mb-3 flex items-center">
          <span className="mr-2">🎮</span>
          Interactive Simulation
        </h3>
        
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-white/20 rounded-lg p-2">
            <p className="text-xs opacity-80">Step</p>
            <p className="text-xl font-bold">{currentStep}</p>
          </div>
          <div className="bg-white/20 rounded-lg p-2">
            <p className="text-xs opacity-80">Defaults</p>
            <p className="text-xl font-bold">{stats.defaults}</p>
          </div>
          <div className="bg-white/20 rounded-lg p-2">
            <p className="text-xs opacity-80">Total Capital</p>
            <p className="text-xl font-bold">${stats.totalCapital.toFixed(0)}M</p>
          </div>
        </div>
        
        {/* Controls */}
        <div className="flex gap-2">
          {!isRunning && (
            <button
              onClick={handleStart}
              className="flex-1 px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-bold transition-all shadow-md"
            >
              ▶️ Start Simulation
            </button>
          )}
          
          {isRunning && !isPaused && (
            <>
              <button
                onClick={handlePause}
                className="flex-1 px-4 py-3 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-bold transition-all shadow-md"
              >
                ⏸️ Pause
              </button>
              <button
                onClick={handleStop}
                className="px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-bold transition-all shadow-md"
              >
                ⏹️ Stop
              </button>
            </>
          )}
          
          {isRunning && isPaused && (
            <>
              <button
                onClick={handleResume}
                className="flex-1 px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-bold transition-all shadow-md"
              >
                ▶️ Resume
              </button>
              <button
                onClick={handleStop}
                className="px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-bold transition-all shadow-md"
              >
                ⏹️ Stop
              </button>
            </>
          )}
        </div>
      </div>
      
      {/* Modification Panel (shown when paused) */}
      {isPaused && showModifyPanel && engineRef.current && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-4">
          <h4 className="text-sm font-bold text-yellow-900 mb-3 flex items-center">
            <span className="mr-2">✏️</span>
            Modify Network (Simulation Paused)
          </h4>
          
          <div className="space-y-3">
            {engineRef.current.banks.filter(b => !b.isDefaulted).map(bank => (
              <div key={bank.id} className="bg-white rounded-lg p-3 border border-yellow-300">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <p className="text-sm font-bold text-gray-800">{bank.name}</p>
                    <p className="text-xs text-gray-600">Capital: ${bank.capital.toFixed(1)}M</p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAddCapital(bank.id, 50)}
                    className="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 text-white text-xs rounded font-bold"
                  >
                    + $50M
                  </button>
                  <button
                    onClick={() => handleAddCapital(bank.id, 100)}
                    className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs rounded font-bold"
                  >
                    + $100M
                  </button>
                  <button
                    onClick={() => handleAddCapital(bank.id, -50)}
                    className="flex-1 px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-xs rounded font-bold"
                  >
                    - $50M
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-3 p-2 bg-blue-50 rounded-lg border border-blue-300">
            <p className="text-xs text-blue-800">
              💡 <span className="font-bold">Tip:</span> Make changes above, then click <span className="font-bold">Resume</span> to see how the network adapts!
            </p>
          </div>
        </div>
      )}
      
      {/* Info Box */}
      <div className="bg-gray-50 border border-gray-300 rounded-lg p-3">
        <p className="text-xs text-gray-700">
          <span className="font-bold">🎯 How it works:</span>
        </p>
        <ul className="text-xs text-gray-600 space-y-1 mt-2 list-disc list-inside">
          <li>Simulation runs <span className="font-bold">live in your browser</span></li>
          <li>Banks pay <span className="font-bold text-green-600">5% interest</span> per step on loans</li>
          <li>Loans automatically repay <span className="font-bold text-blue-600">10%</span> per step</li>
          <li><span className="font-bold text-yellow-600">Pause anytime</span> to modify the network</li>
          <li>All dashboards update <span className="font-bold text-purple-600">in real-time</span></li>
        </ul>
      </div>
    </div>
  );
};

export default InteractiveSimulationPanel;

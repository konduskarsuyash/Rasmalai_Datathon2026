// components/InteractiveSimulationPanel.jsx
// Uses backend API for simulation (no local engine)
import { useState, useEffect, useRef } from 'react';

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
  const [bankStates, setBankStates] = useState([]);
  
  const readerRef = useRef(null);

  const handleStart = async () => {
    try {
      const nodeParameters = institutions
        .filter(inst => inst.type === 'bank' && !inst.isMarket)
        .map(inst => ({
          initial_capital: inst.capital || 100,
          target_leverage: inst.target || 3.0,
          risk_factor: inst.risk || 0.3,
        }));

      const marketNodes = institutions
        .filter(inst => inst.type === 'market' || inst.isMarket)
        .map(inst => ({
          id: inst.id,
          name: inst.name,
        }));

      const payload = {
        num_banks: nodeParameters.length || 5,
        num_steps: 30,
        node_parameters: nodeParameters,
        market_nodes: marketNodes.length > 0 ? marketNodes : null,
        connection_density: 0.2,
        use_featherless: true,
        use_game_theory: true,
      };

      setIsRunning(true);
      setIsPaused(false);
      setCurrentStep(0);
      setStats({ defaults: 0, totalCapital: 0 });

      const response = await fetch('http://localhost:8000/api/interactive/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', response.status, errorText);
        alert(`Failed to start simulation: ${errorText}`);
        setIsRunning(false);
        return;
      }

      const reader = response.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          setIsRunning(false);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || '';

        for (const message of messages) {
          if (message.startsWith('data: ')) {
            try {
              const event = JSON.parse(message.substring(6));
              handleEvent(event);
            } catch (err) {
              console.error('Failed to parse SSE:', err);
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to start simulation:', error);
      alert(`Failed to start: ${error.message}`);
      setIsRunning(false);
    }
  };

  const handleEvent = (event) => {
    if (event.type === 'init') {
      if (onTransactionEvent) onTransactionEvent(event);
    } else if (event.type === 'step_start') {
      setCurrentStep(event.step);
      if (onTransactionEvent) onTransactionEvent(event);
    } else if (event.type === 'transaction') {
      if (onTransactionEvent) onTransactionEvent(event);
    } else if (event.type === 'default') {
      if (onDefaultEvent) onDefaultEvent(event);
      if (onTransactionEvent) onTransactionEvent(event);
    } else if (event.type === 'step_end') {
      setStats({
        defaults: event.total_defaults || 0,
        totalCapital: Math.round(event.total_equity || 0),
      });
      if (event.bank_states) {
        setBankStates(event.bank_states);
      }
      if (onTransactionEvent) onTransactionEvent(event);
    } else if (event.type === 'paused') {
      setIsPaused(true);
    } else if (event.type === 'resumed') {
      setIsPaused(false);
      setShowModifyPanel(false);
    } else if (event.type === 'stopped' || event.type === 'complete') {
      setIsRunning(false);
      setIsPaused(false);
      setShowModifyPanel(false);
      if (onTransactionEvent) onTransactionEvent({ type: 'complete' });
    } else {
      // Forward all other events (market_gain, market_movement, etc.)
      if (onTransactionEvent) onTransactionEvent(event);
    }
  };

  const handlePause = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'pause' }),
      });
      setIsPaused(true);
      setShowModifyPanel(true);
    } catch (error) {
      console.error('Failed to pause:', error);
    }
  };

  const handleResume = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'resume' }),
      });
    } catch (error) {
      console.error('Failed to resume:', error);
    }
  };

  const handleStop = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'stop' }),
      });
      setIsRunning(false);
      setIsPaused(false);
      setShowModifyPanel(false);
      if (readerRef.current) {
        readerRef.current.cancel();
      }
      if (onTransactionEvent) onTransactionEvent({ type: 'complete' });
    } catch (error) {
      console.error('Failed to stop:', error);
    }
  };

  const handleAddCapital = async (bankId, amount) => {
    if (!isPaused) return;
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'add_capital', bank_id: bankId, amount }),
      });
    } catch (error) {
      console.error('Failed to add capital:', error);
    }
  };

  const handleDeleteBank = async (bankId) => {
    if (!isPaused) return;
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'delete_bank', bank_id: bankId }),
      });
    } catch (error) {
      console.error('Failed to delete bank:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (readerRef.current) {
        readerRef.current.cancel();
      }
    };
  }, []);

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-4 text-white shadow-lg">
        <h3 className="text-lg font-bold mb-3 flex items-center">
          <span className="mr-2">🎮</span>
          Interactive Simulation
        </h3>
        
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
            <p className="text-xl font-bold">${stats.totalCapital}M</p>
          </div>
        </div>
        
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
      
      {isPaused && showModifyPanel && bankStates.length > 0 && (
        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-4">
          <h4 className="text-sm font-bold text-yellow-900 mb-3 flex items-center">
            <span className="mr-2">✏️</span>
            Modify Network (Simulation Paused)
          </h4>
          
          <div className="space-y-3">
            {bankStates.filter(b => !b.is_defaulted).map(bank => (
              <div key={bank.bank_id} className="bg-white rounded-lg p-3 border border-yellow-300">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <p className="text-sm font-bold text-gray-800">Bank {bank.bank_id}</p>
                    <p className="text-xs text-gray-600">
                      Capital: ${(bank.capital || 0).toFixed(1)}M | Cash: ${(bank.cash || 0).toFixed(1)}M
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteBank(bank.bank_id)}
                    className="px-2 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded font-bold transition-all"
                    title="Delete bank"
                  >
                    🗑️
                  </button>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleAddCapital(bank.bank_id, 50)}
                    className="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 text-white text-xs rounded font-bold"
                  >
                    + $50M
                  </button>
                  <button
                    onClick={() => handleAddCapital(bank.bank_id, 100)}
                    className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs rounded font-bold"
                  >
                    + $100M
                  </button>
                  <button
                    onClick={() => handleAddCapital(bank.bank_id, -50)}
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
      
      <div className="bg-gray-50 border border-gray-300 rounded-lg p-3">
        <p className="text-xs text-gray-700">
          <span className="font-bold">🎯 How it works:</span>
        </p>
        <ul className="text-xs text-gray-600 space-y-1 mt-2 list-disc list-inside">
          <li>Simulation runs on the <span className="font-bold text-blue-600">backend server</span> with ML policy</li>
          <li>Banks pay <span className="font-bold text-green-600">5% interest</span> per step on loans</li>
          <li>Loans automatically repay <span className="font-bold text-blue-600">10%</span> per step</li>
          <li><span className="font-bold text-yellow-600">Pause anytime</span> to modify the network</li>
          <li>Nash equilibrium <span className="font-bold text-purple-600">game theory</span> drives decisions</li>
          <li>Markets only active if you <span className="font-bold text-pink-600">add market nodes</span></li>
        </ul>
      </div>
    </div>
  );
};

export default InteractiveSimulationPanel;

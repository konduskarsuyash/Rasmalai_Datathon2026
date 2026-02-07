import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Trash2, DollarSign, Plus } from 'lucide-react';

const BackendSimulationPanel = ({ institutions, connections, onTransactionEvent }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [stats, setStats] = useState({
    defaults: 0,
    totalEquity: 0,
    activeTransactions: 0,
  });
  const [selectedBankForAction, setSelectedBankForAction] = useState(null);
  const [capitalAmount, setCapitalAmount] = useState(50);

  const readerRef = useRef(null);

  const startSimulation = async () => {
    if (isRunning) return;

    try {
      const nodeParameters = institutions
        .filter(inst => inst.type === 'bank' && !inst.isMarket)
        .map(inst => ({
          initial_capital: inst.capital || 100,
          target_leverage: inst.target || 3.0,
          risk_factor: inst.risk || 0.3,
        }));
      
      console.log('[BackendSimulationPanel] Starting simulation with node parameters:', nodeParameters);

      const payload = {
        num_banks: nodeParameters.length || 5,
        num_steps: 30,
        node_parameters: nodeParameters,
        connection_density: 0.2,
        use_featherless: false,
      };
      
      console.log('[BackendSimulationPanel] Simulation payload:', payload);

      setIsRunning(true);
      setIsPaused(false);
      setStats({ defaults: 0, totalEquity: 0, activeTransactions: 0 });

      const response = await fetch('http://localhost:8000/api/interactive/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error:', response.status, errorText);
        let errorDetail = errorText;
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorText;
        } catch (e) {}
        alert(`Failed to start simulation: ${errorDetail}`);
        setIsRunning(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const readStream = async () => {
        let buffer = '';
        
        console.log('Starting SSE stream reading...');
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            console.log('Stream completed');
            setIsRunning(false);
            break;
          }
          
          buffer += decoder.decode(value, { stream: true });
          console.log('Received chunk, buffer length:', buffer.length);
          
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || '';
          
          console.log('Processing', messages.length, 'messages');
          
          for (const message of messages) {
            if (message.startsWith('data: ')) {
              try {
                const data = JSON.parse(message.substring(6));
                console.log('Received event:', data.type, data);
                handleEvent(data);
              } catch (err) {
                console.error('Failed to parse SSE data:', err, message);
              }
            }
          }
        }
      };

      readStream().catch(err => {
        console.error('Stream reading error:', err);
        setIsRunning(false);
      });
      
      readerRef.current = reader;

    } catch (error) {
      console.error('Failed to start simulation:', error);
      alert(`Failed to start simulation: ${error.message || error}`);
      setIsRunning(false);
    }
  };

  const handleEvent = (event) => {
    switch (event.type) {
      case 'init':
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'step_start':
        setCurrentStep(event.step);
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'transaction':
        setStats(prev => ({ ...prev, activeTransactions: prev.activeTransactions + 1 }));
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'default':
        setStats(prev => ({ ...prev, defaults: prev.defaults + 1 }));
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'profit_booking':
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'interest_payment':
      case 'loan_repayment':
        setStats(prev => ({ ...prev, activeTransactions: prev.activeTransactions + 1 }));
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'step_end':
        setStats({
          defaults: event.total_defaults,
          totalEquity: Math.round(event.total_equity),
          activeTransactions: stats.activeTransactions,
        });
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;

      case 'complete':
        setIsRunning(false);
        setIsPaused(false);
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        if (readerRef.current) {
          readerRef.current.cancel();
        }
        break;

      case 'paused':
        setIsPaused(true);
        break;

      case 'resumed':
        setIsPaused(false);
        break;

      case 'stopped':
        setIsRunning(false);
        setIsPaused(false);
        if (readerRef.current) {
          readerRef.current.cancel();
        }
        break;

      case 'bank_deleted':
        alert(`Bank ${event.bank_id} deleted`);
        break;

      case 'capital_added':
        alert(`$${event.amount}M added to Bank ${event.bank_id}`);
        break;

      case 'financial_crisis':
        // Handle crisis notification
        console.log('Financial crisis event:', event.message);
        if (onTransactionEvent) {
          onTransactionEvent(event);
        }
        break;
    }
  };

  const pauseSimulation = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'pause' }),
      });
      setIsPaused(true);
    } catch (error) {
      console.error('Failed to pause simulation:', error);
    }
  };

  const resumeSimulation = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'resume' }),
      });
    } catch (error) {
      console.error('Failed to resume simulation:', error);
    }
  };

  const stopSimulation = async () => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'stop' }),
      });
      setIsRunning(false);
      setIsPaused(false);
      if (readerRef.current) {
        readerRef.current.cancel();
      }
    } catch (error) {
      console.error('Failed to stop simulation:', error);
    }
  };

  const restartSimulation = async () => {
    await stopSimulation();
    setTimeout(() => {
      setCurrentStep(0);
      setStats({ defaults: 0, totalEquity: 0, activeTransactions: 0 });
      setSelectedBankForAction(null);
      // Notify parent to reset historical data
      if (onTransactionEvent) {
        onTransactionEvent({ type: 'restart' });
      }
    }, 500);
  };

  const triggerFinancialCrisis = async () => {
    if (!isRunning) {
      alert('Start a simulation first!');
      return;
    }
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'financial_crisis' }),
      });
      alert('💥 Financial Crisis Triggered! Markets are crashing...');
    } catch (error) {
      console.error('Failed to trigger crisis:', error);
    }
  };

  const deleteBank = async (bankId) => {
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

  const addCapital = async (bankId, amount) => {
    try {
      await fetch('http://localhost:8000/api/interactive/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'add_capital', bank_id: bankId, amount }),
      });
      setSelectedBankForAction(null);
    } catch (error) {
      console.error('Failed to add capital:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (readerRef.current) {
        readerRef.current.cancel();
      }
    };
  }, []);

  const banks = institutions.filter(inst => inst.type === 'bank' && !inst.isMarket);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header with Gradient */}
      <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 px-5 py-3.5">
        <h2 className="text-lg font-bold text-white">Control</h2>
      </div>

      <div className="p-5 space-y-4">
        {/* Control Buttons */}
        <div className="flex gap-3">
          {!isRunning && (
            <button
              onClick={startSimulation}
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm font-semibold text-[15px]"
            >
              <Play size={18} className="fill-current" />
              <span>Start</span>
            </button>
          )}
          
          {!isRunning && currentStep > 0 && (
            <button
              onClick={restartSimulation}
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors shadow-sm font-semibold text-[15px]"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              <span>Restart</span>
            </button>
          )}

          {isRunning && !isPaused && (
            <button
              onClick={pauseSimulation}
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm font-semibold text-[15px]"
            >
              <Pause size={18} className="fill-current" />
              <span>Pause</span>
            </button>
          )}

          {isRunning && isPaused && (
            <button
              onClick={resumeSimulation}
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm font-semibold text-[15px]"
            >
              <Play size={18} className="fill-current" />
              <span>Resume</span>
            </button>
          )}

          {isRunning && (
            <button
              onClick={stopSimulation}
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors shadow-sm font-semibold text-[15px]"
            >
              <Square size={18} className="fill-current" />
              <span>Stop</span>
            </button>
          )}
        </div>

        {/* Crisis Button */}
        {isRunning && (
          <button
            onClick={triggerFinancialCrisis}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-3 bg-gradient-to-r from-red-600 to-orange-600 text-white rounded-xl hover:from-red-700 hover:to-orange-700 transition-all shadow-lg font-bold text-[15px] border-2 border-red-800"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L1 21h22L12 2zm0 3.5L19.5 19h-15L12 5.5zm-1 8.5h2v2h-2v-2zm0-6h2v5h-2V8z"/></svg>
            <span>💥 Trigger Financial Crisis</span>
          </button>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-3">
          {/* Current Step */}
          <div className="bg-blue-50 rounded-xl p-4 text-center">
            <p className="text-[11px] font-bold text-blue-600 uppercase tracking-wide mb-1">
              CURRENT STEP
            </p>
            <p className="text-sm font-bold text-blue-600">{currentStep}</p>
          </div>
          
          {/* Defaults */}
          <div className="bg-red-50 rounded-xl p-4 text-center">
            <p className="text-[11px] font-bold text-red-600 uppercase tracking-wide mb-1">
              DEFAULTS
            </p>
            <p className="text-sm font-bold text-red-600">{stats.defaults}</p>
          </div>
          
          {/* Total Capital */}
          <div className="bg-green-50 rounded-xl p-4 text-center">
            <p className="text-[11px] font-bold text-green-600 uppercase tracking-wide mb-1">
              TOTAL CAPITAL
            </p>
            <p className="text-sm font-bold text-green-600">${stats.totalEquity}M</p>
          </div>
        </div>

        {/* Paused State */}
        {isPaused && (
          <div className="border-2 border-yellow-400 bg-yellow-50 rounded-2xl p-4">
            {/* Header */}
            <div className="flex items-start gap-3 mb-4">
              <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
                <Pause size={24} className="text-white fill-current" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-amber-900 text-lg leading-tight">
                  Simulation Paused
                </h3>
                <p className="text-amber-700 text-sm mt-0.5">
                  Modify the network below
                </p>
              </div>
            </div>
            
            {/* Bank Selection */}
            <div className="space-y-3">
              <p className="text-sm font-semibold text-gray-700">
                Select a bank to modify:
              </p>
              
              {/* Bank List */}
              <div className="space-y-2.5 max-h-[280px] overflow-y-auto">
                {banks.map((bank, idx) => (
                  <div key={bank.id} className="flex items-center gap-2.5">
                    <button
                      onClick={() => setSelectedBankForAction(idx)}
                      className={`flex-1 px-4 py-3.5 rounded-xl border-2 transition-all font-semibold text-[15px] ${
                        selectedBankForAction === idx
                          ? 'bg-blue-600 border-blue-600 text-white shadow-md'
                          : 'bg-white border-gray-200 text-gray-800 hover:border-blue-300 hover:bg-blue-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>Bank {idx + 1}</span>
                        <span className={`text-sm ${selectedBankForAction === idx ? 'text-blue-100' : 'text-gray-500'}`}>
                          ${bank.capital}M
                        </span>
                      </div>
                    </button>
                    
                    <button
                      onClick={() => deleteBank(idx)}
                      className="p-3.5 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-all shadow-sm border-2 border-transparent hover:border-red-300"
                      title="Delete Bank"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                ))}
              </div>

              {/* Capital Addition Form */}
              {selectedBankForAction !== null && (
                <div className="mt-4 p-4 bg-blue-50 border-2 border-blue-300 rounded-xl">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                      <DollarSign size={18} className="text-white" />
                    </div>
                    <p className="text-sm font-semibold text-gray-800">
                      Add capital to Bank {selectedBankForAction + 1}
                    </p>
                  </div>
                  
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={capitalAmount}
                      onChange={(e) => setCapitalAmount(Number(e.target.value))}
                      className="w-20 px-3 py-2.5 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center font-semibold"
                      placeholder="0"
                    />
                    
                    <button
                      onClick={() => addCapital(selectedBankForAction, capitalAmount)}
                      className="flex items-center gap-2 px-5 py-2.5 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-semibold"
                    >
                      <Plus size={18} />
                      <span>Add</span>
                    </button>
                    
                    <button
                      onClick={() => setSelectedBankForAction(null)}
                      className="px-5 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BackendSimulationPanel;
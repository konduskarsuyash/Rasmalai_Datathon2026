import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, Trash2, DollarSign } from 'lucide-react';

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
      // Prepare node parameters from institutions
      const nodeParameters = institutions
        .filter(inst => inst.type === 'bank' && !inst.isMarket)
        .map(inst => ({
          initial_capital: inst.capital || 100,
          target_leverage: inst.target || 3.0,
          risk_factor: inst.risk || 0.2,
        }));

      const payload = {
        num_banks: nodeParameters.length || 5,
        num_steps: 30,
        node_parameters: nodeParameters,
        connection_density: 0.2,
        use_featherless: false,
      };

      setIsRunning(true);
      setIsPaused(false);
      setStats({ defaults: 0, totalEquity: 0, activeTransactions: 0 });

      // Start the simulation via fetch with readable stream
      const response = await fetch('http://localhost:8000/api/interactive/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        alert(`Failed to start simulation: ${error.detail}`);
        setIsRunning(false);
        return;
      }

      // Read the SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      const readStream = async () => {
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            setIsRunning(false);
            break;
          }
          
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete SSE messages
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || ''; // Keep incomplete message
          
          for (const message of messages) {
            if (message.startsWith('data: ')) {
              try {
                const data = JSON.parse(message.substring(6));
                handleEvent(data);
              } catch (err) {
                console.error('Failed to parse SSE data:', err);
              }
            }
          }
        }
      };

      readStream().catch(err => {
        console.error('Stream reading error:', err);
        setIsRunning(false);
      });
      
      // Store reader for cleanup
      readerRef.current = reader;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleEvent(data);
        } catch (err) {
          console.error('Failed to parse SSE data:', err);
        }
      };

      eventSource.onerror = () => {
        console.error('SSE connection error');
        setIsRunning(false);
        eventSource.close();
      };

    } catch (error) {
      console.error('Failed to start simulation:', error);
      alert('Failed to start simulation');
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
    <div className="bg-white p-6 rounded-lg shadow-lg border border-gray-200 relative z-50">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Backend Simulation Control</h2>

      {/* Control Buttons */}
      <div className="flex gap-3 mb-6">
        {!isRunning && (
          <button
            onClick={startSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
          >
            <Play size={18} />
            Start Simulation
          </button>
        )}

        {isRunning && !isPaused && (
          <button
            onClick={pauseSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-all"
          >
            <Pause size={18} />
            Pause
          </button>
        )}

        {isRunning && isPaused && (
          <button
            onClick={resumeSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
          >
            <Play size={18} />
            Resume
          </button>
        )}

        {isRunning && (
          <button
            onClick={stopSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all"
          >
            <Square size={18} />
            Stop
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">Current Step</p>
          <p className="text-2xl font-bold text-blue-700">{currentStep}</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-gray-600">Defaults</p>
          <p className="text-2xl font-bold text-red-700">{stats.defaults}</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-gray-600">Total Capital</p>
          <p className="text-2xl font-bold text-green-700">${stats.totalEquity}M</p>
        </div>
      </div>

      {/* Paused Controls */}
      {isPaused && (
        <div className="border border-yellow-300 bg-yellow-50 p-4 rounded-lg mb-4">
          <h3 className="font-bold text-yellow-800 mb-3">⏸️ Simulation Paused - Modify Network</h3>
          
          {/* Bank Actions */}
          <div className="space-y-2">
            <p className="text-sm text-gray-700 font-medium">Select a bank to modify:</p>
            <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
              {banks.map((bank, idx) => (
                <div key={bank.id} className="flex items-center gap-2">
                  <button
                    onClick={() => setSelectedBankForAction(idx)}
                    className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded hover:bg-blue-50 text-sm"
                  >
                    Bank {idx + 1} (${bank.capital}M)
                  </button>
                  <button
                    onClick={() => deleteBank(idx)}
                    className="p-2 bg-red-100 text-red-600 rounded hover:bg-red-200"
                    title="Delete Bank"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>

            {selectedBankForAction !== null && (
              <div className="mt-3 p-3 bg-white border border-blue-300 rounded">
                <p className="text-sm font-medium mb-2">Add capital to Bank {selectedBankForAction + 1}:</p>
                <div className="flex gap-2">
                  <textarea
                    value={String(capitalAmount || '')}
                    onChange={(e) => {
                      e.stopPropagation();
                      const value = e.target.value;
                      if (value === '' || !isNaN(value)) {
                        setCapitalAmount(value === '' ? 0 : Number(value));
                      }
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded resize-none"
                    placeholder="Amount ($M)"
                    rows="1"
                    onClick={(e) => e.stopPropagation()}
                    onMouseDown={(e) => e.stopPropagation()}
                    onMouseUp={(e) => e.stopPropagation()}
                    onKeyDown={(e) => e.stopPropagation()}
                  />
                  <button
                    onClick={() => addCapital(selectedBankForAction, capitalAmount)}
                    className="flex items-center gap-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    <DollarSign size={16} />
                    Add
                  </button>
                  <button
                    onClick={() => setSelectedBankForAction(null)}
                    className="px-3 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status */}
      <div className="text-sm text-gray-600">
        {!isRunning && <p>⚪ Ready to start</p>}
        {isRunning && !isPaused && <p className="text-green-600">🟢 Running simulation...</p>}
        {isRunning && isPaused && <p className="text-yellow-600">🟡 Paused - modify network above</p>}
      </div>
    </div>
  );
};

export default BackendSimulationPanel;

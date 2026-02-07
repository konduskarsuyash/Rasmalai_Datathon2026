# Node Parameters Feature

## Overview

The backend simulation now supports **per-node (per-bank) parameters**, allowing you to customize individual banks in the playground and use those specific configurations in the simulation.

## What's New

### Backend Changes

1. **New Schema: `NodeParameters`** (`backend/app/schemas/simulation.py`)
   - `node_id`: Optional identifier for the node
   - `initial_capital`: Starting capital for the bank
   - `initial_liquidity`: Starting cash/liquidity
   - `risk_level`: Risk tolerance (0-1)
   - `strategy`: Strategy type ("conservative", "balanced", "aggressive")
   - `lending_amount`: Per-action lending amount
   - `investment_amount`: Per-action investment amount

2. **Updated `SimulationRunRequest`**
   - Added `node_parameters`: Optional list of node configurations
   - Added `connection_density`: Controls interbank connection density

3. **New `BankConfig` Class** (`backend/app/core/simulation_v2.py`)
   - Internal configuration object for bank initialization
   - Maps node parameters to bank settings

4. **Enhanced `create_banks` Function** (`backend/app/core/bank.py`)
   - Now accepts optional `bank_configs` parameter
   - Uses custom configs when provided
   - Falls back to default randomization for banks without configs

5. **Updated Simulation Logic**
   - Per-bank lending and investment amounts
   - Configurable connection density
   - Strategy-based target settings

### Frontend Changes

1. **Enhanced `BackendSimulationPanel`** (`frontend/src/components/BackendSimulationPanel.jsx`)
   - New toggle: "Use Playground Nodes"
   - When enabled, sends all playground institutions as node parameters
   - Automatically maps playground properties to backend schema
   - Shows count of nodes being used

2. **Integration with Playground**
   - Playground institutions now directly influence simulation
   - Capital, liquidity, risk, and strategy are respected
   - Node count matches playground nodes when toggle is enabled

## API Usage

### Basic Simulation (No Node Parameters)

```json
POST /api/simulation/run
{
  "num_banks": 20,
  "num_steps": 30,
  "use_featherless": false,
  "verbose": false,
  "lending_amount": 10.0,
  "investment_amount": 10.0,
  "connection_density": 0.2
}
```

### Custom Node Parameters

```json
POST /api/simulation/run
{
  "num_banks": 3,
  "num_steps": 30,
  "use_featherless": false,
  "verbose": false,
  "connection_density": 0.3,
  "node_parameters": [
    {
      "node_id": "bank1",
      "initial_capital": 200.0,
      "initial_liquidity": 100.0,
      "risk_level": 0.1,
      "strategy": "conservative",
      "lending_amount": 15.0,
      "investment_amount": 5.0
    },
    {
      "node_id": "bank2",
      "initial_capital": 150.0,
      "initial_liquidity": 75.0,
      "risk_level": 0.3,
      "strategy": "balanced",
      "lending_amount": 10.0,
      "investment_amount": 10.0
    },
    {
      "node_id": "bank3",
      "initial_capital": 100.0,
      "initial_liquidity": 40.0,
      "risk_level": 0.5,
      "strategy": "aggressive",
      "lending_amount": 5.0,
      "investment_amount": 20.0
    }
  ]
}
```

## Frontend Usage

### In the Playground

1. **Create Nodes**: Add banks, exchanges, and clearinghouses in the playground
2. **Configure Properties**: Set capital, liquidity, risk, and strategy for each node
3. **Toggle Feature**: In the Backend Simulation panel, enable "Use Playground Nodes"
4. **Run Simulation**: Click "Run simulation" - the backend will use your playground configuration

### Node Property Mapping

| Playground Property | Backend Parameter | Description |
|---------------------|-------------------|-------------|
| `capital` | `initial_capital` | Starting capital for the bank |
| `liquidity` | `initial_liquidity` | Starting cash/liquidity |
| `risk` | `risk_level` | Risk tolerance (0-1) |
| `strategy` | `strategy` | "conservative", "balanced", or "aggressive" |
| N/A | `lending_amount` | Fixed at 10.0 (can be customized) |
| N/A | `investment_amount` | Fixed at 10.0 (can be customized) |

## Strategy Impact

Different strategies affect bank behavior through target settings:

### Conservative Strategy
- **Target Leverage**: 2.0 (lower)
- **Target Liquidity**: 0.4 (higher)
- **Target Market Exposure**: 0.1 (lower)
- **Behavior**: Prioritizes safety and liquidity

### Balanced Strategy
- **Target Leverage**: 3.0 (medium)
- **Target Liquidity**: 0.3 (medium)
- **Target Market Exposure**: 0.2 (medium)
- **Behavior**: Balances growth and safety

### Aggressive Strategy
- **Target Leverage**: 4.5 (higher)
- **Target Liquidity**: 0.15 (lower)
- **Target Market Exposure**: 0.35 (higher)
- **Behavior**: Prioritizes growth and returns

## Testing

Run the test suite to verify functionality:

```bash
cd backend
python test_node_params.py
```

This test covers:
1. Basic simulation without node parameters
2. Full custom node parameters
3. Mixed scenario (partial custom + default banks)

## Examples

### Example 1: Conservative Banks Network

Test financial crisis resilience with all conservative banks:

```json
{
  "num_steps": 50,
  "node_parameters": [
    {"initial_capital": 200, "initial_liquidity": 120, "risk_level": 0.1, "strategy": "conservative"},
    {"initial_capital": 180, "initial_liquidity": 100, "risk_level": 0.12, "strategy": "conservative"},
    {"initial_capital": 190, "initial_liquidity": 110, "risk_level": 0.08, "strategy": "conservative"}
  ],
  "connection_density": 0.3
}
```

### Example 2: Mixed Risk Network

Simulate contagion from high-risk to low-risk banks:

```json
{
  "num_steps": 50,
  "node_parameters": [
    {"initial_capital": 250, "initial_liquidity": 150, "risk_level": 0.05, "strategy": "conservative"},
    {"initial_capital": 150, "initial_liquidity": 80, "risk_level": 0.3, "strategy": "balanced"},
    {"initial_capital": 100, "initial_liquidity": 40, "risk_level": 0.6, "strategy": "aggressive"},
    {"initial_capital": 80, "initial_liquidity": 30, "risk_level": 0.7, "strategy": "aggressive"}
  ],
  "connection_density": 0.5
}
```

### Example 3: Liquidity Stress Test

Test liquidity crisis with low initial liquidity:

```json
{
  "num_steps": 30,
  "node_parameters": [
    {"initial_capital": 200, "initial_liquidity": 20, "risk_level": 0.3, "strategy": "balanced"},
    {"initial_capital": 180, "initial_liquidity": 15, "risk_level": 0.35, "strategy": "balanced"},
    {"initial_capital": 190, "initial_liquidity": 18, "risk_level": 0.32, "strategy": "balanced"}
  ],
  "connection_density": 0.4
}
```

## Implementation Details

### Backend Flow

1. Frontend sends `node_parameters` array in simulation request
2. Router (`simulation.py`) converts to `BankConfig` objects
3. `SimulationConfig` stores bank configs
4. `create_banks()` uses configs to initialize banks with specific properties
5. Simulation loop uses per-bank lending/investment amounts
6. Results reflect the customized bank configurations

### Key Files Modified

- `backend/app/schemas/simulation.py` - New schemas
- `backend/app/routers/simulation.py` - Request handling
- `backend/app/core/simulation_v2.py` - Simulation logic
- `backend/app/core/bank.py` - Bank initialization
- `backend/app/core/__init__.py` - Exports
- `frontend/src/components/BackendSimulationPanel.jsx` - UI controls
- `frontend/src/components/FinancialNetworkPlayground.jsx` - Data passing

## Future Enhancements

Potential improvements:
- Per-node connection specifications (custom edges)
- Dynamic lending/investment amounts based on node state
- Node-specific shock scenarios
- Custom risk models per strategy type
- Visualization of per-node parameters in results
- Save/load node configurations
- Template node configurations for common scenarios

## Troubleshooting

### Issue: Simulation ignores node parameters

**Solution**: Check that:
1. `node_parameters` array is present in request body
2. Each node has required fields: `initial_capital`, `initial_liquidity`, `risk_level`, `strategy`
3. Frontend toggle "Use Playground Nodes" is enabled

### Issue: Different results despite same parameters

**Explanation**: The simulation includes stochastic elements:
- Random counterparty selection
- Random market selection
- Initial interbank network is randomized
- ML policy includes some randomness

**Solution**: For reproducible results, you'd need to add a random seed parameter (future enhancement)

### Issue: All banks default quickly

**Possible causes**:
1. Initial liquidity too low
2. Connection density too high (contagion spreads fast)
3. Aggressive strategies with high risk levels
4. Lending amounts exceed liquidity

**Solution**: Adjust node parameters to increase stability:
- Increase `initial_liquidity`
- Reduce `connection_density`
- Use "conservative" or "balanced" strategies
- Reduce `lending_amount` and `investment_amount`

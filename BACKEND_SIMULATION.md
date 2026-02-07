# Backend-Driven Interactive Simulation

## Overview

The simulation has been completely redesigned to run **entirely in the backend** with full ML/financial logic, while providing **real-time interactive controls** from the frontend.

## Architecture

### Backend (`/api/interactive`)

- **`POST /start`**: Start an interactive simulation
  - Accepts node parameters (capital, target leverage, risk factor)
  - Streams events via Server-Sent Events (SSE)
  - Runs sophisticated ML-based decision logic
  
- **`POST /control`**: Send commands to running simulation
  - `pause`: Pause the simulation
  - `resume`: Resume from pause
  - `stop`: Stop completely
  - `delete_bank`: Remove a bank during pause
  - `add_capital`: Add capital to a bank during pause
  
- **`GET /status`**: Get current simulation status

### Frontend (`BackendSimulationPanel`)

- **Start/Pause/Resume/Stop** controls
- **Real-time statistics** (step, defaults, total capital)
- **Modify network during pause**:
  - Add capital to any bank
  - Delete banks
- **Live event streaming** with visual updates

## Bank Actions (Three Core Strategies)

Each bank chooses one of three actions per timestep based on ML policy:

1. **LEND** (`INCREASE_LENDING`): Lend money to another bank
   - Increases interbank connections
   - Provides liquidity to borrower
   - Earns interest over time

2. **BORROW** (`DECREASE_LENDING`): Reduce lending (call back loans)
   - Increases own liquidity
   - Reduces exposure to counterparty risk

3. **INVEST** (`INVEST_MARKET` / `DIVEST_MARKET`): Invest in market indices
   - `BANK_INDEX`: Bank sector index
   - `FIN_SERVICES`: Financial services index
   - **Profit booking**: Every 5 steps, banks automatically book profits/losses based on market returns
   - Returns are dynamic based on market flows

## Event Types

### Simulation Events (SSE Stream)

- `init`: Initial network state (banks, markets, connections)
- `step_start`: Beginning of timestep
- `transaction`: Bank action (LEND/BORROW/INVEST/DIVEST)
- `profit_booking`: Bank books profit from investments
- `default`: Bank defaults (equity < 0)
- `cascade`: Default triggers cascade
- `step_end`: End of timestep with full state snapshot
- `complete`: Simulation finished

### Control Events

- `paused`: Simulation paused
- `resumed`: Simulation resumed
- `stopped`: Simulation stopped
- `bank_deleted`: Bank removed
- `capital_added`: Capital injected into bank

## Usage

1. **Setup Network**: Add banks in playground with parameters:
   - Capital (initial equity)
   - Target (target leverage ratio)
   - Risk (risk factor 0-1)

2. **Start Simulation**: Click "Start Simulation"
   - Backend generates interbank connections
   - ML policy decides actions each timestep
   - Markets evolve based on flows

3. **Monitor**: Watch real-time:
   - Transaction animations
   - Bank dashboards (click banks)
   - Market dashboards (click markets)
   - Live activity feed

4. **Pause & Modify** (Optional):
   - Click "Pause"
   - Add capital to struggling banks
   - Delete failed banks
   - Click "Resume"

## Key Differences from Frontend Simulation

### ✅ Backend (Current)
- Sophisticated ML decision-making
- Proper financial modeling (balance sheets, leverage, liquidity)
- Market dynamics with price discovery
- Profit booking from investments
- Cascade propagation
- Scalable to 100+ banks

### ❌ Frontend (Old)
- Simple hardcoded logic
- No proper balance sheet accounting
- Static decision rules
- No profit realization
- Limited to ~20 banks

## Technical Details

### Profit Booking Logic

Every 5 timesteps, each bank:
1. Checks investment positions in each market
2. Calculates profit = invested_amount × market_return
3. Books profit to cash
4. Logs profit_booking event

### Bank Decision Process

For each bank at each timestep:
1. **Observe**: Gather local state (equity, cash, leverage, neighbor defaults)
2. **Prioritize**: ML model suggests strategic priority (PROFIT/LIQUIDITY/STABILITY)
3. **Decide**: Policy network selects action (LEND/BORROW/INVEST/DIVEST/HOLD)
4. **Execute**: Update balance sheet, log transaction
5. **Check**: Detect defaults, propagate cascades

### Market Dynamics

Markets use flow-based pricing:
- Net inflow → price increases
- Net outflow → price decreases
- Sensitivity: 0.001 (1 dollar moves price by 0.001)
- Returns calculated from initial price

## Files Modified

### Backend
- `backend/app/routers/interactive_simulation.py` (NEW)
- `backend/app/main.py` (added router)
- `backend/app/core/bank.py` (added `book_investment_profit`)

### Frontend
- `frontend/src/components/BackendSimulationPanel.jsx` (NEW)
- `frontend/src/components/FinancialNetworkPlayground.jsx` (integrated new panel)

## Future Enhancements

- [ ] Adjustable profit booking frequency
- [ ] Interest payments on loans
- [ ] Loan repayment schedules
- [ ] Dynamic connection creation/removal
- [ ] Risk-weighted asset calculations
- [ ] Regulatory capital requirements
- [ ] Central bank interventions

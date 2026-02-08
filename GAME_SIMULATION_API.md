# Game-Theoretic Financial Simulation API

Complete implementation of step-based, stateful financial network simulation with game theory, margin calls, clearing system, and contagion dynamics.

## 🎯 Architecture Overview

The system implements a **6-layer architecture** with **step-by-step execution** control:

```
Layer 1: User Control → Configuration & Commands
Layer 2: Orchestrator → Simulation State Management
Layer 3: Strategy/AI → Bank Decision Making
Layer 4: Network → Interbank Connections & Flows
Layer 5: Clearing → Margin Calls & Forced Liquidation
Layer 6: Output → Metrics & Events
```

## 🔄 Simulation Lifecycle

### State Machine

```
UNINITIALIZED → INITIALIZED → RUNNING → PAUSED → RUNNING → STOPPED/COMPLETED
```

1. **UNINITIALIZED**: No simulation exists
2. **INITIALIZED**: Simulation created, banks added, connections made
3. **RUNNING**: Step-by-step execution in progress
4. **PAUSED**: Execution frozen, can resume
5. **STOPPED**: User-terminated
6. **COMPLETED**: All steps executed

## 📡 API Endpoints

### Simulation Control

#### Initialize Simulation

```bash
POST /api/simulation/init
```

Creates simulation context WITHOUT starting execution.

```json
{
  "network": {
    "num_banks": 20,
    "connection_density": 0.2
  },
  "simulation": {
    "steps": 30,
    "use_featherless": false,
    "verbose_logging": false
  },
  "market": {
    "price_sensitivity": 0.002,
    "volatility": 0.03,
    "momentum": 0.1
  }
}
```

**Response:**

```json
{
  "session_id": "uuid-string",
  "state": "INITIALIZED",
  "total_steps": 30,
  "banks_count": 0
}
```

#### Start Simulation

```bash
POST /api/simulation/start
```

Locks inputs and moves to RUNNING state.

#### Execute Step

```bash
POST /api/simulation/step
```

Executes **single step** with 9-phase lifecycle:

1. **step_start**: Initialize step
2. **information_update**: Update bank visibility
3. **strategy_selection**: Banks choose actions
4. **action_execution**: Execute chosen actions
5. **margin_and_constraints**: Check margin requirements
6. **settlement_and_clearing**: Settle transactions
7. **market_update**: Update prices based on flows
8. **contagion_check**: Detect defaults, propagate cascade
9. **step_end**: Finalize metrics

**Response:**

```json
{
  "step": 12,
  "events": ["transaction", "margin_call", "default"],
  "defaults": ["BANK_7", "BANK_3"],
  "system_liquidity": 0.42,
  "state": "RUNNING"
}
```

#### Pause / Resume / Stop

```bash
POST /api/simulation/pause
POST /api/simulation/resume
POST /api/simulation/stop
```

#### Get Status

```bash
GET /api/simulation/status
```

### Bank (Node) APIs

#### Create Bank

```bash
POST /api/banks
```

```json
{
  "capital": 100000000,
  "target_leverage": 3.0,
  "risk_factor": 0.2,
  "interbank_rate": 0.025,
  "collateral_haircut": 0.15,
  "reserve_requirement": 0.1,
  "objective": "SURVIVAL",
  "info_visibility": 0.6
}
```

**Objectives**: `SURVIVAL`, `GROWTH`, `AGGRESSIVE`

**Response**: Full bank state with calculated balance sheet

#### Update Bank (Runtime Safe)

```bash
PUT /api/banks/{bank_id}
```

Allowed updates: `risk_factor`, `target_leverage`, `objective`

#### Get Bank State

```bash
GET /api/banks/{bank_id}
```

Returns complete balance sheet + status

#### List All Banks

```bash
GET /api/banks
```

### Connection (Edge) APIs

#### Create Connection

```bash
POST /api/connections
```

```json
{
  "from_bank": "BANK_1",
  "to_bank": "BANK_7",
  "type": "credit",
  "exposure": 20000000
}
```

**Types**: `credit`, `lending`, `exposure`

#### Get Network

```bash
GET /api/network
```

Returns complete graph: nodes + edges with weights

### Strategy & Game Theory

#### Evaluate Strategy

```bash
POST /api/strategy/evaluate
```

```json
{
  "bank_id": "BANK_3",
  "observed_state": {
    "local_liquidity": 0.32,
    "neighbor_defaults": 1,
    "market_trend": -0.04
  }
}
```

**Response:**

```json
{
  "bank_id": "BANK_3",
  "chosen_action": "HOARD_CASH",
  "confidence": 0.78
}
```

**Actions**:

- `INVEST_MARKET`: Buy market assets
- `DIVEST_MARKET`: Sell market assets
- `LEND_INTERBANK`: Lend to other banks
- `BORROW_INTERBANK`: Borrow from banks
- `HOARD_CASH`: Preserve liquidity
- `REDUCE_LEVERAGE`: Pay down debt

### Action Execution

#### Execute Action

```bash
POST /api/actions/execute
```

```json
{
  "bank_id": "BANK_3",
  "action": "INVEST_MARKET"
}
```

Manually trigger bank action (normally auto-selected in step lifecycle)

### Margin & Clearing

#### Check Margin

```bash
POST /api/margin/check
```

```json
{
  "bank_id": "BANK_5",
  "market_price_change": -0.06
}
```

Calculates variation margin requirement

#### Issue Margin Call

```bash
POST /api/margin/call
```

#### Force Liquidation

```bash
POST /api/liquidation/force
```

Fire sale of bank investments, impacts market price

### Market APIs

#### Get Market State

```bash
GET /api/market
```

**Response:**

```json
{
  "BANK_INDEX": {
    "price": 92.4,
    "volatility": 0.031,
    "momentum": -0.015,
    "net_flow": -45000000
  }
}
```

#### Update Market (Manual)

```bash
POST /api/market/update
```

### Default & Contagion

#### Check Defaults

```bash
POST /api/defaults/check
```

Checks all banks for default conditions:

- Equity <= 0
- Liquidity ratio < 5%

#### Propagate Cascade

```bash
POST /api/cascade/propagate
```

```json
"BANK_7"
```

Manually trigger contagion cascade from defaulted bank

### Interventions (Runtime Controls)

#### Capital Injection

```bash
POST /api/intervention/add_capital
```

```json
{
  "bank_id": "BANK_9",
  "amount": 50000000
}
```

Regulatory intervention - inject capital

#### Financial Crisis

```bash
POST /api/intervention/financial_crisis
```

System-wide shock:

- 15% price drop
- 30% liquidity drain
- 1.5x risk multiplier

### Observability

#### Get Events

```bash
GET /api/events
```

Stream of all simulation events with timestamps

#### Get Metrics

```bash
GET /api/metrics
```

**Response:**

```json
{
  "total_defaults": 4,
  "default_rate": 0.2,
  "surviving_banks": 16,
  "total_equity": 1200000000,
  "cascade_events": 3,
  "system_collapsed": false
}
```

## 🎮 Frontend Integration

### Game Simulation Panel

New `GameSimulationPanel` component provides full control interface:

```jsx
import GameSimulationPanel from "./components/GameSimulationPanel";

<GameSimulationPanel />;
```

**Features:**

- Initialize with custom parameters
- Start/Pause/Resume/Stop controls
- Single-step execution
- Auto-step mode (continuous execution)
- Real-time metrics display
- Event visualization
- Crisis intervention button

### API Client

```javascript
import * as gameApi from "./api/gameSimulation";

// Initialize
const result = await gameApi.initSimulation({
  network: { num_banks: 20, connection_density: 0.2 },
  simulation: { steps: 30, use_featherless: false },
  market: { price_sensitivity: 0.002, volatility: 0.03 },
});

// Create banks
const bank = await gameApi.createBank({
  capital: 100_000_000,
  target_leverage: 3.0,
  risk_factor: 0.2,
  objective: "SURVIVAL",
});

// Create connections
await gameApi.createConnection({
  from_bank: "BANK_1",
  to_bank: "BANK_2",
  type: "credit",
  exposure: 20_000_000,
});

// Start simulation
await gameApi.startSimulation();

// Execute steps
const stepResult = await gameApi.executeStep();
console.log(stepResult.events); // ["transaction", "margin_call"]

// Get metrics
const metrics = await gameApi.getMetrics();
```

## 🔥 Key Features

### Game-Theoretic Behavior

Banks make strategic decisions based on:

- **Objective**: SURVIVAL (defensive), GROWTH (balanced), AGGRESSIVE (risky)
- **Information visibility**: Partial network observability
- **Liquidity pressure**: Margin calls force fire sales
- **Contagion risk**: Neighbor defaults reduce liquidity

### Realistic Clearing System

- **Variation margin**: Calculated from market exposure × price change
- **Margin calls**: Triggered when insufficient cash reserves
- **Fire sales**: Forced liquidation impacts market prices (cascades)
- **Collateral haircuts**: 15% haircut on secured lending

### Contagion Dynamics

1. Bank defaults when equity ≤ 0 OR liquidity < 5%
2. Connected banks lose liquidity (exposure × 50%)
3. Fire sales drop market prices
4. Other banks face margin calls
5. **Cascade loop**: Steps 1-4 repeat

### System Collapse Detection

System collapsed when:

- Surviving banks < 30% of initial
- Automatically flagged in metrics

## 📊 Example Workflow

```bash
# 1. Initialize
POST /api/simulation/init
{ "network": {"num_banks": 10}, "simulation": {"steps": 30} }

# 2. Create banks
for i in 1..10:
  POST /api/banks
  { "capital": 100M, "target_leverage": 3.0, "objective": random() }

# 3. Create connections
POST /api/connections (random pairs with density 0.2)

# 4. Start
POST /api/simulation/start

# 5. Execute steps
for step in 1..30:
  POST /api/simulation/step
  → System executes 9-phase lifecycle
  → Returns events, defaults, liquidity

  # Optional interventions
  if liquidity < 0.3:
    POST /api/intervention/add_capital

  if step == 15:
    POST /api/intervention/financial_crisis

# 6. Stop and get final metrics
POST /api/simulation/stop
GET /api/metrics
```

## 🧪 Testing

### Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Visit: http://localhost:8000/docs (Swagger UI)

### Frontend

```bash
cd frontend
npm run dev
```

Visit: http://localhost:5173

Navigate to Financial Network Playground → see GameSimulationPanel in left sidebar

## 🔧 Architecture Files

- **Backend:**
  - `backend/app/core/stateful_simulation.py` - Stateful simulation engine
  - `backend/app/routers/game_simulation.py` - All API endpoints
  - `backend/app/main.py` - FastAPI app with router registration

- **Frontend:**
  - `frontend/src/api/gameSimulation.js` - API client
  - `frontend/src/components/GameSimulationPanel.jsx` - Control panel UI
  - `frontend/src/components/FinancialNetworkPlayground.jsx` - Main playground (includes panel)

## 🎯 Design Principles

1. **Stateful**: Backend maintains simulation state across requests
2. **Step-based**: Granular control, single-step execution
3. **Observable**: Complete event stream and metrics
4. **Interventable**: Runtime controls for testing scenarios
5. **Realistic**: Margin calls, fire sales, contagion cascades
6. **Game-theoretic**: Strategic bank behavior based on objectives

## 🚀 Next Steps

- Connect to **Featherless AI** for ML-driven strategy selection
- Visualize **network graph** with real-time default propagation
- Add **regulatory scenarios** (capital requirements, stress tests)
- Implement **portfolio optimization** for bank strategies
- Add **historical replay** of simulation events

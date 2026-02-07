# Real-Time Backend Simulation - Architecture Explained

## ⚠️ Important: This is NOT a Replay!

The simulation is **100% real-time** and runs entirely in the **backend** via **Server-Sent Events (SSE)**. Here's exactly how it works:

## How It Actually Works

### 1. You Click "Start Simulation"

```
Frontend → POST /api/interactive/start
Backend  → Starts Python generator function
Backend  → Opens SSE stream (keeps connection open)
```

### 2. Backend Runs Simulation **Live**

```python
for t in range(30):  # Each timestep
    # Banks make decisions RIGHT NOW
    for bank in banks:
        action = ML_policy.decide()  # Real ML decision
        bank.execute_action()        # Happens NOW
        
        # Stream event IMMEDIATELY to frontend
        yield f"data: {json.dumps(transaction_event)}\n\n"
        await asyncio.sleep(0.4)  # Small delay for visualization
    
    # Calculate interest NOW
    for loan in loans:
        interest = loan * 0.05
        borrower.pay_interest(interest)
        yield f"data: {json.dumps(interest_event)}\n\n"
    
    # Process repayments NOW
    for loan in loans:
        repayment = loan * 0.1
        borrower.repay(repayment)
        yield f"data: {json.dumps(repayment_event)}\n\n"
```

### 3. Frontend Receives Events **As They Happen**

```javascript
// SSE stream reading - receives events LIVE
const reader = response.body.getReader();
while (true) {
    const { value } = await reader.read();
    // Parse event that JUST happened in backend
    const event = JSON.parse(value);
    
    // Update UI IMMEDIATELY
    if (event.type === 'transaction') {
        animateParticle(from, to);  // Show RIGHT NOW
    }
    if (event.type === 'interest_payment') {
        animateInterest(from, to);  // Show RIGHT NOW
    }
}
```

## Features You Mentioned - Already Implemented!

### ✅ Real-Time (NOT Replay)
- Backend streams events via SSE as they happen
- Frontend receives and displays immediately
- No recording/playback - it's live

### ✅ Pause/Resume
```javascript
// Click "Pause"
POST /api/interactive/control { command: "pause" }

// Backend STOPS at current step
while (is_paused) {
    await sleep(0.5)
    // Check for commands
}

// Click "Resume"  
POST /api/interactive/control { command: "resume" }
// Backend CONTINUES from where it stopped
```

### ✅ Modify Network During Pause
```javascript
// During pause:
// 1. Add capital to bank
POST /api/interactive/control {
    command: "add_capital",
    bank_id: 2,
    amount: 100
}
// Backend IMMEDIATELY updates bank.cash += 100

// 2. Delete bank
POST /api/interactive/control {
    command: "delete_bank",
    bank_id: 3
}
// Backend marks bank.is_defaulted = True

// 3. Click Resume
// Simulation continues with NEW state
```

### ✅ Interest Payments (Just Added!)
```python
# Every timestep, for each loan:
interest = loan_amount * 0.05  # 5% per step
borrower.cash -= interest
lender.cash += interest

# Stream to frontend
yield f"data: {{type: 'interest_payment', ...}}\n\n"
```

### ✅ Loan Repayments (Just Added!)
```python
# Every timestep, for each loan:
repayment = min(loan * 0.1, borrower.cash * 0.3)  # 10% of principal
borrower.cash -= repayment
lender.cash += repayment
loan_balance -= repayment

# Stream to frontend
yield f"data: {{type: 'loan_repayment', ...}}\n\n"
```

### ✅ Real-Time Dashboards
```javascript
// As events arrive:
case 'step_end':
    historicalData.push(event)  // Store step data
    // Dashboard auto-updates via React state
    // Charts redraw with new data
    // Transaction logs append new entries
```

### ✅ Temporary Session Storage
```python
# Backend stores in-memory during simulation:
ACTIVE_SIMULATION = {
    "state": SimulationState(),  # Full state
    "is_running": True,
    "is_paused": False,
}

# Frontend stores for current session:
const [historicalData, setHistoricalData] = useState([]);
const [allTransactions, setAllTransactions] = useState([]);
```

## Event Flow Diagram

```
TIME 0s: User clicks "Start"
    ↓
TIME 0.1s: Backend creates network
    → SSE: {type: 'init', banks: [...], markets: [...]}
    → Frontend: Draws initial network
    ↓
TIME 1s: Backend step 0 starts
    → SSE: {type: 'step_start', step: 0}
    → Frontend: Updates step counter
    ↓
TIME 1.2s: Bank 0 lends to Bank 1
    → Backend: Updates balance sheets NOW
    → SSE: {type: 'transaction', action: 'LEND', ...}
    → Frontend: Animates particle Bank0 → Bank1
    ↓
TIME 1.6s: Bank 2 invests in market
    → Backend: Updates investments NOW
    → SSE: {type: 'transaction', action: 'INVEST', ...}
    → Frontend: Animates particle Bank2 → Market
    ↓
TIME 2s: Interest payments processed
    → Backend: Calculates interest NOW
    → SSE: {type: 'interest_payment', ...}
    → Frontend: Shows interest flow animation
    ↓
TIME 2.2s: Loan repayments processed
    → Backend: Updates loan balances NOW
    → SSE: {type: 'loan_repayment', ...}
    → Frontend: Shows repayment animation
    ↓
TIME 2.5s: Step 0 ends
    → SSE: {type: 'step_end', bank_states: [...], market_states: [...]}
    → Frontend: Updates all dashboards, charts, logs
    ↓
TIME 3s: Step 1 starts...
    (REPEAT FOR 30 STEPS)
```

## What Makes It Real-Time

1. **No Pre-Computation**: Backend doesn't run simulation then send results. It runs AND sends simultaneously.

2. **Async Generator**: Python `async def` with `yield` streams events as they're produced:
   ```python
   async def simulation_generator():
       for step in steps:
           event = compute_event()  # Happens NOW
           yield f"data: {json.dumps(event)}\n\n"  # Sent IMMEDIATELY
   ```

3. **SSE (Server-Sent Events)**: Browser keeps HTTP connection open, receives data as it arrives:
   ```javascript
   const response = await fetch('/api/interactive/start');
   const reader = response.body.getReader();
   // Stream stays open, data arrives in real-time
   ```

4. **No Recording**: Backend doesn't store full simulation results. It generates events on-the-fly and streams them.

## Why It Might FEEL Like Replay

The small `asyncio.sleep(0.4)` delays between transactions are for **visualization pacing**, not because it's pre-recorded. Without them, 100 transactions would happen in 10ms and you'd see nothing!

## Proof It's Real-Time

1. **Check Backend Terminal**: You'll see `[INTERACTIVE SIM] Starting step X` messages appearing in real-time as simulation runs.

2. **Click Pause Mid-Simulation**: Backend STOPS immediately at current step (not at end of pre-recorded data).

3. **Add Capital During Pause**: The change takes effect IMMEDIATELY when you resume (not after "replay" finishes).

4. **Network Tab**: Open browser DevTools → Network. You'll see `/api/interactive/start` request stays "pending" for 30+ seconds while streaming data.

## Summary

✅ **Real-time backend simulation** - Not replay
✅ **SSE streaming** - Events sent as they happen  
✅ **Pause/Resume** - Working
✅ **Modify during pause** - Working (add capital, delete banks)
✅ **Interest payments** - Just added (5% per step)
✅ **Loan repayments** - Just added (10% per step)
✅ **Real-time dashboards** - Updates as events arrive
✅ **Session storage** - Temporary in-memory state

**The system is exactly what you described!** 🎉

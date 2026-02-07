# Testing the Backend-Driven Simulation

## Prerequisites

1. Backend running: `uvicorn app.main:app --reload` (in `backend/` directory)
2. Frontend running: `npm run dev` (in `frontend/` directory)

## Test Steps

### 1. Basic Simulation

1. Open http://localhost:5173
2. Add 5-10 banks with varying parameters:
   - Capital: 100-1000
   - Target: 2.0-5.0
   - Risk: 0.1-0.8
3. Click "Start Simulation"
4. Watch:
   - Transaction animations (particles between nodes)
   - Live statistics (step, defaults, capital)
   - Banks taking actions (lending, investing)

### 2. Interactive Controls

1. During simulation, click "Pause"
2. Verify simulation stops but UI remains responsive
3. Select a bank and add capital (e.g., $100M)
4. Verify capital_added notification
5. Click "Resume" and watch simulation continue
6. Click "Stop" to end simulation

### 3. Bank Actions Verification

Banks should exhibit three types of actions:

**LEND (INCREASE_LENDING)**:
- Look for transactions between banks
- Particle animation from lender to borrower
- Connection line appears/strengthens

**INVEST (INVEST_MARKET)**:
- Look for transactions from banks to markets
- Particle animation from bank to market node
- Connection to market node

**Profit Booking** (every 5 steps):
- Check console for "profit_booking" events
- Banks with investments should gain/lose capital
- Watch bank dashboards show capital changes

### 4. Dashboard Visualization

1. During simulation, click on a bank
2. Verify dashboard shows:
   - Capital chart over time
   - Detailed metrics (cash, investments, loans)
   - Transaction log
3. Click on a market node
4. Verify market dashboard shows:
   - Index price chart
   - Market metrics
   - Activity log

### 5. Delete Bank Feature

1. Start simulation with 5+ banks
2. Click "Pause"
3. Click the trash icon next to a bank
4. Verify bank is marked as defaulted
5. Click "Resume"
6. Verify remaining banks continue simulation

### 6. Default Cascade

1. Create network with high-risk banks (risk > 0.7)
2. Give them low capital (< 200)
3. Run simulation
4. Watch for defaults and cascades
5. Verify:
   - Default events displayed
   - Cascade events logged
   - Affected banks shown in red

## Expected Behaviors

### Bank Decision-Making

Banks choose actions based on:
- **Risk Factor**:
  - Low risk (< 0.3): Conservative, lends cautiously
  - Medium risk (0.3-0.6): Balanced lending/investing
  - High risk (> 0.6): Aggressive investing
  
- **Leverage Gap**:
  - Below target: Increase lending/investing
  - Above target: Reduce exposure, hoard cash
  
- **Liquidity**:
  - Low liquidity: Divest or call back loans
  - High liquidity: Lend or invest

### Market Dynamics

- **Net Inflow**: Price increases
- **Net Outflow**: Price decreases
- **Returns**: Calculated from initial price (100)
- **Profit Booking**: Every 5 timesteps

### Default Mechanics

Bank defaults when: `equity = (cash + investments + loans_given - borrowed) < 0`

Cascade triggers when:
- Defaulted bank has outstanding loans
- Lenders lose loan value
- May cause additional defaults

## Common Issues

### Backend Not Starting

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Connection Error

Check CORS settings in `backend/.env`:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,*
```

### No Transactions Visible

- Check browser console for errors
- Verify backend SSE stream is working
- Check network tab for `/api/interactive/start` request

### Banks Not Acting

This should be fixed! Banks now have proper decision logic. If still an issue:
1. Check backend logs for bank decisions
2. Verify `book_investment_profit` is being called
3. Check that banks have sufficient cash to act

## Debug Commands

### Check Backend API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/interactive/status
```

### Monitor Backend Logs

Watch the backend terminal for:
- Bank observations
- ML policy decisions
- Transaction logs
- Default events

### Browser Console

Open DevTools (F12) and check for:
- SSE event messages
- Transaction event handling
- Error messages

## Success Criteria

✅ Simulation runs for 30 steps without crashing
✅ Banks perform all three actions (LEND/INVEST/HOLD)
✅ Markets show price changes
✅ Profit booking occurs every 5 steps
✅ Pause/resume/stop controls work
✅ Add capital during pause works
✅ Delete bank during pause works
✅ Bank/market dashboards display correctly
✅ Defaults and cascades are detected
✅ Live activity feed updates in real-time

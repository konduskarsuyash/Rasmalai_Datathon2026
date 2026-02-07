# Quick Start Guide - Real-Time Simulation

## What Changed?

Your Financial Network platform now has **real-time simulation** with simplified parameters!

### New Features
1. **3 Simple Parameters** - Capital, Target Leverage, Risk Factor
2. **Live Transactions** - See money flowing between banks in real-time
3. **Dynamic Connections** - Watch the network form as simulation runs
4. **Animated Visualization** - Green particles show active transactions

---

## How to Use

### Step 1: Start the Backend
```bash
cd backend
uvicorn app.main:app --reload
```
Backend runs at: http://localhost:8000

### Step 2: Start the Frontend
```bash
cd frontend
npm run dev
```
Frontend runs at: http://localhost:5173

### Step 3: Create Your Network

1. Go to http://localhost:5173/playground
2. Click "Add Institution" → Select "Bank"
3. Click on the bank to edit its parameters:
   - **Capital**: $500M (how much money the bank has)
   - **Target Leverage**: 3.0x (how aggressively it wants to lend)
   - **Risk Factor**: 30% (how much risk it tolerates)
4. Add 3-5 banks with different parameters

### Step 4: Run Real-Time Simulation

1. Scroll down in the left panel to "Real-Time Simulation"
2. Make sure "Use Playground Banks" is **ON**
3. Set simulation steps (try 20-30 for first run)
4. Click **"Start Real-Time Simulation"**

### Step 5: Watch the Magic! ✨

You'll see:
- **Green glowing particles** = Transactions happening
- **Cyan connections** = Lending relationships forming
- **Orange pulses** = Market investments
- **Red alerts** = Bank defaults

---

## Parameter Guide

### Capital ($100M - $1000M)
- **Low (100-300)**: Small bank, limited lending
- **Medium (500-800)**: Regional bank, moderate activity
- **High (1000+)**: Major bank, high volume

### Target Leverage (1.0x - 10.0x)
- **Conservative (1.5-2.5)**: Cautious lending
- **Balanced (2.5-4.0)**: Normal operations
- **Aggressive (4.0-10.0)**: Maximum leverage

### Risk Factor (0% - 100%)
- **Low (0-30%)**: Safe, conservative strategy
- **Medium (30-60%)**: Balanced risk/reward
- **High (60-100%)**: Aggressive, high-risk strategy

---

## Example Scenarios

### Scenario 1: Stable Network
```
Bank A: Capital=$1000M, Target=2.0x, Risk=10%
Bank B: Capital=$800M, Target=2.5x, Risk=15%
Bank C: Capital=$600M, Target=3.0x, Risk=20%
```
Result: Low defaults, stable system

### Scenario 2: Risky Network
```
Bank A: Capital=$300M, Target=8.0x, Risk=80%
Bank B: Capital=$250M, Target=9.0x, Risk=90%
Bank C: Capital=$200M, Target=10.0x, Risk=95%
```
Result: High defaults, cascades likely

### Scenario 3: Mixed Network
```
Bank A: Capital=$1000M, Target=2.0x, Risk=10% (Anchor)
Bank B: Capital=$500M, Target=5.0x, Risk=50% (Medium risk)
Bank C: Capital=$200M, Target=10.0x, Risk=90% (High risk)
```
Result: Watch how failure spreads from C to B

---

## Troubleshooting

### "401 Unauthorized" Error
- Fixed! The endpoint now works without authentication
- If still seeing errors, refresh the page

### Simulation Not Starting
1. Check backend is running (http://localhost:8000/health)
2. Check browser console for errors
3. Try with fewer banks (3-5) first

### No Transactions Visible
1. Make sure "Use Playground Banks" is ON
2. Check you have at least 2 banks in playground
3. Try increasing simulation steps

### Slow Performance
1. Reduce number of steps
2. Use fewer banks (5-10 max)
3. Close other browser tabs

---

## What's Happening Behind the Scenes?

### When You Click "Start Simulation":

1. **Backend receives your bank configs**
   - Capital, Target Leverage, Risk Factor

2. **Backend creates initial network**
   - Calculates liquidity from capital/target
   - Sets up random connections
   - Assigns strategies based on risk

3. **Simulation runs step-by-step**
   - Each bank decides: lend, borrow, invest, or hold
   - AI (ML policy) makes decisions
   - Transactions executed in real-time

4. **Events streamed to frontend**
   - Via Server-Sent Events (SSE)
   - ~500ms between steps
   - ~100ms between transactions

5. **Canvas updates live**
   - Green particles for transactions
   - Cyan lines for connections
   - Alerts for defaults

---

## Tips for Best Experience

1. **Start Small**: Begin with 3-5 banks
2. **Vary Parameters**: Mix conservative and aggressive banks
3. **Watch Patterns**: See how risk spreads through network
4. **Experiment**: Try extreme values to see what happens
5. **Read Alerts**: Bottom-left shows important events

---

## Need Help?

- **Backend logs**: Check terminal running uvicorn
- **Frontend logs**: Open browser DevTools (F12) → Console
- **API docs**: http://localhost:8000/docs

---

## Next Steps

Try these experiments:

1. **Contagion Test**: One risky bank + several safe banks
2. **Cascade Simulation**: All aggressive banks
3. **Resilience Test**: All conservative banks + one shock
4. **Network Effects**: Vary connection density

Enjoy watching your financial network come alive in real-time! 🚀

# 🚀 Quick Test Guide - Interactive Simulation

## Step-by-Step Testing

### 1. Open Application
```
http://localhost:5173/playground
```

### 2. Open Browser Console (IMPORTANT!)
```
Press F12 → Click "Console" tab
```
This is where you'll see what banks are doing!

### 3. Set Up Network
```
Click "Add Bank" 3 times
```

### 4. Configure Banks
Click each bank and set:
- **Bank 1**: Capital=$500M, Risk=0.6 (high risk)
- **Bank 2**: Capital=$800M, Risk=0.3 (medium risk)
- **Bank 3**: Capital=$600M, Risk=0.15 (low risk)

### 5. Start Simulation
```
Scroll down to "Interactive Simulation" panel
Click "▶️ Start Simulation"
```

### 6. Watch Console Output
You should see:
```
🚀 LocalSimulationEngine initializing...
✅ Initialized banks: [{id: 0, capital: 500, cash: 250, ...}, ...]
🎬 Starting simulation with 3 banks

📍 Step 1 starting...
Bank 0 deciding: {capital: "500.0", cash: "250.0", cashRatio: "0.50", riskFactor: 0.6}
Bank 0 investing $75.0M in FIN_SERVICES
Bank 1 deciding: {capital: "800.0", cash: "400.0", cashRatio: "0.50", riskFactor: 0.3}
Bank 1 lending $100.0M to Bank 2
Bank 2 deciding: {capital: "600.0", cash: "300.0", cashRatio: "0.50", riskFactor: 0.15}
Bank 2 (conservative) lending $30.0M to Bank 0
✅ Step 1 complete. Transactions this step: 3
```

### 7. Watch Activity Feed
Bottom-right corner should show:
```
📊 Live Activity Feed | Step 1

📈 Bank 0
INVEST → FIN_SERVICES    $75.0M

💰 Bank 1  
LEND → Bank 2    $100.0M

💰 Bank 2
LEND → Bank 0    $30.0M
```

### 8. Test Pause
```
After 5 steps, click "⏸️ Pause"
```

Should see:
- ✅ Step counter stops
- ✅ Activity feed pauses
- ✅ Modification panel appears

### 9. Modify Network
```
Add $100M to Bank 0
```

Should see in console:
```
Bank 0 capital updated: 485 → 585
```

### 10. Resume
```
Click "▶️ Resume"
```

Should see in console:
```
📍 Step 6 starting...
Bank 0 deciding: {capital: "585.0", cash: "280.0", ...}
Bank 0 lending $70.0M to Bank 1  ← Larger loan due to more capital!
```

---

## Troubleshooting

### If Console Shows "holding cash" for all banks:

**Check 1**: Are risk factors set?
```javascript
// In console, type:
localStorage.getItem('banks')
// Should show risk: 0.2-0.6, NOT 0
```

**Check 2**: Is cash positive?
```javascript
// Look for this in console:
"cash": "250.0"  ✅ Good
"cash": "0.0"    ❌ Problem
```

**Check 3**: Are there multiple banks?
```javascript
// Should see:
"🎬 Starting simulation with 3 banks"  ✅ Good
"🎬 Starting simulation with 0 banks"  ❌ Problem
```

### If No Console Logs Appear:

**Check 1**: Is InteractiveSimulationPanel rendering?
- Look for "Interactive Simulation" header in left panel
- Should see Start button

**Check 2**: Did you click Start?
- Button should change to "Pause" after clicking

**Check 3**: Browser console errors?
- Look for red errors in console
- Share the error message

---

## Expected Behavior

### Every Step Should Show:
1. Interest payments (if loans exist)
2. Loan repayments (if loans exist)
3. 3 bank decisions (one per bank)
4. Market updates
5. Total: **3-6 transactions per step**

### Activity Feed Should Show:
- Mix of colors (green, purple, blue, orange)
- Different actions (LEND, INVEST, HOLD)
- All 3 banks appearing

### Canvas Should Show:
- Particles moving between banks
- Particles moving to markets
- Connections forming (cyan, purple lines)

---

## Quick Debug Checklist

- [ ] Browser console open (F12)
- [ ] "Interactive Simulation" panel visible
- [ ] 3 banks added with different risk factors
- [ ] Risk factors NOT zero (0.15-0.6)
- [ ] Capital amounts are reasonable ($500M-$1200M)
- [ ] Clicked "Start Simulation" button
- [ ] See initialization logs in console
- [ ] See "Step 1 starting..." in console
- [ ] See "Bank X deciding..." for each bank
- [ ] See transactions logged
- [ ] Activity feed updating

---

## 🎯 If Everything Works

You'll see:
```
Step 1: 3 transactions
Step 2: 5 transactions (3 new + 2 interest/repayment)
Step 3: 6 transactions
...
Step 10: 8 transactions
```

Activity feed will be **constantly scrolling** with colorful transaction cards! 🎉

**Test it now and check your console!** 📊

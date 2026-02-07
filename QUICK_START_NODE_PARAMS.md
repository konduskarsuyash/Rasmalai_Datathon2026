# Quick Start Guide: Using Node Parameters

## For Frontend Developers

### Basic Usage in Playground

1. **Open the playground** at `/playground`

2. **Add institutions** using the control panel (banks, exchanges, clearinghouses)

3. **Configure each institution:**
   - Click on a node to select it
   - In the right panel, edit:
     - Capital (e.g., 200)
     - Liquidity (e.g., 100)
     - Risk (0.1 = conservative, 0.5 = aggressive)
     - Strategy (conservative/balanced/aggressive)

4. **Enable node parameters:**
   - In the left panel, scroll to "Backend Simulation (v2)"
   - Toggle "Use Playground Nodes" to ON
   - The button will turn blue and show the node count

5. **Run simulation:**
   - Click "Run simulation"
   - Wait for results
   - View metrics in the right panel

### Example JavaScript Code

```javascript
// Send custom node parameters via API
const response = await fetch('http://localhost:8000/api/simulation/run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    num_banks: 3,
    num_steps: 30,
    use_featherless: false,
    verbose: false,
    connection_density: 0.3,
    node_parameters: [
      {
        node_id: "bank_1",
        initial_capital: 200.0,
        initial_liquidity: 100.0,
        risk_level: 0.1,
        strategy: "conservative",
        lending_amount: 15.0,
        investment_amount: 5.0
      },
      {
        node_id: "bank_2",
        initial_capital: 150.0,
        initial_liquidity: 75.0,
        risk_level: 0.3,
        strategy: "balanced",
        lending_amount: 10.0,
        investment_amount: 10.0
      }
    ]
  })
});

const result = await response.json();
console.log('Simulation complete:', result.summary);
```

---

## For Backend Developers

### Using the API Directly

```python
import requests

# Endpoint
url = "http://localhost:8000/api/simulation/run"

# Request with node parameters
payload = {
    "num_banks": 3,
    "num_steps": 30,
    "use_featherless": False,
    "verbose": False,
    "connection_density": 0.3,
    "node_parameters": [
        {
            "node_id": "conservative_bank",
            "initial_capital": 200.0,
            "initial_liquidity": 120.0,
            "risk_level": 0.1,
            "strategy": "conservative",
            "lending_amount": 20.0,
            "investment_amount": 5.0
        },
        {
            "node_id": "aggressive_bank",
            "initial_capital": 100.0,
            "initial_liquidity": 40.0,
            "risk_level": 0.6,
            "strategy": "aggressive",
            "lending_amount": 5.0,
            "investment_amount": 25.0
        },
        {
            "node_id": "balanced_bank",
            "initial_capital": 150.0,
            "initial_liquidity": 75.0,
            "risk_level": 0.3,
            "strategy": "balanced",
            "lending_amount": 10.0,
            "investment_amount": 10.0
        }
    ]
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Total defaults: {result['summary']['total_defaults']}")
print(f"Surviving banks: {result['summary']['surviving_banks']}")
print(f"Default rate: {result['summary']['default_rate']:.2%}")
```

### Using Python Core Directly

```python
from app.core import run_simulation_v2, SimulationConfig, BankConfig

# Create bank configurations
bank_configs = [
    BankConfig(
        initial_capital=200.0,
        initial_liquidity=100.0,
        risk_level=0.1,
        strategy="conservative",
        lending_amount=15.0,
        investment_amount=5.0
    ),
    BankConfig(
        initial_capital=150.0,
        initial_liquidity=75.0,
        risk_level=0.3,
        strategy="balanced",
        lending_amount=10.0,
        investment_amount=10.0
    ),
    BankConfig(
        initial_capital=100.0,
        initial_liquidity=40.0,
        risk_level=0.5,
        strategy="aggressive",
        lending_amount=5.0,
        investment_amount=20.0
    )
]

# Create simulation configuration
config = SimulationConfig(
    num_banks=3,
    num_steps=30,
    use_featherless=False,
    verbose=True,
    connection_density=0.3,
    bank_configs=bank_configs
)

# Run simulation
history = run_simulation_v2(config)

# Access results
print(f"Total steps: {history['summary']['total_steps']}")
print(f"Total defaults: {history['summary']['total_defaults']}")
print(f"Surviving banks: {history['summary']['surviving_banks']}")
```

---

## Common Scenarios

### Scenario 1: Test Systemic Risk with Mixed Strategies

```python
node_parameters = [
    # 2 conservative banks (safe)
    {"initial_capital": 250, "initial_liquidity": 150, "risk_level": 0.05, "strategy": "conservative"},
    {"initial_capital": 230, "initial_liquidity": 140, "risk_level": 0.08, "strategy": "conservative"},
    
    # 2 balanced banks (medium risk)
    {"initial_capital": 150, "initial_liquidity": 80, "risk_level": 0.3, "strategy": "balanced"},
    {"initial_capital": 160, "initial_liquidity": 85, "risk_level": 0.28, "strategy": "balanced"},
    
    # 2 aggressive banks (risky)
    {"initial_capital": 100, "initial_liquidity": 40, "risk_level": 0.6, "strategy": "aggressive"},
    {"initial_capital": 90, "initial_liquidity": 35, "risk_level": 0.65, "strategy": "aggressive"}
]
```

### Scenario 2: Liquidity Crisis Simulation

```python
node_parameters = [
    # All banks have very low liquidity
    {"initial_capital": 200, "initial_liquidity": 15, "risk_level": 0.3, "strategy": "balanced"},
    {"initial_capital": 180, "initial_liquidity": 12, "risk_level": 0.35, "strategy": "balanced"},
    {"initial_capital": 190, "initial_liquidity": 18, "risk_level": 0.32, "strategy": "balanced"},
    {"initial_capital": 170, "initial_liquidity": 10, "risk_level": 0.38, "strategy": "balanced"}
]
```

### Scenario 3: Contagion from Weak Bank

```python
node_parameters = [
    # 1 very weak bank
    {"initial_capital": 50, "initial_liquidity": 10, "risk_level": 0.8, "strategy": "aggressive"},
    
    # 4 strong banks that will be affected
    {"initial_capital": 300, "initial_liquidity": 150, "risk_level": 0.1, "strategy": "conservative"},
    {"initial_capital": 280, "initial_liquidity": 140, "risk_level": 0.12, "strategy": "conservative"},
    {"initial_capital": 290, "initial_liquidity": 145, "risk_level": 0.11, "strategy": "conservative"},
    {"initial_capital": 270, "initial_liquidity": 135, "risk_level": 0.13, "strategy": "conservative"}
]
```

---

## Parameter Guidelines

### Capital (initial_capital)
- **Low**: 50-100 (vulnerable to shocks)
- **Medium**: 100-200 (typical bank)
- **High**: 200-400 (systemically important bank)

### Liquidity (initial_liquidity)
- **Low**: 10-50 (liquidity stress)
- **Medium**: 50-100 (normal operations)
- **High**: 100-200 (well-capitalized)

### Risk Level (risk_level)
- **Conservative**: 0.05-0.15 (safe banks)
- **Moderate**: 0.2-0.4 (typical risk)
- **Aggressive**: 0.5-0.8 (high-risk banks)

### Strategy
- **conservative**: Lower leverage (2.0), higher liquidity (0.4), low market exposure (0.1)
- **balanced**: Medium leverage (3.0), medium liquidity (0.3), medium exposure (0.2)
- **aggressive**: Higher leverage (4.5), lower liquidity (0.15), high exposure (0.35)

### Connection Density
- **Low**: 0.1-0.2 (sparse network, less contagion)
- **Medium**: 0.3-0.5 (typical interconnected)
- **High**: 0.6-0.9 (highly interconnected, more contagion)

---

## Testing Your Changes

### 1. Start the Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Run Import Test
```bash
cd backend
python test_imports.py
```

Expected output:
```
[OK] BankConfig imported successfully
[OK] SimulationConfig imported successfully
[OK] NodeParameters imported successfully
[OK] SimulationRunRequest imported successfully
[OK] BankConfig instance created: ...
[OK] NodeParameters instance created: ...
[SUCCESS] All imports and instantiations successful!
```

### 3. Run Integration Test
```bash
cd backend
python test_node_params.py
```

Expected output:
```
Testing Simulation with Node Parameters
========================================
Test 1: Basic simulation (no node params)
Status: 200
[OK] Success! Summary: {...}

Test 2: Simulation with custom node parameters
Status: 200
[OK] Success with custom node params!
...
```

### 4. Test Frontend
1. Start frontend: `cd frontend && npm run dev`
2. Open browser: `http://localhost:5173`
3. Navigate to `/playground`
4. Add some nodes and configure them
5. Toggle "Use Playground Nodes" ON
6. Click "Run simulation"
7. Check results in right panel

---

## Troubleshooting

### Backend Issues

**Problem**: Import errors
```
Solution: Ensure you're in the backend directory and virtual environment is activated
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Problem**: Module not found
```
Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Problem**: 500 error when running simulation
```
Solution: Check backend logs for traceback, verify all required fields in request
```

### Frontend Issues

**Problem**: Toggle doesn't appear
```
Solution: Ensure institutions array is populated (add nodes in playground first)
```

**Problem**: Simulation fails with node params
```
Solution: Check browser console for request payload, verify all required fields present
```

**Problem**: Results don't reflect node params
```
Solution: Ensure toggle is ON (should be blue), check network tab to verify params sent
```

---

## API Response Example

```json
{
  "summary": {
    "total_steps": 30,
    "total_defaults": 1,
    "default_rate": 0.333,
    "total_cascade_events": 0,
    "surviving_banks": 2,
    "final_total_equity": 450.75,
    "transactions_logged": 87,
    "system_collapsed": false
  },
  "steps_count": 30,
  "defaults_over_time": [0, 0, 0, 1, 1, 1, ...],
  "total_equity_over_time": [500.0, 498.5, 496.2, ...],
  "market_prices": [...],
  "cascade_events": [],
  "system_logs": [...]
}
```

---

## Additional Resources

- Full documentation: `NODE_PARAMETERS.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- API documentation: `http://localhost:8000/docs`
- Project README: `README.md`

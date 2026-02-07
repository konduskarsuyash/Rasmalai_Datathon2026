# Financial Network MVP - Technical Documentation

## Overview

A **Network-Based Strategic Simulation** of financial infrastructure that models emergent equilibrium behavior under repeated interaction among banks. Uses **Featherless.ai** for AI-driven strategic priority selection.

---

## Architecture

```
financial_network_mvp/
├── config/
│   └── settings.py          # API keys, simulation parameters
├── core/
│   ├── balance_sheet.py     # Assets/Liabilities/Equity tracking
│   ├── bank.py              # Bank agent with 4 types
│   ├── market.py            # Reactive market indices
│   ├── transaction.py       # Transaction ledger with priority
│   ├── payoff.py            # Utility and stability analysis
│   ├── simulation.py        # v1 network simulation
│   └── simulation_v2.py     # v2 balance sheet simulation
├── ml/
│   └── policy.py            # ML action selector (local-info only)
├── featherless/
│   └── decision_engine.py   # Featherless.ai priority selection
├── utils/
│   └── metrics.py           # Metrics and reporting
├── main.py                  # CLI entry point
└── .env                     # API key (FEATHERLESS_API_KEY)
```

---

## Two Simulation Modes

| Mode | State | Uses | Purpose |
|------|-------|------|---------|
| v1 | Network graph | Credit/margin strategies | Stress testing |
| v2 | Balance sheets | 5 discrete actions | Micro→macro dynamics |

---

## Bank Types & Targets

Each bank type has **different target ratios** that drive behavior:

| Type | Index | Cash | Target Leverage | Target Liquidity | Market Exposure |
|------|-------|------|-----------------|------------------|-----------------|
| Large | 0,4,8... | $150-200 | 2.0x | 40% | 10% |
| Medium | 1,5,9... | $80-120 | 3.0x | 30% | 20% |
| Small | 2,6,10... | $30-60 | 2.5x | 50% | 10% |
| Aggressive | 3,7,11... | $60-90 | 4.5x | 15% | 35% |

---

## Actions

| Action | Effect | Triggers When |
|--------|--------|---------------|
| `INCREASE_LENDING` | cash↓, loans↑ | Under-leveraged |
| `DECREASE_LENDING` | cash↑, loans↓ | Over-leveraged |
| `INVEST_MARKET` | cash↓, investments↑ | Excess liquidity |
| `DIVEST_MARKET` | cash↑, investments↓ | Low cash |
| `HOARD_CASH` | No change | Defensive mode |

---

## Local Information Constraint

Banks operate with **incomplete information**:

✅ **What banks CAN see:**
- Own balance sheet (cash, equity, leverage)
- Number of neighbor defaults
- Aggregate market stress (one scalar)

❌ **What banks CANNOT see:**
- Global system metrics
- Other banks' strategies
- Future market states

---

## Featherless.ai Integration

Featherless acts as **meta-strategy selector** (NOT action selector).

| Priority | Meaning | Effect |
|----------|---------|--------|
| `PROFIT` | Pursue growth | Allow aggressive actions |
| `LIQUIDITY` | Need cash reserves | Override to HOARD/DIVEST |
| `STABILITY` | Reduce risk | Override to DECREASE_LENDING |

---

## Transaction Ledger

Every action logs:
- **Time step**
- **Initiator bank**
- **Counterparty** (bank or market)
- **Type** (LOAN, INVEST, DIVEST, REPAY)
- **Amount**
- **Reason** (target gap, priority trigger)
- **Priority** (PROFIT/LIQUIDITY/STABILITY)

---

## Simulation Loop (v2)

**STRICT ORDER** (8 steps):

1. **Observe**: Bank reads local state only
2. **ML Policy**: Proposes action from target gaps
3. **Featherless**: May override priority
4. **Execute**: Action modifies balance sheet
5. **Log**: Transaction recorded with reason/priority
6. **Markets**: Update prices from flows
7. **Defaults**: Check equity < 0
8. **Cascades**: Propagate losses to lenders

---

## Usage

```powershell
# v2 with Featherless (default)
python main.py --v2 --banks 20 --steps 30

# v2 rule-based (faster)
python main.py --v2 --banks 20 --no-llm

# v1 network simulation
python main.py --agents 40 --steps 30
```

---

## Sample Output

```
Bank0: HOARD_CASH [STABILITY] | cash=$173 eq=$123
Bank1: HOARD_CASH [LIQUIDITY] | cash=$95 eq=$53
Bank2: HOARD_CASH [LIQUIDITY] | cash=$36 eq=$19
Bank3: DECREASE_LENDING [STABILITY] | cash=$82 eq=$26
Bank4: INVEST_MARKET [PROFIT] | cash=$134 eq=$114
```

---

## Policy Learning (NEW)

Banks adapt strategies over time using **bounded rational learning**:

### Reward Computation (Per-Bank, Local)
```
Reward = Profit - LiquidityPenalty - LeveragePenalty - ExposurePenalty
```

### What Updates:

| Component | Update Mechanism | Speed |
|-----------|------------------|-------|
| Action Preferences | Bandit-style EMA | Fast (α=0.1) |
| Target Ratios | Streak-triggered | Slow (α=0.02) |

### Constraints (Non-Negotiable):
- ❌ No global reward
- ❌ No shared learning across banks
- ❌ No backprop / training epochs
- ❌ No future reward lookahead

### 10-Step Simulation Loop:
1. Observe local state
2. ML proposes action
3. Featherless sets priority
4. Execute action
5. Log transaction
6. Markets update
7. Check defaults
8. Propagate cascades
9. **Compute reward** ← NEW
10. **Update policy & targets** ← NEW

---

## For Judges

**Key Differentiators:**
1. "Emergent equilibrium behavior under repeated interaction"
2. "LLM selects strategic priorities, not numeric values"
3. "Every transaction auditable with reason and priority"
4. "Cascades emerge naturally from balance sheet contagion"
5. "Banks only see local information - no global omniscience"
6. "Bounded rational learning - banks adapt from rewards"

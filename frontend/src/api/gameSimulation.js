/**
 * Game-Theoretic Simulation API Client
 * Full step-based simulation with control flow
 */

const getBase = () => import.meta.env.VITE_API_URL || "";

// ============ Simulation Control ============

export async function initSimulation(config, token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/init`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(config),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Init failed: ${res.status}`);
  }
  return res.json();
}

export async function startSimulation(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/start`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Start failed");
  return res.json();
}

export async function executeStep(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/step`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Step execution failed");
  return res.json();
}

export async function pauseSimulation(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/pause`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Pause failed");
  return res.json();
}

export async function resumeSimulation(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/resume`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Resume failed");
  return res.json();
}

export async function stopSimulation(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/stop`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Stop failed");
  return res.json();
}

export async function getSimulationStatus(token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/status`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Status fetch failed");
  return res.json();
}

// ============ Bank APIs ============

export async function createBank(bankData, token = null) {
  const base = getBase();
  const url = `${base}/api/banks`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(bankData),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Create bank failed: ${res.status}`);
  }
  return res.json();
}

export async function updateBank(bankId, updates, token = null) {
  const base = getBase();
  const url = `${base}/api/banks/${bankId}`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "PUT",
    headers,
    body: JSON.stringify(updates),
  });

  if (!res.ok) throw new Error("Update bank failed");
  return res.json();
}

export async function getBankState(bankId, token = null) {
  const base = getBase();
  const url = `${base}/api/banks/${bankId}`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Get bank failed");
  return res.json();
}

export async function listBanks(token = null) {
  const base = getBase();
  const url = `${base}/api/banks`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("List banks failed");
  return res.json();
}

// ============ Connection APIs ============

export async function createConnection(connectionData, token = null) {
  const base = getBase();
  const url = `${base}/api/connections`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(connectionData),
  });

  if (!res.ok) throw new Error("Create connection failed");
  return res.json();
}

export async function getNetwork(token = null) {
  const base = getBase();
  const url = `${base}/api/network`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Get network failed");
  return res.json();
}

// ============ Action Execution ============

export async function executeAction(bankId, action, token = null) {
  const base = getBase();
  const url = `${base}/api/actions/execute`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ bank_id: bankId, action }),
  });

  if (!res.ok) throw new Error("Execute action failed");
  return res.json();
}

// ============ Strategy APIs ============

export async function evaluateStrategy(bankId, observedState, token = null) {
  const base = getBase();
  const url = `${base}/api/strategy/evaluate`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ bank_id: bankId, observed_state: observedState }),
  });

  if (!res.ok) throw new Error("Evaluate strategy failed");
  return res.json();
}

// ============ Margin & Clearing ============

export async function checkMargin(bankId, priceChange, token = null) {
  const base = getBase();
  const url = `${base}/api/margin/check`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ bank_id: bankId, market_price_change: priceChange }),
  });

  if (!res.ok) throw new Error("Margin check failed");
  return res.json();
}

export async function issueMarginCall(bankId, token = null) {
  const base = getBase();
  const url = `${base}/api/margin/call`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(bankId),
  });

  if (!res.ok) throw new Error("Margin call failed");
  return res.json();
}

export async function forceLiquidation(bankId, token = null) {
  const base = getBase();
  const url = `${base}/api/liquidation/force`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(bankId),
  });

  if (!res.ok) throw new Error("Liquidation failed");
  return res.json();
}

// ============ Market APIs ============

export async function getMarketState(token = null) {
  const base = getBase();
  const url = `${base}/api/market`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Get market failed");
  return res.json();
}

export async function updateMarket(token = null) {
  const base = getBase();
  const url = `${base}/api/market/update`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Market update failed");
  return res.json();
}

// ============ Default & Contagion ============

export async function checkDefaults(token = null) {
  const base = getBase();
  const url = `${base}/api/defaults/check`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Check defaults failed");
  return res.json();
}

export async function propagateCascade(bankId, token = null) {
  const base = getBase();
  const url = `${base}/api/cascade/propagate`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(bankId),
  });

  if (!res.ok) throw new Error("Cascade propagation failed");
  return res.json();
}

// ============ Interventions ============

export async function injectCapital(bankId, amount, token = null) {
  const base = getBase();
  const url = `${base}/api/intervention/add_capital`;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ bank_id: bankId, amount }),
  });

  if (!res.ok) throw new Error("Capital injection failed");
  return res.json();
}

export async function triggerFinancialCrisis(token = null) {
  const base = getBase();
  const url = `${base}/api/intervention/financial_crisis`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { method: "POST", headers });
  if (!res.ok) throw new Error("Crisis trigger failed");
  return res.json();
}

// ============ Observability ============

export async function getEvents(token = null) {
  const base = getBase();
  const url = `${base}/api/events`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Get events failed");
  return res.json();
}

export async function getMetrics(token = null) {
  const base = getBase();
  const url = `${base}/api/metrics`;
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("Get metrics failed");
  return res.json();
}

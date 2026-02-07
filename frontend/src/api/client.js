/**
 * API client for backend. Uses Vite proxy in dev: /api -> http://localhost:8000
 */
const getBase = () => import.meta.env.VITE_API_URL || '';

/**
 * Run backend simulation v2.
 * @param {Object} body - { num_banks?, num_steps?, use_featherless?, verbose?, lending_amount?, investment_amount? }
 * @param {string} [token] - Optional Clerk token for Authorization header
 * @returns {Promise<Object>} - { summary, steps_count, defaults_over_time, total_equity_over_time, market_prices, cascade_events, system_logs, bank_logs? }
 */
export async function runSimulation(body, token = null) {
  const base = getBase();
  const url = `${base}/api/simulation/run`;
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Simulation failed: ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch public config from backend.
 */
export async function getConfig(token = null) {
  const base = getBase();
  const url = `${base}/api/config/`;
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('Config fetch failed');
  return res.json();
}

/**
 * Create a network (wireframe).
 */
export async function createNetwork(body, token = null) {
  const base = getBase();
  const url = `${base}/api/networks/`;
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Create network failed');
  }
  return res.json();
}

// src/services/apiService.js
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Helper function to handle API requests
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    "Content-Type": "application/json",
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

// Configuration API
export const getConfig = async () => {
  return apiRequest("/api/config");
};

// Network API
export const createNetwork = async (networkData) => {
  return apiRequest("/api/networks/", {
    method: "POST",
    body: JSON.stringify(networkData),
  });
};

export const listNetworks = async () => {
  return apiRequest("/api/networks/");
};

export const getNetwork = async (networkId) => {
  return apiRequest(`/api/networks/${networkId}`);
};

// Simulation API
export const runSimulation = async (simulationParams) => {
  return apiRequest("/api/simulation/run", {
    method: "POST",
    body: JSON.stringify(simulationParams),
  });
};

// Health check
export const checkHealth = async () => {
  return apiRequest("/health");
};

// User info
export const getCurrentUser = async () => {
  return apiRequest("/api/me");
};

export default {
  getConfig,
  createNetwork,
  listNetworks,
  getNetwork,
  runSimulation,
  checkHealth,
  getCurrentUser,
};

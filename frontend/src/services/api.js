const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Fetches the list of tracked companies.
 */
export async function fetchCompanies() {
  const response = await fetch(`${API_BASE_URL}/companies`);
  if (!response.ok) {
    throw new Error('Failed to fetch companies list');
  }
  return await response.json();
}

/**
 * Fetches stock metrics and historical data for a symbol.
 * @param {string} symbol - Stock symbol (e.g. A32, SSI)
 * @param {boolean} forceRefresh - If true, forces backend to fetch fresh data from CafeF
 */
export async function fetchStockData(symbol, forceRefresh = false) {
  const url = `${API_BASE_URL}/stocks/${symbol}${forceRefresh ? '?force_refresh=true' : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch stock data for ${symbol}`);
  }
  return await response.json();
}

/**
 * Adds a new company symbol to track.
 * @param {string} symbol
 */
export async function addCompany(symbol) {
  const response = await fetch(`${API_BASE_URL}/companies/${symbol}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to add company ${symbol}`);
  }
  return await response.json();
}

/**
 * App config from Vite env. POLLING_INTERVAL: ms between admin data refreshes (default 15s).
 * API_BASE_URL: backend base for /health, /admin/* (default http://localhost:8000).
 */
export const POLLING_INTERVAL = Number(import.meta.env.VITE_POLLING_INTERVAL) || 15000;
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

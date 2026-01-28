// API Configuration
// Uses environment variable with fallback to localhost for development

// Base URL for API calls - configurable via environment
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// WebSocket URL - derived from API base URL
export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

// Auth URLs for OAuth providers
export const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || API_BASE_URL;

// Sandbox preview backend URL (set dynamically per preview session)
let _sandboxBackendUrl = null;

/**
 * Set the sandbox backend URL for preview mode.
 * Call this when launching a sandbox preview.
 */
export const setSandboxBackendUrl = (url) => {
  _sandboxBackendUrl = url;
};

/**
 * Clear the sandbox backend URL (return to main API).
 */
export const clearSandboxBackendUrl = () => {
  _sandboxBackendUrl = null;
};

/**
 * Get the current effective API base URL.
 * Returns sandbox URL if set, otherwise the main API URL.
 */
export const getEffectiveApiUrl = () => {
  return _sandboxBackendUrl || API_BASE_URL;
};

/**
 * Get the current effective WebSocket URL.
 */
export const getEffectiveWsUrl = () => {
  const baseUrl = _sandboxBackendUrl || API_BASE_URL;
  return baseUrl.replace(/^http/, 'ws');
};

/**
 * Check if currently in sandbox preview mode.
 */
export const isSandboxMode = () => {
  return _sandboxBackendUrl !== null;
};

// Helper function for API calls
export const apiUrl = (path) => {
  const baseUrl = getEffectiveApiUrl();
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${baseUrl}/${cleanPath}`;
};

// Helper function for WebSocket connections
export const wsUrl = (path) => {
  const baseUrl = getEffectiveWsUrl();
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${baseUrl}/${cleanPath}`;
};

// Helper for auth URLs (always use main backend, not sandbox)
export const authUrl = (path) => {
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${AUTH_BASE_URL}/${cleanPath}`;
};

export default API_BASE_URL;

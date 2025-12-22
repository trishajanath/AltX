// API Configuration
export const API_BASE_URL = 'http://localhost:8000';

// Helper function for API calls
export const apiUrl = (path) => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
};

export default API_BASE_URL;

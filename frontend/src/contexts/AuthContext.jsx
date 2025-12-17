import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user from localStorage or sessionStorage on mount
  useEffect(() => {
    let storedToken = null;
    let parsedUser = null;

    try {
      storedToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');

      if (storedToken && storedUser) {
        parsedUser = JSON.parse(storedUser);
        console.log('✅ Auth restored from storage:', parsedUser.email || parsedUser.username);
      } else {
        console.log('ℹ️ No stored auth found');
      }
    } catch (error) {
      console.error('❌ Error loading auth from storage:', error);
      // Clear corrupted data
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('user');
      storedToken = null;
      parsedUser = null;
    }

    // Update all state at once - React will batch these
    setToken(storedToken);
    setUser(parsedUser);
    setLoading(false);
    console.log('🔓 Auth initialization complete');
  }, []);

  const login = (userData, accessToken, rememberMe = false) => {
    console.log('🔐 Login called with:', { user: userData.email || userData.username, rememberMe });
    
    // Update state FIRST
    setUser(userData);
    setToken(accessToken);
    
    // Then persist to storage
    if (rememberMe) {
      // Store in localStorage for persistent login
      console.log('💾 Storing in localStorage (persistent)');
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('user', JSON.stringify(userData));
    } else {
      // Store in sessionStorage for session-only login
      console.log('💾 Storing in sessionStorage (session-only)');
      sessionStorage.setItem('access_token', accessToken);
      sessionStorage.setItem('user', JSON.stringify(userData));
    }
    
    console.log('✅ Login complete, user state updated, isAuth will be:', !!(userData && accessToken));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user');
  };

  const isAuthenticated = !!token && !!user;

  // API helper with authentication
  const authenticatedFetch = async (url, options = {}) => {
    const headers = {
      ...options.headers,
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      
      // Handle 401 (unauthorized) - token expired or invalid
      if (response.status === 401) {
        logout();
        throw new Error('Authentication expired. Please login again.');
      }

      return response;
    } catch (error) {
      throw error;
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    logout,
    authenticatedFetch
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;

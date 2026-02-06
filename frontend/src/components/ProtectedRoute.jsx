
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Check storage synchronously (not in useEffect which runs after render)
const checkStorageAuth = () => {
  try {
    const storedToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
    return !!(storedToken && storedUser);
  } catch {
    return false;
  }
};

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // 🚀 1) If the URL has OAuth params — do NOT block route.
  if (location.search.includes("auth=success")) {
    return children;
  }

  // ⏳ 2) Wait for AuthProvider to finish loading from storage
  if (loading) {
    return (
      <div className="loading-screen">
        Loading...
      </div>
    );
  }

  // 🔐 3) Check storage synchronously during render (not in useEffect)
  const hasStoredAuth = checkStorageAuth();
  
  console.log('🔍 ProtectedRoute check:', { isAuthenticated, hasStoredAuth, loading });

  // ✅ 4) Allow if either React state OR storage has auth
  // Storage check handles the race condition after login() where state hasn't updated yet
  if (isAuthenticated || hasStoredAuth) {
    return children;
  }

  // 🚫 5) No auth anywhere - redirect to login
  console.log('🚫 No auth found, redirecting to login');
  return <Navigate to="/login" replace />;
};

export default ProtectedRoute;

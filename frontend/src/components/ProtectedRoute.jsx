
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // 🚀 1) If the URL has OAuth params — do NOT block route.
  if (location.search.includes("auth=success")) {
    return children;
  }

  // ⏳ 2) Wait for AuthProvider to read storage 
  if (loading) {
    return (
      <div className="loading-screen">
        Loading...
      </div>
    );
  }

  // 🔐 3) Block only after storage is loaded
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;

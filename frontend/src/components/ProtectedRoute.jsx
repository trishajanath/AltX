import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  // Initialize auth state from localStorage immediately to prevent flickering
  const getInitialAuthState = () => {
    try {
      const userData = localStorage.getItem('user');
      const token = localStorage.getItem('access_token');
      
      if (userData && token) {
        const user = JSON.parse(userData);
        if (user.email && user.name) {
          return true;
        }
      }
    } catch (error) {
      console.error('Error reading initial auth state:', error);
    }
    return null; // null means we need to check for OAuth callback
  };

  const [isAuthenticated, setIsAuthenticated] = useState(getInitialAuthState());
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // First, check if this is an OAuth callback
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth');
        const userEmail = urlParams.get('user');
        const userName = urlParams.get('name');
        const userAvatar = urlParams.get('avatar');
        const error = urlParams.get('error');

        // Handle OAuth callback
        if (authStatus === 'success' && userEmail) {
          setIsProcessingAuth(true);
          
          // Store user info in localStorage
          const userInfo = {
            email: userEmail,
            name: userName || 'User',
            avatar: userAvatar || '',
            authenticatedAt: new Date().toISOString()
          };
          localStorage.setItem('user', JSON.stringify(userInfo));
          localStorage.setItem('access_token', 'google_oauth_token'); // Add a token indicator
          
          // Clean URL
          window.history.replaceState({}, document.title, window.location.pathname);
          
          console.log('✅ Google authentication successful:', userInfo);
          setIsAuthenticated(true);
          setIsProcessingAuth(false);
          return;
        } else if (error) {
          console.error('❌ Google authentication failed:', error);
          
          // Clean URL and clear any auth data
          window.history.replaceState({}, document.title, window.location.pathname);
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
          setIsProcessingAuth(false);
          return;
        }

        // If we already have auth from initial state, skip revalidation
        if (isAuthenticated === true) {
          return;
        }

        // Check for existing authentication only if we don't have it already
        const userData = localStorage.getItem('user');
        const token = localStorage.getItem('access_token');
        
        if (userData && token) {
          const user = JSON.parse(userData);
          // Check if user data is valid and has required fields
          if (user.email && user.name) {
            setIsAuthenticated(true);
            return;
          }
        }
        
        // If no valid authentication data, clear any stale data
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
      } catch (error) {
        console.error('Error checking authentication:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
        setIsProcessingAuth(false);
      }
    };

    checkAuth();
  }, []);

  // Show loading state while checking authentication or processing OAuth
  if (isAuthenticated === null || isProcessingAuth) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#000000',
        color: '#ffffff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            border: '3px solid rgba(255,255,255,0.1)', 
            borderTop: '3px solid #ffffff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <div>{isProcessingAuth ? 'Processing authentication...' : 'Checking authentication...'}</div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  // Render the protected component if authenticated
  return children;
};

export default ProtectedRoute;

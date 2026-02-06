import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent multiple executions
    if (hasProcessed.current) {
      console.log('⚠️ OAuth callback already processed, skipping');
      return;
    }

    const authSuccess = searchParams.get('auth');
    const token = searchParams.get('token');
    const userBase64 = searchParams.get('user');

    console.log('🔍 OAuth callback params:', { authSuccess, hasToken: !!token, hasUser: !!userBase64 });

    if (authSuccess === 'success' && token && userBase64) {
      try {
        // Mark as processed immediately
        hasProcessed.current = true;

        // Decode base64 user data
        const userJson = atob(userBase64);
        const userData = JSON.parse(userJson);

        console.log('✅ Decoded user data:', userData);

        // Save to auth context (writes to storage first, then updates state)
        login(userData, token, false);

        console.log('🚀 Redirecting to /voice-chat');
        
        // Navigate directly - storage is written synchronously by login()
        navigate("/voice-chat", { replace: true });
      } catch (error) {
        console.error('❌ Failed to process OAuth callback:', error);
        hasProcessed.current = true;
        navigate('/login?error=oauth_failed', { replace: true });
      }
    } else {
      console.log('⚠️ Invalid OAuth callback, redirecting to login');
      hasProcessed.current = true;
      navigate('/login', { replace: true });
    }
  }, []); // Empty dependency array - run only once on mount

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white text-lg">Processing login...</p>
      </div>
    </div>
  );
};

export default OAuthCallback;

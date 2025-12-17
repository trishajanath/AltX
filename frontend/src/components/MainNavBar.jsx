import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { User, ChevronDown, LogOut } from 'lucide-react';

const MainNavBar = ({ user, isAuthenticated, onLogout }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const profileMenuRef = useRef(null);

  // Mark as mounted after first render to prevent flickering
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Navigation links configuration
  const navLinks = [
    { path: '/voice-chat', label: 'Voice Builder' },
    { path: '/repo-analysis', label: 'Scan Repo' },
    { path: '/security', label: 'Scan Website' },
    { path: '/home', label: 'Dashboard' }
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setIsProfileMenuOpen(false);
      }
    };

    if (isProfileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isProfileMenuOpen]);

  // Style constants
  const navContainerStyle = {
    position: 'fixed',
    top: '1.5rem',
    left: '0',
    right: '0',
    zIndex: 99,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    pointerEvents: 'none'
  };

  const navBarStyle = {
    display: 'flex',
    gap: '0.75rem',
    background: 'var(--glass-bg)',
    backdropFilter: 'blur(10px)',
    padding: '0.6rem 1rem',
    borderRadius: '50px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
    border: '1px solid var(--border-color)',
    alignItems: 'center',
    pointerEvents: 'auto',
    opacity: isMounted ? 1 : 0,
    transition: 'opacity 0.15s ease-in'
  };

  const logoStyle = {
    height: '24px',
    marginRight: '0.5rem'
  };

  const getButtonStyle = (isActive) => ({
    background: isActive ? 'var(--accent-glow)' : 'transparent',
    color: isActive ? '#000000' : 'var(--text-secondary)',
    border: 'none',
    borderRadius: '25px',
    padding: '0.5rem 1rem',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background 0.2s ease, color 0.2s ease',
    whiteSpace: 'nowrap',
    minWidth: 'fit-content'
  });

  const authButtonStyle = {
    background: 'transparent',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: '25px',
    padding: '0.5rem 1rem',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease',
    whiteSpace: 'nowrap',
    minWidth: 'fit-content'
  };

  const signUpButtonStyle = {
    ...authButtonStyle,
    background: 'var(--accent)',
    color: '#000000',
    border: 'none',
    transition: 'background 0.2s ease, color 0.2s ease'
  };

  const profileButtonStyle = {
    background: 'transparent',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: '25px',
    padding: '0.5rem 1rem',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    position: 'relative',
    whiteSpace: 'nowrap'
  };

  const avatarStyle = {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    objectFit: 'cover',
    border: '1px solid var(--border-color)'
  };

  const dropdownStyle = {
    position: 'absolute',
    top: 'calc(100% + 0.5rem)',
    right: 0,
    background: 'var(--glass-bg)',
    backdropFilter: 'blur(10px)',
    border: '1px solid var(--border-color)',
    borderRadius: '12px',
    padding: '0.75rem',
    minWidth: '200px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
    zIndex: 100
  };

  const userInfoStyle = {
    padding: '0.5rem',
    borderBottom: '1px solid var(--border-color)',
    marginBottom: '0.5rem'
  };

  const userNameStyle = {
    color: 'var(--text-primary)',
    fontSize: '14px',
    fontWeight: '600',
    marginBottom: '0.25rem'
  };

  const userEmailStyle = {
    color: 'var(--text-secondary)',
    fontSize: '12px'
  };

  const logoutButtonStyle = {
    width: '100%',
    background: 'transparent',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-color)',
    borderRadius: '8px',
    padding: '0.5rem 1rem',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    justifyContent: 'center'
  };

  return (
    <div style={navContainerStyle}>
      <div style={navBarStyle}>
        <img 
          src="/logos/xverta-logo.png" 
          alt="AltX Logo" 
          style={logoStyle}
        />
        
        {/* Navigation Links */}
        {navLinks.map(link => (
          <button
            key={link.path}
            onClick={() => navigate(link.path)}
            style={getButtonStyle(location.pathname === link.path)}
          >
            {link.label}
          </button>
        ))}

        {/* Authentication Section */}
        {!isAuthenticated ? (
          <>
            <button
              onClick={() => navigate('/login')}
              style={authButtonStyle}
            >
              Login
            </button>
            <button
              onClick={() => navigate('/signup')}
              style={signUpButtonStyle}
            >
              Sign Up
            </button>
          </>
        ) : (
          <div ref={profileMenuRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              style={profileButtonStyle}
            >
              {user?.avatar ? (
                <img src={user.avatar} alt="Profile" style={avatarStyle} />
              ) : (
                <User size={16} />
              )}
              {user?.username || user?.name || 'User'}
              <ChevronDown size={16} />
            </button>

            {isProfileMenuOpen && (
              <div style={dropdownStyle}>
                <div style={userInfoStyle}>
                  {user?.avatar && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                      <img src={user.avatar} alt="Profile" style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }} />
                      <div>
                        <div style={userNameStyle}>{user?.username || user?.name || 'User'}</div>
                        <div style={userEmailStyle}>{user?.email}</div>
                      </div>
                    </div>
                  )}
                  {!user?.avatar && (
                    <>
                      <div style={userNameStyle}>{user?.username || user?.name || 'User'}</div>
                      <div style={userEmailStyle}>{user?.email}</div>
                    </>
                  )}
                </div>
                <button
                  onClick={() => {
                    setIsProfileMenuOpen(false);
                    onLogout();
                  }}
                  style={logoutButtonStyle}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                    e.currentTarget.style.color = '#ef4444';
                    e.currentTarget.style.borderColor = '#ef4444';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-primary)';
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                  }}
                >
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MainNavBar;

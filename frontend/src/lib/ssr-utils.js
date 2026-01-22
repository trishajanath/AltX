// SSR-safe utilities for browser APIs

export const isBrowser = typeof window !== 'undefined';

// Safe window access
export const safeWindow = isBrowser ? window : undefined;

// Safe document access  
export const safeDocument = isBrowser ? document : undefined;

// Safe localStorage wrapper
export const safeLocalStorage = {
  getItem: (key) => {
    if (!isBrowser) return null;
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key, value) => {
    if (!isBrowser) return;
    try {
      localStorage.setItem(key, value);
    } catch {
      // Storage might be full or disabled
    }
  },
  removeItem: (key) => {
    if (!isBrowser) return;
    try {
      localStorage.removeItem(key);
    } catch {
      // Ignore errors
    }
  }
};

// Safe sessionStorage wrapper
export const safeSessionStorage = {
  getItem: (key) => {
    if (!isBrowser) return null;
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem: (key, value) => {
    if (!isBrowser) return;
    try {
      sessionStorage.setItem(key, value);
    } catch {
      // Storage might be full or disabled
    }
  },
  removeItem: (key) => {
    if (!isBrowser) return;
    try {
      sessionStorage.removeItem(key);
    } catch {
      // Ignore errors
    }
  }
};

// Hook for client-only code
export const useIsClient = () => {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  return isClient;
};

import { useState, useEffect } from 'react';

// Component wrapper for client-only rendering
export const ClientOnly = ({ children, fallback = null }) => {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
  }, []);
  
  return mounted ? children : fallback;
};

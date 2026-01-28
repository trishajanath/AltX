/**
 * useSandboxCleanup Hook
 * ======================
 * React hook for automatic sandbox cleanup on preview end.
 * 
 * Features:
 * - Auto-cleanup on component unmount
 * - Auto-cleanup on page unload/navigation
 * - TTL auto-extension while user is active
 * - Manual cleanup trigger
 * 
 * Usage:
 * ```jsx
 * function PreviewPanel({ sessionId }) {
 *   const {
 *     cleanup,
 *     extend,
 *     status,
 *     isActive,
 *   } = useSandboxCleanup(sessionId, {
 *     autoExtend: true,
 *     cleanupOnUnmount: true,
 *   });
 * 
 *   return (
 *     <div>
 *       <button onClick={() => extend(15)}>Extend 15 min</button>
 *       <button onClick={cleanup}>End Preview</button>
 *       {status && <span>TTL: {status.ttl_seconds}s</span>}
 *     </div>
 *   );
 * }
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  cleanupSandbox,
  extendSandboxTTL,
  getCleanupStatus,
  startTTLAutoExtend,
} from '../config/sandboxCleanup';

export function useSandboxCleanup(sessionId, options = {}) {
  const {
    autoExtend = true,
    autoExtendInterval = 10 * 60 * 1000, // 10 minutes
    cleanupOnUnmount = true,
    cleanupOnPageUnload = true,
    pollStatusInterval = null, // Set to e.g. 30000 for status polling
  } = options;

  const [status, setStatus] = useState(null);
  const [isActive, setIsActive] = useState(true);
  const [isCleaningUp, setIsCleaningUp] = useState(false);
  const [error, setError] = useState(null);
  
  const cleanupRef = useRef(false);
  const stopAutoExtendRef = useRef(null);

  // Cleanup function
  const cleanup = useCallback(async (reason = 'manual') => {
    if (!sessionId || cleanupRef.current) {
      return { success: true, alreadyCleaned: true };
    }
    
    cleanupRef.current = true;
    setIsCleaningUp(true);
    setError(null);
    
    try {
      // Stop auto-extend
      if (stopAutoExtendRef.current) {
        stopAutoExtendRef.current();
        stopAutoExtendRef.current = null;
      }
      
      const result = await cleanupSandbox(sessionId, reason);
      
      if (result.success) {
        setIsActive(false);
        console.log(`✅ Sandbox ${sessionId} cleaned up (${reason})`);
      } else {
        setError(result.error);
        console.error(`❌ Cleanup failed: ${result.error}`);
      }
      
      return result;
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsCleaningUp(false);
    }
  }, [sessionId]);

  // Extend TTL
  const extend = useCallback(async (minutes = 15) => {
    if (!sessionId || cleanupRef.current) {
      return { success: false, error: 'Session not active' };
    }
    
    try {
      const result = await extendSandboxTTL(sessionId, minutes);
      
      if (result.success) {
        // Refresh status
        const newStatus = await getCleanupStatus(sessionId);
        setStatus(newStatus);
      }
      
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, [sessionId]);

  // Refresh status
  const refreshStatus = useCallback(async () => {
    if (!sessionId || cleanupRef.current) return null;
    
    try {
      const newStatus = await getCleanupStatus(sessionId);
      setStatus(newStatus);
      return newStatus;
    } catch (err) {
      return null;
    }
  }, [sessionId]);

  // Reset cleanup state (for re-use)
  const reset = useCallback(() => {
    cleanupRef.current = false;
    setIsActive(true);
    setError(null);
    setStatus(null);
  }, []);

  // Setup auto-extend
  useEffect(() => {
    if (!sessionId || !autoExtend || cleanupRef.current) return;
    
    stopAutoExtendRef.current = startTTLAutoExtend(sessionId, autoExtendInterval);
    
    return () => {
      if (stopAutoExtendRef.current) {
        stopAutoExtendRef.current();
        stopAutoExtendRef.current = null;
      }
    };
  }, [sessionId, autoExtend, autoExtendInterval]);

  // Status polling
  useEffect(() => {
    if (!sessionId || !pollStatusInterval || cleanupRef.current) return;
    
    // Initial fetch
    refreshStatus();
    
    const intervalId = setInterval(refreshStatus, pollStatusInterval);
    
    return () => clearInterval(intervalId);
  }, [sessionId, pollStatusInterval, refreshStatus]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupOnUnmount && sessionId && !cleanupRef.current) {
        // Fire and forget cleanup
        cleanupSandbox(sessionId, 'unmount').catch(console.error);
      }
    };
  }, [sessionId, cleanupOnUnmount]);

  // Cleanup on page unload
  useEffect(() => {
    if (!cleanupOnPageUnload || !sessionId) return;
    
    const handleBeforeUnload = (event) => {
      if (!cleanupRef.current) {
        // Use sendBeacon for reliable cleanup on page unload
        const url = `/api/cleanup/container`;
        const data = JSON.stringify({
          session_id: sessionId,
          reason: 'page_unload'
        });
        
        // Try sendBeacon first (most reliable)
        if (navigator.sendBeacon) {
          navigator.sendBeacon(url, data);
        } else {
          // Fallback to sync XHR (blocking but reliable)
          const xhr = new XMLHttpRequest();
          xhr.open('POST', url, false); // sync
          xhr.setRequestHeader('Content-Type', 'application/json');
          xhr.send(data);
        }
      }
    };
    
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden' && !cleanupRef.current) {
        // Page is being hidden, might be closing
        // Use sendBeacon for non-blocking cleanup
        if (navigator.sendBeacon && sessionId) {
          const url = `/api/cleanup/container`;
          const data = JSON.stringify({
            session_id: sessionId,
            reason: 'visibility_hidden'
          });
          navigator.sendBeacon(url, data);
        }
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [sessionId, cleanupOnPageUnload]);

  return {
    // Actions
    cleanup,
    extend,
    refreshStatus,
    reset,
    
    // State
    status,
    isActive,
    isCleaningUp,
    error,
    
    // Computed
    ttlSeconds: status?.ttl_seconds ?? null,
    expiresAt: status?.expires_at ? new Date(status.expires_at) : null,
  };
}

export default useSandboxCleanup;

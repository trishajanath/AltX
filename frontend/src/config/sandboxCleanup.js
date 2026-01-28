/**
 * Sandbox Cleanup Service
 * =======================
 * Frontend service for managing sandbox container cleanup.
 * 
 * Features:
 * - Cleanup on preview end
 * - TTL extension
 * - Status monitoring
 */

import { apiUrl } from './api';

/**
 * Clean up a sandbox container
 * @param {string} sessionId - The session ID to clean up
 * @param {string} reason - Reason for cleanup
 * @returns {Promise<{success: boolean, details: object}>}
 */
export async function cleanupSandbox(sessionId, reason = 'preview_ended') {
  try {
    const response = await fetch(apiUrl('/api/cleanup/container'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        reason: reason,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      console.error('Cleanup failed:', error);
      return { success: false, error: error.detail || 'Cleanup failed' };
    }

    const result = await response.json();
    console.log(`🧹 Cleaned up sandbox ${sessionId}:`, result);
    return result;
  } catch (error) {
    console.error('Cleanup request failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Extend the TTL of a sandbox container
 * @param {string} sessionId - The session ID
 * @param {number} minutes - Additional minutes to add
 * @returns {Promise<{success: boolean}>}
 */
export async function extendSandboxTTL(sessionId, minutes = 15) {
  try {
    const response = await fetch(apiUrl(`/api/cleanup/extend/${sessionId}?minutes=${minutes}`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      return { success: false, error: error.detail };
    }

    const result = await response.json();
    console.log(`⏰ Extended TTL for ${sessionId} by ${minutes} minutes`);
    return result;
  } catch (error) {
    console.error('TTL extension failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Get cleanup status for a session or overall system
 * @param {string|null} sessionId - Optional session ID
 * @returns {Promise<object>}
 */
export async function getCleanupStatus(sessionId = null) {
  try {
    const url = sessionId 
      ? apiUrl(`/api/cleanup/status/${sessionId}`)
      : apiUrl('/api/cleanup/status');
    
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      return { error: error.detail };
    }

    return await response.json();
  } catch (error) {
    console.error('Status request failed:', error);
    return { error: error.message };
  }
}

/**
 * Cleanup hook for React components
 * Automatically cleans up sandbox when component unmounts
 * 
 * Usage:
 * ```jsx
 * const cleanup = useSandboxCleanup(sessionId);
 * // cleanup.extend() - extend TTL
 * // cleanup.cleanup() - manual cleanup
 * // auto-cleans on unmount
 * ```
 */
export function createCleanupHandler(sessionId) {
  let isCleanedUp = false;
  
  const handler = {
    sessionId,
    
    async cleanup(reason = 'manual') {
      if (isCleanedUp) return { success: true, alreadyCleaned: true };
      isCleanedUp = true;
      return await cleanupSandbox(sessionId, reason);
    },
    
    async extend(minutes = 15) {
      if (isCleanedUp) return { success: false, error: 'Already cleaned up' };
      return await extendSandboxTTL(sessionId, minutes);
    },
    
    async getStatus() {
      return await getCleanupStatus(sessionId);
    },
    
    // Call this when preview ends (component unmount, navigation, etc.)
    async onPreviewEnd() {
      return await this.cleanup('preview_ended');
    },
    
    // Reset cleanup state (e.g., after restarting preview)
    reset() {
      isCleanedUp = false;
    }
  };
  
  return handler;
}

/**
 * Auto-extend TTL while user is active
 * @param {string} sessionId - The session ID
 * @param {number} intervalMs - Check interval in milliseconds (default: 10 min)
 * @returns {function} Stop function to call on cleanup
 */
export function startTTLAutoExtend(sessionId, intervalMs = 10 * 60 * 1000) {
  let lastActivity = Date.now();
  let intervalId = null;
  
  // Track user activity
  const activityHandler = () => {
    lastActivity = Date.now();
  };
  
  window.addEventListener('mousemove', activityHandler);
  window.addEventListener('keypress', activityHandler);
  window.addEventListener('click', activityHandler);
  window.addEventListener('scroll', activityHandler);
  
  // Periodic TTL extension if user is active
  intervalId = setInterval(async () => {
    // Only extend if user was active in the last 5 minutes
    if (Date.now() - lastActivity < 5 * 60 * 1000) {
      console.log('User active, extending sandbox TTL...');
      await extendSandboxTTL(sessionId, 15);
    } else {
      console.log('User inactive, not extending TTL');
    }
  }, intervalMs);
  
  // Return stop function
  return () => {
    if (intervalId) {
      clearInterval(intervalId);
    }
    window.removeEventListener('mousemove', activityHandler);
    window.removeEventListener('keypress', activityHandler);
    window.removeEventListener('click', activityHandler);
    window.removeEventListener('scroll', activityHandler);
  };
}

export default {
  cleanupSandbox,
  extendSandboxTTL,
  getCleanupStatus,
  createCleanupHandler,
  startTTLAutoExtend,
};

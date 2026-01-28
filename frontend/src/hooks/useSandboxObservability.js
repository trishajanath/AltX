/**
 * useSandboxObservability Hook
 * =============================
 * React hook for consuming sandbox observability data.
 * 
 * Features:
 * - Real-time log streaming
 * - Auto-refreshing health metrics
 * - Failure detection and analysis
 * - Complete debug snapshots
 * 
 * Usage:
 *   const {
 *     logs,
 *     health,
 *     failures,
 *     snapshot,
 *     isLoading,
 *     error,
 *     subscribeToLogs,
 *     refresh,
 *   } = useSandboxObservability(sessionId);
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  sandboxObservability,
  getHealthStateColor,
  getHealthStateIcon,
  formatUptime,
  formatLogEntry,
} from '../services/sandboxObservability';

// =============================================================================
// Main Hook
// =============================================================================

/**
 * Hook for sandbox observability
 * @param {string} sessionId - Session identifier
 * @param {Object} [options]
 * @param {boolean} [options.autoRefresh=true] - Auto-refresh health metrics
 * @param {number} [options.refreshInterval=5000] - Refresh interval in ms
 * @param {boolean} [options.streamLogs=false] - Enable real-time log streaming
 * @param {number} [options.logTail=100] - Number of logs to fetch
 */
export function useSandboxObservability(sessionId, {
  autoRefresh = true,
  refreshInterval = 5000,
  streamLogs = false,
  logTail = 100,
} = {}) {
  // State
  const [logs, setLogs] = useState([]);
  const [health, setHealth] = useState(null);
  const [failures, setFailures] = useState([]);
  const [failureAnalysis, setFailureAnalysis] = useState(null);
  const [snapshot, setSnapshot] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Refs
  const unsubscribeRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // ==========================================================================
  // Data Fetching
  // ==========================================================================

  /**
   * Fetch logs
   */
  const fetchLogs = useCallback(async () => {
    if (!sessionId) return;

    try {
      const result = await sandboxObservability.getLogs(sessionId, { tail: logTail });
      setLogs(result.logs);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      // Don't set error for log fetch failures - they're non-critical
    }
  }, [sessionId, logTail]);

  /**
   * Fetch health metrics
   */
  const fetchHealth = useCallback(async () => {
    if (!sessionId) return;

    try {
      const result = await sandboxObservability.getHealth(sessionId);
      setHealth(result);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch health:', err);
      setError(err.message);
    }
  }, [sessionId]);

  /**
   * Fetch failures
   */
  const fetchFailures = useCallback(async () => {
    if (!sessionId) return;

    try {
      const result = await sandboxObservability.getFailures(sessionId);
      setFailures(result.failures);
    } catch (err) {
      console.error('Failed to fetch failures:', err);
    }
  }, [sessionId]);

  /**
   * Fetch failure analysis
   */
  const fetchFailureAnalysis = useCallback(async () => {
    if (!sessionId) return;

    try {
      const result = await sandboxObservability.analyzeFailure(sessionId);
      setFailureAnalysis(result);
    } catch (err) {
      console.error('Failed to fetch failure analysis:', err);
    }
  }, [sessionId]);

  /**
   * Fetch complete snapshot
   */
  const fetchSnapshot = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    try {
      const result = await sandboxObservability.getSnapshot(sessionId);
      setSnapshot(result);
      setLogs(result.recent_logs);
      setHealth(result.health);
      setFailures(result.failures);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch snapshot:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  /**
   * Refresh all data
   */
  const refresh = useCallback(async () => {
    await Promise.all([
      fetchLogs(),
      fetchHealth(),
      fetchFailures(),
    ]);
  }, [fetchLogs, fetchHealth, fetchFailures]);

  // ==========================================================================
  // Log Streaming
  // ==========================================================================

  /**
   * Start log streaming
   */
  const startLogStream = useCallback(() => {
    if (!sessionId || unsubscribeRef.current) return;

    unsubscribeRef.current = sandboxObservability.subscribeToLogs(sessionId, (log) => {
      setLogs((prev) => {
        // Avoid duplicates
        const exists = prev.some(
          (l) => l.timestamp === log.timestamp && l.message === log.message
        );
        if (exists) return prev;

        // Keep tail limit
        const newLogs = [...prev, log];
        if (newLogs.length > logTail) {
          return newLogs.slice(-logTail);
        }
        return newLogs;
      });
    });
  }, [sessionId, logTail]);

  /**
   * Stop log streaming
   */
  const stopLogStream = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
  }, []);

  // ==========================================================================
  // Effects
  // ==========================================================================

  // Initial fetch when sessionId changes
  useEffect(() => {
    if (sessionId) {
      refresh();
    }
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-refresh health
  useEffect(() => {
    if (!autoRefresh || !sessionId) return;

    refreshTimerRef.current = setInterval(() => {
      fetchHealth();
      fetchFailures();
    }, refreshInterval);

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [autoRefresh, refreshInterval, sessionId, fetchHealth, fetchFailures]);

  // Log streaming
  useEffect(() => {
    if (streamLogs && sessionId) {
      // Fetch initial logs then start streaming
      fetchLogs().then(startLogStream);
    }

    return () => {
      stopLogStream();
    };
  }, [streamLogs, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLogStream();
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [stopLogStream]);

  // ==========================================================================
  // Computed Values
  // ==========================================================================

  const hasFailures = failures.length > 0;
  const isHealthy = health?.state === 'healthy';
  const isUnhealthy = health?.state === 'unhealthy' || health?.state === 'failed';
  const healthIcon = health ? getHealthStateIcon(health.state) : '❓';
  const healthColor = health ? getHealthStateColor(health.state) : '#6b7280';

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // Data
    logs,
    health,
    failures,
    failureAnalysis,
    snapshot,

    // Status
    isLoading,
    error,
    hasFailures,
    isHealthy,
    isUnhealthy,
    healthIcon,
    healthColor,

    // Actions
    refresh,
    fetchLogs,
    fetchHealth,
    fetchFailures,
    fetchFailureAnalysis,
    fetchSnapshot,

    // Log streaming
    startLogStream,
    stopLogStream,
    isStreaming: !!unsubscribeRef.current,
  };
}

// =============================================================================
// Specialized Hooks
// =============================================================================

/**
 * Hook for just log streaming
 * @param {string} sessionId 
 * @param {Object} [options]
 * @param {number} [options.maxLogs=200]
 */
export function useSandboxLogs(sessionId, { maxLogs = 200 } = {}) {
  const [logs, setLogs] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const unsubscribeRef = useRef(null);

  const startStreaming = useCallback(async () => {
    if (!sessionId || isStreaming) return;

    // Fetch initial logs
    try {
      const result = await sandboxObservability.getLogs(sessionId, { tail: maxLogs });
      setLogs(result.logs);
    } catch (err) {
      console.error('Failed to fetch initial logs:', err);
    }

    // Start streaming
    unsubscribeRef.current = sandboxObservability.subscribeToLogs(sessionId, (log) => {
      setLogs((prev) => {
        const newLogs = [...prev, log];
        return newLogs.slice(-maxLogs);
      });
    });
    setIsStreaming(true);
  }, [sessionId, maxLogs, isStreaming]);

  const stopStreaming = useCallback(() => {
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, [stopStreaming]);

  return {
    logs,
    isStreaming,
    startStreaming,
    stopStreaming,
    clearLogs,
    formattedLogs: logs.map(formatLogEntry),
  };
}

/**
 * Hook for health monitoring with alerts
 * @param {string} sessionId 
 * @param {Object} [options]
 * @param {number} [options.pollInterval=3000]
 * @param {function} [options.onHealthChange]
 * @param {function} [options.onFailure]
 */
export function useSandboxHealthMonitor(sessionId, {
  pollInterval = 3000,
  onHealthChange,
  onFailure,
} = {}) {
  const [health, setHealth] = useState(null);
  const [previousState, setPreviousState] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const intervalRef = useRef(null);

  const startMonitoring = useCallback(() => {
    if (!sessionId || isMonitoring) return;

    const poll = async () => {
      try {
        const result = await sandboxObservability.getHealth(sessionId);
        setHealth(result);

        // Check for state change
        if (previousState && result.state !== previousState) {
          onHealthChange?.(result.state, previousState);

          // Check for failure
          if (result.state === 'failed' || result.state === 'unhealthy') {
            const analysis = await sandboxObservability.analyzeFailure(sessionId);
            onFailure?.(analysis);
          }
        }

        setPreviousState(result.state);
      } catch (err) {
        console.error('Health poll failed:', err);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, pollInterval);
    setIsMonitoring(true);
  }, [sessionId, pollInterval, previousState, isMonitoring, onHealthChange, onFailure]);

  const stopMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsMonitoring(false);
  }, []);

  useEffect(() => {
    return () => {
      stopMonitoring();
    };
  }, [stopMonitoring]);

  return {
    health,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    isHealthy: health?.state === 'healthy',
    isUnhealthy: health?.state === 'unhealthy' || health?.state === 'failed',
    uptime: health ? formatUptime(health.uptime_seconds) : null,
    responseTime: health?.last_check?.response_time_ms,
  };
}

/**
 * Hook for waiting until sandbox is healthy
 * @param {string} sessionId 
 * @param {Object} [options]
 * @param {number} [options.timeout=60000]
 * @param {number} [options.interval=2000]
 */
export function useWaitForHealthy(sessionId, {
  timeout = 60000,
  interval = 2000,
} = {}) {
  const [status, setStatus] = useState('idle'); // idle, waiting, success, failed, timeout
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  const startWaiting = useCallback(async () => {
    if (!sessionId) return;

    setStatus('waiting');
    setError(null);

    try {
      const result = await sandboxObservability.waitForHealthy(sessionId, {
        timeout,
        interval,
        onUpdate: setHealth,
      });
      setHealth(result);
      setStatus('success');
      return result;
    } catch (err) {
      setError(err.message);
      setStatus(err.message.includes('Timeout') ? 'timeout' : 'failed');
      throw err;
    }
  }, [sessionId, timeout, interval]);

  const reset = useCallback(() => {
    setStatus('idle');
    setHealth(null);
    setError(null);
  }, []);

  return {
    status,
    health,
    error,
    isWaiting: status === 'waiting',
    isSuccess: status === 'success',
    isFailed: status === 'failed' || status === 'timeout',
    startWaiting,
    reset,
  };
}

export default useSandboxObservability;

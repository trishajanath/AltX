/**
 * Sandbox Observability Service
 * ==============================
 * Frontend service for sandbox preview observability.
 * 
 * Provides:
 * - Log retrieval and streaming
 * - Health metrics fetching
 * - Failure detection and analysis
 * - Complete debug snapshots
 * 
 * Usage:
 *   import { sandboxObservability } from './services/sandboxObservability';
 *   
 *   const logs = await sandboxObservability.getLogs(sessionId);
 *   const health = await sandboxObservability.getHealth(sessionId);
 *   const snapshot = await sandboxObservability.getSnapshot(sessionId);
 */

// Configuration
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const OBSERVABILITY_BASE = `${API_BASE}/api/observability`;

// =============================================================================
// Types
// =============================================================================

/**
 * @typedef {'debug'|'info'|'warning'|'error'|'critical'} LogLevel
 */

/**
 * @typedef {'unknown'|'starting'|'healthy'|'degraded'|'unhealthy'|'failed'} HealthState
 */

/**
 * @typedef {'build_error'|'dependency_error'|'import_error'|'syntax_error'|'runtime_error'|'port_binding_error'|'timeout_error'|'network_error'|'resource_error'|'config_error'|'unknown_error'} FailureCategory
 */

/**
 * @typedef {Object} LogEntry
 * @property {string} timestamp
 * @property {LogLevel} level
 * @property {string} message
 * @property {string} source
 * @property {string} session_id
 * @property {string} [raw_line]
 */

/**
 * @typedef {Object} HealthMetrics
 * @property {string} session_id
 * @property {HealthState} state
 * @property {number} uptime_seconds
 * @property {{total: number, failed: number, success_rate: number}} health_checks
 * @property {{time: string, response_time_ms: number}} last_check
 * @property {number} avg_response_time_ms
 * @property {{memory_mb: number, cpu_percent: number}} resources
 * @property {number} restart_count
 * @property {string[]} errors
 */

/**
 * @typedef {Object} StartupFailure
 * @property {FailureCategory} category
 * @property {string} message
 * @property {string} details
 * @property {string} suggestion
 * @property {string} timestamp
 * @property {string[]} relevant_logs
 * @property {string} [traceback]
 */

/**
 * @typedef {Object} FailureAnalysis
 * @property {boolean} has_failure
 * @property {StartupFailure} [failure]
 * @property {string[]} actionable_steps
 */

/**
 * @typedef {Object} ObservabilitySnapshot
 * @property {string} session_id
 * @property {string} [container_name]
 * @property {string} status
 * @property {HealthMetrics} health
 * @property {LogEntry[]} recent_logs
 * @property {StartupFailure[]} failures
 * @property {Array<{timestamp: string, event: string, data: Object}>} timeline
 * @property {Object} debug_context
 */

// =============================================================================
// Log Level Utilities
// =============================================================================

/**
 * Get color for log level (for UI rendering)
 * @param {LogLevel} level 
 * @returns {string}
 */
export function getLogLevelColor(level) {
  const colors = {
    debug: '#6b7280',    // gray
    info: '#3b82f6',     // blue
    warning: '#f59e0b',  // amber
    error: '#ef4444',    // red
    critical: '#dc2626', // dark red
  };
  return colors[level] || colors.info;
}

/**
 * Get badge variant for log level
 * @param {LogLevel} level 
 * @returns {string}
 */
export function getLogLevelBadge(level) {
  const badges = {
    debug: 'secondary',
    info: 'info',
    warning: 'warning',
    error: 'destructive',
    critical: 'destructive',
  };
  return badges[level] || 'secondary';
}

/**
 * Get icon for health state
 * @param {HealthState} state 
 * @returns {string}
 */
export function getHealthStateIcon(state) {
  const icons = {
    unknown: '❓',
    starting: '🔄',
    healthy: '✅',
    degraded: '⚠️',
    unhealthy: '❌',
    failed: '💥',
  };
  return icons[state] || icons.unknown;
}

/**
 * Get color for health state
 * @param {HealthState} state 
 * @returns {string}
 */
export function getHealthStateColor(state) {
  const colors = {
    unknown: '#6b7280',
    starting: '#3b82f6',
    healthy: '#22c55e',
    degraded: '#f59e0b',
    unhealthy: '#ef4444',
    failed: '#dc2626',
  };
  return colors[state] || colors.unknown;
}

// =============================================================================
// Main Service Class
// =============================================================================

class SandboxObservabilityService {
  constructor() {
    this._eventSources = new Map(); // session_id -> EventSource
    this._logCallbacks = new Map(); // session_id -> Set<callback>
  }

  /**
   * Get logs for a session
   * @param {string} sessionId 
   * @param {Object} [options]
   * @param {number} [options.tail=100]
   * @param {LogLevel} [options.level]
   * @returns {Promise<{session_id: string, count: number, logs: LogEntry[]}>}
   */
  async getLogs(sessionId, { tail = 100, level } = {}) {
    const params = new URLSearchParams();
    params.set('tail', tail.toString());
    if (level) params.set('level', level);

    const response = await fetch(
      `${OBSERVABILITY_BASE}/logs/${sessionId}?${params}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch logs: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Subscribe to real-time log streaming
   * @param {string} sessionId 
   * @param {function(LogEntry): void} callback 
   * @returns {function(): void} Unsubscribe function
   */
  subscribeToLogs(sessionId, callback) {
    // Add callback to set
    if (!this._logCallbacks.has(sessionId)) {
      this._logCallbacks.set(sessionId, new Set());
    }
    this._logCallbacks.get(sessionId).add(callback);

    // Start EventSource if not already running
    if (!this._eventSources.has(sessionId)) {
      this._startLogStream(sessionId);
    }

    // Return unsubscribe function
    return () => {
      const callbacks = this._logCallbacks.get(sessionId);
      if (callbacks) {
        callbacks.delete(callback);
        if (callbacks.size === 0) {
          this._stopLogStream(sessionId);
        }
      }
    };
  }

  /**
   * Start log stream for a session
   * @private
   */
  _startLogStream(sessionId) {
    const eventSource = new EventSource(
      `${OBSERVABILITY_BASE}/logs/${sessionId}/stream`
    );

    eventSource.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        const callbacks = this._logCallbacks.get(sessionId);
        if (callbacks) {
          callbacks.forEach((cb) => cb(log));
        }
      } catch (e) {
        console.error('Failed to parse log event:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('Log stream error:', error);
      // Auto-reconnect after delay
      setTimeout(() => {
        if (this._logCallbacks.has(sessionId) && 
            this._logCallbacks.get(sessionId).size > 0) {
          this._stopLogStream(sessionId);
          this._startLogStream(sessionId);
        }
      }, 5000);
    };

    this._eventSources.set(sessionId, eventSource);
  }

  /**
   * Stop log stream for a session
   * @private
   */
  _stopLogStream(sessionId) {
    const eventSource = this._eventSources.get(sessionId);
    if (eventSource) {
      eventSource.close();
      this._eventSources.delete(sessionId);
    }
    this._logCallbacks.delete(sessionId);
  }

  /**
   * Get health metrics for a session
   * @param {string} sessionId 
   * @returns {Promise<HealthMetrics>}
   */
  async getHealth(sessionId) {
    const response = await fetch(
      `${OBSERVABILITY_BASE}/health/${sessionId}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch health: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get detected failures for a session
   * @param {string} sessionId 
   * @returns {Promise<{session_id: string, count: number, failures: StartupFailure[]}>}
   */
  async getFailures(sessionId) {
    const response = await fetch(
      `${OBSERVABILITY_BASE}/failures/${sessionId}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch failures: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Analyze failures and get actionable steps
   * @param {string} sessionId 
   * @returns {Promise<FailureAnalysis>}
   */
  async analyzeFailure(sessionId) {
    const response = await fetch(
      `${OBSERVABILITY_BASE}/failures/${sessionId}/analyze`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to analyze failure: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get complete observability snapshot
   * @param {string} sessionId 
   * @returns {Promise<ObservabilitySnapshot>}
   */
  async getSnapshot(sessionId) {
    const response = await fetch(
      `${OBSERVABILITY_BASE}/snapshot/${sessionId}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch snapshot: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Clear observability data for a session
   * @param {string} sessionId 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clearSession(sessionId) {
    // Stop any active log streams
    this._stopLogStream(sessionId);

    const response = await fetch(
      `${OBSERVABILITY_BASE}/session/${sessionId}`,
      {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to clear session: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get summary of all active sessions
   * @returns {Promise<{total_sessions: number, sessions: Array}>}
   */
  async getSummary() {
    const response = await fetch(
      `${OBSERVABILITY_BASE}/summary`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch summary: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Poll for health status until healthy or timeout
   * @param {string} sessionId 
   * @param {Object} [options]
   * @param {number} [options.interval=2000] - Poll interval in ms
   * @param {number} [options.timeout=60000] - Max wait time in ms
   * @param {function(HealthMetrics): void} [options.onUpdate] - Called on each poll
   * @returns {Promise<HealthMetrics>}
   */
  async waitForHealthy(sessionId, { interval = 2000, timeout = 60000, onUpdate } = {}) {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      try {
        const health = await this.getHealth(sessionId);
        
        if (onUpdate) {
          onUpdate(health);
        }

        if (health.state === 'healthy') {
          return health;
        }

        if (health.state === 'failed') {
          throw new Error('Health check failed');
        }

        await new Promise((resolve) => setTimeout(resolve, interval));
      } catch (error) {
        if (Date.now() - startTime >= timeout) {
          throw error;
        }
        await new Promise((resolve) => setTimeout(resolve, interval));
      }
    }

    throw new Error(`Timeout waiting for healthy state after ${timeout}ms`);
  }

  /**
   * Cleanup all active streams
   */
  cleanup() {
    for (const sessionId of this._eventSources.keys()) {
      this._stopLogStream(sessionId);
    }
  }
}

// Export singleton instance
export const sandboxObservability = new SandboxObservabilityService();

// =============================================================================
// Convenience Functions
// =============================================================================

/**
 * Format log entry for display
 * @param {LogEntry} log 
 * @returns {string}
 */
export function formatLogEntry(log) {
  const time = new Date(log.timestamp).toLocaleTimeString();
  const level = log.level.toUpperCase().padEnd(8);
  return `[${time}] ${level} ${log.message}`;
}

/**
 * Format uptime for display
 * @param {number} seconds 
 * @returns {string}
 */
export function formatUptime(seconds) {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (minutes < 60) {
    return `${minutes}m ${secs}s`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

/**
 * Format bytes for display
 * @param {number} mb 
 * @returns {string}
 */
export function formatMemory(mb) {
  if (mb === null || mb === undefined) return 'N/A';
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(2)} GB`;
  }
  return `${mb.toFixed(1)} MB`;
}

/**
 * Get failure category display name
 * @param {FailureCategory} category 
 * @returns {string}
 */
export function getFailureCategoryName(category) {
  const names = {
    build_error: 'Build Error',
    dependency_error: 'Dependency Error',
    import_error: 'Import Error',
    syntax_error: 'Syntax Error',
    runtime_error: 'Runtime Error',
    port_binding_error: 'Port Binding Error',
    timeout_error: 'Timeout Error',
    network_error: 'Network Error',
    resource_error: 'Resource Error',
    config_error: 'Configuration Error',
    unknown_error: 'Unknown Error',
  };
  return names[category] || 'Error';
}

/**
 * Get failure category icon
 * @param {FailureCategory} category 
 * @returns {string}
 */
export function getFailureCategoryIcon(category) {
  const icons = {
    build_error: '🔨',
    dependency_error: '📦',
    import_error: '📥',
    syntax_error: '⚠️',
    runtime_error: '💥',
    port_binding_error: '🔌',
    timeout_error: '⏰',
    network_error: '🌐',
    resource_error: '💾',
    config_error: '⚙️',
    unknown_error: '❓',
  };
  return icons[category] || '❓';
}

export default sandboxObservability;

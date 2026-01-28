/**
 * SandboxDebugPanel Component
 * ============================
 * A comprehensive debug panel for sandbox preview observability.
 * 
 * Features:
 * - Real-time log viewer with filtering
 * - Health metrics dashboard
 * - Failure detection and actionable suggestions
 * - Resource usage monitoring
 * - Collapsible panel design
 * 
 * Usage:
 *   <SandboxDebugPanel sessionId={sessionId} />
 *   <SandboxDebugPanel sessionId={sessionId} expanded={true} onClose={handleClose} />
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useSandboxObservability, useSandboxLogs } from '../hooks/useSandboxObservability';
import {
  getLogLevelColor,
  getHealthStateIcon,
  getHealthStateColor,
  getFailureCategoryIcon,
  getFailureCategoryName,
  formatUptime,
  formatMemory,
} from '../services/sandboxObservability';

// =============================================================================
// Styles
// =============================================================================

const styles = {
  panel: {
    position: 'fixed',
    bottom: 0,
    right: 0,
    width: '450px',
    maxHeight: '500px',
    backgroundColor: '#1e1e1e',
    borderTopLeftRadius: '12px',
    boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.3)',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    fontSize: '13px',
    color: '#e0e0e0',
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  panelCollapsed: {
    maxHeight: '44px',
    cursor: 'pointer',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 16px',
    backgroundColor: '#252526',
    borderBottom: '1px solid #333',
    cursor: 'pointer',
    userSelect: 'none',
  },
  headerTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: 600,
  },
  headerBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '2px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 500,
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  iconButton: {
    background: 'none',
    border: 'none',
    color: '#808080',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    fontSize: '16px',
    lineHeight: 1,
  },
  tabs: {
    display: 'flex',
    backgroundColor: '#252526',
    borderBottom: '1px solid #333',
  },
  tab: {
    flex: 1,
    padding: '8px 12px',
    backgroundColor: 'transparent',
    border: 'none',
    color: '#808080',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    transition: 'all 0.15s',
    borderBottom: '2px solid transparent',
  },
  tabActive: {
    color: '#fff',
    borderBottomColor: '#007acc',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: '12px',
  },
  // Logs tab
  logsContainer: {
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: '11px',
    lineHeight: 1.5,
  },
  logEntry: {
    display: 'flex',
    gap: '8px',
    padding: '2px 0',
    borderBottom: '1px solid #2a2a2a',
  },
  logTime: {
    color: '#808080',
    flexShrink: 0,
  },
  logLevel: {
    width: '60px',
    flexShrink: 0,
    textTransform: 'uppercase',
    fontWeight: 600,
  },
  logMessage: {
    flex: 1,
    wordBreak: 'break-word',
  },
  logControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
    padding: '8px',
    backgroundColor: '#252526',
    borderRadius: '6px',
  },
  select: {
    backgroundColor: '#3c3c3c',
    border: '1px solid #555',
    borderRadius: '4px',
    color: '#e0e0e0',
    padding: '4px 8px',
    fontSize: '11px',
  },
  // Health tab
  healthGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
  },
  healthCard: {
    backgroundColor: '#252526',
    borderRadius: '8px',
    padding: '12px',
  },
  healthCardLabel: {
    fontSize: '11px',
    color: '#808080',
    marginBottom: '4px',
  },
  healthCardValue: {
    fontSize: '18px',
    fontWeight: 600,
  },
  // Failures tab
  failureCard: {
    backgroundColor: '#3c1f1f',
    border: '1px solid #5c2f2f',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '12px',
  },
  failureHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '8px',
  },
  failureTitle: {
    fontWeight: 600,
    color: '#ff6b6b',
  },
  failureDetails: {
    backgroundColor: '#2d1515',
    borderRadius: '4px',
    padding: '8px',
    fontFamily: 'monospace',
    fontSize: '11px',
    marginBottom: '8px',
    color: '#ffaaaa',
    wordBreak: 'break-word',
  },
  suggestionBox: {
    backgroundColor: '#1a3d1a',
    border: '1px solid #2d5a2d',
    borderRadius: '6px',
    padding: '10px',
    marginTop: '8px',
  },
  suggestionTitle: {
    fontWeight: 600,
    color: '#7dff7d',
    marginBottom: '6px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  suggestionList: {
    margin: 0,
    paddingLeft: '20px',
    color: '#a0d8a0',
  },
  // Traceback
  traceback: {
    backgroundColor: '#1a1a1a',
    borderRadius: '4px',
    padding: '8px',
    fontFamily: 'monospace',
    fontSize: '10px',
    whiteSpace: 'pre-wrap',
    color: '#ff8888',
    maxHeight: '150px',
    overflow: 'auto',
  },
  // Empty states
  emptyState: {
    textAlign: 'center',
    padding: '24px',
    color: '#808080',
  },
};

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Log Viewer Tab
 */
function LogsTab({ sessionId }) {
  const { logs, isStreaming, startStreaming, stopStreaming, clearLogs } = useSandboxLogs(sessionId);
  const [levelFilter, setLevelFilter] = useState('all');
  const logsEndRef = useRef(null);
  const containerRef = useRef(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (logsEndRef.current && isStreaming) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs.length, isStreaming]);

  // Start streaming on mount
  useEffect(() => {
    startStreaming();
    return () => stopStreaming();
  }, [sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredLogs = useMemo(() => {
    if (levelFilter === 'all') return logs;
    return logs.filter((log) => log.level === levelFilter);
  }, [logs, levelFilter]);

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <div>
      <div style={styles.logControls}>
        <select
          style={styles.select}
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
        >
          <option value="all">All Levels</option>
          <option value="error">Errors</option>
          <option value="warning">Warnings</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>
        <button
          style={{ ...styles.iconButton, color: isStreaming ? '#4caf50' : '#808080' }}
          onClick={() => (isStreaming ? stopStreaming() : startStreaming())}
          title={isStreaming ? 'Pause streaming' : 'Resume streaming'}
        >
          {isStreaming ? '⏸' : '▶'}
        </button>
        <button
          style={styles.iconButton}
          onClick={clearLogs}
          title="Clear logs"
        >
          🗑
        </button>
        <span style={{ marginLeft: 'auto', color: '#808080', fontSize: '11px' }}>
          {filteredLogs.length} logs
        </span>
      </div>

      <div ref={containerRef} style={styles.logsContainer}>
        {filteredLogs.length === 0 ? (
          <div style={styles.emptyState}>
            {isStreaming ? 'Waiting for logs...' : 'No logs available'}
          </div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} style={styles.logEntry}>
              <span style={styles.logTime}>{formatTime(log.timestamp)}</span>
              <span style={{ ...styles.logLevel, color: getLogLevelColor(log.level) }}>
                {log.level}
              </span>
              <span style={styles.logMessage}>{log.message}</span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}

/**
 * Health Metrics Tab
 */
function HealthTab({ health }) {
  if (!health) {
    return <div style={styles.emptyState}>Loading health metrics...</div>;
  }

  const stateColor = getHealthStateColor(health.state);
  const stateIcon = getHealthStateIcon(health.state);

  return (
    <div>
      {/* Status Banner */}
      <div
        style={{
          ...styles.healthCard,
          backgroundColor: `${stateColor}20`,
          border: `1px solid ${stateColor}40`,
          marginBottom: '12px',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '24px', marginBottom: '4px' }}>{stateIcon}</div>
        <div style={{ fontWeight: 600, color: stateColor, textTransform: 'uppercase' }}>
          {health.state}
        </div>
      </div>

      {/* Metrics Grid */}
      <div style={styles.healthGrid}>
        <div style={styles.healthCard}>
          <div style={styles.healthCardLabel}>Uptime</div>
          <div style={styles.healthCardValue}>{formatUptime(health.uptime_seconds)}</div>
        </div>

        <div style={styles.healthCard}>
          <div style={styles.healthCardLabel}>Response Time</div>
          <div style={styles.healthCardValue}>
            {health.last_check?.response_time_ms != null
              ? `${Math.round(health.last_check.response_time_ms)}ms`
              : 'N/A'}
          </div>
        </div>

        <div style={styles.healthCard}>
          <div style={styles.healthCardLabel}>Health Checks</div>
          <div style={styles.healthCardValue}>
            {health.health_checks.success_rate}%
            <span style={{ fontSize: '11px', color: '#808080', marginLeft: '4px' }}>
              ({health.health_checks.total - health.health_checks.failed}/{health.health_checks.total})
            </span>
          </div>
        </div>

        <div style={styles.healthCard}>
          <div style={styles.healthCardLabel}>Avg Response</div>
          <div style={styles.healthCardValue}>
            {health.avg_response_time_ms > 0
              ? `${Math.round(health.avg_response_time_ms)}ms`
              : 'N/A'}
          </div>
        </div>

        {health.resources?.memory_mb != null && (
          <div style={styles.healthCard}>
            <div style={styles.healthCardLabel}>Memory</div>
            <div style={styles.healthCardValue}>{formatMemory(health.resources.memory_mb)}</div>
          </div>
        )}

        {health.resources?.cpu_percent != null && (
          <div style={styles.healthCard}>
            <div style={styles.healthCardLabel}>CPU</div>
            <div style={styles.healthCardValue}>{health.resources.cpu_percent.toFixed(1)}%</div>
          </div>
        )}
      </div>

      {/* Errors */}
      {health.errors?.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <div style={{ fontWeight: 600, marginBottom: '8px', color: '#ff6b6b' }}>
            Recent Errors
          </div>
          {health.errors.map((error, index) => (
            <div
              key={index}
              style={{
                backgroundColor: '#3c1f1f',
                borderRadius: '4px',
                padding: '6px 8px',
                fontSize: '11px',
                marginBottom: '4px',
                color: '#ffaaaa',
              }}
            >
              {error}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Failures Tab
 */
function FailuresTab({ failures, failureAnalysis, onRefresh }) {
  if (failures.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={{ fontSize: '32px', marginBottom: '8px' }}>✅</div>
        <div>No failures detected</div>
        <div style={{ fontSize: '11px', marginTop: '4px' }}>
          The sandbox is running normally
        </div>
      </div>
    );
  }

  return (
    <div>
      {failures.map((failure, index) => (
        <div key={index} style={styles.failureCard}>
          <div style={styles.failureHeader}>
            <span style={{ fontSize: '18px' }}>
              {getFailureCategoryIcon(failure.category)}
            </span>
            <span style={styles.failureTitle}>
              {getFailureCategoryName(failure.category)}
            </span>
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#808080' }}>
              {new Date(failure.timestamp).toLocaleTimeString()}
            </span>
          </div>

          <div style={styles.failureDetails}>{failure.details}</div>

          {failure.traceback && (
            <details style={{ marginBottom: '8px' }}>
              <summary style={{ cursor: 'pointer', color: '#808080', fontSize: '11px' }}>
                Show Stack Trace
              </summary>
              <pre style={styles.traceback}>{failure.traceback}</pre>
            </details>
          )}

          <div style={styles.suggestionBox}>
            <div style={styles.suggestionTitle}>
              💡 Suggestion
            </div>
            <div style={{ color: '#a0d8a0', fontSize: '12px' }}>{failure.suggestion}</div>
          </div>
        </div>
      ))}

      {failureAnalysis?.actionable_steps?.length > 0 && (
        <div style={styles.suggestionBox}>
          <div style={styles.suggestionTitle}>
            🔧 How to Fix
          </div>
          <ol style={styles.suggestionList}>
            {failureAnalysis.actionable_steps.map((step, index) => (
              <li key={index} style={{ marginBottom: '4px' }}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export function SandboxDebugPanel({
  sessionId,
  expanded: initialExpanded = false,
  onClose,
  position = 'bottom-right', // 'bottom-right', 'bottom-left'
}) {
  const [expanded, setExpanded] = useState(initialExpanded);
  const [activeTab, setActiveTab] = useState('logs');

  const {
    health,
    failures,
    failureAnalysis,
    fetchFailureAnalysis,
    refresh,
    isHealthy,
    hasFailures,
    healthIcon,
    healthColor,
  } = useSandboxObservability(sessionId, {
    autoRefresh: true,
    refreshInterval: 5000,
  });

  // Fetch failure analysis when failures change
  useEffect(() => {
    if (hasFailures) {
      fetchFailureAnalysis();
    }
  }, [hasFailures, fetchFailureAnalysis]);

  // Auto-expand on failure
  useEffect(() => {
    if (hasFailures && !expanded) {
      setExpanded(true);
      setActiveTab('failures');
    }
  }, [hasFailures, expanded]);

  const positionStyle =
    position === 'bottom-left'
      ? { left: 0, right: 'auto', borderTopLeftRadius: 0, borderTopRightRadius: '12px' }
      : {};

  const panelStyle = {
    ...styles.panel,
    ...positionStyle,
    ...(expanded ? {} : styles.panelCollapsed),
  };

  const tabs = [
    { id: 'logs', label: 'Logs', icon: '📜' },
    { id: 'health', label: 'Health', icon: healthIcon },
    { id: 'failures', label: 'Failures', icon: hasFailures ? '🔴' : '✅', count: failures.length },
  ];

  return (
    <div style={panelStyle}>
      {/* Header */}
      <div style={styles.header} onClick={() => setExpanded(!expanded)}>
        <div style={styles.headerTitle}>
          <span>🔍</span>
          <span>Debug Panel</span>
          <span
            style={{
              ...styles.headerBadge,
              backgroundColor: `${healthColor}30`,
              color: healthColor,
            }}
          >
            {healthIcon} {isHealthy ? 'Healthy' : health?.state || 'Loading'}
          </span>
          {hasFailures && (
            <span
              style={{
                ...styles.headerBadge,
                backgroundColor: '#ff4d4d30',
                color: '#ff4d4d',
              }}
            >
              {failures.length} issue{failures.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div style={styles.headerActions}>
          <button
            style={styles.iconButton}
            onClick={(e) => {
              e.stopPropagation();
              refresh();
            }}
            title="Refresh"
          >
            🔄
          </button>
          {onClose && (
            <button
              style={styles.iconButton}
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              title="Close"
            >
              ✕
            </button>
          )}
          <span style={{ color: '#808080', fontSize: '14px' }}>
            {expanded ? '▼' : '▲'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      {expanded && (
        <div style={styles.tabs}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              style={{
                ...styles.tab,
                ...(activeTab === tab.id ? styles.tabActive : {}),
              }}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.icon} {tab.label}
              {tab.count > 0 && (
                <span
                  style={{
                    marginLeft: '4px',
                    backgroundColor: '#ff4d4d',
                    color: '#fff',
                    borderRadius: '10px',
                    padding: '1px 6px',
                    fontSize: '10px',
                  }}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {expanded && (
        <div style={styles.content}>
          {activeTab === 'logs' && <LogsTab sessionId={sessionId} />}
          {activeTab === 'health' && <HealthTab health={health} />}
          {activeTab === 'failures' && (
            <FailuresTab
              failures={failures}
              failureAnalysis={failureAnalysis}
              onRefresh={refresh}
            />
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Compact Error Banner (for inline use)
// =============================================================================

export function SandboxErrorBanner({ sessionId, onShowDebug }) {
  const { failures, hasFailures, fetchFailureAnalysis, failureAnalysis } =
    useSandboxObservability(sessionId, {
      autoRefresh: true,
      refreshInterval: 10000,
    });

  useEffect(() => {
    if (hasFailures) {
      fetchFailureAnalysis();
    }
  }, [hasFailures, fetchFailureAnalysis]);

  if (!hasFailures) return null;

  const primaryFailure = failures[0];

  return (
    <div
      style={{
        backgroundColor: '#3c1f1f',
        border: '1px solid #5c2f2f',
        borderRadius: '8px',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}
    >
      <span style={{ fontSize: '24px' }}>
        {getFailureCategoryIcon(primaryFailure.category)}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, color: '#ff6b6b' }}>
          {getFailureCategoryName(primaryFailure.category)}
        </div>
        <div style={{ fontSize: '12px', color: '#ffaaaa', marginTop: '2px' }}>
          {primaryFailure.suggestion}
        </div>
      </div>
      {onShowDebug && (
        <button
          onClick={onShowDebug}
          style={{
            backgroundColor: '#5c2f2f',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 12px',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: 500,
          }}
        >
          View Details
        </button>
      )}
    </div>
  );
}

// =============================================================================
// Health Status Badge (compact)
// =============================================================================

export function SandboxHealthBadge({ sessionId, onClick }) {
  const { health, healthIcon, healthColor, isHealthy } = useSandboxObservability(
    sessionId,
    { autoRefresh: true, refreshInterval: 5000 }
  );

  if (!health) return null;

  return (
    <div
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '4px 10px',
        backgroundColor: `${healthColor}20`,
        border: `1px solid ${healthColor}40`,
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: 500,
        color: healthColor,
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      {healthIcon}
      <span style={{ textTransform: 'capitalize' }}>{health.state}</span>
      {health.last_check?.response_time_ms && (
        <span style={{ color: '#808080', fontSize: '11px' }}>
          {Math.round(health.last_check.response_time_ms)}ms
        </span>
      )}
    </div>
  );
}

export default SandboxDebugPanel;

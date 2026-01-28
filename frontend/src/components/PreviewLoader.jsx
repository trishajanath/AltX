/**
 * PreviewLoader Component
 * =======================
 * Displays orchestration progress while the backend is being prepared.
 * 
 * Shows:
 * - Current stage with icon
 * - Progress bar
 * - Stage-specific messages
 * - Error state with mock mode fallback option
 */

import React from 'react';
import { OrchestrationStage } from '../config/previewOrchestration';

// Stage icons (using emoji for simplicity, can be replaced with icons)
const STAGE_ICONS = {
  [OrchestrationStage.PENDING]: '⏳',
  [OrchestrationStage.GENERATING_BACKEND]: '⚙️',
  [OrchestrationStage.BUILDING_IMAGE]: '🐳',
  [OrchestrationStage.DEPLOYING_CONTAINER]: '🚀',
  [OrchestrationStage.WAITING_FOR_HEALTH]: '💓',
  [OrchestrationStage.BACKEND_READY]: '✅',
  [OrchestrationStage.PREPARING_FRONTEND]: '🎨',
  [OrchestrationStage.READY]: '🎉',
  [OrchestrationStage.FAILED]: '❌',
};

// Stage colors
const STAGE_COLORS = {
  [OrchestrationStage.PENDING]: '#6b7280',
  [OrchestrationStage.GENERATING_BACKEND]: '#3b82f6',
  [OrchestrationStage.BUILDING_IMAGE]: '#0ea5e9',
  [OrchestrationStage.DEPLOYING_CONTAINER]: '#8b5cf6',
  [OrchestrationStage.WAITING_FOR_HEALTH]: '#f59e0b',
  [OrchestrationStage.BACKEND_READY]: '#10b981',
  [OrchestrationStage.PREPARING_FRONTEND]: '#6366f1',
  [OrchestrationStage.READY]: '#22c55e',
  [OrchestrationStage.FAILED]: '#ef4444',
};

// Pipeline stages in order
const PIPELINE_STAGES = [
  OrchestrationStage.GENERATING_BACKEND,
  OrchestrationStage.BUILDING_IMAGE,
  OrchestrationStage.DEPLOYING_CONTAINER,
  OrchestrationStage.WAITING_FOR_HEALTH,
  OrchestrationStage.PREPARING_FRONTEND,
];

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '300px',
    padding: '40px',
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    borderRadius: '16px',
    color: '#fff',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '24px',
  },
  icon: {
    fontSize: '48px',
    animation: 'pulse 2s infinite',
  },
  title: {
    fontSize: '24px',
    fontWeight: '600',
    margin: 0,
  },
  progressContainer: {
    width: '100%',
    maxWidth: '400px',
    marginBottom: '24px',
  },
  progressBar: {
    height: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '4px',
    overflow: 'hidden',
    marginBottom: '8px',
  },
  progressFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s ease, background 0.3s ease',
  },
  progressText: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  message: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: '24px',
  },
  pipeline: {
    display: 'flex',
    gap: '8px',
    marginBottom: '24px',
  },
  pipelineStage: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  pipelineDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    transition: 'all 0.3s ease',
  },
  pipelineLabel: {
    fontSize: '10px',
    color: 'rgba(255, 255, 255, 0.5)',
    textTransform: 'uppercase',
  },
  pipelineLine: {
    width: '24px',
    height: '2px',
    background: 'rgba(255, 255, 255, 0.2)',
    marginTop: '5px',
  },
  errorContainer: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    padding: '16px',
    marginTop: '16px',
    maxWidth: '400px',
  },
  errorText: {
    color: '#fca5a5',
    fontSize: '14px',
    margin: 0,
  },
  mockModeNotice: {
    background: 'rgba(251, 191, 36, 0.1)',
    border: '1px solid rgba(251, 191, 36, 0.3)',
    borderRadius: '8px',
    padding: '16px',
    marginTop: '16px',
    maxWidth: '400px',
  },
  mockModeText: {
    color: '#fde68a',
    fontSize: '14px',
    margin: 0,
  },
  button: {
    marginTop: '16px',
    padding: '10px 24px',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
};

// Add keyframe animation via style tag
const keyframes = `
  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

export function PreviewLoader({
  stage = OrchestrationStage.PENDING,
  progress = 0,
  message = 'Loading...',
  error = null,
  mockMode = false,
  onContinueWithMocks = null,
  onRetry = null,
}) {
  const icon = STAGE_ICONS[stage] || '⏳';
  const color = STAGE_COLORS[stage] || '#6b7280';
  const isFailed = stage === OrchestrationStage.FAILED;

  // Determine which pipeline stages are complete/active
  const currentStageIndex = PIPELINE_STAGES.indexOf(stage);

  return (
    <>
      <style>{keyframes}</style>
      <div style={styles.container}>
        {/* Header with icon and title */}
        <div style={styles.header}>
          <span style={{ 
            ...styles.icon, 
            animation: isFailed ? 'none' : 'pulse 2s infinite' 
          }}>
            {icon}
          </span>
          <h2 style={styles.title}>
            {isFailed ? 'Preview Failed' : 'Preparing Preview'}
          </h2>
        </div>

        {/* Progress bar */}
        {!isFailed && (
          <div style={styles.progressContainer}>
            <div style={styles.progressBar}>
              <div 
                style={{ 
                  ...styles.progressFill, 
                  width: `${progress}%`,
                  background: `linear-gradient(90deg, ${color}, ${color}cc)`
                }} 
              />
            </div>
            <div style={styles.progressText}>
              <span>{stage.replace(/_/g, ' ').toUpperCase()}</span>
              <span>{progress}%</span>
            </div>
          </div>
        )}

        {/* Pipeline visualization */}
        <div style={styles.pipeline}>
          {PIPELINE_STAGES.map((pStage, idx) => {
            const isComplete = idx < currentStageIndex;
            const isActive = idx === currentStageIndex;
            const isPending = idx > currentStageIndex;
            
            return (
              <React.Fragment key={pStage}>
                <div style={styles.pipelineStage}>
                  <div style={{
                    ...styles.pipelineDot,
                    background: isComplete ? '#22c55e' : 
                               isActive ? color : 
                               'rgba(255, 255, 255, 0.2)',
                    boxShadow: isActive ? `0 0 10px ${color}` : 'none',
                    transform: isActive ? 'scale(1.3)' : 'scale(1)',
                  }} />
                  <span style={{
                    ...styles.pipelineLabel,
                    color: isActive ? '#fff' : 'rgba(255, 255, 255, 0.5)',
                  }}>
                    {pStage.replace('_', ' ').split(' ')[0]}
                  </span>
                </div>
                {idx < PIPELINE_STAGES.length - 1 && (
                  <div style={{
                    ...styles.pipelineLine,
                    background: isComplete ? '#22c55e' : 'rgba(255, 255, 255, 0.2)',
                  }} />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Status message */}
        <p style={styles.message}>{message}</p>

        {/* Error display */}
        {error && (
          <div style={styles.errorContainer}>
            <p style={styles.errorText}>
              <strong>Error:</strong> {error}
            </p>
          </div>
        )}

        {/* Mock mode notice */}
        {mockMode && (
          <div style={styles.mockModeNotice}>
            <p style={styles.mockModeText}>
              🔶 <strong>Mock Mode Active:</strong> Using simulated API responses. 
              The backend could not be started, but you can still preview the UI.
            </p>
          </div>
        )}

        {/* Action buttons */}
        {isFailed && (
          <div style={{ display: 'flex', gap: '12px' }}>
            {onRetry && (
              <button 
                style={{ ...styles.button, background: 'rgba(59, 130, 246, 0.2)' }}
                onClick={onRetry}
                onMouseOver={(e) => e.target.style.background = 'rgba(59, 130, 246, 0.4)'}
                onMouseOut={(e) => e.target.style.background = 'rgba(59, 130, 246, 0.2)'}
              >
                🔄 Retry
              </button>
            )}
            {onContinueWithMocks && (
              <button 
                style={{ ...styles.button, background: 'rgba(251, 191, 36, 0.2)' }}
                onClick={onContinueWithMocks}
                onMouseOver={(e) => e.target.style.background = 'rgba(251, 191, 36, 0.4)'}
                onMouseOut={(e) => e.target.style.background = 'rgba(251, 191, 36, 0.2)'}
              >
                ⚡ Continue with Mocks
              </button>
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default PreviewLoader;

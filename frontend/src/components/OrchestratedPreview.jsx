/**
 * OrchestatedPreview Component
 * ============================
 * A complete preview component that orchestrates backend deployment
 * before loading the frontend preview.
 * 
 * CRITICAL: This ensures the frontend does NOT load before backend is ready.
 * 
 * Usage:
 * ```jsx
 * <OrchestratedPreview
 *   projectName="my-app"
 *   projectFiles={{ 'App.jsx': '...', 'index.js': '...' }}
 *   backendFiles={{ 'main.py': '...' }}  // Optional
 *   onReady={(backendUrl) => console.log('Ready!', backendUrl)}
 *   onError={(error, mockMode) => console.error('Failed', error)}
 * />
 * ```
 */

import React, { useEffect, useCallback, useState } from 'react';
import { usePreviewOrchestration } from '../hooks/usePreviewOrchestration';
import PreviewLoader from './PreviewLoader';
import { OrchestrationStage } from '../config/previewOrchestration';

export function OrchestratedPreview({
  projectName,
  projectFiles,
  backendFiles = null,
  userId = null,
  ttlMinutes = 45,
  generateBackend = true,
  onReady = null,
  onError = null,
  onProgress = null,
  previewUrl = null,  // If provided, use this instead of generating
  children = null,    // Custom preview content
  className = '',
  style = {},
}) {
  const {
    startPreview,
    cancelPreview,
    checkHealth,
    stage,
    progress,
    message,
    isLoading,
    isReady,
    isFailed,
    error,
    backendUrl,
    frontendPreviewUrl,
    mockMode,
    backendConfig,
  } = usePreviewOrchestration();

  const [showMockPreview, setShowMockPreview] = useState(false);
  const [healthCheckFailed, setHealthCheckFailed] = useState(false);

  // Start orchestration when project changes
  useEffect(() => {
    if (!projectName || !projectFiles || Object.keys(projectFiles).length === 0) {
      return;
    }

    // Skip orchestration if we already have a preview URL
    if (previewUrl) {
      onReady?.(null, previewUrl);
      return;
    }

    startPreview({
      projectName,
      projectFiles,
      backendFiles,
      userId,
      ttlMinutes,
      generateBackend,
    });

    return () => {
      cancelPreview();
    };
  }, [projectName]); // Only re-run when project changes

  // Notify parent of state changes
  useEffect(() => {
    onProgress?.(stage, progress, message);
  }, [stage, progress, message, onProgress]);

  useEffect(() => {
    if (isReady && backendUrl) {
      onReady?.(backendUrl, frontendPreviewUrl, backendConfig);
    }
  }, [isReady, backendUrl, frontendPreviewUrl, backendConfig, onReady]);

  useEffect(() => {
    if (isFailed && error) {
      onError?.(error, mockMode);
    }
  }, [isFailed, error, mockMode, onError]);

  // Periodic health check when ready
  useEffect(() => {
    if (!isReady || !backendUrl) return;

    const interval = setInterval(async () => {
      const health = await checkHealth();
      if (!health.healthy) {
        setHealthCheckFailed(true);
        console.warn('⚠️ Backend health check failed');
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [isReady, backendUrl, checkHealth]);

  // Handle retry
  const handleRetry = useCallback(() => {
    setShowMockPreview(false);
    setHealthCheckFailed(false);
    startPreview({
      projectName,
      projectFiles,
      backendFiles,
      userId,
      ttlMinutes,
      generateBackend,
    });
  }, [projectName, projectFiles, backendFiles, userId, ttlMinutes, generateBackend, startPreview]);

  // Handle continue with mocks
  const handleContinueWithMocks = useCallback(() => {
    setShowMockPreview(true);
    // Notify parent that we're using mock mode
    onError?.(error || 'Backend unavailable', true);
  }, [error, onError]);

  // If we have a direct preview URL, just render the iframe
  if (previewUrl) {
    return (
      <div className={className} style={{ width: '100%', height: '100%', ...style }}>
        <iframe
          src={previewUrl}
          title="Preview"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: '8px',
          }}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </div>
    );
  }

  // Show loader while orchestrating
  if (isLoading || (!isReady && !showMockPreview)) {
    return (
      <div className={className} style={{ width: '100%', height: '100%', ...style }}>
        <PreviewLoader
          stage={stage}
          progress={progress}
          message={message}
          error={error}
          mockMode={mockMode}
          onRetry={isFailed ? handleRetry : null}
          onContinueWithMocks={isFailed ? handleContinueWithMocks : null}
        />
      </div>
    );
  }

  // Show health check warning if backend became unhealthy
  if (healthCheckFailed && !showMockPreview) {
    return (
      <div className={className} style={{ width: '100%', height: '100%', ...style }}>
        <PreviewLoader
          stage={OrchestrationStage.FAILED}
          progress={0}
          message="Backend connection lost"
          error="The backend server is no longer responding"
          mockMode={true}
          onRetry={handleRetry}
          onContinueWithMocks={handleContinueWithMocks}
        />
      </div>
    );
  }

  // Custom content rendering
  if (children) {
    return (
      <div className={className} style={{ width: '100%', height: '100%', ...style }}>
        {typeof children === 'function' 
          ? children({ backendUrl, frontendPreviewUrl, mockMode, backendConfig })
          : children
        }
      </div>
    );
  }

  // Default: render iframe with the frontend preview URL
  const iframeUrl = mockMode 
    ? `${frontendPreviewUrl || ''}&mock_mode=true`
    : frontendPreviewUrl;

  if (!iframeUrl) {
    return (
      <div className={className} style={{ 
        width: '100%', 
        height: '100%', 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#666',
        ...style 
      }}>
        No preview URL available
      </div>
    );
  }

  return (
    <div className={className} style={{ width: '100%', height: '100%', position: 'relative', ...style }}>
      {/* Mock mode indicator */}
      {mockMode && (
        <div style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          zIndex: 10,
          background: 'rgba(251, 191, 36, 0.9)',
          color: '#000',
          padding: '4px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: '600',
        }}>
          🔶 Mock Mode
        </div>
      )}
      
      {/* Preview iframe */}
      <iframe
        src={iframeUrl}
        title="Preview"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          borderRadius: '8px',
        }}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
}

export default OrchestratedPreview;

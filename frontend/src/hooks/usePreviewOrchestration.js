/**
 * usePreviewOrchestration Hook
 * ============================
 * React hook for managing preview orchestration lifecycle.
 * 
 * CRITICAL: This ensures the frontend does NOT load before the backend is ready.
 * 
 * Usage:
 * ```jsx
 * function PreviewContainer({ projectName, projectFiles }) {
 *   const {
 *     startPreview,
 *     cancelPreview,
 *     stage,
 *     progress,
 *     isLoading,
 *     isReady,
 *     isFailed,
 *     error,
 *     backendUrl,
 *     mockMode,
 *   } = usePreviewOrchestration();
 * 
 *   useEffect(() => {
 *     startPreview({ projectName, projectFiles });
 *     return () => cancelPreview();
 *   }, [projectName]);
 * 
 *   if (isLoading) return <PreviewLoader stage={stage} progress={progress} />;
 *   if (isFailed) return <PreviewError error={error} mockMode={mockMode} />;
 *   if (!isReady) return null;
 * 
 *   // Only render preview when backend is READY
 *   return <PreviewIframe backendUrl={backendUrl} />;
 * }
 * ```
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  startPreviewOrchestration,
  checkBackendHealth,
  cancelPreview as cancelPreviewApi,
  cleanupPreview,
  OrchestrationStage,
  STAGE_MESSAGES,
} from '../config/previewOrchestration';
import { setSandboxBackendUrl, clearSandboxBackendUrl } from '../config/api';

/**
 * @typedef {Object} PreviewOrchestrationState
 * @property {string|null} sessionId - Current session ID
 * @property {string} stage - Current orchestration stage
 * @property {number} progress - Overall progress (0-100)
 * @property {string} message - Current status message
 * @property {boolean} isLoading - True while orchestrating
 * @property {boolean} isReady - True when backend is ready
 * @property {boolean} isFailed - True if orchestration failed
 * @property {string|null} error - Error message if failed
 * @property {string|null} backendUrl - Backend API URL when ready
 * @property {string|null} frontendPreviewUrl - Full preview URL
 * @property {boolean} mockMode - True if using mock APIs (fallback)
 * @property {Object|null} backendConfig - Backend configuration (auth, etc.)
 */

/**
 * @typedef {Object} PreviewOrchestrationActions
 * @property {function} startPreview - Start the orchestration flow
 * @property {function} cancelPreview - Cancel and cleanup
 * @property {function} checkHealth - Check backend health
 * @property {function} reset - Reset state
 */

/**
 * React hook for preview orchestration.
 * 
 * @returns {PreviewOrchestrationState & PreviewOrchestrationActions}
 */
export function usePreviewOrchestration() {
  // State
  const [sessionId, setSessionId] = useState(null);
  const [stage, setStage] = useState(OrchestrationStage.PENDING);
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendUrl, setBackendUrl] = useState(null);
  const [frontendPreviewUrl, setFrontendPreviewUrl] = useState(null);
  const [mockMode, setMockMode] = useState(false);
  const [backendConfig, setBackendConfig] = useState(null);

  // Refs for cleanup
  const isMountedRef = useRef(true);
  const currentSessionRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (currentSessionRef.current) {
        cancelPreviewApi(currentSessionRef.current).catch(() => {});
      }
      cleanupPreview();
    };
  }, []);

  // Computed states
  const isReady = stage === OrchestrationStage.READY && !mockMode;
  const isFailed = stage === OrchestrationStage.FAILED;

  /**
   * Start the preview orchestration flow.
   */
  const startPreview = useCallback(async (options) => {
    if (!isMountedRef.current) return;

    // Reset state
    setIsLoading(true);
    setError(null);
    setStage(OrchestrationStage.PENDING);
    setProgress(0);
    setMessage('Starting preview orchestration...');
    setMockMode(false);
    setBackendUrl(null);
    setFrontendPreviewUrl(null);
    setBackendConfig(null);

    // Cancel any existing session
    if (currentSessionRef.current) {
      await cancelPreviewApi(currentSessionRef.current).catch(() => {});
      currentSessionRef.current = null;
    }

    try {
      const result = await startPreviewOrchestration({
        ...options,
        onProgress: (stg, prog, msg) => {
          if (!isMountedRef.current) return;
          setStage(stg);
          setProgress(prog);
          setMessage(msg);
        },
        onStageChange: (stg, msg) => {
          if (!isMountedRef.current) return;
          setStage(stg);
          setMessage(msg);
          console.log(`📍 Stage: ${stg} - ${msg}`);
        },
      });

      if (!isMountedRef.current) return;

      if (result.success) {
        setSessionId(result.session_id);
        currentSessionRef.current = result.session_id;
        setBackendUrl(result.backend_url);
        setFrontendPreviewUrl(result.frontend_preview_url);
        setBackendConfig(result.backend_config);
        setMockMode(result.mock_mode);
        setStage(OrchestrationStage.READY);
        setProgress(100);
        setMessage('Preview ready!');
        
        // Configure sandbox URL
        if (result.backend_url) {
          setSandboxBackendUrl(result.backend_url);
        }
        
        console.log('✅ Preview orchestration complete:', result);
      } else {
        // Orchestration failed - enable mock mode as fallback
        setError(result.error);
        setStage(OrchestrationStage.FAILED);
        setMockMode(true);
        setMessage(`Failed: ${result.error}. Using mock APIs.`);
        
        console.warn('⚠️ Preview orchestration failed, mock mode enabled:', result.error);
      }
    } catch (err) {
      if (!isMountedRef.current) return;
      
      const errorMsg = err.message || 'Unknown error';
      setError(errorMsg);
      setStage(OrchestrationStage.FAILED);
      setMockMode(true);
      setMessage(`Error: ${errorMsg}. Using mock APIs.`);
      
      console.error('❌ Preview orchestration error:', err);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, []);

  /**
   * Cancel the current preview and cleanup.
   */
  const cancelPreview = useCallback(async () => {
    if (currentSessionRef.current) {
      await cancelPreviewApi(currentSessionRef.current).catch(() => {});
      currentSessionRef.current = null;
    }
    
    clearSandboxBackendUrl();
    
    if (isMountedRef.current) {
      setSessionId(null);
      setStage(OrchestrationStage.PENDING);
      setProgress(0);
      setMessage('');
      setIsLoading(false);
      setError(null);
      setBackendUrl(null);
      setFrontendPreviewUrl(null);
      setMockMode(false);
      setBackendConfig(null);
    }
  }, []);

  /**
   * Check if the backend is still healthy.
   */
  const checkHealth = useCallback(async () => {
    if (!sessionId) return { healthy: false, error: 'No session' };
    
    const result = await checkBackendHealth(sessionId);
    
    if (!result.healthy && isMountedRef.current) {
      console.warn('⚠️ Backend health check failed, enabling mock mode');
      setMockMode(true);
    }
    
    return result;
  }, [sessionId]);

  /**
   * Reset the hook state.
   */
  const reset = useCallback(() => {
    cancelPreview();
  }, [cancelPreview]);

  return {
    // State
    sessionId,
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
    
    // Actions
    startPreview,
    cancelPreview,
    checkHealth,
    reset,
    
    // Constants (for UI)
    stageMessages: STAGE_MESSAGES,
  };
}

export default usePreviewOrchestration;

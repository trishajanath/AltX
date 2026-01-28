/**
 * Preview Orchestration Service (Frontend)
 * =========================================
 * Coordinates frontend preview loading with backend deployment.
 * 
 * CRITICAL: Frontend must NOT load before backend is ready.
 * 
 * Flow:
 * 1. Call /api/preview/start to begin orchestration
 * 2. Poll /api/preview/status/{session_id} until ready
 * 3. Inject backend URL into frontend config
 * 4. Only THEN load the preview iframe
 * 
 * If orchestration fails, enable mock fallback mode.
 */

import { API_BASE_URL, setSandboxBackendUrl, clearSandboxBackendUrl } from './api';

// Orchestration stages (mirrors backend)
export const OrchestrationStage = {
  PENDING: 'pending',
  GENERATING_BACKEND: 'generating_backend',
  BUILDING_IMAGE: 'building_image',
  DEPLOYING_CONTAINER: 'deploying_container',
  WAITING_FOR_HEALTH: 'waiting_for_health',
  BACKEND_READY: 'backend_ready',
  PREPARING_FRONTEND: 'preparing_frontend',
  READY: 'ready',
  FAILED: 'failed',
};

// Human-readable stage messages
export const STAGE_MESSAGES = {
  [OrchestrationStage.PENDING]: 'Preparing preview...',
  [OrchestrationStage.GENERATING_BACKEND]: 'Generating backend API...',
  [OrchestrationStage.BUILDING_IMAGE]: 'Building Docker image...',
  [OrchestrationStage.DEPLOYING_CONTAINER]: 'Deploying sandbox container...',
  [OrchestrationStage.WAITING_FOR_HEALTH]: 'Waiting for backend to start...',
  [OrchestrationStage.BACKEND_READY]: 'Backend ready!',
  [OrchestrationStage.PREPARING_FRONTEND]: 'Preparing frontend...',
  [OrchestrationStage.READY]: 'Preview ready!',
  [OrchestrationStage.FAILED]: 'Preview failed',
};

/**
 * @typedef {Object} OrchestrationProgress
 * @property {string} session_id
 * @property {string} stage
 * @property {number} stage_progress
 * @property {number} overall_progress
 * @property {string} message
 * @property {string|null} error
 * @property {string|null} backend_url
 * @property {string|null} frontend_preview_url
 * @property {Object|null} backend_config
 */

/**
 * @typedef {Object} PreviewResult
 * @property {boolean} success
 * @property {string} session_id
 * @property {string} backend_url
 * @property {string} frontend_preview_url
 * @property {boolean} mock_mode
 * @property {Object|null} backend_config
 * @property {string|null} error
 */

/**
 * Start the preview orchestration flow.
 * 
 * @param {Object} options
 * @param {string} options.projectName - Project slug/name
 * @param {Object<string, string>} options.projectFiles - Project files (filename -> content)
 * @param {Object<string, string>} [options.backendFiles] - Backend-specific files
 * @param {string} [options.userId] - User identifier
 * @param {number} [options.ttlMinutes=45] - Container TTL
 * @param {boolean} [options.generateBackend=true] - Whether to generate backend
 * @param {function} [options.onProgress] - Progress callback (stage, progress, message)
 * @param {function} [options.onStageChange] - Stage change callback (stage, message)
 * @returns {Promise<PreviewResult>}
 */
export async function startPreviewOrchestration(options) {
  const {
    projectName,
    projectFiles,
    backendFiles = null,
    userId = null,
    ttlMinutes = 45,
    generateBackend = true,
    onProgress = null,
    onStageChange = null,
  } = options;

  // Notify: Starting
  onProgress?.(OrchestrationStage.PENDING, 0, 'Initializing preview orchestration...');
  onStageChange?.(OrchestrationStage.PENDING, STAGE_MESSAGES[OrchestrationStage.PENDING]);

  try {
    // Start orchestration on backend
    const startResponse = await fetch(`${API_BASE_URL}/api/preview/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_name: projectName,
        project_files: projectFiles,
        backend_files: backendFiles,
        user_id: userId,
        ttl_minutes: ttlMinutes,
        generate_backend: generateBackend,
      }),
    });

    if (!startResponse.ok) {
      const errorData = await startResponse.json().catch(() => ({}));
      throw new Error(errorData.detail || `Orchestration failed: ${startResponse.status}`);
    }

    const result = await startResponse.json();

    if (!result.success) {
      throw new Error(result.error || result.message || 'Orchestration failed');
    }

    // Orchestration succeeded - configure frontend
    if (result.backend_url) {
      setSandboxBackendUrl(result.backend_url);
      console.log('✅ Sandbox backend URL configured:', result.backend_url);
    }

    onProgress?.(OrchestrationStage.READY, 100, 'Preview ready!');
    onStageChange?.(OrchestrationStage.READY, STAGE_MESSAGES[OrchestrationStage.READY]);

    return {
      success: true,
      session_id: result.session_id,
      backend_url: result.backend_url,
      frontend_preview_url: result.frontend_preview_url,
      mock_mode: result.mock_mode || false,
      backend_config: result.backend_config,
      error: null,
    };

  } catch (error) {
    console.error('❌ Preview orchestration failed:', error);
    
    // Enable mock mode as fallback
    console.warn('🔶 Enabling mock mode as fallback');
    
    onProgress?.(OrchestrationStage.FAILED, 0, `Failed: ${error.message}`);
    onStageChange?.(OrchestrationStage.FAILED, error.message);

    return {
      success: false,
      session_id: null,
      backend_url: null,
      frontend_preview_url: null,
      mock_mode: true, // IMPORTANT: Enable mocks as fallback
      backend_config: null,
      error: error.message,
    };
  }
}

/**
 * Poll orchestration status until ready or failed.
 * Use this for long-running orchestrations with progress updates.
 * 
 * @param {string} sessionId
 * @param {Object} options
 * @param {function} [options.onProgress]
 * @param {function} [options.onStageChange]
 * @param {number} [options.pollInterval=1000]
 * @param {number} [options.maxWaitMs=120000]
 * @returns {Promise<OrchestrationProgress>}
 */
export async function pollOrchestrationStatus(sessionId, options = {}) {
  const {
    onProgress = null,
    onStageChange = null,
    pollInterval = 1000,
    maxWaitMs = 120000, // 2 minute max wait
  } = options;

  const startTime = Date.now();
  let lastStage = null;

  while (Date.now() - startTime < maxWaitMs) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/preview/status/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.status}`);
      }

      const progress = await response.json();

      // Notify progress
      onProgress?.(progress.stage, progress.overall_progress, progress.message);
      
      // Notify stage change
      if (progress.stage !== lastStage) {
        lastStage = progress.stage;
        onStageChange?.(progress.stage, STAGE_MESSAGES[progress.stage] || progress.message);
      }

      // Check terminal states
      if (progress.stage === OrchestrationStage.READY) {
        return progress;
      }

      if (progress.stage === OrchestrationStage.FAILED) {
        throw new Error(progress.error || 'Orchestration failed');
      }

      // Continue polling
      await new Promise(resolve => setTimeout(resolve, pollInterval));

    } catch (error) {
      console.error('Status poll error:', error);
      throw error;
    }
  }

  throw new Error('Orchestration timed out');
}

/**
 * Check if the backend for a session is still healthy.
 * Call this before making API calls in the preview.
 * 
 * @param {string} sessionId
 * @returns {Promise<{healthy: boolean, responseTimeMs: number, error?: string}>}
 */
export async function checkBackendHealth(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/preview/health-check/${sessionId}`);
    
    if (!response.ok) {
      return { healthy: false, responseTimeMs: 0, error: `HTTP ${response.status}` };
    }

    const data = await response.json();
    return {
      healthy: data.healthy,
      responseTimeMs: data.response_time_ms,
      authConfig: data.auth_config,
      error: data.error,
    };

  } catch (error) {
    return {
      healthy: false,
      responseTimeMs: 0,
      error: error.message,
    };
  }
}

/**
 * Cancel a preview session and cleanup resources.
 * This triggers cleanup of the backend container.
 * 
 * @param {string} sessionId
 * @returns {Promise<boolean>}
 */
export async function cancelPreview(sessionId) {
  try {
    // Cancel orchestration
    const cancelResponse = await fetch(`${API_BASE_URL}/api/preview/cancel/${sessionId}`, {
      method: 'POST',
    });
    
    // Also trigger container cleanup
    try {
      await fetch(`${API_BASE_URL}/api/cleanup/container`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          reason: 'preview_cancelled',
        }),
      });
      console.log(`🧹 Cleanup requested for session ${sessionId}`);
    } catch (cleanupError) {
      // Non-critical, cleanup manager will handle it via TTL
      console.warn('Cleanup request failed (will be handled by TTL):', cleanupError);
    }
    
    // Clear sandbox URL
    clearSandboxBackendUrl();
    
    return cancelResponse.ok;
  } catch (error) {
    console.error('Cancel preview error:', error);
    clearSandboxBackendUrl();
    return false;
  }
}

/**
 * Cleanup preview resources and reset configuration.
 */
export function cleanupPreview() {
  clearSandboxBackendUrl();
  console.log('🧹 Preview cleanup complete');
}

/**
 * React hook for preview orchestration with state management.
 * 
 * Usage:
 * ```jsx
 * const { 
 *   startPreview, 
 *   stage, 
 *   progress, 
 *   isLoading, 
 *   isReady, 
 *   error,
 *   backendUrl,
 *   mockMode 
 * } = usePreviewOrchestration();
 * 
 * // Start preview
 * await startPreview({ projectName: 'my-app', projectFiles: {...} });
 * 
 * // Only render preview when ready
 * if (isReady) {
 *   return <PreviewIframe url={frontendPreviewUrl} />;
 * }
 * ```
 */
export function createPreviewOrchestrationState() {
  return {
    sessionId: null,
    stage: OrchestrationStage.PENDING,
    progress: 0,
    message: '',
    isLoading: false,
    isReady: false,
    error: null,
    backendUrl: null,
    frontendPreviewUrl: null,
    mockMode: false,
    backendConfig: null,
  };
}

export default {
  startPreviewOrchestration,
  pollOrchestrationStatus,
  checkBackendHealth,
  cancelPreview,
  cleanupPreview,
  createPreviewOrchestrationState,
  OrchestrationStage,
  STAGE_MESSAGES,
};

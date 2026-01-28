# Preview Orchestration Integration Guide

This document explains how to integrate the new Preview Orchestration system into your components.

## Overview

The Preview Orchestration system ensures that:
1. **Backend is deployed and healthy BEFORE frontend loads**
2. **No mocked APIs in normal operation** - real HTTP requests to real backends
3. **Graceful fallback to mock mode** if backend deployment fails
4. **Clear error surfacing** with user-friendly messages

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Preview Orchestration Flow                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PENDING          → Start orchestration request              │
│  2. GENERATING       → AI generates FastAPI backend code        │
│  3. BUILDING_IMAGE   → Docker builds the backend image          │
│  4. DEPLOYING        → Container starts on unique port          │
│  5. WAITING_HEALTH   → Poll /health until 200 OK                │
│  6. BACKEND_READY    → Backend confirmed responsive             │
│  7. PREPARING        → Inject backend URL into frontend env     │
│  8. READY            → Frontend preview can now load!           │
│                                                                 │
│  ⚠️ FAILED (any stage) → Show error, offer mock mode fallback   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Use OrchestratedPreview Component (Recommended)

The simplest way - drop-in component that handles everything:

```jsx
import { OrchestratedPreview } from '../components/OrchestratedPreview';

function MyPreviewPanel({ projectName, projectFiles }) {
  return (
    <OrchestratedPreview
      projectName={projectName}
      projectFiles={projectFiles}
      generateBackend={true}  // Auto-generate FastAPI backend
      onReady={(backendUrl, frontendUrl) => {
        console.log('✅ Preview ready!');
        console.log('Backend:', backendUrl);
        console.log('Frontend:', frontendUrl);
      }}
      onError={(error, isMockMode) => {
        if (isMockMode) {
          console.warn('⚠️ Running in mock mode:', error);
        } else {
          console.error('❌ Preview failed:', error);
        }
      }}
    />
  );
}
```

### Option 2: Use the Hook for Custom UI

For more control over the UI:

```jsx
import { usePreviewOrchestration } from '../hooks/usePreviewOrchestration';
import PreviewLoader from '../components/PreviewLoader';

function CustomPreview({ projectName, projectFiles }) {
  const {
    startPreview,
    stage,
    progress,
    message,
    isLoading,
    isReady,
    isFailed,
    error,
    backendUrl,
    mockMode,
  } = usePreviewOrchestration();

  useEffect(() => {
    startPreview({
      projectName,
      projectFiles,
      generateBackend: true,
    });
  }, [projectName]);

  // Show loader during orchestration
  if (isLoading) {
    return (
      <PreviewLoader
        stage={stage}
        progress={progress}
        message={message}
        error={error}
        mockMode={mockMode}
      />
    );
  }

  // Show error state
  if (isFailed) {
    return <div className="error">Failed: {error}</div>;
  }

  // Only render preview when READY
  if (isReady) {
    return (
      <iframe
        src={backendUrl ? `/preview?api=${backendUrl}` : '/preview?mock=true'}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  return null;
}
```

### Option 3: Direct API Calls

For maximum control, use the service directly:

```jsx
import {
  startPreviewOrchestration,
  pollOrchestrationStatus,
  checkBackendHealth,
  OrchestrationStage,
} from '../config/previewOrchestration';

async function deployPreview(projectName, projectFiles) {
  // Start orchestration
  const { session_id } = await startPreviewOrchestration({
    project_name: projectName,
    project_files: projectFiles,
    generate_backend: true,
    ttl_minutes: 45,
  });

  // Poll until ready or failed
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      const status = await pollOrchestrationStatus(session_id);
      
      if (status.stage === OrchestrationStage.READY) {
        clearInterval(interval);
        resolve({
          backendUrl: status.backend_url,
          frontendUrl: status.frontend_preview_url,
          config: status.backend_config,
        });
      }
      
      if (status.stage === OrchestrationStage.FAILED) {
        clearInterval(interval);
        reject(new Error(status.error));
      }
    }, 2000);
  });
}
```

## Integration with MonacoProjectEditor

To integrate with the existing MonacoProjectEditor, follow these steps:

### Step 1: Import Required Components

Add to the imports section:

```jsx
import { OrchestratedPreview } from './OrchestratedPreview';
import { usePreviewOrchestration } from '../hooks/usePreviewOrchestration';
```

### Step 2: Add State for Orchestration

Add to the component state:

```jsx
const [useOrchestration, setUseOrchestration] = useState(true);
const [orchestrationBackendUrl, setOrchestrationBackendUrl] = useState(null);
```

### Step 3: Replace Preview Iframe

Replace the existing preview iframe section with:

```jsx
{/* Preview Mode with Backend Orchestration */}
{layoutMode === 'preview' && useOrchestration && !previewUrl && (
  <OrchestratedPreview
    projectName={projectName}
    projectFiles={fileContents}
    generateBackend={true}
    onReady={(backendUrl, frontendUrl, config) => {
      setOrchestrationBackendUrl(backendUrl);
      setPreviewUrl(frontendUrl);
    }}
    onError={(error, mockMode) => {
      if (mockMode) {
        // Continue with mock mode
        console.warn('Using mock mode:', error);
      }
    }}
  />
)}

{/* Existing preview iframe (when orchestration complete) */}
{layoutMode === 'preview' && previewUrl && (
  <iframe
    src={ensurePreviewUrlHasAuth(previewUrl)}
    style={{ width: '100%', height: '100%', border: 'none' }}
    title="Live Preview"
    sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  />
)}
```

### Step 4: Pass Backend URL to Preview

When the preview loads, it needs to know the backend URL:

```jsx
// In ensurePreviewUrlHasAuth function, add:
const ensurePreviewUrlHasAuth = (url) => {
  try {
    const urlObj = new URL(url, window.location.origin);
    
    // Add orchestrated backend URL if available
    if (orchestrationBackendUrl && !urlObj.searchParams.has('api_url')) {
      urlObj.searchParams.set('api_url', orchestrationBackendUrl);
    }
    
    // ... rest of the function
  } catch (e) {
    return url;
  }
};
```

## API Reference

### PreviewOrchestration Config (`/config/previewOrchestration.js`)

```javascript
// Orchestration stages
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

// Start orchestration
startPreviewOrchestration({ project_name, project_files, backend_files, user_id, ttl_minutes, generate_backend })

// Poll status
pollOrchestrationStatus(sessionId)

// Check backend health
checkBackendHealth(sessionId)

// Cancel orchestration
cancelPreviewOrchestration(sessionId)
```

### usePreviewOrchestration Hook

```javascript
const {
  // Actions
  startPreview,      // Start orchestration flow
  cancelPreview,     // Cancel current orchestration
  checkHealth,       // Check backend health
  
  // State
  stage,             // Current orchestration stage
  progress,          // Progress percentage (0-100)
  message,           // Current status message
  
  // Computed state
  isLoading,         // True while orchestrating
  isReady,           // True when preview ready
  isFailed,          // True if orchestration failed
  
  // Data
  error,             // Error message if failed
  backendUrl,        // Backend API URL when ready
  frontendPreviewUrl, // Frontend preview URL when ready
  mockMode,          // True if running in mock mode
  backendConfig,     // Backend config (demo user, jwt secret, etc.)
} = usePreviewOrchestration();
```

### OrchestratedPreview Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `projectName` | string | required | Project identifier |
| `projectFiles` | object | required | Map of filename → content |
| `backendFiles` | object | null | Custom backend files (optional) |
| `userId` | string | null | User ID for session tracking |
| `ttlMinutes` | number | 45 | Container TTL |
| `generateBackend` | boolean | true | Auto-generate FastAPI backend |
| `onReady` | function | null | Called when preview ready |
| `onError` | function | null | Called on error |
| `onProgress` | function | null | Called on stage/progress change |
| `previewUrl` | string | null | Skip orchestration, use this URL |
| `children` | node/function | null | Custom preview content |

## Backend Endpoints

### POST `/api/preview/start`

Start a new preview orchestration:

```json
{
  "project_name": "my-app",
  "project_files": { "App.jsx": "...", "index.js": "..." },
  "backend_files": null,
  "user_id": "user123",
  "ttl_minutes": 45,
  "generate_backend": true
}
```

Response:
```json
{
  "session_id": "abc123",
  "stage": "pending",
  "message": "Starting preview orchestration..."
}
```

### GET `/api/preview/status/{session_id}`

Poll orchestration status:

```json
{
  "session_id": "abc123",
  "stage": "backend_ready",
  "progress": 75,
  "message": "Backend is ready and healthy",
  "backend_url": "http://localhost:9001",
  "container_id": "docker-abc123",
  "backend_config": {
    "demo_user": {
      "email": "demo@sandbox.local",
      "password": "demo123456"
    },
    "jwt_secret": "sandbox-isolated-jwt-secret-abc123"
  }
}
```

### POST `/api/preview/cancel/{session_id}`

Cancel a running orchestration:

```json
{
  "success": true,
  "message": "Orchestration cancelled"
}
```

### GET `/api/preview/health-check/{session_id}`

Check backend health:

```json
{
  "healthy": true,
  "response_time_ms": 45,
  "last_checked": "2024-01-15T10:30:00Z"
}
```

## Troubleshooting

### Backend won't start

1. Check Docker is running: `docker ps`
2. Check port availability: `lsof -i :9000-9999`
3. Check container logs: `docker logs <container_id>`

### Health check failing

1. Ensure `/health` endpoint exists in backend
2. Check backend logs for errors
3. Increase health check timeout in config

### Preview shows mock mode unexpectedly

1. Check network connectivity to backend
2. Verify backend URL is correct
3. Check browser console for fetch errors

### Orchestration stuck at BUILDING_IMAGE

1. Docker build may be slow first time
2. Check Docker disk space
3. Check for build errors in Docker logs

## Best Practices

1. **Always use orchestration for new previews** - Don't load frontend until backend ready
2. **Monitor health periodically** - Check every 30 seconds to detect failures
3. **Show clear mock mode indicators** - Users should know when using mocks
4. **Clean up containers** - Set reasonable TTL (45 min default)
5. **Handle errors gracefully** - Offer mock mode as fallback, not error screen

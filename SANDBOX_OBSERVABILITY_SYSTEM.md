# Sandbox Observability System

## Overview

The sandbox observability system provides comprehensive monitoring and debugging capabilities for preview sandboxes. It captures logs, tracks health metrics, detects failures, and surfaces actionable debugging information to users.

## Components

### Backend

#### `sandbox_observability.py`
Core observability service with:
- **Log Collection**: Background task collects container logs every 5 seconds
- **Failure Detection**: Pattern matching against 11 error categories
- **Health Metrics**: Tracks uptime, response times, resource usage
- **Debug Snapshots**: Complete observability state in one request

### Frontend

#### `sandboxObservability.js`
Service layer with:
- Log fetching and real-time SSE streaming
- Health metrics API
- Failure analysis API
- Utility functions for UI rendering

#### `useSandboxObservability.js`
React hooks:
- `useSandboxObservability`: Full observability data with auto-refresh
- `useSandboxLogs`: Specialized log streaming hook
- `useSandboxHealthMonitor`: Health monitoring with callbacks
- `useWaitForHealthy`: Wait for sandbox to become healthy

#### `SandboxDebugPanel.jsx`
UI components:
- `SandboxDebugPanel`: Full debug panel with tabs (Logs, Health, Failures)
- `SandboxErrorBanner`: Inline error display
- `SandboxHealthBadge`: Compact health indicator

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/observability/logs/{session_id}` | GET | Get logs (query params: `tail`, `level`) |
| `/api/observability/logs/{session_id}/stream` | GET | SSE log streaming |
| `/api/observability/health/{session_id}` | GET | Detailed health metrics |
| `/api/observability/failures/{session_id}` | GET | Detected failures |
| `/api/observability/failures/{session_id}/analyze` | GET | Failure analysis with suggestions |
| `/api/observability/snapshot/{session_id}` | GET | Complete debug snapshot |
| `/api/observability/session/{session_id}` | DELETE | Clear session data |
| `/api/observability/summary` | GET | All sessions summary |

## Error Categories

The system detects and categorizes these failure types:

| Category | Examples | Suggestion |
|----------|----------|------------|
| `import_error` | ModuleNotFoundError | Add missing package to requirements.txt |
| `syntax_error` | SyntaxError, IndentationError | Check code for typos |
| `dependency_error` | DistributionNotFound | Check requirements.txt versions |
| `port_binding_error` | Address already in use | Wait for cleanup |
| `runtime_error` | ValueError, TypeError | Review stack trace |
| `network_error` | ConnectionRefused | Backend may be starting |
| `resource_error` | MemoryError, OOM | Simplify code |
| `config_error` | ValidationError | Check environment variables |
| `build_error` | Docker build failed | Check Dockerfile |
| `timeout_error` | Operation timed out | Backend taking too long |
| `unknown_error` | Other errors | Check logs |

## Usage Examples

### Backend Integration

```python
from sandbox_observability import init_observability, get_observability

# Initialize with deployment service and orchestrator
observability = init_observability(
    deployment_service=deployment_service,
    orchestrator=orchestrator
)
await observability.start()

# Get snapshot for debugging
snapshot = await observability.get_full_snapshot(session_id)

# Analyze failure
analysis = await observability.analyze_failure(session_id)
```

### Frontend Integration

```jsx
import { SandboxDebugPanel, SandboxHealthBadge } from './components/SandboxDebugPanel';
import { useSandboxObservability } from './hooks/useSandboxObservability';

// Full debug panel
function PreviewPage({ sessionId }) {
  const [showDebug, setShowDebug] = useState(false);
  
  return (
    <div>
      <SandboxHealthBadge 
        sessionId={sessionId} 
        onClick={() => setShowDebug(true)} 
      />
      {showDebug && <SandboxDebugPanel sessionId={sessionId} />}
    </div>
  );
}

// Using the hook
function MyComponent({ sessionId }) {
  const {
    logs,
    health,
    failures,
    hasFailures,
    isHealthy,
    refresh
  } = useSandboxObservability(sessionId, {
    autoRefresh: true,
    streamLogs: true
  });

  if (hasFailures) {
    return <ErrorDisplay failures={failures} />;
  }

  return <div>Status: {health?.state}</div>;
}
```

### Real-time Log Streaming

```javascript
import { sandboxObservability } from './services/sandboxObservability';

// Subscribe to logs
const unsubscribe = sandboxObservability.subscribeToLogs(sessionId, (log) => {
  console.log(`[${log.level}] ${log.message}`);
});

// Later: cleanup
unsubscribe();
```

### Wait for Healthy

```jsx
import { useWaitForHealthy } from './hooks/useSandboxObservability';

function PreviewLoader({ sessionId }) {
  const { status, health, startWaiting, error } = useWaitForHealthy(sessionId);

  useEffect(() => {
    startWaiting();
  }, []);

  if (status === 'waiting') return <Spinner />;
  if (status === 'success') return <Preview />;
  if (status === 'failed') return <Error message={error} />;
}
```

## Health States

| State | Description | Icon | Color |
|-------|-------------|------|-------|
| `unknown` | Status not determined | ❓ | Gray |
| `starting` | Container initializing | 🔄 | Blue |
| `healthy` | All checks passing | ✅ | Green |
| `degraded` | Some checks failing | ⚠️ | Amber |
| `unhealthy` | Most checks failing | ❌ | Red |
| `failed` | Critical failure | 💥 | Dark Red |

## Debug Panel Features

### Logs Tab
- Real-time log streaming with play/pause
- Filter by log level (debug, info, warning, error)
- Auto-scroll to latest
- Clear logs button
- Color-coded log levels

### Health Tab
- Large status indicator with icon
- Uptime display
- Response time metrics
- Success rate percentage
- Memory and CPU usage (when available)
- Recent errors list

### Failures Tab
- Categorized failure cards
- Expandable stack traces
- Actionable suggestions
- Step-by-step fix instructions

## Configuration

Environment variables:
```bash
# API base URL for frontend
VITE_API_BASE_URL=http://localhost:8000

# Host URL for containers
SANDBOX_HOST_URL=http://localhost
API_HOST_URL=http://localhost:8000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend                                 │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ SandboxDebugPanel│  │ useSandboxObservability Hooks  │  │
│  └────────┬─────────┘  └──────────────┬─────────────────┘  │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       │                                     │
│           ┌───────────▼───────────┐                        │
│           │ sandboxObservability  │                        │
│           │      Service          │                        │
│           └───────────┬───────────┘                        │
└───────────────────────┼─────────────────────────────────────┘
                        │ HTTP/SSE
┌───────────────────────┼─────────────────────────────────────┐
│                       │ Backend                             │
│           ┌───────────▼───────────┐                        │
│           │  /api/observability   │                        │
│           │       Router          │                        │
│           └───────────┬───────────┘                        │
│                       │                                     │
│           ┌───────────▼───────────┐                        │
│           │ SandboxObservability  │                        │
│           │      Service          │                        │
│           └───┬───────────────┬───┘                        │
│               │               │                             │
│   ┌───────────▼───┐   ┌───────▼───────────┐               │
│   │ Deployment    │   │ Preview           │               │
│   │ Service       │   │ Orchestrator      │               │
│   └───────────────┘   └───────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Files Created

| File | Purpose |
|------|---------|
| `backend/sandbox_observability.py` | Core observability service |
| `frontend/src/services/sandboxObservability.js` | Frontend API service |
| `frontend/src/hooks/useSandboxObservability.js` | React hooks |
| `frontend/src/components/SandboxDebugPanel.jsx` | Debug UI components |

## Integration Points

The observability service integrates with:
1. **SandboxDeploymentService**: Gets container info and logs
2. **PreviewOrchestrator**: Gets orchestration status and progress
3. **main.py**: Startup/shutdown lifecycle

All components are optional - the system gracefully handles missing dependencies.

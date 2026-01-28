/**
 * Automatic Error Detection and Reporting System
 * Captures runtime errors and sends them to backend for automatic fixing
 */

class ErrorInterceptor {
  constructor(projectSlug, userId, apiBaseUrl = null) {
    this.projectSlug = projectSlug;
    this.userId = userId;
    this.reportedErrors = new Set();
    this.isEnabled = true;
    // Use provided URL, window.API_BASE_URL, or fall back to default
    this.apiBaseUrl = apiBaseUrl || window.API_BASE_URL || 'http://localhost:8000';
    
    this.init();
  }
  
  init() {
    // Intercept console.error
    const originalError = console.error;
    console.error = (...args) => {
      originalError.apply(console, args);
      
      if (this.isEnabled) {
        const errorMessage = args.map(arg => 
          typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
        ).join(' ');
        
        this.reportError(errorMessage, new Error().stack);
      }
    };
    
    // Intercept window.onerror
    window.addEventListener('error', (event) => {
      if (this.isEnabled) {
        this.reportError(
          event.message,
          event.error?.stack || '',
          event.filename
        );
      }
    });
    
    // Intercept unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      if (this.isEnabled) {
        this.reportError(
          `Unhandled Promise Rejection: ${event.reason}`,
          event.reason?.stack || ''
        );
      }
    });
    
    console.log('🤖 Auto-fix agent initialized - errors will be automatically fixed');
  }
  
  async reportError(errorMessage, errorStack = '', filePath = null) {
    // Create unique error signature to avoid duplicate reports
    const errorSignature = `${errorMessage}-${filePath}`.substring(0, 100);
    
    if (this.reportedErrors.has(errorSignature)) {
      return; // Already reported
    }
    
    this.reportedErrors.add(errorSignature);
    
    // Show visual feedback
    this.showAutoFixNotification(errorMessage);
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/auto-fix-errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_name: this.projectSlug,
          user_id: this.userId,
          error_message: errorMessage,
          error_stack: errorStack,
          file_path: filePath,
          timestamp: new Date().toISOString()
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log(`✅ Auto-fix applied: ${result.message}`);
        this.showFixedNotification(result);
        
        // Wait a moment then reload to apply fix
        setTimeout(() => {
          console.log('🔄 Reloading to apply fix...');
          window.location.reload();
        }, 2000);
      } else {
        console.warn(`⚠️ Auto-fix failed: ${result.error}`);
      }
      
    } catch (error) {
      console.error('Failed to report error to auto-fix agent:', error);
    }
  }
  
  showAutoFixNotification(errorMessage) {
    const notification = document.createElement('div');
    notification.id = 'auto-fix-notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 10000;
      font-family: system-ui, -apple-system, sans-serif;
      font-size: 14px;
      max-width: 400px;
      animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="spinner" style="
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          animation: spin 1s linear infinite;
        "></div>
        <div>
          <div style="font-weight: 600; margin-bottom: 4px;">🤖 AI Auto-Fix Activated</div>
          <div style="font-size: 12px; opacity: 0.9;">Analyzing: ${errorMessage.substring(0, 60)}...</div>
        </div>
      </div>
    `;
    
    // Add animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
  }
  
  showFixedNotification(result) {
    const existing = document.getElementById('auto-fix-notification');
    if (existing) {
      existing.style.background = 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)';
      existing.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="font-size: 24px;">✅</div>
          <div>
            <div style="font-weight: 600; margin-bottom: 4px;">Auto-Fix Applied!</div>
            <div style="font-size: 12px; opacity: 0.9;">
              Fixed ${result.error_type} in ${result.file_path?.split('/').pop()}
            </div>
            <div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">
              Reloading in 2 seconds...
            </div>
          </div>
        </div>
      `;
      
      setTimeout(() => {
        existing.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => existing.remove(), 300);
      }, 3000);
    }
  }
  
  disable() {
    this.isEnabled = false;
    console.log('🛑 Auto-fix agent disabled');
  }
  
  enable() {
    this.isEnabled = true;
    console.log('✅ Auto-fix agent enabled');
  }
}

// Auto-initialize for sandbox previews
if (window.location.pathname.includes('/sandbox-preview/') || 
    window.location.search.includes('auto_fix=true')) {
  
  // Extract project slug from URL
  const pathParts = window.location.pathname.split('/');
  const projectSlug = pathParts[pathParts.indexOf('sandbox-preview') + 1] || 
                      new URLSearchParams(window.location.search).get('project');
  
  const userId = new URLSearchParams(window.location.search).get('user_id_alt') ||
                 new URLSearchParams(window.location.search).get('user_email') ||
                 'anonymous';
  
  if (projectSlug) {
    window.errorInterceptor = new ErrorInterceptor(projectSlug, userId);
  }
}

// Export for manual initialization
window.ErrorInterceptor = ErrorInterceptor;

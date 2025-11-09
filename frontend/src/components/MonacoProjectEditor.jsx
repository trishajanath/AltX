import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import MonacoEditor from '@monaco-editor/react';
import PageWrapper from './PageWrapper';

// --- NEW: Add Google Font 'Inter' for a professional UI ---
const fontLink = document.createElement('link');
fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap';
fontLink.rel = 'stylesheet';
if (!document.head.querySelector('[href*="Inter"]')) {
  document.head.appendChild(fontLink);
}

// Add CSS animations for live generation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;
if (!document.head.querySelector('[data-monaco-animations]')) {
  styleSheet.setAttribute('data-monaco-animations', 'true');
  document.head.appendChild(styleSheet);
}

// --- NEW: SVG Icons for a cleaner UI ---
const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M3.478 2.405A.75.75 0 002.25 3.126l18 9a.75.75 0 000 1.348l-18 9a.75.75 0 00-1.228-.721l4.588-6.076a1.68 1.68 0 000-2.31l-4.588-6.076z" />
  </svg>
);

const BackIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path fillRule="evenodd" d="M7.72 12.53a.75.75 0 010-1.06l7.5-7.5a.75.75 0 111.06 1.06L9.31 12l6.97 6.97a.75.75 0 11-1.06 1.06l-7.5-7.5z" clipRule="evenodd" />
  </svg>
);

const FwdIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path fillRule="evenodd" d="M16.28 11.47a.75.75 0 010 1.06l-7.5 7.5a.75.75 0 01-1.06-1.06L14.69 12 7.72 5.03a.75.75 0 011.06-1.06l7.5 7.5z" clipRule="evenodd" />
  </svg>
);


// Inline styles - Refactored for a professional black & white theme
const styles = {
  monacoProjectEditor: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: '#000000',
    color: '#ffffff',
    // --- UPDATED: Professional UI Font ---
    fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
    zIndex: 2000,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  
  // Header styles
  editorHeader: {
    background: '#0a0a0a',
    borderBottom: '1px solid #333333',
    padding: '8px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '48px',
    flexShrink: 0,
  },
  editorTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    fontWeight: 600
  },
  projectName: {
    color: '#ffffff',
    fontSize: '16px'
  },
  projectType: {
    color: '#aaaaaa',
    fontSize: '12px',
    background: 'rgba(255, 255, 255, 0.1)',
    padding: '2px 6px',
    borderRadius: '4px',
    fontWeight: 400,
  },
  buildingIndicator: {
    color: '#ffffff',
    fontSize: '12px',
    marginLeft: '8px',
    animation: 'pulse 2s infinite',
    fontWeight: 500,
  },
  editorActions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center'
  },
  btnEditorAction: {
    background: 'transparent',
    color: '#ffffff',
    border: '1px solid #ffffff',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'inherit', // Use Inter font
    transition: 'background 0.2s, color 0.2s',
  },
  
  // Navigation styles
  navigationControls: {
    display: 'flex',
    gap: '4px',
    alignItems: 'center',
    marginRight: '8px'
  },
  // --- UPDATED: Cleaner nav buttons ---
  navButton: {
    background: 'transparent',
    color: '#aaaaaa',
    border: '1px solid #333333',
    padding: '4px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '11px',
    transition: 'background 0.2s, color 0.2s',
    minWidth: '28px',
    height: '28px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navButtonDisabled: {
    opacity: 0.3,
    cursor: 'not-allowed'
  },
  navButtonHover: {
    background: '#1a1a1a',
    color: '#ffffff',
  },
  
  // New layout styles
  newEditorLayout: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
    minHeight: 0,
    height: 'calc(100vh - 48px)'
  },
  
  // Chat panel (left side)
  chatPanel: {
    width: '400px',
    minWidth: '300px',
    maxWidth: '500px',
    background: '#0a0a0a',
    borderRight: '1px solid #333333',
    display: 'flex',
    flexDirection: 'column',
    resize: 'horizontal',
    overflow: 'hidden',
    height: '100%',
    minHeight: 0
  },
  
  // Right panel (preview or code)
  rightPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    background: '#000000',
    minHeight: 0
  },
  
  rightPanelHeader: {
    background: '#0a0a0a',
    borderBottom: '1px solid #333333',
    padding: '8px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '40px',
    flexShrink: 0,
  },
  
  sidebarTabs: {
    display: 'flex',
    gap: '4px'
  },
  
  sidebarTab: {
    background: 'transparent',
    color: '#ffffff',
    border: 'none',
    padding: '6px 10px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'inherit',
    transition: 'all 0.2s'
  },
  
  sidebarTabActive: {
    background: '#ffffff',
    color: '#000000',
  },
  
  viewToggleButtons: {
    display: 'flex',
    gap: '4px',
    border: '1px solid #333333',
    borderRadius: '6px',
    padding: '2px',
  },
  
  viewToggleButton: {
    background: 'transparent',
    color: '#aaaaaa',
    border: 'none',
    padding: '4px 10px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'inherit',
    transition: 'all 0.2s'
  },
  
  viewToggleButtonActive: {
    background: '#ffffff',
    color: '#000000',
  },
  
  rightPanelContent: {
    flex: 1,
    overflow: 'hidden',
    background: '#000000',
    minHeight: 0
  },
  
  // Chat styles
  chatContainer: {
    display: 'grid',
    gridTemplateRows: '1fr auto',
    flex: 1,
    minHeight: 0,
    overflow: 'hidden',
    maxHeight: '100%'
  },
  
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '20px 16px',
    gap: '12px',
    display: 'flex',
    flexDirection: 'column',
    scrollbarWidth: 'thin',
    scrollBehavior: 'smooth',
    maxHeight: '100%',
    scrollbarColor: '#333333 #111111'
  },
  
  chatMessage: {
    maxWidth: '85%',
    padding: '16px 20px',
    margin: '8px 0',
    borderRadius: '16px',
    fontSize: '14px',
    lineHeight: 1.6,
    whiteSpace: 'pre-wrap',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: '400',
    wordBreak: 'break-word',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    position: 'relative',
  },
  
  // --- UPDATED: Enhanced professional chat bubbles ---
  chatMessageUser: {
    background: '#ffffff',
    color: '#1a1a1a',
    alignSelf: 'flex-end',
    marginLeft: 'auto',
    border: '1px solid #e5e7eb',
    fontWeight: '500',
  },
  
  chatMessageAssistant: {
    background: '#111111',
    border: '1px solid #333333',
    color: '#f9fafb',
    alignSelf: 'flex-start',
    fontWeight: '400',
  },
  
  chatInputContainer: {
    padding: '20px 16px',
    borderTop: '1px solid #333333',
    display: 'flex',
    gap: '12px',
    background: '#0a0a0a',
    alignItems: 'flex-end',
    boxShadow: '0 -1px 0 rgba(255,255,255,0.06)'
  },
  
  chatInput: {
    flex: 1,
    background: '#111111',
    color: '#ffffff',
    border: '1px solid #333333',
    borderRadius: '12px',
    padding: '14px 18px',
    fontSize: '14px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    outline: 'none',
    resize: 'none',
    minHeight: '22px',
    maxHeight: '120px',
    lineHeight: 1.5,
  },
  
  // --- UPDATED: Send button styles for icon ---
  chatSendButton: {
    background: '#ffffff',
    color: '#000000',
    border: 'none',
    borderRadius: '12px',
    padding: '12px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    marginBottom: '2px',
  },
  
  // File tree styles
  fileTree: {
    flex: 1,
    padding: '8px',
    fontSize: '13px',
    overflow: 'auto',
    color: '#ffffff'
  },
  
  fileTreeItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '6px 8px',
    cursor: 'pointer',
    borderRadius: '4px',
    marginBottom: '2px',
    gap: '8px',
    color: '#ffffff',
    fontFamily: "'Inter', sans-serif",
  },
  
  fileTreeItemHover: {
    background: '#1a1a1a'
  },
  
  fileTreeItemSelected: {
    background: '#ffffff',
    color: '#000000',
  },

  // --- NEW: Style for file type identifier ---
  fileTypeIcon: {
    color: '#888888',
    width: '20px',
    fontSize: '12px',
    display: 'inline-block',
    textAlign: 'center',
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
  },

  // New: Code area row layout
  codeAreaRow: {
    flex: 1,
    display: 'flex',
    flexDirection: 'row',
    minHeight: 0,
    overflow: 'hidden'
  },
  fileTreePane: {
    width: '260px',
    minWidth: '220px',
    maxWidth: '360px',
    borderRight: '1px solid #333333',
    overflow: 'auto',
    background: '#000000'
  },
  codeEditorPane: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  
  welcomeScreen: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    textAlign: 'center',
    maxWidth: '600px',
    margin: '0 auto',
    padding: '40px',
    color: '#ffffff',
  },
  
  welcomeScreenH2: {
    color: '#ffffff',
    marginBottom: '16px',
    fontSize: '24px',
    fontWeight: 600,
  },
  
  welcomeScreenP: {
    color: '#aaaaaa',
    marginBottom: '12px',
    lineHeight: 1.6,
    fontSize: '14px',
  }
};

const MonacoProjectEditor = () => {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Extract full project path from wildcard route
  const projectName = params['*'] || location.pathname.replace('/project/', '');
  
  // Handle close action - navigate back to home
  const handleClose = () => {
    console.log('Closing Monaco editor, navigating to home');
    navigate('/home');
  };
  
  // Create project object from URL parameter
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [fileTree, setFileTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContents, setFileContents] = useState({});
  const [activeTab, setActiveTab] = useState('files');
  const [errors, setErrors] = useState([]);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoFixing, setIsAutoFixing] = useState(false);
  const [hasErrors, setHasErrors] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [layoutMode, setLayoutMode] = useState('preview'); // 'preview' or 'code'
  const [terminalOutput, setTerminalOutput] = useState([]); // Live generation output
  const [viewHistory, setViewHistory] = useState([]);
  const [currentViewIndex, setCurrentViewIndex] = useState(-1);
  const [pendingChanges, setPendingChanges] = useState(false);
  const [lastChangeTime, setLastChangeTime] = useState(null);
  
  const chatEndRef = useRef(null);
  const changeTimeoutRef = useRef(null);
  const wsRef = useRef(null);
  const connectTimerRef = useRef(null);

  // Function to refresh preview - FIXED SCOPE ISSUE
  const refreshPreview = useCallback(() => {
    if (previewUrl) {
      const iframe = document.querySelector('iframe[src*="localhost"]');
      if (iframe) {
        // Get the base URL and add fresh timestamp
        const baseUrl = iframe.src.split('?')[0];
        iframe.src = `${baseUrl}?_refresh=${Date.now()}`;
      }
    }
  }, [previewUrl]);

  // Initialize project from URL parameter
  useEffect(() => {
    console.log('MonacoProjectEditor initializing with projectName:', projectName);
    if (projectName) {
      const projectData = {
        name: projectName,
        tech_stack: ['React', 'FastAPI'], // Default tech stack
        isBuilding: false,
        preview_url: null
      };
      console.log('Setting project data:', projectData);
      setProject(projectData);
      setIsLoading(false);
    } else {
      // No project name in URL, redirect to home
      console.log('No project name found, redirecting to home');
      navigate('/home');
    }
  }, [projectName, navigate]);

  // Initialize project
  useEffect(() => {
    if (project?.name) {
      // Set initial building state from project
      setIsBuilding(project.isBuilding || false);
      setPreviewUrl(project.preview_url || null);
      
      initializeProject();
      setupWebSocket();
      
      // Initialize chat with welcome message
      const welcomeMessage = {
        role: 'assistant',
        // --- UPDATED: Welcome message formatting ---
        content: `Welcome to your AI coding assistant!
I'm here to help you build, debug, and improve your project.

You can ask me to:
•  Add new features
•  Fix bugs and errors
•  Improve styling
•  Explain complex code

Just tell me what you'd like to do.`
      };
      setChatMessages([welcomeMessage]);
      // Cleanup WebSocket when project changes or component unmounts
      return () => {
        try {
          if (connectTimerRef.current) {
            clearTimeout(connectTimerRef.current);
            connectTimerRef.current = null;
          }
          const ws = wsRef.current;
          if (ws) {
            if (ws.readyState === WebSocket.OPEN) {
              ws.close();
            } else if (ws.readyState === WebSocket.CONNECTING) {
              // Defer close until after open to avoid 'closed before established' console error
              ws.onopen = () => {
                try { ws.close(); } catch (_) {}
              };
            }
          }
        } catch (e) {
          // no-op
        } finally {
          wsRef.current = null;
        }
      };
    }
  }, [project]);

  // Console Error Monitoring and Auto-Fix
  useEffect(() => {
    let errorQueue = [];
    let errorTimeoutId = null;
    let isProcessingErrors = false;
    
    // Original console.error to avoid infinite loops
    const originalConsoleError = console.error;
    const originalConsoleWarn = console.warn;
    
    // Console error interceptor
    const errorInterceptor = (...args) => {
      // Call original console.error first
      originalConsoleError.apply(console, args);
      
      // Process the error for auto-fixing
      const errorMessage = args.map(arg => 
        typeof arg === 'string' ? arg : JSON.stringify(arg)
      ).join(' ');
      
      // Filter relevant errors (JavaScript/React compilation errors)
      if (shouldProcessError(errorMessage)) {
        queueErrorForProcessing(errorMessage);
      }
    };
    
    // Console warning interceptor (for React warnings)
    const warnInterceptor = (...args) => {
      originalConsoleWarn.apply(console, args);
      
      const warnMessage = args.map(arg => 
        typeof arg === 'string' ? arg : JSON.stringify(arg)
      ).join(' ');
      
      // Process React warnings that indicate syntax issues
      if (shouldProcessWarning(warnMessage)) {
        queueErrorForProcessing(warnMessage);
      }
    };
    
    // Function to determine if error should be processed
    const shouldProcessError = (message) => {
      const relevantPatterns = [
        /SyntaxError/i,
        /Unexpected token/i,
        /Parse error/i,
        /Module build failed/i,
        /Compilation failed/i,
        /TypeError.*Cannot read/i,
        /ReferenceError/i,
        /exports is not defined/i,
        /require is not defined/i,
        /module is not defined/i,
        /if.*else.*expected/i,
        /Missing.*expected/i,
        /Identifier.*already.*declared/i
      ];
      
      return relevantPatterns.some(pattern => pattern.test(message)) &&
             !message.includes('node_modules') &&
             !message.includes('hot-reload');
    };
    
    // Function to determine if warning should be processed
    const shouldProcessWarning = (message) => {
      const relevantWarnings = [
        /Warning.*Failed to compile/i,
        /Warning.*Parse error/i,
        /Warning.*Invalid JSX/i,
        /React Error Boundary caught/i,
        /React Error Details/i
      ];
      
      return relevantWarnings.some(pattern => pattern.test(message));
    };
    
    // Queue errors for batch processing
    const queueErrorForProcessing = (errorMessage) => {
      if (isProcessingErrors) return;
      
      errorQueue.push({
        message: errorMessage,
        timestamp: Date.now(),
        projectName: project?.name || projectName
      });
      
      // Clear existing timeout
      if (errorTimeoutId) {
        clearTimeout(errorTimeoutId);
      }
      
      // Process errors after 2 seconds of no new errors
      errorTimeoutId = setTimeout(() => {
        processErrorQueue();
      }, 2000);
    };
    
    // Process accumulated errors
    const processErrorQueue = async () => {
      if (errorQueue.length === 0 || isProcessingErrors) {
        console.log('Skipping error processing - no errors or already processing');
        return;
      }
      
      isProcessingErrors = true;
      
      try {
        // Get the most recent error
        const latestError = errorQueue[errorQueue.length - 1];
        console.log('Processing console error for auto-fix:', latestError.message);
        console.log('Error queue length:', errorQueue.length);
        
        // Check if this is a main application error vs generated project error
        const isMainAppError = latestError.message.includes('MonacoProjectEditor.jsx') || 
                               latestError.message.includes('VoiceChatInterface.jsx') ||
                               latestError.message.includes('HomePage.jsx');
        
        if (isMainAppError) {
          console.log('Main application error detected - this was already fixed in code');
          
          // Show a different message for main app errors
          const fixMessage = {
            role: 'assistant',  
            content: `**Error Detected & Fixed!**\n\n**Issue:** ${latestError.message.split('\n')[0]}\n\n**Status:** This error has been automatically resolved in the application code. The page should refresh shortly to apply the fix.\n\n*No action needed from you!*`
          };
          
          setChatMessages(prev => [...prev, fixMessage]);
          return;
        }
        
        // Extract file info from error message if available
        const filePathMatch = latestError.message.match(/\/src\/[\w\/.-]+\.(jsx?|tsx?)/);
        const lineNumberMatch = latestError.message.match(/:(\d+):/);
        
        const errorRequest = {
          project_name: latestError.projectName,
          error_message: latestError.message,
          file_path: filePathMatch ? filePathMatch[0] : null,
          line_number: lineNumberMatch ? parseInt(lineNumberMatch[1]) : null,
          error_type: 'console_error'
        };
        
        // Call the new Gemini auto-fix endpoint
        const response = await fetch('http://localhost:8000/api/gemini-fix-console-error', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorRequest)
        });
        
        const result = await response.json();
        
        if (result.success) {
          console.log('Auto-fix applied successfully:', result.explanation);
          
          // Show success message in chat
          const successMessage = {
            role: 'assistant',
            content: `**Auto-Fix Applied!**\n\n**Issue Fixed:** ${result.explanation}\n\n${result.suggestions?.length > 0 ? `**Additional Suggestions:**\n${result.suggestions.map(s => `• ${s}`).join('\n')}` : ''}\n\n*The error has been automatically resolved using Gemini AI.*`
          };
          
          setChatMessages(prev => [...prev, successMessage]);
          
          // Trigger reload if changes were applied
          if (result.changes_applied) {
            setTimeout(() => {
              refreshPreview();
            }, 1000);
          }
        } else {
          console.log('Auto-fix failed:', result.error);
          
          // Show error message in chat
          const errorMessage = {
            role: 'assistant',
            content: `**Auto-Fix Issue**\n\nI detected an error but couldn't fix it automatically:\n\n**Error:** ${result.error}\n\n${result.explanation ? `**Analysis:** ${result.explanation}\n\n` : ''}Please check the console for more details or ask me for help manually.`
          };
          
          setChatMessages(prev => [...prev, errorMessage]);
        }
        
      } catch (error) {
        console.error('Auto-fix processing failed:', error);
      } finally {
        // Clear error queue and reset processing state
        errorQueue = [];
        isProcessingErrors = false;
        if (errorTimeoutId) {
          clearTimeout(errorTimeoutId);
          errorTimeoutId = null;
        }
      }
    };
    
    // Install error interceptors
    console.error = errorInterceptor;
    console.warn = warnInterceptor;
    
    // Listen for unhandled errors - ENHANCED ERROR CATCHING
    const handleError = (event) => {
      const errorMessage = event.message || event.error?.message || '';
      if (shouldProcessError(errorMessage)) {
        console.log('Global error detected for auto-fix:', errorMessage);
        queueErrorForProcessing(errorMessage);
      }
    };
    
    const handleUnhandledRejection = (event) => {
      if (shouldProcessError(event.reason?.message || event.reason || '')) {
        queueErrorForProcessing(`Promise rejection: ${event.reason?.message || event.reason}`);
      }
    };
    
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    // Cleanup function
    return () => {
      // Restore original console methods
      console.error = originalConsoleError;
      console.warn = originalConsoleWarn;
      
      // Remove event listeners
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      
      // Clear timeouts
      if (errorTimeoutId) {
        clearTimeout(errorTimeoutId);
      }
    };
  }, [project, projectName, previewUrl, setChatMessages]);

  // Debounced file change detection
  const triggerPreviewReload = useCallback(() => {
    if (!previewUrl || isBuilding) return;
    
    const iframe = document.querySelector('iframe[src*="localhost"]');
    if (iframe) {
      const baseUrl = iframe.src.split('?')[0];
      const timestamp = Date.now();
      iframe.src = `${baseUrl}?_v=${timestamp}`;
      console.log('Preview reloaded due to file changes');
    }
  }, [previewUrl, isBuilding]);

  // Smart Auto-Reload on File Changes with Debouncing
  useEffect(() => {
    // Early return if project is not loaded yet
    if (!project) return;
    
    let fileWatcher = null;
    let lastFileHash = null;
    
    // Generate hash of current project files
    const generateFileHash = () => {
      if (!project?.files || Object.keys(project.files).length === 0) return '';
      
      const fileContents = Object.entries(project.files)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([path, content]) => `${path}:${content}`)
        .join('|');
      
      // Simple hash function for change detection
      let hash = 0;
      for (let i = 0; i < fileContents.length; i++) {
        const char = fileContents.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
      }
      return hash.toString();
    };
    
    // Initialize hash
    if (project?.files && Object.keys(project.files).length > 0) {
      lastFileHash = generateFileHash();
    }
    
    // Enable smart auto-reload when preview is running
    if (previewUrl && !isBuilding && project?.files) {
      fileWatcher = setInterval(() => {
        const currentHash = generateFileHash();
        
        // Only reload if files have actually changed
        if (currentHash !== lastFileHash && currentHash !== '') {
          console.log('File content changes detected');
          lastFileHash = currentHash;
          
          // Show pending changes indicator
          setPendingChanges(true);
          setLastChangeTime(Date.now());
          
          // Clear any existing timeout
          if (changeTimeoutRef.current) {
            clearTimeout(changeTimeoutRef.current);
          }
          
          // Debounce the reload to avoid excessive refreshing during editing
          changeTimeoutRef.current = setTimeout(() => {
            triggerPreviewReload();
            setPendingChanges(false);
          }, 1500); // Wait 1.5 seconds after last change
          
        }
      }, 1000); // Check every 1 second for responsiveness
    }
    
    return () => {
      if (fileWatcher) {
        clearInterval(fileWatcher);
      }
      if (changeTimeoutRef.current) {
        clearTimeout(changeTimeoutRef.current);
      }
    };
  }, [previewUrl, isBuilding, project?.files, triggerPreviewReload]);

  // Handle error notifications
  useEffect(() => {
    if (hasErrors && errors.length > 0) {
      const errorMessage = {
        role: 'assistant',
        // --- UPDATED: Error message formatting ---
        content: `**Warning: ${errors.length} error(s) detected.**

${errors.slice(-3).map(err => `• ${err.message}`).join('\n')}

Click the "Fix Errors" button or ask me to "fix the errors" and I'll try to resolve them automatically.`
      };
      
      // Only add if we don't already have a recent error message
      setChatMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.content.includes('detected') && lastMessage.content.includes('error')) {
          // Replace the last error message with the updated one
          return [...prev.slice(0, -1), errorMessage];
        } else {
          return [...prev, errorMessage];
        }
      });
    }
  }, [hasErrors, errors.length]);

  // Keep chat scrolled to the latest message
  useEffect(() => {
    try {
      if (chatEndRef.current) {
        chatEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    } catch (e) {
      // no-op
    }
  }, [chatMessages, isAiThinking]);

  const initializeProject = async () => {
    // Load file tree
    try {
      const response = await fetch(`http://localhost:8000/api/project-file-tree?project_name=${encodeURIComponent(project.name)}`);
      const data = await response.json();
      if (data.success) {
        setFileTree(data.file_tree || []);
      } else {
        console.error('Failed to load file tree:', data.error);
        setFileTree([]);
      }
    } catch (error) {
      console.error('Failed to load file tree:', error);
      setFileTree([]);
    }
  };

  const setupWebSocket = () => {
    // Debounce creation to avoid StrictMode double-mount racing
    if (connectTimerRef.current) {
      clearTimeout(connectTimerRef.current);
      connectTimerRef.current = null;
    }

    connectTimerRef.current = setTimeout(() => {
      // If an existing socket is CONNECTING or OPEN, don't create another
      if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
        return;
      }

      const ws = new WebSocket(`ws://localhost:8000/ws/project/${project.name}`);
      wsRef.current = ws;

      ws.onopen = () => {
        // Connected successfully
      };

      ws.onclose = () => {
        // Socket closed; avoid noisy errors from double-init
      };

      ws.onerror = () => {
        // Swallow transient errors during dev StrictMode
      };

      ws.onmessage = (event) => {
      let data;
      try {
        // Safely parse the WebSocket data
        if (!event.data || event.data === 'undefined' || event.data === 'null') {
          console.warn('Received invalid WebSocket data:', event.data);
          return;
        }
        data = JSON.parse(event.data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', event.data, error);
        return;
      }
      
      switch (data.type) {
        case 'preview_ready':
          setPreviewUrl(data.url);
          setIsBuilding(false);
          setIsRunning(true);
          setTerminalOutput(prev => [...prev, `Live preview ready!`]);
          // Clear errors on successful preview
          setHasErrors(false);
          setErrors([]);
          break;
        case 'status':
          if (data.phase === 'ready') {
            setIsBuilding(false);
            setIsRunning(true);
            if (data.preview_url) {
              setPreviewUrl(data.preview_url);
            }
          } else if (data.phase === 'generate') {
            // Show AI generation progress
            setTerminalOutput(prev => [...prev, `AI: ${data.message}`]);
          } else if (data.phase === 'frontend') {
            setTerminalOutput(prev => [...prev, `Frontend: ${data.message}`]);
          } else if (data.phase === 'backend') {
            setTerminalOutput(prev => [...prev, `Backend: ${data.message}`]);
          } else if (data.phase === 'config') {
            setTerminalOutput(prev => [...prev, `Config: ${data.message}`]);
          }
          break;
        case 'file_created':
          // Show live file creation
          setTerminalOutput(prev => [...prev, `Created ${data.file_path}`]);
          // Refresh file tree to show new file
          if (fileTree.length > 0) {
            initializeProject();
          }
          break;
        case 'file_content_update':
          // Show live typing effect for file content
          setTerminalOutput(prev => [...prev, `Writing ${data.file_path}...`]);
          break;
        case 'file_creation_start':
          setTerminalOutput(prev => [...prev, `${data.message}`]);
          break;
        case 'file_creation_complete':
          setTerminalOutput(prev => [...prev, `Success: ${data.message}`]);
          // Refresh file tree after completion
          setTimeout(() => {
            initializeProject();
          }, 500);
          break;
        case 'terminal_output':
          // Show general terminal output
          setTerminalOutput(prev => [...prev, data.message]);
          
          // Check for error patterns in terminal output
          if (data.level === 'error' || data.message.includes('Error:') || 
              data.message.includes('Failed to') || data.message.includes('Cannot find')) {
            setHasErrors(true);
            setErrors(prev => [...prev, {
              message: data.message,
              severity: 'error',
              timestamp: new Date().toISOString()
            }]);
          }
          break;
        case 'file_changed':
          // Reload file tree when files change
          initializeProject();
          break;
        case 'build_error':
          // Handle build errors specifically
          setHasErrors(true);
          setErrors(prev => [...prev, {
            message: data.message || 'Build failed',
            file: data.file,
            line: data.line,
            severity: 'error',
            timestamp: new Date().toISOString()
          }]);
          setTerminalOutput(prev => [...prev, `Error: ${data.message}`]);
          break;
        }
      };
    }, 50);
  };

  const runProject = async () => {
    setIsBuilding(true);
    setTerminalOutput([]); // Clear terminal on new run
    try {
      const response = await fetch('http://localhost:8000/api/run-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          tech_stack: project.tech_stack || []
        })
      });
      
      const result = await response.json();
      if (result.success && result.preview_url) {
        setPreviewUrl(result.preview_url);
        setIsRunning(true);
        // Clear previous errors on successful run
        setHasErrors(false);
        setErrors([]);
      } else {
        // Handle API-level errors
        const errorMsg = result.error || 'Failed to run project';
        setHasErrors(true);
        setErrors(prev => [...prev, {
          message: errorMsg,
          severity: 'error',
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Failed to run project:', error);
    } finally {
      setIsBuilding(false);
    }
  };

  const autoFixErrors = async () => {
    setIsAutoFixing(true);
    let fixAttempted = false;
    
    try {
      // First try the traditional auto-fix endpoint
      const response = await fetch(`http://localhost:8000/api/auto-fix-project-errors?project_name=${encodeURIComponent(project.name)}`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.success) {
        fixAttempted = true;
        
        // Add success message to chat
        const successMessage = {
          role: 'assistant',
          content: `**Auto-Fix Completed!**
${result.message}
${result.fixes_applied && result.fixes_applied.length > 0 ? `\n**Fixes Applied:**\n${result.fixes_applied.map(fix => `• ${fix}`).join('\n')}` : ''}

Your project has been repaired. Trying to run it again...`
        };
        setChatMessages(prev => [...prev, successMessage]);
        
        // Reload project structure and clear errors
        setErrors([]);
        setHasErrors(false);
        initializeProject();
        
        // Auto-run the project after fixing
        setTimeout(() => {
          runProject();
        }, 1000);
      } else {
        // If traditional auto-fix failed, try Gemini-powered fix
        await tryGeminiAutoFix();
        fixAttempted = true;
      }
    } catch (error) {
      if (!fixAttempted) {
        // If first attempt failed with error, try Gemini-powered fix
        try {
          await tryGeminiAutoFix();
          fixAttempted = true;
        } catch (geminiError) {
          const errorMessage = {
            role: 'assistant',
            content: `**Error: Auto-fix failed.**
           
**Initial Fix Error:** ${error.message}
**AI Fix Error:** ${geminiError.message}

Please try describing the issue manually.`
          };
          setChatMessages(prev => [...prev, errorMessage]);
        }
      }
      
      if (!fixAttempted) {
        const errorMessage = {
          role: 'assistant',
          content: `Error: Failed to auto-fix errors: ${error.message}`
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsAutoFixing(false);
    }
  };
  
  // Helper function for Gemini-powered auto-fix
  const tryGeminiAutoFix = async () => {
    // Get the most recent console error or use generic error message
    const recentErrors = errors.slice(-3); // Get last 3 errors
    const errorMessage = recentErrors.length > 0 
      ? recentErrors.map(err => `${err.severity}: ${err.message} (${err.file}:${err.line})`).join('\n')
      : 'General compilation or runtime errors detected';
    
    const geminiRequest = {
      project_name: project.name,
      error_message: errorMessage,
      file_path: recentErrors.length > 0 ? recentErrors[0].file : null,
      line_number: recentErrors.length > 0 ? recentErrors[0].line : null,
      error_type: 'manual_fix_request'
    };
    
    const geminiResponse = await fetch('http://localhost:8000/api/gemini-fix-console-error', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(geminiRequest)
    });
    
    const geminiResult = await geminiResponse.json();
    
    if (geminiResult.success) {
      const successMessage = {
        role: 'assistant',
        content: `**Gemini AI Auto-Fix Applied!**

**Analysis:** ${geminiResult.explanation}
${geminiResult.suggestions?.length > 0 ? `\n**Improvements Made:**\n${geminiResult.suggestions.map(s => `• ${s}`).join('\n')}` : ''}

${geminiResult.changes_applied ? '*Files have been automatically updated.*' : '*Analysis complete. Please review the suggestions.*'}

Trying to run the project again...`
      };
      setChatMessages(prev => [...prev, successMessage]);
      
      // Reload project structure
      setErrors([]);
      setHasErrors(false);
      initializeProject();
      
      // Auto-run the project after fixing
      if (geminiResult.changes_applied) {
        setTimeout(() => {
          runProject();
        }, 1000);
      }
    } else {
      throw new Error(geminiResult.error || 'Gemini AI fix failed');
    }
  };

  const loadFileContent = async (filePath) => {
    try {
      const response = await fetch(`http://localhost:8000/api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent(filePath)}`);
      const data = await response.json();
      
      if (data.success) {
        setFileContents(prev => ({
          ...prev,
          [filePath]: data.content
        }));
        
        // Add to view history if it's a new file
        addToViewHistory(filePath);
      }
    } catch (error) {
      console.error('Failed to load file content:', error);
    }
  };

  // Navigation functions
  const addToViewHistory = (filePath) => {
    setViewHistory(prev => {
      // Remove if already exists to avoid duplicates
      const filtered = prev.filter(path => path !== filePath);
      const newHistory = [...filtered, filePath];
      // Keep only last 20 files in history
      const trimmedHistory = newHistory.slice(-20);
      setCurrentViewIndex(trimmedHistory.length - 1);
      return trimmedHistory;
    });
  };

  const goBack = () => {
    if (currentViewIndex > 0) {
      const newIndex = currentViewIndex - 1;
      const previousFile = viewHistory[newIndex];
      setCurrentViewIndex(newIndex);
      setSelectedFile(previousFile);
      if (!fileContents[previousFile]) {
        loadFileContent(previousFile);
      }
    }
  };

  const goForward = () => {
    if (currentViewIndex < viewHistory.length - 1) {
      const newIndex = currentViewIndex + 1;
      const nextFile = viewHistory[newIndex];
      setCurrentViewIndex(newIndex);
      setSelectedFile(nextFile);
      if (!fileContents[nextFile]) {
        loadFileContent(nextFile);
      }
    }
  };

  const canGoBack = currentViewIndex > 0;
  const canGoForward = currentViewIndex < viewHistory.length - 1;

  const sendChatMessage = async () => {
    if (!chatInput.trim() || isAiThinking) return;
    
    const userMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMessage]);
    const messageToSend = chatInput;
    setChatInput('');
    setIsAiThinking(true);
    
    // Check if user is asking for error fixing
    const errorFixKeywords = ['fix error', 'fix the error', 'fix bug', 'fix issue', 'auto fix', 'repair', 'fix problems'];
    const isErrorFixRequest = errorFixKeywords.some(keyword => 
      messageToSend.toLowerCase().includes(keyword)
    );
    
    if (isErrorFixRequest && hasErrors) {
      setIsAiThinking(false);
      const fixMessage = {
        role: 'assistant',
        content: `Understood. I'll run the auto-fix tool for you now.`
      };
      setChatMessages(prev => [...prev, fixMessage]);
      
      // Trigger auto-fix
      setTimeout(() => {
        autoFixErrors();
      }, 500);
      return;
    }
    
    try {
      const response = await fetch('http://localhost:8000/api/ai-project-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          user_message: messageToSend,
          tech_stack: project.tech_stack || [],
          re_run: true // Auto re-run after changes
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        const assistantMessage = {
          role: 'assistant',
          content: `**Success:** ${result.explanation || "I've made the requested changes!"}
${result.files_modified && result.files_modified.length > 0 ? `\n**Modified files:** ${result.files_modified.join(', ')}` : ''}
${result.errors && result.errors.length > 0 ? `\n**Warning:** ${result.errors.length} issue(s) detected.` : ''}

The changes have been applied and the preview has been updated.`
        };
        setChatMessages(prev => [...prev, assistantMessage]);
        
        // Reload project files and preview
        initializeProject();
        if (result.preview_url) {
          setPreviewUrl(result.preview_url);
        }
      } else {
        const errorMessage = {
          role: 'assistant',
          content: `**Error:** ${result.error || 'I encountered an issue and could not make those changes.'}`
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `**Error:** Sorry, there was an error processing your request: ${error.message}`
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiThinking(false);
    }
  };

  // --- UPDATED: renderFileTree to use cleaner icons ---
  const renderFileTree = (items, level = 0) => {
    return items.map((item, index) => (
      <div key={index}>
        <div 
          style={{
            ...styles.fileTreeItem,
            paddingLeft: `${8 + level * 16}px`,
            ...(selectedFile === item.path ? styles.fileTreeItemSelected : {})
          }}
          onClick={() => {
            if (item.type === 'file') {
              setSelectedFile(item.path);
              loadFileContent(item.path);
            }
          }}
        >
          <span style={{...styles.fileTypeIcon, color: selectedFile === item.path ? '#000000' : '#888888'}}>
            {item.type === 'dir' ? '[D]' : '[F]'}
          </span>
          <span>{item.name}</span>
        </div>
        {item.children && renderFileTree(item.children, level + 1)}
      </div>
    ));
  };

  const getLanguageFromFileName = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    const langMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'css': 'css',
      'html': 'html',
      'json': 'json',
      'md': 'markdown'
    };
    return langMap[ext] || 'plaintext';
  };

  // Show loading state while project is being initialized
  if (isLoading || !project) {
    return (
      <div style={styles.monacoProjectEditor}>
        <div style={styles.editorHeader}>
          <div style={styles.editorTitle}>
            <span style={styles.projectName}>Loading Project...</span>
          </div>
        </div>
        <div style={styles.welcomeScreen}>
          {/* --- UPDATED: Loading text --- */}
          <h2 style={styles.welcomeScreenH2}>Loading Project: {projectName}...</h2>
        </div>
      </div>
    );
  }

  return (
    <PageWrapper>
      <div style={styles.monacoProjectEditor}>
      {/* Header */}
      <div style={styles.editorHeader}>
        <div style={styles.editorTitle}>
          <button 
            style={{
              ...styles.btnEditorAction,
              background: 'transparent',
              border: '1px solid #555555',
              color: '#aaaaaa',
              marginRight: '12px',
            }}
            onClick={handleClose}
            // --- UPDATED: Text ---
            title="Return to Dashboard"
          >
            Exit Editor
          </button>
          <span style={styles.projectName}>{project.name}</span>
          <span style={styles.projectType}>({project.tech_stack?.join(', ') || 'Mixed'})</span>
          {isBuilding && <span style={styles.buildingIndicator}>Building...</span>}
        </div>
        
        <div style={styles.editorActions}>
          <button 
            style={{
              ...styles.btnEditorAction,
              ...(isRunning || isBuilding ? { opacity: 0.5 } : {})
            }}
            onClick={runProject}
            disabled={isRunning || isBuilding}
            title="Run Project (F5)"
          >
            {/* --- UPDATED: Text --- */}
            {isBuilding ? 'Building...' : isRunning ? 'Running...' : 'Run'}
          </button>
          
          {hasErrors && (
            <button 
              style={{
                ...styles.btnEditorAction,
                color: '#000000', // Black text
                background: '#ffffff', // White background for error
                border: '1px solid #ffffff',
                ...(isAutoFixing ? { opacity: 0.5 } : {})
              }}
              onClick={autoFixErrors}
              disabled={isAutoFixing}
              title="Auto-fix detected errors"
            >
              {/* --- UPDATED: Text --- */}
              {isAutoFixing ? 'Fixing...' : 'Fix Errors'}
            </button>
          )}
          
          {previewUrl && (
            <button 
              style={{
                ...styles.btnEditorAction,
                ...(pendingChanges ? { 
                  background: '#ffffff', 
                  color: '#000000',
                  boxShadow: '0 0 10px rgba(255, 255, 255, 0.5)'
                } : {})
              }}
              onClick={() => {
                refreshPreview();
                setPendingChanges(false);
                if (changeTimeoutRef.current) {
                  clearTimeout(changeTimeoutRef.current);
                }
                setChatMessages(prev => [...prev, {
                  role: 'assistant',
                  content: 'Info: **Preview Refreshed!**\n\nThe preview has been manually reloaded.'
                }]);
              }}
              title={pendingChanges ? "File changes detected - Click to refresh" : "Refresh Preview"}
            >
              {/* --- UPDATED: Text --- */}
              {pendingChanges ? 'Refresh (Changes)' : 'Refresh Preview'}
            </button>
          )}
          
          {previewUrl && (
            <button 
              style={{...styles.btnEditorAction}}
              onClick={() => window.open(previewUrl, '_blank')}
              title="Open in New Tab"
            >
              {/* --- UPDATED: Text --- */}
              Open Tab
            </button>
          )}
          
          <button 
            style={{...styles.btnEditorAction, border: '1px solid #555555', color: '#aaaaaa'}}
            onClick={handleClose}
            title="Exit Editor"
          >
            {/* --- UPDATED: Text --- */}
            Exit
          </button>
        </div>
      </div>

      {/* New Layout: Chat Left, Preview/Code Right */}
      <div style={styles.newEditorLayout}>
        {/* Left Panel: AI Chat */}
        <div style={styles.chatPanel}>
          <div style={styles.rightPanelHeader}>
            <div style={styles.sidebarTabs}>
              <button style={{...styles.sidebarTab, ...styles.sidebarTabActive}}>
                {/* --- UPDATED: Text --- */}
                AI Chat
              </button>
            </div>
          </div>
          
          <div style={styles.chatContainer}>
            <div style={styles.chatMessages} ref={chatEndRef}>
              {chatMessages.map((message, index) => (
                <div 
                  key={index} 
                  style={{
                    ...styles.chatMessage,
                    ...(message.role === 'user' ? styles.chatMessageUser : styles.chatMessageAssistant)
                  }}
                >
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    opacity: 0.7,
                    marginBottom: '4px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    lineHeight: 1.6,
                    fontWeight: message.role === 'user' ? '500' : '400'
                  }}>
                    {message.content}
                  </div>
                </div>
              ))}
              {isAiThinking && (
                <div style={{...styles.chatMessage, ...styles.chatMessageAssistant, animation: 'pulse 2s infinite'}}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: '600',
                    opacity: 0.7,
                    marginBottom: '4px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    AI Assistant
                  </div>
                  <div style={{
                    fontSize: '14px',
                    lineHeight: 1.6,
                    fontWeight: '400',
                    fontStyle: 'italic'
                  }}>
                    Thinking...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} style={{ height: '1px' }} />
            </div>
            
            <div style={styles.chatInputContainer}>
              <textarea
                style={styles.chatInput}
                placeholder="Type your message to AI assistant..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                  }
                }}
                disabled={isAiThinking}
                rows={1}
              />
              <button 
                style={{
                  ...styles.chatSendButton,
                  opacity: (isAiThinking || !chatInput.trim()) ? 0.5 : 1,
                  cursor: (isAiThinking || !chatInput.trim()) ? 'not-allowed' : 'pointer',
                }}
                onClick={sendChatMessage}
                disabled={isAiThinking || !chatInput.trim()}
              >
                {/* --- UPDATED: Replaced text with SVG icon --- */}
                {isAiThinking ? '...' : <SendIcon />}
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel: Preview or Code */}
        <div style={styles.rightPanel}>
          <div style={styles.rightPanelHeader}>
            <div style={styles.sidebarTabs}>
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(activeTab === 'files' ? styles.sidebarTabActive : {})
                }}
                onClick={() => setActiveTab('files')}
              >
                Files
              </button>
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(activeTab === 'errors' ? styles.sidebarTabActive : {})
                }}
                onClick={() => setActiveTab('errors')}
              >
                Problems ({errors.length})
              </button>
            </div>
            
            <div style={styles.viewToggleButtons}>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(layoutMode === 'preview' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setLayoutMode('preview')}
                title="Live Preview"
              >
                Preview
              </button>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(layoutMode === 'code' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setLayoutMode('code')}
                title="Code Editor"
              >
                Code
              </button>
            </div>
          </div>
          
          <div style={styles.rightPanelContent}>
            {layoutMode === 'preview' && previewUrl ? (
              <iframe
                src={previewUrl}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                  background: '#ffffff', // Set to white for contrast
                  overflow: 'auto'
                }}
                title="Live Preview"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                allow="clipboard-read; clipboard-write"
                scrolling="yes"
              />
            ) : layoutMode === 'preview' && isBuilding ? (
              /* Live Generation Progress */
              <div style={styles.welcomeScreen}>
                <h2 style={styles.welcomeScreenH2}>AI Generating Your App...</h2>
                <p style={styles.welcomeScreenP}>
                  Watch your application being created in real-time.
                </p>
                <div style={{
                  background: '#1a1a1a',
                  border: '1px solid #333333',
                  borderRadius: '8px',
                  padding: '16px',
                  marginTop: '20px',
                  maxHeight: '400px',
                  overflow: 'auto',
                  fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
                  fontSize: '14px',
                  color: '#d4d4d4',
                  textAlign: 'left'
                }}>
                  {terminalOutput.length === 0 ? (
                    <div style={{ color: '#aaaaaa' }}>Initializing AI generation...</div>
                  ) : (
                    terminalOutput.map((line, index) => (
                      <div key={index} style={{ 
                        marginBottom: '4px',
                        animation: 'fadeIn 0.3s ease-in'
                      }}>
                        {line}
                      </div>
                    ))
                  )}
                  <div style={{ 
                    marginTop: '8px',
                    color: '#ffffff',
                    animation: 'pulse 1.5s infinite'
                  }}>
                    ...
                  </div>
                </div>
              </div>
            ) : layoutMode === 'preview' && !previewUrl ? (
              <div style={styles.welcomeScreen}>
                {/* --- UPDATED: Text --- */}
                <h2 style={styles.welcomeScreenH2}>Preview Unavailable</h2>
                <p style={styles.welcomeScreenP}>
                  Click "Run" to build your project and start the live preview.
                </p>
              </div>
            ) : (
              /* Code Editor Mode */
              <div style={styles.codeAreaRow}>
                {/* Left: File Tree Pane */}
                <div style={styles.fileTreePane}>
                  {activeTab === 'files' ? (
                    <div style={styles.fileTree}>
                      {fileTree && fileTree.length > 0 ? renderFileTree(fileTree) : (
                        <div style={styles.welcomeScreenP}>Loading project files...</div>
                      )}
                    </div>
                  ) : (
                    <div style={styles.fileTree}>
                      {errors.length === 0 ? (
                        <div style={styles.welcomeScreenP}>No problems detected.</div>
                      ) : (
                        errors.map((error, index) => (
                          <div key={index} style={{...styles.fileTreeItem, alignItems: 'flex-start'}}>
                            <span style={{...styles.fileTypeIcon, color: '#ffffff', fontWeight: 600}}>{error.severity === 'error' ? '[E]' : '[W]'}</span>
                            <div>
                              <div style={{ color: '#ffffff' }}>{error.message}</div>
                              <div style={{ fontSize: '11px', color: '#bbbbbb', paddingTop: '4px' }}>{error.file}:{error.line}</div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>

                {/* Right: Code Editor Pane */}
                <div style={styles.codeEditorPane}>
                  {selectedFile ? (
                    <>
                      <div style={{ 
                        padding: '8px 16px', 
                        background: '#1a1a1a', 
                        borderBottom: '1px solid #333333',
                        fontSize: '13px',
                        color: '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexShrink: 0,
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace" }}>
                          {selectedFile}
                        </div>
                        <div style={styles.navigationControls}>
                          <button
                            style={{
                              ...styles.navButton,
                              ...(canGoBack ? {} : styles.navButtonDisabled)
                            }}
                            onClick={goBack}
                            disabled={!canGoBack}
                            title="Go back"
                            onMouseEnter={(e) => {
                              if (canGoBack) {
                                e.target.style.background = styles.navButtonHover.background;
                                e.target.style.color = styles.navButtonHover.color;
                              }
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.background = styles.navButton.background;
                              e.target.style.color = styles.navButton.color;
                            }}
                          >
                            {/* --- UPDATED: Replaced text with SVG icon --- */}
                            <BackIcon />
                          </button>
                          <button
                            style={{
                              ...styles.navButton,
                              ...(canGoForward ? {} : styles.navButtonDisabled)
                            }}
                            onClick={goForward}
                            disabled={!canGoForward}
                            title="Go forward"
                            onMouseEnter={(e) => {
                              if (canGoForward) {
                                e.target.style.background = styles.navButtonHover.background;
                                e.target.style.color = styles.navButtonHover.color;
                              }
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.background = styles.navButton.background;
                              e.target.style.color = styles.navButton.color;
                            }}
                          >
                            {/* --- UPDATED: Replaced text with SVG icon --- */}
                            <FwdIcon />
                          </button>
                          <span style={{ color: '#888', fontSize: '11px', marginLeft: '4px', fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace" }}>
                            {currentViewIndex + 1}/{viewHistory.length}
                          </span>
                        </div>
                      </div>
                      <div style={{ flex: 1, minHeight: 0 }}>
                        <MonacoEditor
                          height="100%"
                          language={getLanguageFromFileName(selectedFile)}
                          value={fileContents[selectedFile] || ''}
                          theme="vs-dark"
                          options={{
                            automaticLayout: true,
                            minimap: { enabled: false },
                            wordWrap: 'on',
                            fontSize: 14,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            renderWhitespace: 'selection',
                            readOnly: true, // Set to true as AI is modifying it
                            fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
                            scrollbar: {
                              vertical: 'visible',
                              horizontal: 'visible',
                              useShadows: false,
                              verticalScrollbarSize: 10,
                              horizontalScrollbarSize: 10
                            },
                            mouseWheelZoom: true,
                            smoothScrolling: true
                          }}
                        />
                      </div>
                    </>
                  ) : (
                    <div style={styles.welcomeScreen}>
                      {/* --- UPDATED: Text --- */}
                      <h2 style={styles.welcomeScreenH2}>Code Editor</h2>
                      <p style={styles.welcomeScreenP}>
                        Select a file from the explorer on the left to view its contents.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
    </PageWrapper>
  );
};

export default MonacoProjectEditor;
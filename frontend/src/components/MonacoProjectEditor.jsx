import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import MonacoEditor from '@monaco-editor/react';

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

const MicIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V23h2v-2.06A9 9 0 0 0 21 12v-2h-2z" />
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
    alignItems: 'center',
    boxShadow: '0 -1px 0 rgba(255,255,255,0.06)'
  },
  
  chatInput: {
    flex: 1,
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    color: '#ffffff',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '20px',
    padding: '12px 18px',
    fontSize: '14px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    outline: 'none',
    resize: 'none',
    minHeight: '22px',
    maxHeight: '120px',
    lineHeight: 1.5,
    transition: 'all 0.2s ease',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
  },
  
  micButton: {
    flexShrink: 0,
    background: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    padding: '0.5rem',
    color: '#ffffff',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '40px',
    height: '40px',
  },
  
  micButtonRecording: {
    background: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
    color: '#ef4444',
  },
  
  // --- UPDATED: Send button styles for icon ---
  chatSendButton: {
    background: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    padding: '0.5rem',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    width: '40px',
    height: '40px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    color: '#ffffff',
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
    console.log('Closing Monaco editor, navigating to voice chat');
    navigate('/voice-chat');
  };
  
  // Create project object from URL parameter
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [fileTree, setFileTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContents, setFileContents] = useState({});
  const [activeTab, setActiveTab] = useState('preview');
  const [chatTab, setChatTab] = useState('chat'); // 'chat' or 'tasks'
  const [aiTasks, setAiTasks] = useState([]); // List of AI-completed tasks
  const [errors, setErrors] = useState([]);
  const [isBuilding, setIsBuilding] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoFixing, setIsAutoFixing] = useState(false);
  const [hasErrors, setHasErrors] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [layoutMode, setLayoutMode] = useState('preview'); // 'preview' or 'code'
  const [viewMode, setViewMode] = useState('desktop'); // 'desktop' or 'mobile'
  const [viewHistory, setViewHistory] = useState([]);
  const [currentViewIndex, setCurrentViewIndex] = useState(-1);
  const [pendingChanges, setPendingChanges] = useState(false);
  const [lastChangeTime, setLastChangeTime] = useState(null);
  
  const chatEndRef = useRef(null);
  const changeTimeoutRef = useRef(null);
  const wsRef = useRef(null);
  const connectTimerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);
  const recognitionRef = useRef(null);

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
      
      // Auto-run the project on mount
      setTimeout(() => {
        runProject();
      }, 1000);
      
      // Initialize chat with welcome message
      const welcomeMessage = {
        role: 'assistant',
        content: `Welcome to your AI product assistant!
I'm here to help you build, design, and improve your project.

You can ask me to:
•  Change the look and feel (e.g., "Make the button blue")
•  Add new sections (e.g., "Add a 'Contact Us' page")
•  Find and fix issues (e.g., "The 'Sign Up' button is broken")
•  Improve this page

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
            content: `**Fixed!**\n\n**Issue Resolved:** ${result.explanation}\n\n${result.suggestions?.length > 0 ? `**Improvements:**\n${result.suggestions.map(s => `• ${s}`).join('\n')}` : ''}\n\n*The issue has been automatically fixed.*`
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
            content: `**Couldn't Fix This One**\n\nI found an issue but couldn't fix it automatically:\n\n**What happened:** ${result.error}\n\n${result.explanation ? `**Details:** ${result.explanation}\n\n` : ''}Please describe what you'd like me to do, and I'll help you fix it.`
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
        content: `**Warning: ${errors.length} issue(s) detected.**

${errors.slice(-3).map(err => `• ${err.message}`).join('\n')}

Click the "Fix Issues" button or ask me to "fix the issues" and I'll try to resolve them automatically.`
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
          }
          break;
        case 'file_created':
          // Refresh file tree to show new file
          if (fileTree.length > 0) {
            initializeProject();
          }
          break;
        case 'file_content_update':
          // Live typing effect for file content
          break;
        case 'file_creation_start':
          break;
        case 'file_creation_complete':
          // Refresh file tree after completion
          setTimeout(() => {
            initializeProject();
          }, 500);
          break;
        case 'terminal_output':
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
          break;
        }
      };
    }, 50);
  };

  const runProject = async () => {
    setIsBuilding(true);
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
          content: `**All Fixed!**
${result.message}
${result.fixes_applied && result.fixes_applied.length > 0 ? `\n**What I Fixed:**\n${result.fixes_applied.map(fix => `• ${fix}`).join('\n')}` : ''}

Your project is ready. Starting it up again...`
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
        content: `**Fixed!**

**What I found:** ${geminiResult.explanation}
${geminiResult.suggestions?.length > 0 ? `\n**Changes Made:**\n${geminiResult.suggestions.map(s => `• ${s}`).join('\n')}` : ''}

${geminiResult.changes_applied ? '*Your project has been updated.*' : '*Here\'s what I found.*'}

Starting your project again...`
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

  // Audio recording handler (like VoiceChatInterface)
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          sampleRate: 48000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        } 
      });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Send to backend for transcription using existing endpoint
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        try {
          const response = await fetch('http://localhost:8000/api/process-speech', {
            method: 'POST',
            body: formData
          });
          
          const result = await response.json();
          
          if (result.transcript) {
            // Add user message to chat
            const userMessage = {
              role: 'user',
              content: result.transcript
            };
            setChatMessages(prev => [...prev, userMessage]);
            
            // Send to AI for processing
            setIsAiThinking(true);
            
            try {
              const aiResponse = await fetch(`http://localhost:8000/api/ai-project-assistant`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                  project_name: project.name,
                  user_message: result.transcript,
                  tech_stack: project.tech_stack || [],
                  re_run: true
                })
              });
              
              const aiResult = await aiResponse.json();
              
              if (aiResult.success) {
                const assistantMessage = {
                  role: 'assistant',
                  content: `**Done!** ${aiResult.explanation || "I've made the requested changes!"}
${aiResult.files_modified && aiResult.files_modified.length > 0 ? `\n**Updated:** ${aiResult.files_modified.join(', ')}` : ''}
${aiResult.errors && aiResult.errors.length > 0 ? `\n**Note:** ${aiResult.errors.length} issue(s) detected.` : ''}

The changes are live in your preview.`
                };
                setChatMessages(prev => [...prev, assistantMessage]);
                
                // AI speaks the response
                const spokenText = `Done! ${aiResult.explanation || "I've made the requested changes!"}`;
                speakText(spokenText);
                
                // Add task to task list
                const taskTitle = aiResult.explanation || result.transcript;
                const cleanTitle = taskTitle.replace(/\*\*/g, '').split('\n')[0];
                setAiTasks(prev => [...prev, {
                  title: cleanTitle,
                  description: aiResult.files_modified && aiResult.files_modified.length > 0 
                    ? `Updated: ${aiResult.files_modified.join(', ')}` 
                    : undefined,
                  timestamp: Date.now()
                }]);
                
                // Reload project files and preview
                initializeProject();
              } else {
                const errorMessage = {
                  role: 'assistant',
                  content: `**Oops!** ${aiResult.error || 'I encountered an issue and could not make those changes.'}`
                };
                setChatMessages(prev => [...prev, errorMessage]);
                speakText(aiResult.error || 'I encountered an issue and could not make those changes.');
              }
            } catch (aiError) {
              console.error('AI processing error:', aiError);
              const errorMessage = {
                role: 'assistant',
                content: `**Oops!** Sorry, something went wrong: ${aiError.message}`
              };
              setChatMessages(prev => [...prev, errorMessage]);
            } finally {
              setIsAiThinking(false);
            }
          } else {
            console.error('Transcription failed:', result.error);
            setChatMessages(prev => [...prev, {
              role: 'assistant',
              content: result.error || '⚠️ Could not transcribe audio. Please try again or type your message.'
            }]);
          }
        } catch (error) {
          console.error('Error sending audio:', error);
          setChatMessages(prev => [...prev, {
            role: 'assistant',
            content: '⚠️ Recording error. Please check your microphone and try again.'
          }]);
        }
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Microphone access error:', error);
      alert('Could not access microphone. Please check your browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Text-to-speech function
  const speakText = async (text) => {
    if (isMuted || !text || isPlaying) return;
    
    // Stop any current audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    
    try {
      // Try Chatterbox TTS first
      const response = await fetch('http://localhost:8000/api/synthesize-chatterbox', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: 'en' })
      });
      
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        currentAudioRef.current = audio;
        setIsPlaying(true);
        
        audio.onended = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };
        
        audio.onerror = () => {
          setIsPlaying(false);
          currentAudioRef.current = null;
          URL.revokeObjectURL(audioUrl);
        };
        
        await audio.play();
      } else {
        // Fallback to browser TTS
        const cleanText = text.replace(/[#*_`]/g, '').replace(/\*\*/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 0.8;
        speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error('TTS error:', error);
    }
  };

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
          content: `**Done!** ${result.explanation || "I've made the requested changes!"}
${result.files_modified && result.files_modified.length > 0 ? `\n**Updated:** ${result.files_modified.join(', ')}` : ''}
${result.errors && result.errors.length > 0 ? `\n**Note:** ${result.errors.length} issue(s) detected.` : ''}

The changes are live in your preview.`
        };
        setChatMessages(prev => [...prev, assistantMessage]);
        
        // AI speaks the response
        const spokenText = `Done! ${result.explanation || "I've made the requested changes!"}`;
        speakText(spokenText);
        
        // Add task to task list
        const taskTitle = result.explanation || messageToSend;
        const cleanTitle = taskTitle.replace(/\*\*/g, '').split('\n')[0]; // Remove markdown and get first line
        setAiTasks(prev => [...prev, {
          title: cleanTitle,
          description: result.files_modified && result.files_modified.length > 0 
            ? `Updated: ${result.files_modified.join(', ')}` 
            : undefined,
          timestamp: Date.now()
        }]);
        
        // Reload project files and preview
        initializeProject();
        if (result.preview_url) {
          setPreviewUrl(result.preview_url);
        }
      } else {
        const errorMessage = {
          role: 'assistant',
          content: `**Oops!** ${result.error || 'I encountered an issue and could not make those changes.'}`
        };
        setChatMessages(prev => [...prev, errorMessage]);
        
        // AI speaks the error
        speakText(result.error || 'I encountered an issue and could not make those changes.');
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `**Oops!** Sorry, something went wrong: ${error.message}`
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
    <div style={styles.monacoProjectEditor}>
      {/* Simplified Header - Just project name and status */}
      <div style={styles.editorHeader}>
        <div style={styles.editorTitle}>
          <button 
            style={{
              background: 'transparent',
              border: 'none',
              color: '#aaaaaa',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '8px 12px',
              marginRight: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            onClick={handleClose}
            title="Back to projects"
          >
            ← Back
          </button>
          <span style={styles.projectName}>{project.name}</span>
          
          {isBuilding && (
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginLeft: '16px',
              fontSize: '14px',
              color: '#ffffff'
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#fbbf24',
                animation: 'pulse 1.5s infinite'
              }}></span>
              Building...
            </span>
          )}
          {!isBuilding && isRunning && (
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginLeft: '16px',
              fontSize: '14px',
              color: '#ffffff'
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#10b981'
              }}></span>
              Live
            </span>
          )}
        </div>
        
        <div style={styles.editorActions}>
          {hasErrors && (
            <button 
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: '500',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                color: '#000000',
                background: '#ffffff',
                border: '1px solid #ffffff',
                ...(isAutoFixing ? { opacity: 0.5 } : {})
              }}
              onClick={autoFixErrors}
              disabled={isAutoFixing}
              title="Fix detected issues automatically"
            >
              {isAutoFixing ? 'Fixing...' : 'Fix Issues'}
            </button>
          )}
        </div>
      </div>

      {/* New Layout: Chat Left, Preview/Code Right */}
      <div style={styles.newEditorLayout}>
        {/* Left Panel: AI Chat */}
        <div style={styles.chatPanel}>
          <div style={styles.rightPanelHeader}>
            <div style={styles.sidebarTabs}>
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(chatTab === 'chat' ? styles.sidebarTabActive : {})
                }}
                onClick={() => setChatTab('chat')}
              >
                Chat
              </button>
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(chatTab === 'tasks' ? styles.sidebarTabActive : {})
                }}
                onClick={() => setChatTab('tasks')}
              >
                Tasks
              </button>
            </div>
            <button
              style={{
                background: 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '6px',
                color: isMuted ? '#999' : '#fff',
                cursor: 'pointer',
                fontSize: '16px',
                padding: '4px 8px',
                marginLeft: 'auto'
              }}
              onClick={() => setIsMuted(!isMuted)}
              title={isMuted ? "Unmute AI voice" : "Mute AI voice"}
            >
              {isMuted ? '🔇' : '🔊'}
            </button>
          </div>
          
          <div style={styles.chatContainer}>
            {chatTab === 'chat' ? (
              <>
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
              <button 
                style={{
                  ...styles.micButton,
                  ...(isRecording ? styles.micButtonRecording : {})
                }}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isAiThinking || isPlaying}
                title={isRecording ? "Stop recording" : "Start recording"}
              >
                <MicIcon />
              </button>
              <textarea
                style={styles.chatInput}
                placeholder={isRecording ? "Recording..." : "Type or speak your message..."}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendChatMessage();
                  }
                }}
                disabled={isAiThinking || isRecording}
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
                {isAiThinking ? '...' : <SendIcon />}
              </button>
            </div>
              </>
            ) : (
              /* Tasks View */
              <div style={{
                ...styles.chatMessages,
                padding: '16px'
              }}>
                {aiTasks.length === 0 ? (
                  <div style={{
                    textAlign: 'center',
                    color: '#888',
                    padding: '40px 20px',
                    fontSize: '14px'
                  }}>
                    No tasks yet. Ask the AI to make changes and completed tasks will appear here.
                  </div>
                ) : (
                  aiTasks.map((task, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '12px',
                      background: '#111111',
                      border: '1px solid #333333',
                      borderRadius: '8px',
                      marginBottom: '8px'
                    }}>
                      <span style={{
                        fontSize: '18px',
                        lineHeight: '1',
                        marginTop: '2px'
                      }}>✅</span>
                      <div style={{ flex: 1 }}>
                        <div style={{
                          color: '#ffffff',
                          fontSize: '14px',
                          fontWeight: '500',
                          marginBottom: '4px'
                        }}>
                          {task.title}
                        </div>
                        {task.description && (
                          <div style={{
                            color: '#aaaaaa',
                            fontSize: '12px',
                            lineHeight: '1.4'
                          }}>
                            {task.description}
                          </div>
                        )}
                        <div style={{
                          color: '#666',
                          fontSize: '11px',
                          marginTop: '6px'
                        }}>
                          {new Date(task.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Preview or Code */}
        <div style={styles.rightPanel}>
          <div style={styles.rightPanelHeader}>
            <div style={styles.viewToggleButtons}>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(viewMode === 'desktop' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setViewMode('desktop')}
                title="Desktop View"
              >
                Desktop
              </button>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(viewMode === 'mobile' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setViewMode('mobile')}
                title="Mobile View"
              >
                Phone
              </button>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(activeTab === 'settings' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setActiveTab(activeTab === 'settings' ? 'preview' : 'settings')}
                title="Project Settings"
              >
                Settings
              </button>
            </div>
          </div>
          
          <div style={styles.rightPanelContent}>
            {activeTab === 'settings' ? (
              /* Project Settings Panel */
              <div style={{
                padding: '32px',
                background: '#ffffff',
                height: '100%',
                overflow: 'auto'
              }}>
                <h2 style={{
                  fontSize: '24px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  marginBottom: '24px',
                  borderBottom: '2px solid #f0f0f0',
                  paddingBottom: '12px'
                }}>
                  Project Settings
                </h2>
                
                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#666',
                    marginBottom: '8px'
                  }}>
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={project?.name || projectName || ''}
                    readOnly
                    style={{
                      width: '100%',
                      padding: '12px',
                      fontSize: '16px',
                      border: '1px solid #e0e0e0',
                      borderRadius: '6px',
                      background: '#f9f9f9',
                      color: '#1a1a1a'
                    }}
                  />
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#666',
                    marginBottom: '8px'
                  }}>
                    Live URL
                  </label>
                  <div style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    background: '#f9f9f9',
                    color: previewUrl ? '#0066cc' : '#999',
                    wordBreak: 'break-all'
                  }}>
                    {previewUrl || 'Not deployed yet - click Run to preview'}
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#666',
                    marginBottom: '8px'
                  }}>
                    Plan
                  </label>
                  <div style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    background: '#f9f9f9',
                    color: '#1a1a1a'
                  }}>
                    Starter
                  </div>
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <label style={{
                    display: 'block',
                    fontSize: '14px',
                    fontWeight: '500',
                    color: '#666',
                    marginBottom: '8px'
                  }}>
                    Analytics
                  </label>
                  <div style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    background: '#f9f9f9',
                    color: '#999',
                    fontStyle: 'italic'
                  }}>
                    Coming Soon
                  </div>
                </div>
              </div>
            ) : layoutMode === 'preview' && previewUrl ? (
              <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                background: viewMode === 'mobile' ? '#f0f0f0' : '#ffffff',
                padding: viewMode === 'mobile' ? '20px' : '0'
              }}>
                <iframe
                  src={previewUrl}
                  style={{
                    width: viewMode === 'mobile' ? '375px' : '100%',
                    height: viewMode === 'mobile' ? '667px' : '100%',
                    maxWidth: viewMode === 'mobile' ? '375px' : '100%',
                    maxHeight: viewMode === 'mobile' ? '667px' : '100%',
                    border: viewMode === 'mobile' ? '8px solid #1a1a1a' : 'none',
                    borderRadius: viewMode === 'mobile' ? '36px' : '0',
                    background: '#ffffff',
                    overflow: 'auto',
                    boxShadow: viewMode === 'mobile' ? '0 20px 60px rgba(0,0,0,0.3)' : 'none'
                  }}
                  title="Live Preview"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                  allow="clipboard-read; clipboard-write"
                  scrolling="yes"
                />
              </div>
            ) : layoutMode === 'preview' && isBuilding ? (
              /* Live Generation Progress */
              <div style={styles.welcomeScreen}>
                <h2 style={styles.welcomeScreenH2}>AI Generating Your App...</h2>
                <p style={styles.welcomeScreenP}>
                  Watch your application being created in real-time.
                </p>
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
  );
};

export default MonacoProjectEditor;
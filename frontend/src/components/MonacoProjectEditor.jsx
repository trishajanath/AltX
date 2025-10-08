import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import MonacoEditor from '@monaco-editor/react';
import PageWrapper from './PageWrapper';

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

// Inline styles - simplified for new layout
const styles = {
  monacoProjectEditor: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: '#0b0b0b',
    color: '#ffffff',
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
  zIndex: 2000,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  
  // Header styles
  editorHeader: {
    background: '#111111',
    borderBottom: '1px solid #222222',
    padding: '8px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '48px'
  },
  editorTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: 600
  },
  projectIcon: {
    fontSize: '18px'
  },
  projectName: {
    color: '#ffffff',
    fontSize: '16px'
  },
  projectType: {
    color: '#ffffff',
    fontSize: '12px',
    background: 'rgba(255, 255, 255, 0.08)',
    padding: '2px 6px',
    borderRadius: '4px'
  },
  buildingIndicator: {
    color: '#ffffff',
    fontSize: '12px',
    marginLeft: '8px',
    animation: 'pulse 2s infinite'
  },
  editorActions: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center'
  },
  btnEditorAction: {
    background: '#1f1f23',
    color: '#ffffff',
    border: '1px solid #333333',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    transition: 'background 0.2s'
  },
  btnEditorActionPreview: {
    background: '#262626',
    border: '1px solid #2f6f4f'
  },
  btnEditorActionStop: {
    background: '#262626',
    border: '1px solid #6f2f2f'
  },
  btnEditorActionClose: {
    background: '#262626',
    border: '1px solid #6f2f2f'
  },
  
  // Navigation styles
  navigationControls: {
    display: 'flex',
    gap: '4px',
    alignItems: 'center',
    marginRight: '8px'
  },
  navButton: {
    background: '#1f1f23',
    color: '#ffffff',
    border: 'none',
    padding: '4px 8px',
    borderRadius: '3px',
    cursor: 'pointer',
    fontSize: '11px',
    transition: 'background 0.2s',
    minWidth: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  navButtonDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed'
  },
  navButtonHover: {
    background: '#2a2a2f'
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
    background: '#0f0f0f',
    borderRight: '1px solid #222222',
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
    background: '#0b0b0b',
    minHeight: 0
  },
  
  rightPanelHeader: {
    background: '#111111',
    borderBottom: '1px solid #222222',
    padding: '8px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '40px'
  },
  
  sidebarTabs: {
    display: 'flex',
    gap: '4px'
  },
  
  sidebarTab: {
    background: 'transparent',
    color: '#ffffff',
    border: 'none',
    padding: '6px 8px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '11px',
    transition: 'all 0.2s'
  },
  
  sidebarTabActive: {
    background: '#1a1a1a',
    color: '#ffffff',
    border: '1px solid #333333'
  },
  
  viewToggleButtons: {
    display: 'flex',
    gap: '4px'
  },
  
  viewToggleButton: {
    background: 'transparent',
    color: '#ffffff',
    border: '1px solid #222222',
    padding: '6px 12px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '12px',
    transition: 'all 0.2s'
  },
  
  viewToggleButtonActive: {
    background: '#1a1a1a',
    color: '#ffffff',
    border: '1px solid #333333'
  },
  
  rightPanelContent: {
    flex: 1,
    overflow: 'hidden',
    background: '#0b0b0b',
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
    padding: '16px',
    paddingBottom: '16px',
    gap: '16px',
    display: 'flex',
    flexDirection: 'column',
    scrollbarWidth: 'thin',
    scrollBehavior: 'smooth',
    maxHeight: '100%'
  },
  
  chatMessage: {
    maxWidth: '80%',
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    lineHeight: 1.4,
    whiteSpace: 'pre-wrap'
  },
  
  chatMessageUser: {
    background: '#1f1f23',
    color: '#ffffff',
    alignSelf: 'flex-end',
    marginLeft: 'auto'
  },
  
  chatMessageAssistant: {
    background: '#1a1a1a',
    color: '#ffffff',
    alignSelf: 'flex-start'
  },
  
  chatInputContainer: {
    padding: '16px',
    borderTop: '1px solid #222222',
    display: 'flex',
    gap: '8px',
    background: '#0f0f0f',
    height: '56px',
    alignItems: 'center',
    boxShadow: '0 -1px 0 rgba(255,255,255,0.06)'
  },
  
  chatInput: {
    flex: 1,
    background: '#111111',
    color: '#ffffff',
    border: '1px solid #333333',
    borderRadius: '4px',
    padding: '8px 12px',
    fontSize: '14px',
    outline: 'none',
    resize: 'none',
    lineHeight: 1.4
  },
  
  chatSendButton: {
    background: '#0e639c',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    padding: '8px 12px',
    cursor: 'pointer',
    fontSize: '14px'
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
    padding: '4px 8px',
    cursor: 'pointer',
    borderRadius: '4px',
    marginBottom: '2px',
    gap: '6px',
    color: '#ffffff'
  },
  
  fileTreeItemHover: {
    background: '#1a1a1a'
  },
  
  fileTreeItemSelected: {
    background: '#1f1f23',
    color: '#ffffff',
    border: '1px solid #333333'
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
    borderRight: '1px solid #222222',
    overflow: 'auto',
    background: '#0b0b0b'
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
    padding: '40px'
  },
  
  welcomeScreenH2: {
    color: '#ffffff',
    marginBottom: '16px',
    fontSize: '24px'
  },
  
  welcomeScreenP: {
    color: '#ffffff',
    marginBottom: '12px',
    lineHeight: 1.5
  }
};

const MonacoProjectEditor = () => {
  const { projectName } = useParams();
  const navigate = useNavigate();
  
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
        content: `👋 Welcome to your AI coding assistant! I'm here to help you build amazing apps.

I can help you:
• Add new features to your app
• Fix bugs and errors
• Improve styling and design
• Optimize performance
• Explain code functionality

Just tell me what you'd like to do with your project!`
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
        /Warning.*Invalid JSX/i
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
      if (errorQueue.length === 0 || isProcessingErrors) return;
      
      isProcessingErrors = true;
      
      try {
        // Get the most recent error
        const latestError = errorQueue[errorQueue.length - 1];
        console.log('🔧 Processing console error for auto-fix:', latestError.message);
        
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
          console.log('✅ Auto-fix applied successfully:', result.explanation);
          
          // Show success message in chat
          const successMessage = {
            role: 'assistant',
            content: `🔧 **Auto-Fix Applied!**\n\n**Issue Fixed:** ${result.explanation}\n\n${result.suggestions?.length > 0 ? `**Additional Suggestions:**\n${result.suggestions.map(s => `• ${s}`).join('\n')}` : ''}\n\n*The error has been automatically resolved using Gemini AI.*`
          };
          
          setChatMessages(prev => [...prev, successMessage]);
          
          // Trigger reload if changes were applied
          if (result.changes_applied) {
            setTimeout(() => {
              refreshPreview();
            }, 1000);
          }
        } else {
          console.log('❌ Auto-fix failed:', result.error);
          
          // Show error message in chat
          const errorMessage = {
            role: 'assistant',
            content: `⚠️ **Auto-Fix Issue**\n\nI detected an error but couldn't fix it automatically:\n\n**Error:** ${result.error}\n\n${result.explanation ? `**Analysis:** ${result.explanation}\n\n` : ''}Please check the console for more details or ask me for help manually.`
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
    
    // Function to refresh preview
    const refreshPreview = () => {
      if (previewUrl) {
        const iframe = document.querySelector('iframe[src*="localhost"]');
        if (iframe) {
          // Get the base URL and add fresh timestamp
          const baseUrl = iframe.src.split('?')[0];
          iframe.src = `${baseUrl}?_refresh=${Date.now()}`;
        }
      }
    };
    
    // Install error interceptors
    console.error = errorInterceptor;
    console.warn = warnInterceptor;
    
    // Listen for unhandled errors
    const handleError = (event) => {
      if (shouldProcessError(event.message || event.error?.message || '')) {
        queueErrorForProcessing(event.message || event.error?.message || 'Unknown error');
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
      console.log('🔄 Preview reloaded due to file changes');
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
          console.log('� File content changes detected');
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
        content: `⚠️ I detected ${errors.length} error(s) in your project:

${errors.slice(-3).map(err => `• ${err.message}`).join('\n')}

💡 I can automatically fix common issues! Click the "Auto-Fix" button in the toolbar above, or just ask me to "fix the errors" and I'll take care of it for you.`
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
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'preview_ready':
          setPreviewUrl(data.url);
          setIsBuilding(false);
          setIsRunning(true);
          setTerminalOutput(prev => [...prev, `🌐 Live preview ready!`]);
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
            setTerminalOutput(prev => [...prev, `🤖 ${data.message}`]);
          } else if (data.phase === 'frontend') {
            setTerminalOutput(prev => [...prev, `🎨 ${data.message}`]);
          } else if (data.phase === 'backend') {
            setTerminalOutput(prev => [...prev, `⚡ ${data.message}`]);
          } else if (data.phase === 'config') {
            setTerminalOutput(prev => [...prev, `📄 ${data.message}`]);
          }
          break;
        case 'file_created':
          // Show live file creation
          setTerminalOutput(prev => [...prev, `📄 Created ${data.file_path}`]);
          // Refresh file tree to show new file
          if (fileTree.length > 0) {
            initializeProject();
          }
          break;
        case 'file_content_update':
          // Show live typing effect for file content
          setTerminalOutput(prev => [...prev, `✍️ Writing ${data.file_path}...`]);
          break;
        case 'file_creation_start':
          setTerminalOutput(prev => [...prev, `🚀 ${data.message}`]);
          break;
        case 'file_creation_complete':
          setTerminalOutput(prev => [...prev, `✅ ${data.message}`]);
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
          setTerminalOutput(prev => [...prev, `❌ ${data.message}`]);
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
          content: `🔧 Auto-fix completed! ${result.message}

${result.fixes_applied && result.fixes_applied.length > 0 ? `Fixes applied:
${result.fixes_applied.map(fix => `• ${fix}`).join('\n')}` : ''}

Your project has been automatically repaired. Try running it again!`
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
            content: `❌ Both auto-fix methods failed:
            
**Traditional Fix Error:** ${error.message}
**Gemini AI Fix Error:** ${geminiError.message}

Please try manually describing the issue in the chat for personalized assistance.`
          };
          setChatMessages(prev => [...prev, errorMessage]);
        }
      }
      
      if (!fixAttempted) {
        const errorMessage = {
          role: 'assistant',
          content: `❌ Failed to auto-fix errors: ${error.message}`
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
        content: `🤖 **Gemini AI Auto-Fix Applied!**

**Analysis:** ${geminiResult.explanation}

${geminiResult.suggestions?.length > 0 ? `**Improvements Made:**
${geminiResult.suggestions.map(s => `• ${s}`).join('\n')}` : ''}

${geminiResult.changes_applied ? '*Files have been automatically updated.*' : '*Analysis completed - please review the suggested changes.*'}

Try running your project again!`
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
        content: `🔧 I'll help you fix those errors! Let me run the auto-fix tool for you.`
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
          content: `✅ ${result.explanation || "I've made the requested changes to your project!"}

${result.files_modified && result.files_modified.length > 0 ? `Modified files: ${result.files_modified.join(', ')}` : ''}

${result.errors && result.errors.length > 0 ? `\n⚠️ Note: ${result.errors.length} issue(s) detected that may need attention.` : ''}

The changes have been applied and your preview has been updated.`
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
          content: `❌ Sorry, I couldn't make those changes: ${result.error || 'Unknown error'}`
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ Sorry, there was an error processing your request: ${error.message}`
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAiThinking(false);
    }
  };

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
          <span>{item.type === 'dir' ? '📁' : '📄'}</span>
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
            <span style={styles.projectIcon}>⏳</span>
            <span style={styles.projectName}>Loading project...</span>
          </div>
        </div>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          flex: 1,
          fontSize: '18px',
          color: '#666'
        }}>
          🚀 Initializing {projectName}...
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
              background: 'none',
              border: 'none',
              color: '#ffffff',
              fontSize: '18px',
              cursor: 'pointer',
              marginRight: '12px',
              padding: '4px',
              borderRadius: '4px',
            }}
            onClick={handleClose}
            title="Back to Home"
          >
            ≡
          </button>
          <span style={styles.projectIcon}>🚀</span>
          <span style={styles.projectName}>{project.name}</span>
          <span style={styles.projectType}>({project.tech_stack?.join(', ') || 'Mixed'})</span>
          {isBuilding && <span style={styles.buildingIndicator}>⚡ Building...</span>}
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
            {isBuilding ? '⚡' : isRunning ? '⏳' : '▶️'} 
            {isBuilding ? 'Building' : 'Run'}
          </button>
          
          {hasErrors && (
            <button 
              style={{
                ...styles.btnEditorAction,
                backgroundColor: '#ff6b35',
                ...(isAutoFixing ? { opacity: 0.5 } : {})
              }}
              onClick={autoFixErrors}
              disabled={isAutoFixing}
              title="Auto-fix detected errors"
            >
              {isAutoFixing ? '🔧' : '🛠️'} 
              {isAutoFixing ? 'Fixing...' : 'Auto-Fix'}
            </button>
          )}
          
          {previewUrl && (
            <button 
              style={{
                ...styles.btnEditorAction,
                ...(pendingChanges ? { 
                  backgroundColor: '#f59e0b', 
                  color: 'white',
                  boxShadow: '0 0 10px rgba(245, 158, 11, 0.5)'
                } : { backgroundColor: '#28a745' })
              }}
              onClick={() => {
                refreshPreview();
                setPendingChanges(false);
                if (changeTimeoutRef.current) {
                  clearTimeout(changeTimeoutRef.current);
                }
                setChatMessages(prev => [...prev, {
                  role: 'assistant',
                  content: '🔄 **Preview Refreshed!**\n\nThe preview has been manually reloaded with the latest changes.'
                }]);
              }}
              title={pendingChanges ? "File changes detected - Click to refresh now" : "Refresh Preview"}
            >
              {pendingChanges ? '🟠 Changes Detected' : '🔄 Refresh'}
            </button>
          )}
          
          {previewUrl && (
            <button 
              style={{...styles.btnEditorAction, ...styles.btnEditorActionPreview}}
              onClick={() => window.open(previewUrl, '_blank')}
              title="Open in New Tab"
            >
              🔗 Open
            </button>
          )}
          
          <button 
            style={{...styles.btnEditorAction, ...styles.btnEditorActionClose}}
            onClick={handleClose}
            title="Close Editor"
          >
            ✕
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
                🤖 AI Assistant
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
                  {message.content}
                </div>
              ))}
              {isAiThinking && (
                <div style={{...styles.chatMessage, ...styles.chatMessageAssistant}}>
                  🤔 Thinking...
                </div>
              )}
              <div ref={chatEndRef} style={{ height: '1px' }} />
            </div>
            
            <div style={styles.chatInputContainer}>
              <textarea
                style={styles.chatInput}
                placeholder="Ask AI to modify your code..."
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
                style={styles.chatSendButton}
                onClick={sendChatMessage}
                disabled={isAiThinking || !chatInput.trim()}
              >
                {isAiThinking ? '⏳' : '↗️'}
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
                📁 Files
              </button>
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(activeTab === 'errors' ? styles.sidebarTabActive : {})
                }}
                onClick={() => setActiveTab('errors')}
              >
                ⚠️ Problems ({errors.length})
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
                🌐 Preview
              </button>
              <button 
                style={{
                  ...styles.viewToggleButton,
                  ...(layoutMode === 'code' ? styles.viewToggleButtonActive : {})
                }}
                onClick={() => setLayoutMode('code')}
                title="Code Editor"
              >
                📝 Code
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
                  background: '#000000',
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
                <h2 style={styles.welcomeScreenH2}>🤖 AI Generating Your App</h2>
                <p style={styles.welcomeScreenP}>
                  Watch your React + FastAPI application being created in real-time
                </p>
                <div style={{
                  background: '#1e1e1e',
                  border: '1px solid #3e3e42',
                  borderRadius: '8px',
                  padding: '16px',
                  marginTop: '20px',
                  maxHeight: '400px',
                  overflow: 'auto',
                  fontFamily: 'Consolas, Monaco, monospace',
                  fontSize: '14px',
                  color: '#d4d4d4',
                  textAlign: 'left'
                }}>
                  {terminalOutput.length === 0 ? (
                    <div style={{ color: '#ffcc02' }}>⚡ Initializing AI generation...</div>
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
                    color: '#007acc',
                    animation: 'pulse 1.5s infinite'
                  }}>
                    ▊
                  </div>
                </div>
              </div>
            ) : layoutMode === 'preview' && !previewUrl ? (
              <div style={styles.welcomeScreen}>
                <h2 style={styles.welcomeScreenH2}>No Preview Available</h2>
                <p style={styles.welcomeScreenP}>
                  Click "Run" to start your project and see the live preview.
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
                        <div style={styles.welcomeScreenP}>✅ No problems detected</div>
                      ) : (
                        errors.map((error, index) => (
                          <div key={index} style={styles.fileTreeItem}>
                            <span>{error.severity === 'error' ? '❌' : '⚠️'}</span>
                            <div>
                              <div style={{ color: '#ffffff' }}>{error.message}</div>
                              <div style={{ fontSize: '11px', color: '#bbbbbb' }}>{error.file}:{error.line}</div>
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
                        background: '#2d2d30', 
                        borderBottom: '1px solid #3e3e42',
                        fontSize: '12px',
                        color: '#ffffff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        position: 'sticky',
                        top: 0,
                        zIndex: 2
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          📄 {selectedFile}
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
                              }
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.background = styles.navButton.background;
                            }}
                          >
                            ←
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
                              }
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.background = styles.navButton.background;
                            }}
                          >
                            →
                          </button>
                          <span style={{ color: '#888', fontSize: '10px', marginLeft: '4px' }}>
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
                            readOnly: true,
                            scrollbar: {
                              vertical: 'visible',
                              horizontal: 'visible',
                              useShadows: false,
                              verticalHasArrows: true,
                              horizontalHasArrows: true,
                              arrowSize: 11,
                              verticalScrollbarSize: 14,
                              horizontalScrollbarSize: 14
                            },
                            mouseWheelZoom: true,
                            smoothScrolling: true
                          }}
                        />
                      </div>
                    </>
                  ) : (
                    <div style={styles.welcomeScreen}>
                      <h2 style={styles.welcomeScreenH2}>Select a file to view</h2>
                      <p style={styles.welcomeScreenP}>
                        Choose a file from the file tree to view its contents.
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

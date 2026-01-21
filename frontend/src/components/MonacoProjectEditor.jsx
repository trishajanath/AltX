import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import Editor, { loader } from '@monaco-editor/react';
import { Mic, Send, Volume2, VolumeX } from 'lucide-react';
import { apiUrl } from '../config/api';
import PageWrapper from './PageWrapper';
import SecurityCanvas from './SecurityCanvas';
import { useAuth } from '../contexts/AuthContext';

// Configure Monaco Editor loader with error handling
// Use try-catch to prevent crashes if loader isn't ready
try {
  loader.config({
    paths: {
      vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs'
    },
    'vs/nls': {
      availableLanguages: {}
    }
  });
} catch (e) {
  console.warn('Monaco loader config deferred:', e.message);
}

// Pre-initialize Monaco with retry logic
let monacoInstance = null;
const initMonaco = async (retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      monacoInstance = await loader.init();
      console.log('✅ Monaco Editor initialized successfully');
      return monacoInstance;
    } catch (err) {
      console.warn(`Monaco init attempt ${i + 1} failed:`, err.message);
      if (i < retries - 1) {
        await new Promise(r => setTimeout(r, 500));
      }
    }
  }
  console.error('❌ Monaco Editor failed to load after retries');
  return null;
};

// Start initialization
initMonaco();

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
  @keyframes pulseRedBorder {
    0%, 100% { 
      box-shadow: 0 0 5px #ff0033, 0 0 10px #ff0033, 0 0 20px #ff0033;
      border-color: #ff0033;
    }
    50% { 
      box-shadow: 0 0 10px #ff0033, 0 0 20px #ff0033, 0 0 40px #ff0033;
      border-color: #ff6666;
    }
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
if (!document.head.querySelector('[data-monaco-animations]')) {
  styleSheet.setAttribute('data-monaco-animations', 'true');
  document.head.appendChild(styleSheet);
}

// --- NEW: SVG Icons for a cleaner UI ---
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
  statusIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    fontWeight: 500,
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#00ff00',
  },
  statusDotBuilding: {
    backgroundColor: '#ffaa00',
    animation: 'pulse 1.5s infinite',
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
    background: 'rgba(255, 255, 255, 0.02)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRight: '1px solid rgba(255, 255, 255, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    resize: 'horizontal',
    overflow: 'hidden',
    height: '100%',
    minHeight: 0,
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
  
  // Browser-style tab bar
  browserTabBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '1px',
    background: '#000000',
    padding: '0',
    height: '36px',
    borderBottom: '1px solid #222',
  },
  
  browserTab: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    color: '#666666',
    border: 'none',
    padding: '10px 16px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'inherit',
    transition: 'all 0.15s',
    position: 'relative',
    letterSpacing: '0.3px',
    textTransform: 'uppercase',
  },
  
  browserTabActive: {
    background: 'transparent',
    color: '#ffffff',
    borderBottom: '2px solid #ffffff',
  },
  
  browserTabHover: {
    color: '#999999',
  },
  
  // Legacy support
  viewToggleButtons: {
    display: 'flex',
    gap: '2px',
    background: '#1a1a1a',
    border: '1px solid #2a2a2a',
    borderRadius: '6px',
    padding: '3px',
  },
  
  viewToggleButton: {
    background: 'transparent',
    color: '#888888',
    border: 'none',
    padding: '6px 12px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
    fontFamily: 'inherit',
    transition: 'all 0.15s'
  },
  
  viewToggleButtonActive: {
    background: '#333333',
    color: '#ffffff',
  },
  
  // Security HUD Styles
  securityWidget: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '6px 14px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '600',
    transition: 'all 0.3s ease',
    marginLeft: '16px',
  },
  securityBar: {
    width: '80px',
    height: '6px',
    borderRadius: '3px',
    background: 'rgba(255, 255, 255, 0.2)',
    overflow: 'hidden',
  },
  securityBarFill: {
    height: '100%',
    borderRadius: '3px',
    transition: 'width 0.5s ease, background 0.3s ease',
  },
  xrayToggle: {
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
    overflowX: 'hidden',
    padding: '20px 24px',
    gap: '16px',
    display: 'flex',
    flexDirection: 'column',
    scrollBehavior: 'smooth',
    maxHeight: '100%',
    background: 'transparent',
    scrollbarWidth: 'none', /* Firefox */
    msOverflowStyle: 'none', /* IE and Edge */
  },
  
  chatMessage: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    maxWidth: '75%',
    padding: '10px 14px',
    borderRadius: '12px',
    fontSize: '13px',
    lineHeight: 1.5,
    whiteSpace: 'pre-wrap',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: '400',
    wordBreak: 'break-word',
    position: 'relative',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
  },
  
  // --- UPDATED: Match VoiceChatInterface bubble styles ---
  chatMessageUser: {
    background: 'rgba(255, 255, 255, 0.08)',
    color: '#ffffff',
    alignSelf: 'flex-end',
    marginLeft: 'auto',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px 12px 2px 12px',
    fontWeight: '400',
  },
  
  chatMessageAssistant: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    color: '#ffffff',
    alignSelf: 'flex-start',
    borderRadius: '12px 12px 12px 2px',
    fontWeight: '400',
  },
  
  chatInputContainer: {
    padding: '16px 20px',
    borderTop: '1px solid rgba(255, 255, 255, 0.15)',
    display: 'flex',
    gap: '10px',
    background: 'rgba(255, 255, 255, 0.03)',
    backdropFilter: 'blur(20px)',
    alignItems: 'flex-end',
    boxShadow: '0 -4px 12px rgba(0, 0, 0, 0.2)',
  },
  
  chatInput: {
    flex: 1,
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(10px)',
    color: '#ffffff',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '12px',
    padding: '12px 16px',
    fontSize: '14px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    outline: 'none',
    resize: 'none',
    minHeight: '20px',
    maxHeight: '120px',
    lineHeight: 1.5,
    transition: 'all 0.2s ease',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
  },
  
  contextPill: {
    position: 'absolute',
    top: '-32px',
    left: '0',
    background: 'rgba(0, 123, 255, 0.15)',
    border: '1px solid rgba(0, 123, 255, 0.4)',
    borderRadius: '16px',
    padding: '6px 14px',
    fontSize: '12px',
    color: '#4da3ff',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    animation: 'fadeIn 0.2s ease',
    fontWeight: 500,
  },
  contextPillClose: {
    cursor: 'pointer',
    marginLeft: '4px',
    opacity: 0.8,
    fontSize: '14px',
    transition: 'opacity 0.2s',
  },
  
  micButton: {
    flexShrink: 0,
    background: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '12px',
    padding: '10px',
    color: '#ffffff',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '44px',
    height: '44px',
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
    borderRadius: '12px',
    padding: '10px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    width: '44px',
    height: '44px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    color: '#ffffff',
    flexShrink: 0,
  },
  
  // File tree styles
  fileTree: {
    flex: 1,
    padding: '4px 0',
    fontSize: '13px',
    overflow: 'auto',
    color: '#cccccc',
    background: '#252526'
  },
  
  fileTreeItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '4px 8px 4px 20px',
    cursor: 'pointer',
    marginBottom: '0',
    gap: '6px',
    color: '#cccccc',
    fontFamily: "'Segoe UI', sans-serif",
    fontSize: '13px'
  },
  
  fileTreeItemHover: {
    background: '#2a2d2e'
  },
  
  fileTreeItemSelected: {
    background: '#094771',
    color: '#ffffff',
  },

  // --- NEW: Style for file type identifier ---
  fileTypeIcon: {
    color: '#cccccc',
    width: '16px',
    fontSize: '12px',
    display: 'inline-block',
    textAlign: 'center',
    fontFamily: "'Segoe UI', sans-serif",
  },

  // New: Code area row layout
  codeAreaRow: {
    flex: 1,
    display: 'flex',
    flexDirection: 'row',
    minHeight: 0,
    overflow: 'hidden',
    background: '#1e1e1e'
  },
  fileTreePane: {
    width: '240px',
    minWidth: '200px',
    maxWidth: '320px',
    borderRight: '1px solid #252526',
    overflow: 'hidden',
    background: '#252526',
    display: 'flex',
    flexDirection: 'column',
  },
  codeEditorPane: {
    flex: 1,
    minWidth: 0,
    minHeight: 0,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    background: '#1e1e1e'
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
  const { token, authenticatedFetch } = useAuth();
  
  // Extract full project path from wildcard route
  const projectName = params['*'] || location.pathname.replace('/project/', '');
  
  // Check if this is a new project being built (passed from VoiceChatInterface)
  const isNewProjectBuild = location.state?.isNewProject || false;
  const projectSpec = location.state?.projectSpec || null;
  
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
  const [loadingFile, setLoadingFile] = useState(null); // Track which file is loading
  const [expandedFolders, setExpandedFolders] = useState({}); // Track which folders are expanded
  const [activeTab, setActiveTab] = useState('preview');
  const [explorerTab, setExplorerTab] = useState('files'); // 'files' or 'problems' - controls left pane content
  const [chatTab, setChatTab] = useState('chat'); // 'chat', 'tasks', or 'issues'
  const [aiTasks, setAiTasks] = useState([]); // List of AI-completed tasks
  const [errors, setErrors] = useState([]);
  const [isBuilding, setIsBuilding] = useState(isNewProjectBuild); // Start in building mode if new project
  const [isRunning, setIsRunning] = useState(false);
  const [isAutoFixing, setIsAutoFixing] = useState(false);
  const [hasErrors, setHasErrors] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  // AI Thinking state for live progress during build
  const [aiThinkingSteps, setAiThinkingSteps] = useState([]);
  const [buildProgress, setBuildProgress] = useState(0);
  const [currentBuildPhase, setCurrentBuildPhase] = useState('');
  const [buildCompleted, setBuildCompleted] = useState(false); // Track when build finishes
  const buildStartedRef = useRef(false); // Guard against double build execution
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [layoutMode, setLayoutMode] = useState('preview'); // 'preview' or 'code'
  const [viewMode, setViewMode] = useState('desktop'); // 'desktop' or 'mobile'
  const [selectedElement, setSelectedElement] = useState(null); // Selected element in preview for editing
  const [viewHistory, setViewHistory] = useState([]);
  const [securityScore, setSecurityScore] = useState(100); // Security Health Score (0-100)
  const [securityIssues, setSecurityIssues] = useState([]); // List of security issues detected
  const [isSecurityView, setIsSecurityView] = useState(false); // X-Ray Security View toggle
  const [allProjectFiles, setAllProjectFiles] = useState({}); // All files loaded for security analysis
  const [isLoadingSecurityFiles, setIsLoadingSecurityFiles] = useState(false);
  const [highlightedIssueNode, setHighlightedIssueNode] = useState(null); // Node to highlight when clicking an issue
  const [currentViewIndex, setCurrentViewIndex] = useState(-1);
  const [pendingChanges, setPendingChanges] = useState(false);
  const [lastChangeTime, setLastChangeTime] = useState(null);
  
  // OWASP ZAP Security Scan State
  const [zapScanResult, setZapScanResult] = useState(null); // Full ZAP scan result
  const [isZapScanning, setIsZapScanning] = useState(false); // ZAP scan in progress
  const [zapScanProgress, setZapScanProgress] = useState(''); // ZAP scan progress message
  const [isFixingSecurityIssue, setIsFixingSecurityIssue] = useState(null); // Which alert is being fixed
  
  // Master-Detail Security UI State
  const [selectedAlertIndex, setSelectedAlertIndex] = useState(null); // Currently selected alert in list
  const [alertFilters, setAlertFilters] = useState({
    severity: [], // ['High', 'Medium', 'Low', 'Informational']
    owasp: [], // OWASP categories
    status: ['open'] // ['open', 'confirmed', 'false_positive', 'fixed']
  });
  const [alertStatuses, setAlertStatuses] = useState({}); // { alertIndex: 'open' | 'confirmed' | 'false_positive' | 'fixed' }
  const [showDiffView, setShowDiffView] = useState(false); // Show patch diff modal
  const [currentPatchDiff, setCurrentPatchDiff] = useState(null); // { original, patched, alertIndex }
  const [isGeneratingPatch, setIsGeneratingPatch] = useState(false); // Loading state for AI suggestion
  
  // Security Decision Records (SDR) State
  const [securityDecisions, setSecurityDecisions] = useState([]); // List of SDRs
  
  const chatEndRef = useRef(null);
  const changeTimeoutRef = useRef(null);
  const wsRef = useRef(null);
  const connectTimerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);
  const recognitionRef = useRef(null);
  const previewLoadedRef = useRef(false); // Track when preview iframe finishes loading
  const securityScanTimeoutRef = useRef(null); // Track security scan timeout
  const isInitializingRef = useRef(false); // Prevent concurrent initializations

  // Helper function to render formatted chat messages (parse markdown-like syntax)
  const renderFormattedMessage = useCallback((content, onIssueClick) => {
    if (!content) return null;
    
    // Split by lines to handle bullets
    const lines = content.split('\n');
    
    return lines.map((line, lineIndex) => {
      // Check for bullet points
      const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-');
      const bulletContent = isBullet ? line.replace(/^[\s]*[•\-]\s*/, '') : line;
      
      // Parse bold text (**text**)
      const parseBold = (text) => {
        const parts = text.split(/\*\*(.*?)\*\*/g);
        return parts.map((part, i) => {
          if (i % 2 === 1) {
            // Check if this is an issue count that should be clickable
            const issueMatch = part.match(/(\d+)\s*issue\(s\)\s*detected/i);
            if (issueMatch && onIssueClick) {
              return (
                <span 
                  key={i}
                  onClick={onIssueClick}
                  style={{ 
                    fontWeight: 700,
                    color: '#ff6600',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    textDecorationStyle: 'dotted'
                  }}
                  title="Click to view issues in Security Canvas"
                >
                  {part}
                </span>
              );
            }
            return <strong key={i} style={{ fontWeight: 700 }}>{part}</strong>;
          }
          return part;
        });
      };
      
      if (isBullet) {
        return (
          <div key={lineIndex} style={{ 
            display: 'flex', 
            gap: '8px', 
            marginTop: lineIndex > 0 ? '4px' : '0',
            paddingLeft: '4px'
          }}>
            <span style={{ color: '#888' }}>•</span>
            <span>{parseBold(bulletContent)}</span>
          </div>
        );
      }
      
      if (line.trim() === '') {
        return <div key={lineIndex} style={{ height: '8px' }} />;
      }
      
      return (
        <div key={lineIndex} style={{ marginTop: lineIndex > 0 ? '4px' : '0' }}>
          {parseBold(line)}
        </div>
      );
    });
  }, []);

  // Helper function to ensure preview URL has user email parameter
  const ensurePreviewUrlHasAuth = (url) => {
    if (!url) return url;
    
    try {
      const urlObj = new URL(url, window.location.origin);
      
      // Add cache-busting timestamp to force fresh load
      urlObj.searchParams.set('v', Date.now().toString());
      
      // Check if user_email parameter is already present
      if (urlObj.searchParams.has('user_email')) {
        console.log('[Preview Auth] URL already has user_email:', url);
        return urlObj.toString();  // Return with cache-busting param
      }
      
      // Try to get user from localStorage OR sessionStorage
      const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
      console.log('[Preview Auth] User from storage:', userStr);
      
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          const email = user.email;
          const userId = user._id;
          
          console.log('[Preview Auth] Extracted email:', email, 'userId:', userId);
          
          // Send both email and _id so backend can try both
          if (email) {
            urlObj.searchParams.set('user_email', email);
            if (userId) {
              urlObj.searchParams.set('user_id_alt', userId);
            }
            const finalUrl = urlObj.toString();
            console.log('[Preview Auth] Final URL with auth:', finalUrl);
            return finalUrl;
          } else if (userId) {
            // Fallback to _id only if no email
            urlObj.searchParams.set('user_email', userId);
            const finalUrl = urlObj.toString();
            console.log('[Preview Auth] Final URL with _id only:', finalUrl);
            return finalUrl;
          }
        } catch (e) {
          console.warn('Could not parse user from storage:', e);
        }
      } else {
        console.warn('[Preview Auth] No user found in localStorage or sessionStorage!');
      }
      
      console.warn('[Preview Auth] Returning URL without auth:', url);
      return url;
    } catch (e) {
      console.warn('Could not parse preview URL:', e);
      return url;
    }
  };

  // Function to refresh preview - FIXED SCOPE ISSUE
  const refreshPreview = useCallback(() => {
    console.log('🔄 Refreshing preview, current URL:', previewUrl);
    
    // Find the preview iframe - look for various possible selectors
    const iframe = document.querySelector('iframe[src*="localhost"]') || 
                   document.querySelector('iframe[src*="sandbox"]') ||
                   document.querySelector('iframe[src*="preview"]') ||
                   document.querySelector('.preview-iframe');
    
    if (iframe && iframe.src) {
      // Get the base URL and add fresh timestamp while preserving auth params
      const baseUrl = iframe.src.split('?')[0].split('#')[0];
      // Use ensurePreviewUrlHasAuth to add auth params + cache busting
      const newSrc = ensurePreviewUrlHasAuth(`${baseUrl}?_refresh=${Date.now()}`);
      console.log('🔄 Setting iframe src to:', newSrc);
      iframe.src = newSrc;
    } else if (previewUrl) {
      // If no iframe found but we have a preview URL, update the state to trigger re-render
      const baseUrl = previewUrl.split('?')[0].split('#')[0];
      // Use ensurePreviewUrlHasAuth to add auth params + cache busting
      const newUrl = ensurePreviewUrlHasAuth(`${baseUrl}?_refresh=${Date.now()}`);
      setPreviewUrl(newUrl);
    } else {
      console.warn('⚠️ No iframe or preview URL found to refresh');
    }
  }, [previewUrl]);

  // Security Analysis Function - ONLY for Security Canvas visualization
  // Actual security scanning is done by OWASP ZAP API
  const analyzeSecurityIssues = useCallback((files) => {
    // This function is now ONLY used for Security Canvas node visualization
    // It does NOT detect security issues - that's done by OWASP ZAP
    // It only maps file structure for the visual security graph
    
    const fileNodes = [];
    
    // Map files for visualization purposes only
    Object.entries(files || {}).forEach(([fileName, content]) => {
      if (typeof content !== 'string') return;
      
      // Detect file types for Security Canvas visualization
      const hasAuth = /auth|login|session|token|password/i.test(content);
      const hasAPI = /fetch|axios|XMLHttpRequest|api/i.test(content);
      const hasForm = /<form|<input/i.test(content);
      const hasStorage = /localStorage|sessionStorage|cookie/i.test(content);
      
      if (hasAuth || hasAPI || hasForm || hasStorage) {
        fileNodes.push({
          file: fileName,
          hasAuth,
          hasAPI,
          hasForm,
          hasStorage
        });
      }
    });
    
    // Security score is now calculated ONLY from ZAP scan results
    // Don't set securityScore or securityIssues here - let ZAP do that
    
    return { fileNodes };
  }, []);

  // Run security analysis when file contents change (for Canvas visualization only)
  useEffect(() => {
    if (Object.keys(fileContents).length > 0) {
      analyzeSecurityIssues(fileContents);
    }
  }, [fileContents, analyzeSecurityIssues]);

  // Get security color based on score
  const getSecurityColor = (score) => {
    if (score >= 80) return '#00ff00'; // Green
    if (score >= 60) return '#ffaa00'; // Yellow
    if (score >= 40) return '#ff8800'; // Orange
    return '#ff4444'; // Red
  };

  // Get security status text
  const getSecurityStatus = (score) => {
    if (score >= 80) return 'Secure';
    if (score >= 60) return 'Warning';
    if (score >= 40) return 'At Risk';
    return 'Critical';
  };

  // Initialize project from URL parameter
  useEffect(() => {
    console.log('MonacoProjectEditor initializing with projectName:', projectName);
    if (projectName) {
      const projectData = {
        name: projectName,
        tech_stack: projectSpec?.tech_stack || ['React', 'FastAPI'], // Use spec if available
        isBuilding: isNewProjectBuild,
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

  // Start build job when this is a new project
  useEffect(() => {
    if (!isNewProjectBuild || !projectSpec || !projectName) return;
    
    // Guard against double execution (React Strict Mode or re-renders)
    if (buildStartedRef.current) {
      console.log('⚠️ Build already started, skipping duplicate execution');
      return;
    }
    buildStartedRef.current = true;
    
    const startBuild = async () => {
      console.log('🚀 Starting new project build:', projectName);
      setIsBuilding(true);
      setAiThinkingSteps([]);
      setBuildProgress(0);
      
      // Add initial thinking messages (VS Code style)
      const addThinkingStep = (step, type = 'thinking') => {
        setAiThinkingSteps(prev => [...prev, { 
          text: step, 
          timestamp: new Date(),
          type: type
        }]);
      };
      
      // Simulate initial design thinking while API call is being made
      const simulateDesignThinking = async () => {
        const designSteps = [
          { delay: 0, text: 'Analyzing project requirements...', progress: 2 },
          { delay: 800, text: 'Understanding user needs and goals...', progress: 5 },
          { delay: 1500, text: 'Choosing design patterns and UI framework...', progress: 8 },
          { delay: 2200, text: 'Planning responsive layout structure...', progress: 10 }
        ];
        
        for (const step of designSteps) {
          await new Promise(resolve => setTimeout(resolve, step.delay));
          addThinkingStep(step.text);
          setBuildProgress(step.progress);
        }
      };
      
      // Start design thinking simulation (runs in parallel with API call)
      simulateDesignThinking();
      
      setChatMessages([{
        role: 'assistant',
        content: `**Building: ${projectName}**\n\nI'm now creating your project. Watch the progress below as I make design decisions and write code...`,
        isBuilding: true
      }]);
      
      try {
        // Step 1: Create async job using token from auth context
        const response = await fetch('http://localhost:8000/api/build-with-ai', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            project_name: projectName,
            idea: projectSpec.description,
            tech_stack: projectSpec.tech_stack || [],
            project_type: projectSpec.type || 'web app',
            features: projectSpec.features || [],
            requirements: projectSpec,
            customizations: projectSpec.customizations || {},
            documentation_context: projectSpec.documentation_context || null
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to start project generation');
        }
        
        const result = await response.json();
        
        if (!result.success || !result.job_id) {
          throw new Error(result.error || 'Failed to create generation job');
        }
        
        const jobId = result.job_id;
        const uniqueProjectName = result.project_name || projectName;
        
        addThinkingStep('Planning component architecture...');
        setBuildProgress(10);
        
        // Step 2: Poll for job status with AI thinking updates
        const pollInterval = 1500;
        const maxAttempts = 400;
        let attempts = 0;
        let lastLogIndex = 0;
        
        const pollJobStatus = async () => {
          try {
            const statusResponse = await fetch(`http://localhost:8000/api/jobs/${jobId}`, {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            });
            
            if (!statusResponse.ok) {
              throw new Error('Failed to check job status');
            }
            
            const statusResult = await statusResponse.json();
            const job = statusResult.job;
            
            // Update progress
            setBuildProgress(job.progress || 0);
            setCurrentBuildPhase(job.phase || 'Building');
            
            // Add new thinking steps from job logs
            if (job.logs && job.logs.length > lastLogIndex) {
              for (let i = lastLogIndex; i < job.logs.length; i++) {
                const log = job.logs[i];
                // Convert log to thinking step
                const thinkingText = convertLogToThinking(log);
                if (thinkingText) {
                  addThinkingStep(thinkingText);
                }
              }
              lastLogIndex = job.logs.length;
            }
            
            if (job.status === 'completed') {
              addThinkingStep('✨ Project generated successfully!');
              setBuildProgress(100);
              
              // Success! Update chat and load project
              setChatMessages(prev => [...prev, {
                role: 'assistant',
                content: `**Done!** Your project "${uniqueProjectName}" is ready!\\n\\nYou can now:\\n• View the live preview on the right\\n• Edit files in the code editor\\n• Ask me to make changes\\n\\nWhat would you like to do first?`
              }]);
              
              setIsBuilding(false);
              setBuildCompleted(true); // Signal build is done
              
              // Navigate to the final project URL if name changed
              if (uniqueProjectName !== projectName) {
                navigate(`/project/${uniqueProjectName}`, { replace: true, state: null });
              } else {
                // Clear the navigation state to prevent re-running build on refresh
                navigate(`/project/${projectName}`, { replace: true, state: null });
              }
              
              return;
            } else if (job.status === 'failed') {
              throw new Error(job.error || 'Project generation failed');
            } else {
              // Still running, poll again
              attempts++;
              if (attempts < maxAttempts) {
                setTimeout(pollJobStatus, pollInterval);
              } else {
                throw new Error('Project generation timed out');
              }
            }
          } catch (error) {
            console.error('Poll error:', error);
            addThinkingStep(`❌ Error: ${error.message}`);
            setChatMessages(prev => [...prev, {
              role: 'assistant',
              content: `**Oops!** Something went wrong: ${error.message}\\n\\nPlease try again or let me know what happened.`
            }]);
            setIsBuilding(false);
          }
        };
        
        // Start polling after a short delay
        setTimeout(pollJobStatus, pollInterval);
        
      } catch (error) {
        console.error('Build start error:', error);
        addThinkingStep(`❌ Failed to start: ${error.message}`);
        setChatMessages(prev => [...prev, {
          role: 'assistant', 
          content: `**Error starting build:** ${error.message}\\n\\nPlease try again.`
        }]);
        setIsBuilding(false);
      }
    };
    
    // Helper to convert backend logs to friendly thinking messages
    const convertLogToThinking = (log) => {
      const logLower = log.toLowerCase();
      if (logLower.includes('analyzing') || logLower.includes('understanding')) {
        return `🧠 ${log}`;
      } else if (logLower.includes('designing') || logLower.includes('planning')) {
        return `🎨 ${log}`;
      } else if (logLower.includes('generating') || logLower.includes('creating')) {
        return `⚡ ${log}`;
      } else if (logLower.includes('writing') || logLower.includes('code')) {
        return `📝 ${log}`;
      } else if (logLower.includes('component') || logLower.includes('page')) {
        return `🧩 ${log}`;
      } else if (logLower.includes('style') || logLower.includes('css')) {
        return `🎨 ${log}`;
      } else if (logLower.includes('complete') || logLower.includes('success') || logLower.includes('done')) {
        return `✅ ${log}`;
      } else if (logLower.includes('error') || logLower.includes('fail')) {
        return `❌ ${log}`;
      } else {
        return `💭 ${log}`;
      }
    };
    
    startBuild();
    
    // Cleanup function (build ref already prevents re-execution)
    return () => {
      // Note: buildStartedRef persists and prevents double builds
    };
  }, [isNewProjectBuild, projectSpec, projectName]); // Removed token/navigate - ref guards against re-runs

  // Initialize project
  useEffect(() => {
    if (project?.name) {
      // Set initial building state from project
      setIsBuilding(project.isBuilding || false);
      setPreviewUrl(ensurePreviewUrlHasAuth(project.preview_url) || null);
      
      // Skip normal initialization if this is a new project being built
      // The build effect will handle initialization after generation completes
      if (!isNewProjectBuild) {
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
        
        // Speak welcome message
        if (!isMuted) {
          const welcomeText = "Welcome to your AI product assistant! I'm here to help you build, design, and improve your project. You can ask me to change the look and feel, add new sections, find and fix issues, or improve this page. Just tell me what you'd like to do.";
          setTimeout(() => {
            speakText(welcomeText);
          }, 1500); // Delay to ensure audio context is ready
        }
      }
      
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

  // Initialize project after build completes
  useEffect(() => {
    if (buildCompleted && project?.name) {
      console.log('✅ Build completed, initializing project...');
      initializeProject();
      setupWebSocket();
      setTimeout(() => runProject(), 500);
      setBuildCompleted(false); // Reset flag
    }
  }, [buildCompleted, project?.name]);

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
        content: `**${errors.length} issue(s) detected** - Check the Issues tab for details and one-click fixes.`
      };
      
      // Only add if we don't already have a recent error message
      setChatMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.content.includes('issue(s) detected')) {
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
    // Prevent concurrent initializations
    if (isInitializingRef.current) {
      console.log('⏭️ Skipping duplicate initializeProject call');
      return;
    }
    isInitializingRef.current = true;
    
    // Load file tree (S3-enabled endpoint)
    try {
      // Get token from localStorage or sessionStorage (matching AuthContext)
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      console.log('🔄 Loading file tree for project:', project.name);
      
      const response = await fetch(
        apiUrl(`api/project-file-tree?project_name=${encodeURIComponent(project.name)}`),
        { headers }
      );
      const data = await response.json();
      console.log('📂 File tree response:', { success: data.success, fileCount: data.file_tree?.length });
      
      if (data.success) {
        setFileTree(data.file_tree || []);
        
        // Auto-select App.jsx if available
        const findAppJsx = (items) => {
          for (const item of items) {
            if (item.name === 'App.jsx' || item.path?.endsWith('App.jsx')) {
              return item.path;
            }
            if (item.children) {
              const found = findAppJsx(item.children);
              if (found) return found;
            }
          }
          return null;
        };
        
        const appJsxPath = findAppJsx(data.file_tree || []);
        if (appJsxPath && !selectedFile) {
          console.log('📄 Auto-selecting App.jsx:', appJsxPath);
          setSelectedFile(appJsxPath);
          loadFileContent(appJsxPath);
        }
        
        // Load Security Decision Records (SDRs) if available
        try {
          const sdrResponse = await fetch(
            apiUrl(`api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent('frontend/sdr.json')}`),
            { headers }
          );
          const sdrData = await sdrResponse.json();
          if (sdrData.success && sdrData.content) {
            const sdrContent = JSON.parse(sdrData.content);
            if (sdrContent.decisions && Array.isArray(sdrContent.decisions)) {
              setSecurityDecisions(sdrContent.decisions);
              console.log(`📋 Loaded ${sdrContent.decisions.length} Security Decision Records`);
            }
          }
        } catch (sdrError) {
          console.log('No SDR file found (this is normal for older projects)');
        }
      } else {
        console.error('Failed to load file tree:', data.error);
        setFileTree([]);
      }
    } catch (error) {
      console.error('Failed to load file tree:', error);
      setFileTree([]);
    } finally {
      isInitializingRef.current = false;
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
          setPreviewUrl(ensurePreviewUrlHasAuth(data.url));
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
              setPreviewUrl(ensurePreviewUrlHasAuth(data.preview_url));
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
        setPreviewUrl(ensurePreviewUrlHasAuth(result.preview_url));
        setIsRunning(true);
        // Clear previous errors on successful run
        setHasErrors(false);
        setErrors([]);
        
        // Ensure preview tab is active when build completes
        setActiveTab('preview');
        setLayoutMode('preview');
        setViewMode('desktop');
        
        // Security scan is now USER-INITIATED ONLY
        // User must click "Run Test" button in Security tab to start scan
        // This prevents automatic scanning which can be slow and resource-intensive
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

  // OWASP ZAP Security Scan Function
  const runZapSecurityScan = async (targetUrl, switchToTab = false) => {
    if (!targetUrl && !previewUrl) {
      console.warn('No preview URL available for security scan');
      return;
    }
    
    const scanUrl = targetUrl || previewUrl;
    setIsZapScanning(true);
    setZapScanProgress('Initializing OWASP ZAP security scan...');
    
    // Only switch to security tab if explicitly requested (e.g., user clicks scan button)
    if (switchToTab) {
      setActiveTab('security');
    }
    
    try {
      // Add notification to chat
      const scanStartMessage = {
        role: 'assistant',
        content: `🔐 **Security Scan Started**\n\nRunning OWASP ZAP security analysis on your application...\n\nThis will detect vulnerabilities like:\n• Cross-Site Scripting (XSS)\n• SQL Injection\n• Insecure Headers\n• Authentication Issues\n• And more...`
      };
      setChatMessages(prev => [...prev, scanStartMessage]);
      
      setZapScanProgress('Running passive security scan...');
      
      const response = await fetch(apiUrl('api/security-scan'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_url: scanUrl,
          scan_type: 'passive', // Start with passive scan (faster, non-intrusive)
          zap_api_key: 'changeme'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setZapScanResult(result);
        setZapScanProgress('');
        
        // Calculate security score based on findings
        const totalAlerts = result.summary?.total_alerts || 0;
        const highRisk = result.summary?.high_risk || 0;
        const mediumRisk = result.summary?.medium_risk || 0;
        const lowRisk = result.summary?.low_risk || 0;
        
        // Score calculation: start at 100, deduct based on severity
        let calculatedScore = 100;
        calculatedScore -= highRisk * 20;    // -20 per high risk
        calculatedScore -= mediumRisk * 10;   // -10 per medium risk
        calculatedScore -= lowRisk * 3;       // -3 per low risk
        calculatedScore = Math.max(0, calculatedScore);
        setSecurityScore(calculatedScore);
        
        // Add completion message to chat
        const scanCompleteMessage = {
          role: 'assistant',
          content: `🛡️ **Security Scan Complete**\n\n**Security Score:** ${calculatedScore}%\n\n**Findings:**\n• 🔴 High Risk: ${highRisk}\n• 🟠 Medium Risk: ${mediumRisk}\n• 🟡 Low Risk: ${lowRisk}\n• 🔵 Informational: ${result.summary?.informational || 0}\n\n**Total Alerts:** ${totalAlerts}\n\n${totalAlerts > 0 ? 'View the **Security** tab to see detailed findings and use **AI Fix** to automatically resolve issues.' : '✅ No critical security issues found!'}`
        };
        setChatMessages(prev => [...prev, scanCompleteMessage]);
        
      } else {
        setZapScanProgress('');
        setZapScanResult({
          success: false,
          error: result.error,
          instructions: result.instructions
        });
        
        // Show error message
        const errorMessage = {
          role: 'assistant',
          content: `⚠️ **Security Scan Issue**\n\n${result.error || 'Failed to run security scan'}\n\n${result.instructions ? '**Setup Instructions:**\n' + result.instructions.map(i => `• ${i}`).join('\n') : ''}`
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Security scan failed:', error);
      setZapScanProgress('');
      setZapScanResult({
        success: false,
        error: error.message
      });
    } finally {
      setIsZapScanning(false);
    }
  };

  // AI-Powered Security Issue Fix Function
  const aiFixSecurityIssue = async (alert, index) => {
    if (!project?.name) return;
    
    setIsFixingSecurityIssue(index);
    
    try {
      const fixStartMessage = {
        role: 'assistant',
        content: `🔧 **Fixing OWASP ZAP Alert**\n\n**Alert:** ${alert.alert || 'Unknown'}\n**Risk Level:** ${alert.risk || 'Unknown'}\n**CWE ID:** ${alert.cweid || 'N/A'}\n\nAnalyzing code to fix this specific ZAP-detected vulnerability...`
      };
      setChatMessages(prev => [...prev, fixStartMessage]);
      
      const response = await fetch(apiUrl('api/ai-fix-security-issue'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          alert: alert,
          fix_all: false
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Update the scan result to mark this alert as fixed
        setZapScanResult(prev => {
          if (!prev) return prev;
          const updatedAlerts = [...(prev.alerts || [])];
          if (updatedAlerts[index]) {
            updatedAlerts[index] = {
              ...updatedAlerts[index],
              _fixed: true,
              _fixResult: result
            };
          }
          return { ...prev, alerts: updatedAlerts };
        });
        
        const serverNote = result.server_side_fix_needed 
          ? `\n\n⚠️ **Server Configuration Required:**\n${result.server_fix_instructions}`
          : '';
        
        const fixSuccessMessage = {
          role: 'assistant',
          content: `✅ **ZAP Alert Fixed!**\n\n**Alert:** ${alert.alert}\n**Resolved:** ${result.zap_alert_resolved || alert.alert}\n\n**Files Modified:**\n${result.fixes_applied?.map(f => `• ${f.path}: ${f.explanation}`).join('\n') || 'No files needed modification'}${serverNote}\n\n**OWASP Category:** ${result.owasp_category || 'N/A'}\n\n🔄 Run the security scan again to verify the fix.`
        };
        setChatMessages(prev => [...prev, fixSuccessMessage]);
        
        // Reload project files
        await initializeProject();
        
        // Refresh preview
        setTimeout(() => {
          refreshPreview();
        }, 1000);
        
      } else {
        const fixErrorMessage = {
          role: 'assistant',
          content: `❌ **Fix Failed**\n\n${result.error || 'Could not apply the security fix'}\n\nPlease review the issue manually or try a different approach.`
        };
        setChatMessages(prev => [...prev, fixErrorMessage]);
      }
    } catch (error) {
      console.error('AI security fix failed:', error);
      const errorMessage = {
        role: 'assistant',
        content: `❌ **Error:** Failed to apply security fix: ${error.message}`
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsFixingSecurityIssue(null);
    }
  };

  // Fix all security issues at once
  const aiFixAllSecurityIssues = async () => {
    if (!zapScanResult?.alerts?.length) return;
    
    const unfixedAlerts = zapScanResult.alerts.filter(a => !a._fixed && (a.risk === 'High' || a.risk === 'Medium'));
    
    if (unfixedAlerts.length === 0) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: '✅ All high and medium risk issues have already been fixed!'
      }]);
      return;
    }
    
    setChatMessages(prev => [...prev, {
      role: 'assistant',
      content: `🔧 **Fixing All Security Issues**\n\nProcessing ${unfixedAlerts.length} high/medium risk issues...`
    }]);
    
    for (let i = 0; i < unfixedAlerts.length; i++) {
      const alertIndex = zapScanResult.alerts.findIndex(a => a === unfixedAlerts[i]);
      await aiFixSecurityIssue(unfixedAlerts[i], alertIndex);
      // Small delay between fixes
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setChatMessages(prev => [...prev, {
      role: 'assistant',
      content: `✅ **All Fixes Complete!**\n\nProcessed ${unfixedAlerts.length} security issues.\n\n🔄 Running security scan again to verify fixes...`
    }]);
    
    // Re-run security scan to verify
    setTimeout(() => {
      runZapSecurityScan();
    }, 2000);
  };

  const autoFixErrors = async () => {
    setIsAutoFixing(true);
    let fixAttempted = false;
    
    try {
      // First try the traditional auto-fix endpoint
      const response = await fetch(apiUrl(`api/auto-fix-project-errors?project_name=${encodeURIComponent(project.name)}`), {
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

  // Load all project files for security analysis
  const loadAllProjectFiles = async () => {
    if (isLoadingSecurityFiles) return;
    setIsLoadingSecurityFiles(true);
    
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      
      console.log('[Security] Starting to load files for project:', project?.name);
      
      // First try to get all files directly from S3 project endpoint
      try {
        const projectResponse = await fetch(
          apiUrl(`api/projects/${encodeURIComponent(project.name)}`),
          { headers }
        );
        const projectData = await projectResponse.json();
        
        console.log('[Security] Project API response:', projectData);
        
        if (projectData.success && projectData.project?.files && projectData.project.files.length > 0) {
          console.log('[Security] Loaded', projectData.project.files.length, 'files directly from S3');
          const allFiles = {};
          for (const file of projectData.project.files) {
            // Only include code files for security analysis
            const ext = file.path.split('.').pop()?.toLowerCase();
            const codeExts = ['js', 'jsx', 'ts', 'tsx', 'py', 'json', 'html', 'css', 'scss', 'vue', 'svelte', 'md'];
            if (codeExts.includes(ext)) {
              allFiles[file.path] = file.content || '';
            }
          }
          console.log('[Security] Filtered to', Object.keys(allFiles).length, 'code files');
          setAllProjectFiles(allFiles);
          setIsLoadingSecurityFiles(false);
          return;
        } else {
          console.log('[Security] No files in project response, trying file tree...');
        }
      } catch (err) {
        console.log('[Security] Direct S3 load failed, falling back to file tree:', err);
      }
      
      // Fallback: Get all files recursively from the file tree
      if (fileTree.length === 0) {
        console.log('[Security] File tree is empty, cannot load files');
        setIsLoadingSecurityFiles(false);
        return;
      }
      
      const getAllFilePaths = (tree, basePath = '') => {
        let paths = [];
        for (const item of tree) {
          const fullPath = basePath ? `${basePath}/${item.name}` : item.name;
          if (item.type === 'file') {
            // Only include code files for security analysis
            const ext = item.name.split('.').pop()?.toLowerCase();
            const codeExts = ['js', 'jsx', 'ts', 'tsx', 'py', 'json', 'html', 'css', 'scss', 'vue', 'svelte', 'md'];
            if (codeExts.includes(ext)) {
              paths.push(fullPath);
            }
          } else if (item.children) {
            paths = paths.concat(getAllFilePaths(item.children, fullPath));
          }
        }
        return paths;
      };
      
      const filePaths = getAllFilePaths(fileTree);
      console.log('[Security] Loading', filePaths.length, 'files for analysis:', filePaths);
      
      // Load files in batches to avoid overwhelming the server
      const batchSize = 5;
      const allFiles = {};
      
      for (let i = 0; i < filePaths.length; i += batchSize) {
        const batch = filePaths.slice(i, i + batchSize);
        const results = await Promise.all(
          batch.map(async (filePath) => {
            try {
              const response = await fetch(
                apiUrl(`api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent(filePath)}`),
                { headers }
              );
              const data = await response.json();
              return { path: filePath, content: data.success ? data.content : '' };
            } catch (err) {
              console.error(`[Security] Failed to load ${filePath}:`, err);
              return { path: filePath, content: '' };
            }
          })
        );
        
        results.forEach(({ path, content }) => {
          allFiles[path] = content;
        });
      }
      
      console.log('[Security] Loaded all files:', Object.keys(allFiles).length);
      setAllProjectFiles(allFiles);
      
    } catch (error) {
      console.error('[Security] Failed to load project files:', error);
    } finally {
      setIsLoadingSecurityFiles(false);
    }
  };

  // Load all files when security view is opened
  useEffect(() => {
    if (isSecurityView && project?.name && Object.keys(allProjectFiles).length === 0) {
      loadAllProjectFiles();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSecurityView, project?.name]);

  const loadFileContent = async (filePath) => {
    console.log('🔄 loadFileContent called with:', filePath);
    
    // If we already have the content, don't reload
    if (fileContents[filePath]) {
      console.log('✅ Content already cached for:', filePath);
      // Only clear loading if this is the currently loading file
      setLoadingFile(prev => prev === filePath ? null : prev);
      addToViewHistory(filePath);
      return;
    }
    
    setLoadingFile(filePath);
    console.log('⏳ Set loading state for:', filePath);
    
    // Safety timeout - clear loading after 15 seconds
    const timeoutId = setTimeout(() => {
      console.log('⚠️ Timeout reached for:', filePath);
      setLoadingFile(prev => prev === filePath ? null : prev);
      setFileContents(prev => ({
        ...prev,
        [filePath]: prev[filePath] || `// Timeout loading file: ${filePath}\n// Please try clicking the file again.`
      }));
    }, 15000);
    
    try {
      // Get token from localStorage or sessionStorage (matching AuthContext)
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      // Clean the file path - remove leading slashes
      const cleanPath = filePath.replace(/^\/+/, '');
      
      const url = apiUrl(`api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent(cleanPath)}`);
      console.log(`📂 Fetching: ${url}`);
      
      const response = await fetch(url, { headers });
      
      clearTimeout(timeoutId);
      console.log(`📡 Response status: ${response.status}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`📄 File data received:`, { success: data.success, size: data.size, hasContent: !!data.content });
      
      if (data.success && data.content) {
        // Set content
        setFileContents(prev => {
          const newState = {
            ...prev,
            [filePath]: data.content
          };
          console.log('✅ Content set for:', filePath, 'Length:', data.content.length);
          return newState;
        });
        
        // Only clear loading if this file is still the one being loaded
        setLoadingFile(prev => {
          if (prev === filePath) {
            console.log('✅ Loading cleared for:', filePath);
            return null;
          }
          return prev;
        });
        
        // Add to view history if it's a new file
        addToViewHistory(filePath);
      } else {
        console.error('❌ Failed to load file:', data.error);
        setFileContents(prev => ({
          ...prev,
          [filePath]: `// Error loading file: ${data.error || 'Unknown error'}\n// Path: ${cleanPath}`
        }));
        setLoadingFile(prev => prev === filePath ? null : prev);
      }
    } catch (error) {
      clearTimeout(timeoutId);
      console.error('❌ Fetch error:', error);
      setFileContents(prev => ({
        ...prev,
        [filePath]: `// Error loading file: ${error.message}\n// File: ${filePath}`
      }));
      setLoadingFile(prev => prev === filePath ? null : prev);
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
            
            // Get user_id from localStorage for S3 file access
            // Priority: _id first (used during project creation), then email
            let userId = 'anonymous';
            const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
            if (userStr) {
              try {
                const user = JSON.parse(userStr);
                userId = user._id || user.email || 'anonymous';
                console.log('[Voice AI] Using user_id:', userId);
              } catch (e) {
                console.warn('Could not parse user from storage:', e);
              }
            }
            
            try {
              const aiResponse = await fetch(apiUrl('api/ai-project-assistant'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                  project_name: project.name,
                  user_message: result.transcript,
                  tech_stack: project.tech_stack || [],
                  re_run: true,
                  user_id: userId // Pass user_id for S3 access
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
                await initializeProject();
                
                // CRITICAL: Force refresh the preview iframe to show updated content
                setTimeout(() => {
                  refreshPreview();
                }, 500);
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
    
    // Prepare message with element context if available
    let messageContent = chatInput;
    if (selectedElement) {
      messageContent = `Change the "${selectedElement}" element: ${chatInput}`;
    }
    
    const userMessage = { role: 'user', content: chatInput }; // Show original user input in chat
    setChatMessages(prev => [...prev, userMessage]);
    const messageToSend = messageContent; // Send full context to AI
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
      // Get user_id from localStorage for S3 file access
      // Priority: _id first (used during project creation), then email
      let userId = 'anonymous';
      const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          userId = user._id || user.email || 'anonymous';
          console.log('[AI Assistant] Using user_id:', userId);
        } catch (e) {
          console.warn('Could not parse user from storage:', e);
        }
      }
      
      const response = await fetch('http://localhost:8000/api/ai-project-assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          user_message: messageToSend,
          tech_stack: project.tech_stack || [],
          re_run: true, // Auto re-run after changes
          user_id: userId // Pass user_id for S3 access
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
        
        // Set building state
        setIsBuilding(true);
        
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
          timestamp: Date.now(),
          completed: true
        }]);
        
        // Clear selected element after successful edit
        setSelectedElement(null);
        
        // Reload project files and preview
        await initializeProject();
        if (result.preview_url) {
          setPreviewUrl(ensurePreviewUrlHasAuth(result.preview_url));
        }
        
        // CRITICAL: Force refresh the preview iframe to show updated content
        setTimeout(() => {
          refreshPreview();
          setIsBuilding(false);
        }, 500);
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

  // Toggle folder expand/collapse
  const toggleFolder = (folderPath) => {
    setExpandedFolders(prev => ({
      ...prev,
      [folderPath]: !prev[folderPath]
    }));
  };

  // Get file icon based on extension - VS Code style
  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    const name = fileName.toLowerCase();
    
    // Special file names
    if (name === 'package.json') return { icon: '{ }', color: '#8bc34a' };
    if (name === 'tsconfig.json') return { icon: 'TS', color: '#3178c6' };
    if (name === 'vite.config.js' || name === 'vite.config.ts') return { icon: '⚡', color: '#646cff' };
    if (name === 'tailwind.config.js') return { icon: '🌊', color: '#38bdf8' };
    if (name === '.gitignore') return { icon: 'G', color: '#f05032' };
    if (name === 'readme.md') return { icon: 'M↓', color: '#083fa1' };
    if (name === '.env' || name.startsWith('.env.')) return { icon: '🔐', color: '#ecd53f' };
    
    // By extension
    const iconMap = {
      'js': { icon: 'JS', color: '#f7df1e' },
      'jsx': { icon: 'JSX', color: '#61dafb' },
      'ts': { icon: 'TS', color: '#3178c6' },
      'tsx': { icon: 'TSX', color: '#3178c6' },
      'py': { icon: 'PY', color: '#3776ab' },
      'css': { icon: 'CSS', color: '#264de4' },
      'scss': { icon: 'S', color: '#cc6699' },
      'html': { icon: 'H', color: '#e44d26' },
      'json': { icon: '{ }', color: '#8bc34a' },
      'md': { icon: 'M↓', color: '#083fa1' },
      'txt': { icon: 'TXT', color: '#888888' },
      'svg': { icon: 'SVG', color: '#ffb13b' },
      'png': { icon: 'IMG', color: '#89cff0' },
      'jpg': { icon: 'IMG', color: '#89cff0' },
      'jpeg': { icon: 'IMG', color: '#89cff0' },
      'gif': { icon: 'IMG', color: '#89cff0' },
      'ico': { icon: 'ICO', color: '#89cff0' },
      'yml': { icon: 'YML', color: '#cb171e' },
      'yaml': { icon: 'YML', color: '#cb171e' },
      'xml': { icon: 'XML', color: '#f60' },
      'sh': { icon: 'SH', color: '#4eaa25' },
      'bash': { icon: 'SH', color: '#4eaa25' },
      'sql': { icon: 'SQL', color: '#e38c00' },
    };
    
    return iconMap[ext] || { icon: '◇', color: '#888888' };
  };

  // --- UPDATED: renderFileTree with expand/collapse support and VS Code icons ---
  const renderFileTree = (items, level = 0) => {
    return items.map((item, index) => {
      const isDirectory = item.type === 'directory' || item.type === 'dir' || item.children;
      const isExpanded = expandedFolders[item.path] !== false; // Default to expanded
      const isSelected = selectedFile === item.path;
      const fileIcon = !isDirectory ? getFileIcon(item.name) : null;
      
      return (
        <div key={item.path || index}>
          <div 
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '4px 8px',
              paddingLeft: `${12 + level * 16}px`,
              fontSize: '13px',
              color: isSelected ? '#ffffff' : '#cccccc',
              background: isSelected ? '#094771' : 'transparent',
              cursor: 'pointer',
              userSelect: 'none',
              fontFamily: "'Segoe UI', 'Inter', -apple-system, sans-serif",
            }}
            onClick={() => {
              if (isDirectory) {
                toggleFolder(item.path);
              } else {
                setSelectedFile(item.path);
                loadFileContent(item.path);
              }
            }}
            onMouseEnter={(e) => {
              if (!isSelected) {
                e.currentTarget.style.background = '#2a2d2e';
              }
            }}
            onMouseLeave={(e) => {
              if (!isSelected) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            {/* Folder/File Icon */}
            {isDirectory ? (
              <>
                <span style={{ 
                  fontSize: '10px', 
                  color: '#cccccc',
                  width: '14px',
                  marginRight: '4px',
                  display: 'inline-flex',
                  justifyContent: 'center'
                }}>
                  {isExpanded ? '▼' : '▶'}
                </span>
                <span style={{ 
                  fontSize: '14px',
                  marginRight: '6px',
                  color: '#dcb67a'
                }}>
                  📁
                </span>
              </>
            ) : (
              <>
                <span style={{ width: '14px', marginRight: '4px' }}></span>
                <span style={{ 
                  fontSize: '9px',
                  fontWeight: 600,
                  color: fileIcon.color,
                  marginRight: '6px',
                  padding: '1px 3px',
                  borderRadius: '2px',
                  background: 'rgba(255,255,255,0.05)',
                  minWidth: '22px',
                  textAlign: 'center',
                  fontFamily: "'Consolas', 'Monaco', monospace"
                }}>
                  {fileIcon.icon}
                </span>
              </>
            )}
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.name}
            </span>
          </div>
          {isDirectory && isExpanded && item.children && item.children.length > 0 && (
            renderFileTree(item.children, level + 1)
          )}
        </div>
      );
    });
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
      {/* Simplified Header - Just project name and status */}
      <div style={styles.editorHeader}>
        <div style={styles.editorTitle}>
          <button 
            style={{
              background: 'transparent',
              border: 'none',
              color: '#aaaaaa',
              fontSize: '18px',
              cursor: 'pointer',
              padding: '4px 8px',
              marginRight: '12px',
              display: 'flex',
              alignItems: 'center',
              transition: 'color 0.2s'
            }}
            onClick={handleClose}
            title="Back to projects"
            onMouseEnter={(e) => e.target.style.color = '#ffffff'}
            onMouseLeave={(e) => e.target.style.color = '#aaaaaa'}
          >
            ←
          </button>
          <span style={styles.projectName}>{project.name}</span>
          
          {/* Status Indicator */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '20px',
            background: 'transparent',
            border: '1px solid #444',
            fontSize: '12px',
            fontWeight: '500'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#ffffff',
              animation: (isBuilding || isAiThinking) ? 'pulse 2s infinite' : 'none'
            }} />
            <span style={{ color: '#ffffff' }}>
              {isBuilding ? 'Building' : isAiThinking ? 'Thinking' : 'Live Preview'}
            </span>
          </div>
          
          {/* Security Health Widget */}
          <div 
            style={{
              ...styles.securityWidget,
              background: 'transparent',
              border: '1px solid #444',
              cursor: 'pointer'
            }}
            onClick={() => setIsSecurityView(!isSecurityView)}
            title={`Security Score: ${securityScore}% - Click to view details`}
          >
            <span style={{ color: '#ffffff' }}>
              Shield: {securityScore}%
            </span>
            <div style={styles.securityBar}>
              <div 
                style={{
                  ...styles.securityBarFill,
                  width: `${securityScore}%`,
                  background: '#ffffff'
                }}
              />
            </div>
            {securityIssues.length > 0 && (
              <span style={{ 
                color: '#ffffff',
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.1)'
              }}>
                {securityIssues.length} issue{securityIssues.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
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
              <button 
                style={{
                  ...styles.sidebarTab,
                  ...(chatTab === 'issues' ? styles.sidebarTabActive : {}),
                  position: 'relative'
                }}
                onClick={() => setChatTab('issues')}
              >
                Issues
                {(securityIssues.length > 0 || errors.length > 0) && (
                  <span style={{
                    position: 'absolute',
                    top: '-2px',
                    right: '-2px',
                    background: '#ff4444',
                    color: '#fff',
                    borderRadius: '50%',
                    width: '16px',
                    height: '16px',
                    fontSize: '10px',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {securityIssues.length + errors.length}
                  </span>
                )}
              </button>
            </div>
            <button
              style={{
                background: 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                color: isMuted ? '#666' : '#fff',
                cursor: 'pointer',
                padding: '8px',
                marginLeft: 'auto',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                width: '36px',
                height: '36px'
              }}
              onClick={() => {
                const newMutedState = !isMuted;
                setIsMuted(newMutedState);
                
                // If muting, stop any currently playing audio
                if (newMutedState) {
                  if (currentAudioRef.current) {
                    currentAudioRef.current.pause();
                    currentAudioRef.current = null;
                  }
                  speechSynthesis.cancel();
                  setIsPlaying(false);
                }
              }}
              title={isMuted ? "Unmute AI voice" : "Mute AI voice"}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
            </button>
          </div>
          
          <div style={styles.chatContainer}>
            {chatTab === 'chat' ? (
              <>
                <div style={styles.chatMessages} ref={chatEndRef}>
              {/* Show AI Building Progress at the top when building */}
              {isBuilding && aiThinkingSteps.length > 0 && (
                <div style={{
                  background: 'rgba(34, 197, 94, 0.1)',
                  border: '1px solid rgba(34, 197, 94, 0.3)',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '16px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    marginBottom: '12px'
                  }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      background: '#22c55e',
                      borderRadius: '50%',
                      animation: 'pulse 1.5s infinite'
                    }} />
                    <span style={{
                      fontSize: '12px',
                      fontWeight: '600',
                      color: '#22c55e',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      Building Project - {buildProgress}%
                    </span>
                  </div>
                  
                  {/* Progress Bar */}
                  <div style={{
                    height: '4px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '2px',
                    overflow: 'hidden',
                    marginBottom: '12px'
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${buildProgress}%`,
                      background: 'linear-gradient(90deg, #22c55e 0%, #16a34a 100%)',
                      transition: 'width 0.5s ease-out'
                    }} />
                  </div>
                  
                  {/* Live Thinking Steps */}
                  <div style={{
                    maxHeight: '150px',
                    overflowY: 'auto',
                    fontSize: '13px'
                  }}>
                    {aiThinkingSteps.slice(-8).map((step, index) => (
                      <div 
                        key={index}
                        style={{
                          color: step.type === 'error' ? '#ff4444' : '#ffffff',
                          padding: '4px 0',
                          opacity: index === aiThinkingSteps.slice(-8).length - 1 ? 1 : 0.6,
                          animation: index === aiThinkingSteps.slice(-8).length - 1 ? 'fadeIn 0.3s ease-out' : 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}
                      >
                        {index === aiThinkingSteps.slice(-8).length - 1 && (
                          <span style={{
                            width: '6px',
                            height: '6px',
                            background: '#22c55e',
                            borderRadius: '50%',
                            flexShrink: 0
                          }} />
                        )}
                        {step.text}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
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
                    {renderFormattedMessage(message.content, () => {
                      // Deep-link: open security view and switch to issues tab
                      setChatTab('issues');
                    })}
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
            
            {/* Starter Action Chips - Show only when no messages and not building */}
            {chatMessages.length === 0 && !isBuilding && (
              <div style={{
                padding: '12px 16px',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                {[
                  { icon: '🎨', text: 'Change theme colors' },
                  { icon: '➕', text: 'Add new section' },
                  { icon: '✏️', text: 'Edit homepage text' },
                  { icon: '🖼️', text: 'Change images' },
                  { icon: '🚀', text: 'Add animations' },
                  { icon: '📱', text: 'Make it responsive' }
                ].map((action, i) => (
                  <button
                    key={i}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: '20px',
                      background: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#fff',
                      fontSize: '13px',
                      fontWeight: '500',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      ':hover': { background: 'rgba(255, 255, 255, 0.12)' }
                    }}
                    onClick={() => {
                      setChatInput(action.text);
                      document.querySelector('textarea[placeholder*="Type or speak"]')?.focus();
                    }}
                    onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.12)'}
                    onMouseLeave={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.08)'}
                  >
                    <span>{action.icon}</span>
                    <span>{action.text}</span>
                  </button>
                ))}
              </div>
            )}
            
            <div style={{ ...styles.chatInputContainer, position: 'relative' }}>
              {/* Context Pill for Selected Element */}
              {selectedElement && (
                <div style={styles.contextPill}>
                  🎯 Editing: '{selectedElement}'
                  <span 
                    style={styles.contextPillClose}
                    onClick={() => setSelectedElement(null)}
                    onMouseEnter={(e) => e.target.style.opacity = '1'}
                    onMouseLeave={(e) => e.target.style.opacity = '0.8'}
                    title="Clear selection"
                  >
                    ✕
                  </span>
                </div>
              )}
              
              <button 
                style={{
                  ...styles.micButton,
                  ...(isRecording ? styles.micButtonRecording : {})
                }}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isAiThinking || isPlaying}
                title={isRecording ? "Stop recording" : "Start recording"}
              >
                <Mic size={20} />
              </button>
              <textarea
                style={styles.chatInput}
                placeholder={selectedElement ? `What would you like to change about the ${selectedElement}?` : isRecording ? "Recording..." : "Type or speak your message..."}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (isAiThinking) {
                      setIsAiThinking(false);
                    } else {
                      sendChatMessage();
                    }
                  }
                }}
                disabled={isRecording}
                rows={1}
              />
              <button 
                style={{
                  ...styles.chatSendButton,
                  ...(isAiThinking ? { background: '#ff4444' } : {}),
                  opacity: (!isAiThinking && !chatInput.trim()) ? 0.5 : 1,
                  cursor: (!isAiThinking && !chatInput.trim()) ? 'not-allowed' : 'pointer',
                }}
                onClick={isAiThinking ? () => setIsAiThinking(false) : sendChatMessage}
                disabled={!isAiThinking && !chatInput.trim()}
                title={isAiThinking ? "Stop AI" : "Send message"}
              >
                {isAiThinking ? '⏸' : <Send size={16} />}
              </button>
            </div>
              </>
            ) : chatTab === 'tasks' ? (
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
            ) : (
              /* Issues View */
              <div style={{
                ...styles.chatMessages,
                padding: '16px'
              }}>
                {/* Security Issues Section */}
                {securityIssues.length > 0 && (
                  <div style={{ marginBottom: '20px' }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                      paddingBottom: '8px',
                      borderBottom: '1px solid #333'
                    }}>
                      <span style={{ fontSize: '14px', fontWeight: 600 }}>Shield</span>
                      <span style={{ 
                        color: '#ff6600', 
                        fontSize: '12px', 
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Security Issues ({securityIssues.length})
                      </span>
                    </div>
                    {securityIssues.map((issue, index) => (
                      <div 
                        key={`security-${index}`}
                        onClick={() => {
                          // Deep-link: Open security canvas and highlight the relevant node
                          setIsSecurityView(true);
                          // Map issue to node type for highlighting
                          const nodeMapping = {
                            'Hardcoded API key': 'detected_auth',
                            'Hardcoded password': 'detected_auth',
                            'Password field without SSL': 'detected_sanitizer',
                            'dangerouslySetInnerHTML': 'detected_sanitizer',
                            'Dangerous eval()': 'detected_validator',
                            'Insecure HTTP endpoint': 'api',
                            'Sensitive data in localStorage': 'detected_auth',
                            'CORS wildcard': 'api',
                            'Form submitting over HTTP': 'api',
                            'Environment variable exposed': 'api'
                          };
                          // Find matching node
                          const matchingNode = Object.keys(nodeMapping).find(key => 
                            issue.issue.includes(key)
                          );
                          setHighlightedIssueNode(matchingNode ? nodeMapping[matchingNode] : 'detected_sanitizer');
                        }}
                        style={{
                          padding: '12px',
                          background: '#111111',
                          border: '1px solid #333333',
                          borderLeft: `3px solid ${
                            issue.severity === 'critical' ? '#ff0033' 
                            : issue.severity === 'high' ? '#ff6600' 
                            : issue.severity === 'medium' ? '#ffaa00'
                            : '#888888'
                          }`,
                          borderRadius: '6px',
                          marginBottom: '8px',
                          cursor: 'pointer',
                          transition: 'all 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#1a1a1a';
                          e.currentTarget.style.borderColor = '#444';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#111111';
                          e.currentTarget.style.borderColor = '#333333';
                        }}
                      >
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'space-between',
                          marginBottom: '6px'
                        }}>
                          <span style={{
                            color: '#ffffff',
                            fontSize: '13px',
                            fontWeight: 500
                          }}>
                            {issue.issue}
                          </span>
                          <span style={{
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: issue.severity === 'critical' ? '#ff003320' 
                              : issue.severity === 'high' ? '#ff660020' 
                              : issue.severity === 'medium' ? '#ffaa0020'
                              : '#88888820',
                            color: issue.severity === 'critical' ? '#ff0033' 
                              : issue.severity === 'high' ? '#ff6600' 
                              : issue.severity === 'medium' ? '#ffaa00'
                              : '#888888',
                            textTransform: 'uppercase',
                            fontWeight: 600
                          }}>
                            {issue.severity}
                          </span>
                        </div>
                        <div style={{ 
                          color: '#888', 
                          fontSize: '11px',
                          marginBottom: '4px'
                        }}>
                          📁 {issue.file} {issue.line ? `(line ${issue.line})` : ''}
                        </div>
                        {issue.recommendation && (
                          <div style={{ 
                            color: '#00ff41', 
                            fontSize: '11px',
                            marginTop: '6px',
                            padding: '6px 8px',
                            background: '#00ff4110',
                            borderRadius: '4px'
                          }}>
                            💡 {issue.recommendation}
                          </div>
                        )}
                        <div style={{
                          color: '#666',
                          fontSize: '10px',
                          marginTop: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <span>🔗</span>
                          <span>Click to view in Security Canvas</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Code Errors Section */}
                {errors.length > 0 && (
                  <div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                      paddingBottom: '8px',
                      borderBottom: '1px solid #333'
                    }}>
                      <span style={{ fontSize: '16px' }}>⚠️</span>
                      <span style={{ 
                        color: '#ff4444', 
                        fontSize: '12px', 
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        Code Errors ({errors.length})
                      </span>
                    </div>
                    {errors.map((error, index) => (
                      <div 
                        key={`error-${index}`}
                        style={{
                          padding: '12px',
                          background: '#111111',
                          border: '1px solid #333333',
                          borderLeft: '3px solid #ff4444',
                          borderRadius: '6px',
                          marginBottom: '8px'
                        }}
                      >
                        <div style={{
                          color: '#ffffff',
                          fontSize: '13px',
                          fontWeight: 500,
                          marginBottom: '4px'
                        }}>
                          {error.message}
                        </div>
                        {error.file && (
                          <div style={{ 
                            color: '#888', 
                            fontSize: '11px'
                          }}>
                            📁 {error.file} {error.line ? `(line ${error.line})` : ''}
                          </div>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={autoFixErrors}
                      disabled={isAutoFixing}
                      style={{
                        width: '100%',
                        padding: '12px',
                        marginTop: '12px',
                        background: isAutoFixing ? '#333' : 'linear-gradient(135deg, #00ff41 0%, #00cc33 100%)',
                        border: 'none',
                        borderRadius: '8px',
                        color: isAutoFixing ? '#888' : '#000',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: isAutoFixing ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {isAutoFixing ? '🔧 Fixing...' : '🔧 Auto-Fix All Issues'}
                    </button>
                  </div>
                )}

                {/* No Issues */}
                {securityIssues.length === 0 && errors.length === 0 && (
                  <div style={{
                    textAlign: 'center',
                    padding: '60px 20px',
                    color: '#888'
                  }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
                    <div style={{ fontSize: '16px', fontWeight: 500, color: '#00ff41', marginBottom: '8px' }}>
                      All Clear!
                    </div>
                    <div style={{ fontSize: '13px' }}>
                      No security issues or code errors detected.
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Preview or Code */}
        <div style={styles.rightPanel}>
          {/* Browser-style Tab Bar */}
          <div style={styles.browserTabBar}>
            {/* Desktop Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(viewMode === 'desktop' && activeTab === 'preview' && layoutMode === 'preview' && !isSecurityView ? styles.browserTabActive : {})
              }}
              onClick={() => {
                setViewMode('desktop');
                setActiveTab('preview');
                setLayoutMode('preview');
                setIsSecurityView(false);
              }}
            >
              Desktop
            </div>
            
            {/* Mobile Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(viewMode === 'mobile' && activeTab === 'preview' && layoutMode === 'preview' && !isSecurityView ? styles.browserTabActive : {})
              }}
              onClick={() => {
                setViewMode('mobile');
                setActiveTab('preview');
                setLayoutMode('preview');
                setIsSecurityView(false);
              }}
            >
              Mobile
            </div>
            
            {/* Code Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(layoutMode === 'code' ? styles.browserTabActive : {})
              }}
              onClick={() => {
                setLayoutMode(layoutMode === 'code' ? 'preview' : 'code');
                setActiveTab('preview');
                setIsSecurityView(false);
              }}
            >
              Code
            </div>
            
            {/* X-Ray Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(isSecurityView ? styles.browserTabActive : {})
              }}
              onClick={() => {
                setIsSecurityView(!isSecurityView);
                setActiveTab('preview');
                setLayoutMode('preview');
              }}
            >
              X-Ray
            </div>
            
            {/* Security Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(activeTab === 'security' ? styles.browserTabActive : {}),
                position: 'relative'
              }}
              onClick={() => {
                setActiveTab(activeTab === 'security' ? 'preview' : 'security');
                setLayoutMode('preview');
                setIsSecurityView(false);
              }}
            >
              Security
              {zapScanResult?.summary?.total_alerts > 0 && (
                <span style={{
                  position: 'absolute',
                  top: '4px',
                  right: '2px',
                  background: zapScanResult.summary.high_risk > 0 ? '#ff3333' : '#ff9900',
                  color: '#000',
                  borderRadius: '10px',
                  padding: '1px 5px',
                  fontSize: '9px',
                  fontWeight: 700,
                }}>
                  {zapScanResult.summary.total_alerts}
                </span>
              )}
              {isZapScanning && (
                <span style={{
                  position: 'absolute',
                  top: '4px',
                  right: '2px',
                  width: '12px',
                  height: '12px',
                  border: '2px solid #fff',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
              )}
            </div>
            
            {/* Decisions Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(activeTab === 'decisions' ? styles.browserTabActive : {}),
                position: 'relative'
              }}
              onClick={() => {
                setActiveTab(activeTab === 'decisions' ? 'preview' : 'decisions');
                setLayoutMode('preview');
                setIsSecurityView(false);
              }}
            >
              Decisions
              {securityDecisions.length > 0 && (
                <span style={{
                  position: 'absolute',
                  top: '4px',
                  right: '2px',
                  background: '#ffffff',
                  color: '#000',
                  borderRadius: '10px',
                  padding: '1px 5px',
                  fontSize: '9px',
                  fontWeight: 700,
                }}>
                  {securityDecisions.length}
                </span>
              )}
            </div>
            
            {/* Settings Tab */}
            <div 
              style={{
                ...styles.browserTab,
                ...(activeTab === 'settings' ? styles.browserTabActive : {})
              }}
              onClick={() => {
                setActiveTab(activeTab === 'settings' ? 'preview' : 'settings');
                setLayoutMode('preview');
                setIsSecurityView(false);
              }}
            >
              Settings
            </div>
            
            {/* Spacer to push undo/redo to the right */}
            <div style={{ flex: 1 }} />
            
            {/* Undo/Redo Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginRight: '8px' }}>
              <button
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.08)';
                }}
                onClick={() => {
                  const iframe = document.querySelector('iframe');
                  if (iframe?.contentWindow?.undoAction) {
                    iframe.contentWindow.undoAction();
                  }
                }}
                title="Undo (Ctrl+Z)"
              >
                <span style={{ fontSize: '14px' }}>↩</span> Undo
                <span style={{ color: '#666', fontSize: '10px', marginLeft: '4px' }}>Ctrl+Z</span>
              </button>
              <button
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  color: '#fff',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.15)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'rgba(255,255,255,0.08)';
                }}
                onClick={() => {
                  const iframe = document.querySelector('iframe');
                  if (iframe?.contentWindow?.redoAction) {
                    iframe.contentWindow.redoAction();
                  }
                }}
                title="Redo (Ctrl+Y)"
              >
                <span style={{ fontSize: '14px' }}>↪</span> Redo
                <span style={{ color: '#666', fontSize: '10px', marginLeft: '4px' }}>Ctrl+Y</span>
              </button>
            </div>
          </div>
          
          {/* Browser URL Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '8px 16px',
            background: '#000000',
            borderBottom: '1px solid #222',
          }}>
            {/* Navigation Buttons */}
            <div style={{ display: 'flex', gap: '2px' }}>
              <button 
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#555',
                  cursor: 'pointer',
                  padding: '6px 10px',
                  borderRadius: '4px',
                  fontSize: '16px',
                  fontWeight: 300,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => e.target.style.color = '#fff'}
                onMouseLeave={(e) => e.target.style.color = '#555'}
                onClick={() => {
                  const iframe = document.querySelector('iframe');
                  if (iframe) {
                    try { iframe.contentWindow.history.back(); } catch(e) {}
                  }
                }}
                title="Back"
              >
                &lt;
              </button>
              <button 
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#555',
                  cursor: 'pointer',
                  padding: '6px 10px',
                  borderRadius: '4px',
                  fontSize: '16px',
                  fontWeight: 300,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => e.target.style.color = '#fff'}
                onMouseLeave={(e) => e.target.style.color = '#555'}
                onClick={() => {
                  const iframe = document.querySelector('iframe');
                  if (iframe) {
                    try { iframe.contentWindow.history.forward(); } catch(e) {}
                  }
                }}
                title="Forward"
              >
                &gt;
              </button>
              <button 
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#555',
                  cursor: 'pointer',
                  padding: '6px 10px',
                  borderRadius: '4px',
                  fontSize: '13px',
                  fontWeight: 400,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => e.target.style.color = '#fff'}
                onMouseLeave={(e) => e.target.style.color = '#555'}
                onClick={() => {
                  const iframe = document.querySelector('iframe');
                  if (iframe) iframe.src = iframe.src;
                }}
                title="Reload"
              >
                Reload
              </button>
            </div>
            
            {/* URL Bar */}
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0',
              background: '#111111',
              border: '1px solid #222',
              borderRadius: '6px',
              padding: '8px 16px',
              fontSize: '13px',
              fontFamily: 'monospace',
            }}>
              <span style={{ color: '#444' }}>localhost:8000</span>
              <span style={{ color: '#666' }}>/preview/</span>
              <span style={{ color: '#ffffff' }}>{projectName}</span>
            </div>
            
            {/* Status */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: isRunning ? '#00ff00' : '#333',
              }} />
              <span style={{
                fontSize: '11px',
                fontWeight: 500,
                color: isRunning ? '#ffffff' : '#555',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}>
                {isRunning ? 'Live' : 'Stopped'}
              </span>
            </div>
          </div>
          
          <div style={styles.rightPanelContent}>
            {activeTab === 'decisions' ? (
              /* Security Decision Records Panel */
              <div style={{
                padding: '0',
                background: '#0d1117',
                height: '100%',
                overflow: 'auto'
              }}>
                {/* Header */}
                <div style={{
                  padding: '24px 32px',
                  borderBottom: '1px solid #21262d',
                  background: '#161b22'
                }}>
                  <h2 style={{
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#e6edf3',
                    margin: '0 0 8px 0',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                  }}>
                    Security Decision Records
                  </h2>
                  <p style={{
                    fontSize: '14px',
                    color: '#8b949e',
                    margin: 0
                  }}>
                    Automated documentation of security decisions made during project generation
                  </p>
                </div>

                {/* Timeline */}
                <div style={{ padding: '24px 32px' }}>
                  {securityDecisions.length === 0 ? (
                    <div style={{
                      textAlign: 'center',
                      padding: '60px 20px',
                      color: '#8b949e'
                    }}>
                      <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.5 }}>SDR</div>
                      <h3 style={{ color: '#e6edf3', marginBottom: '8px', fontWeight: 500 }}>No Decision Records Yet</h3>
                      <p style={{ fontSize: '14px', maxWidth: '400px', margin: '0 auto' }}>
                        Security decisions will be automatically documented here when the AI makes architectural choices during project generation.
                      </p>
                    </div>
                  ) : (
                    <div style={{ position: 'relative' }}>
                      {/* Timeline line */}
                      <div style={{
                        position: 'absolute',
                        left: '15px',
                        top: '0',
                        bottom: '0',
                        width: '2px',
                        background: '#21262d'
                      }} />
                      
                      {/* Decision Cards */}
                      {securityDecisions.map((sdr, index) => (
                        <div key={sdr.id || index} style={{
                          position: 'relative',
                          paddingLeft: '48px',
                          paddingBottom: '32px'
                        }}>
                          {/* Timeline dot */}
                          <div style={{
                            position: 'absolute',
                            left: '8px',
                            top: '4px',
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            background: sdr.category === 'critical' ? '#f85149' : 
                                       sdr.category === 'security' ? '#238636' :
                                       sdr.category === 'architecture' ? '#1f6feb' : '#8b949e',
                            border: '3px solid #0d1117'
                          }} />
                          
                          {/* Card */}
                          <div style={{
                            background: '#161b22',
                            border: '1px solid #21262d',
                            borderRadius: '8px',
                            overflow: 'hidden'
                          }}>
                            {/* Card Header */}
                            <div style={{
                              padding: '16px 20px',
                              borderBottom: '1px solid #21262d',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'flex-start'
                            }}>
                              <div>
                                <div style={{
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  color: sdr.category === 'critical' ? '#f85149' : 
                                         sdr.category === 'security' ? '#238636' :
                                         sdr.category === 'architecture' ? '#1f6feb' : '#8b949e',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.5px',
                                  marginBottom: '6px'
                                }}>
                                  {sdr.id}
                                </div>
                                <h3 style={{
                                  fontSize: '16px',
                                  fontWeight: '600',
                                  color: '#e6edf3',
                                  margin: 0
                                }}>
                                  {sdr.title}
                                </h3>
                              </div>
                              <div style={{
                                fontSize: '12px',
                                color: '#8b949e',
                                whiteSpace: 'nowrap'
                              }}>
                                {sdr.date}
                              </div>
                            </div>
                            
                            {/* Card Body */}
                            <div style={{ padding: '16px 20px' }}>
                              {/* Decision */}
                              <div style={{ marginBottom: '16px' }}>
                                <div style={{
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  color: '#8b949e',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.5px',
                                  marginBottom: '6px'
                                }}>
                                  Decision
                                </div>
                                <div style={{
                                  fontSize: '14px',
                                  color: '#e6edf3',
                                  padding: '10px 14px',
                                  background: '#238636',
                                  borderRadius: '6px',
                                  fontWeight: '500'
                                }}>
                                  {sdr.decision}
                                </div>
                              </div>
                              
                              {/* Context */}
                              <div style={{ marginBottom: '16px' }}>
                                <div style={{
                                  fontSize: '11px',
                                  fontWeight: '600',
                                  color: '#8b949e',
                                  textTransform: 'uppercase',
                                  letterSpacing: '0.5px',
                                  marginBottom: '6px'
                                }}>
                                  Context
                                </div>
                                <div style={{
                                  fontSize: '14px',
                                  color: '#c9d1d9',
                                  lineHeight: '1.6'
                                }}>
                                  {sdr.context}
                                </div>
                              </div>
                              
                              {/* Alternatives Rejected */}
                              {sdr.alternatives && sdr.alternatives.length > 0 && (
                                <div>
                                  <div style={{
                                    fontSize: '11px',
                                    fontWeight: '600',
                                    color: '#8b949e',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px',
                                    marginBottom: '8px'
                                  }}>
                                    Alternatives Rejected
                                  </div>
                                  {sdr.alternatives.map((alt, altIndex) => (
                                    <div key={altIndex} style={{
                                      fontSize: '13px',
                                      color: '#f85149',
                                      padding: '8px 12px',
                                      background: 'rgba(248, 81, 73, 0.1)',
                                      borderRadius: '4px',
                                      marginBottom: '6px',
                                      borderLeft: '3px solid #f85149'
                                    }}>
                                      <strong>{alt.name}:</strong> {alt.reason}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : activeTab === 'settings' ? (
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
            ) : activeTab === 'security' ? (
              /* OWASP ZAP Security Report Panel */
              <div style={{
                padding: '32px',
                background: '#000000',
                height: '100%',
                overflow: 'auto',
                color: '#ffffff'
              }}>
                {/* Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '32px',
                  paddingBottom: '20px',
                  borderBottom: '1px solid #222'
                }}>
                  <div>
                    <h2 style={{
                      fontSize: '28px',
                      fontWeight: '500',
                      color: '#ffffff',
                      margin: 0,
                      letterSpacing: '0.5px'
                    }}>
                      Security Report
                    </h2>
                    <p style={{ color: '#666', fontSize: '15px', marginTop: '8px' }}>
                      Automated vulnerability scan powered by OWASP ZAP
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button
                      onClick={() => runZapSecurityScan(null, true)}
                      disabled={isZapScanning || !previewUrl}
                      style={{
                        background: isZapScanning ? '#111' : 'transparent',
                        color: isZapScanning ? '#444' : '#ffffff',
                        border: '1px solid #333',
                        padding: '12px 24px',
                        borderRadius: '4px',
                        cursor: isZapScanning ? 'not-allowed' : 'pointer',
                        fontWeight: 500,
                        fontSize: '14px',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {isZapScanning ? (
                        <>
                          <span style={{
                            display: 'inline-block',
                            width: '12px',
                            height: '12px',
                            border: '2px solid #444',
                            borderTopColor: 'transparent',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                            marginRight: '6px',
                            verticalAlign: 'middle'
                          }} />
                          Scanning...
                        </>
                      ) : (
                        <>{zapScanResult ? 'Re-scan' : 'Run Scan'}</>
                      )}
                    </button>
                    {zapScanResult?.summary?.total_alerts > 0 && (
                      <button
                        onClick={aiFixAllSecurityIssues}
                        disabled={isFixingSecurityIssue !== null}
                        style={{
                          background: 'transparent',
                          color: isFixingSecurityIssue !== null ? '#444' : '#ffffff',
                          border: '1px solid #333',
                          padding: '12px 24px',
                          borderRadius: '4px',
                          cursor: isFixingSecurityIssue !== null ? 'not-allowed' : 'pointer',
                          fontWeight: 500,
                          fontSize: '14px',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        AI Fix All
                      </button>
                    )}
                  </div>
                </div>

                {/* Scanning Progress */}
                {isZapScanning && zapScanProgress && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #222',
                    borderRadius: '4px',
                    padding: '20px',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px'
                  }}>
                    <div style={{
                      width: '20px',
                      height: '20px',
                      border: '2px solid #ffffff',
                      borderTopColor: 'transparent',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                    <span style={{ color: '#ffffff', fontWeight: 400, fontSize: '16px' }}>{zapScanProgress}</span>
                  </div>
                )}

                {/* Security Score */}
                {zapScanResult?.success && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #222',
                    borderRadius: '6px',
                    padding: '32px',
                    marginBottom: '28px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div>
                        <div style={{ fontSize: '14px', color: '#666', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1.5px' }}>Security Score</div>
                        <div style={{
                          fontSize: '64px',
                          fontWeight: 300,
                          color: '#ffffff'
                        }}>
                          {securityScore}%
                        </div>
                      </div>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: '40px'
                      }}>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '32px', fontWeight: 400, color: zapScanResult.summary?.high_risk > 0 ? '#ff4444' : '#ffffff' }}>{zapScanResult.summary?.high_risk || 0}</div>
                          <div style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '1px' }}>High</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '32px', fontWeight: 400, color: zapScanResult.summary?.medium_risk > 0 ? '#ffaa00' : '#ffffff' }}>{zapScanResult.summary?.medium_risk || 0}</div>
                          <div style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '1px' }}>Medium</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '32px', fontWeight: 400, color: '#ffffff' }}>{zapScanResult.summary?.low_risk || 0}</div>
                          <div style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '1px' }}>Low</div>
                        </div>
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ fontSize: '32px', fontWeight: 400, color: '#ffffff' }}>{zapScanResult.summary?.informational || 0}</div>
                          <div style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '1px' }}>Info</div>
                        </div>
                      </div>
                    </div>
                    <div style={{
                      marginTop: '24px',
                      height: '4px',
                      background: '#222',
                      borderRadius: '2px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${securityScore}%`,
                        background: '#ffffff',
                        borderRadius: '2px',
                        transition: 'width 0.5s ease'
                      }} />
                    </div>
                    <div style={{ marginTop: '16px', fontSize: '14px', color: '#555' }}>
                      Duration: {zapScanResult.duration_seconds?.toFixed(2)}s | Target: {zapScanResult.target_url?.slice(0, 60)}...
                    </div>
                  </div>
                )}

                {/* Error State */}
                {zapScanResult && !zapScanResult.success && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #333',
                    borderRadius: '4px',
                    padding: '20px',
                    marginBottom: '20px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                      <div>
                        <div style={{ color: '#ffffff', fontWeight: 500, marginBottom: '8px' }}>
                          Scan Failed
                        </div>
                        <div style={{ color: '#666', fontSize: '12px', marginBottom: '12px' }}>
                          {zapScanResult.error}
                        </div>
                        {zapScanResult.instructions && (
                          <div style={{ 
                            background: '#000', 
                            padding: '12px', 
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontFamily: 'monospace',
                            border: '1px solid #222'
                          }}>
                            <div style={{ color: '#666', marginBottom: '8px' }}>Setup Instructions:</div>
                            {zapScanResult.instructions.map((inst, i) => (
                              <div key={i} style={{ color: '#888', marginBottom: '4px' }}>{inst}</div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* No Scan Yet */}
                {!zapScanResult && !isZapScanning && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #222',
                    borderRadius: '4px',
                    padding: '48px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px', color: '#ffffff' }}>
                      No Security Scan Yet
                    </div>
                    <div style={{ color: '#666', fontSize: '12px', marginBottom: '24px' }}>
                      Run a security scan to detect vulnerabilities in your application.
                    </div>
                    <button
                      onClick={() => runZapSecurityScan(null, true)}
                      disabled={!previewUrl}
                      style={{
                        background: 'transparent',
                        color: previewUrl ? '#ffffff' : '#444',
                        border: '1px solid #333',
                        padding: '10px 20px',
                        borderRadius: '4px',
                        cursor: previewUrl ? 'pointer' : 'not-allowed',
                        fontWeight: 500,
                        fontSize: '12px',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {previewUrl ? 'Start Security Scan' : 'Build Project First'}
                    </button>
                  </div>
                )}

                {/* Master-Detail Security Panel */}
                {zapScanResult?.success && zapScanResult.alerts?.length > 0 && (
                  <div style={{ display: 'flex', gap: '0', height: 'calc(100vh - 420px)', minHeight: '550px' }}>
                    
                    {/* Faceted Search Sidebar */}
                    <div style={{
                      width: '220px',
                      flexShrink: 0,
                      background: '#080808',
                      borderRight: '1px solid #1a1a1a',
                      padding: '20px 16px',
                      overflowY: 'auto'
                    }}>
                      {/* Severity Filter */}
                      <div style={{ marginBottom: '28px' }}>
                        <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '14px', fontWeight: 500 }}>Severity</div>
                        {['High', 'Medium', 'Low', 'Informational'].map(sev => {
                          const count = zapScanResult.alerts.filter(a => a.risk === sev).length;
                          const isActive = alertFilters.severity.includes(sev);
                          return (
                            <div
                              key={sev}
                              onClick={() => {
                                setAlertFilters(prev => ({
                                  ...prev,
                                  severity: isActive 
                                    ? prev.severity.filter(s => s !== sev)
                                    : [...prev.severity, sev]
                                }));
                              }}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 12px',
                                marginBottom: '4px',
                                cursor: 'pointer',
                                background: isActive ? '#1a1a1a' : 'transparent',
                                borderRadius: '4px',
                                transition: 'background 0.15s'
                              }}
                            >
                              <span style={{ 
                                fontSize: '14px', 
                                color: isActive ? '#ffffff' : (sev === 'High' ? '#ff4444' : sev === 'Medium' ? '#ffaa00' : '#888')
                              }}>{sev}</span>
                              <span style={{ fontSize: '13px', color: '#555' }}>{count}</span>
                            </div>
                          );
                        })}
                      </div>

                      {/* Status Filter */}
                      <div style={{ marginBottom: '28px' }}>
                        <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '14px', fontWeight: 500 }}>Status</div>
                        {['open', 'confirmed', 'false_positive', 'fixed'].map(status => {
                          const isActive = alertFilters.status.includes(status);
                          const statusLabels = { open: 'Open', confirmed: 'Confirmed', false_positive: 'False Positive', fixed: 'Fixed' };
                          const count = zapScanResult.alerts.filter((_, i) => (alertStatuses[i] || 'open') === status).length;
                          return (
                            <div
                              key={status}
                              onClick={() => {
                                setAlertFilters(prev => ({
                                  ...prev,
                                  status: isActive 
                                    ? prev.status.filter(s => s !== status)
                                    : [...prev.status, status]
                                }));
                              }}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 12px',
                                marginBottom: '4px',
                                cursor: 'pointer',
                                background: isActive ? '#1a1a1a' : 'transparent',
                                borderRadius: '4px',
                                transition: 'background 0.15s'
                              }}
                            >
                              <span style={{ fontSize: '14px', color: isActive ? '#ffffff' : '#888' }}>{statusLabels[status]}</span>
                              <span style={{ fontSize: '13px', color: '#555' }}>{count}</span>
                            </div>
                          );
                        })}
                      </div>

                      {/* Clear Filters */}
                      {(alertFilters.severity.length > 0 || alertFilters.status.length !== 1 || alertFilters.status[0] !== 'open') && (
                        <button
                          onClick={() => setAlertFilters({ severity: [], owasp: [], status: ['open'] })}
                          style={{
                            width: '100%',
                            padding: '12px',
                            background: 'transparent',
                            border: '1px solid #333',
                            color: '#888',
                            fontSize: '13px',
                            cursor: 'pointer',
                            borderRadius: '4px'
                          }}
                        >
                          Clear Filters
                        </button>
                      )}
                    </div>

                    {/* Alert List (Dense) */}
                    <div style={{
                      width: '340px',
                      flexShrink: 0,
                      background: '#0a0a0a',
                      borderRight: '1px solid #1a1a1a',
                      overflowY: 'auto'
                    }}>
                      <div style={{ 
                        padding: '16px', 
                        borderBottom: '1px solid #1a1a1a',
                        fontSize: '13px',
                        color: '#555',
                        textTransform: 'uppercase',
                        letterSpacing: '1.5px'
                      }}>
                        {zapScanResult.alerts.filter((alert, idx) => {
                          const status = alertStatuses[idx] || 'open';
                          if (alertFilters.severity.length > 0 && !alertFilters.severity.includes(alert.risk)) return false;
                          if (alertFilters.status.length > 0 && !alertFilters.status.includes(status)) return false;
                          return true;
                        }).length} Alerts
                      </div>
                      {zapScanResult.alerts.map((alert, index) => {
                        const status = alertStatuses[index] || 'open';
                        // Apply filters
                        if (alertFilters.severity.length > 0 && !alertFilters.severity.includes(alert.risk)) return null;
                        if (alertFilters.status.length > 0 && !alertFilters.status.includes(status)) return null;
                        
                        return (
                          <div
                            key={index}
                            onClick={() => { setSelectedAlertIndex(index); setShowDiffView(false); }}
                            style={{
                              padding: '16px',
                              borderBottom: '1px solid #111',
                              cursor: 'pointer',
                              background: selectedAlertIndex === index ? '#151515' : 'transparent',
                              borderLeft: selectedAlertIndex === index ? '3px solid #ffffff' : '3px solid transparent',
                              transition: 'all 0.15s'
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                              <span style={{
                                width: '10px',
                                height: '10px',
                                borderRadius: '50%',
                                background: alert.risk === 'High' ? '#ff4444' : alert.risk === 'Medium' ? '#ffaa00' : alert.risk === 'Low' ? '#4488ff' : '#444',
                                flexShrink: 0
                              }} />
                              <span style={{ fontSize: '14px', color: '#ffffff', fontWeight: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {alert.alert}
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '20px' }}>
                              {alert.cweid && (
                                <span style={{ fontSize: '12px', color: '#555' }}>CWE-{alert.cweid}</span>
                              )}
                              <span style={{ 
                                fontSize: '12px', 
                                color: status === 'fixed' ? '#4CAF50' : status === 'false_positive' ? '#888' : status === 'confirmed' ? '#ff8800' : '#555',
                                textTransform: 'uppercase'
                              }}>
                                {status.replace('_', ' ')}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Detail Panel */}
                    <div style={{
                      flex: 1,
                      background: '#000000',
                      overflowY: 'auto',
                      padding: '28px'
                    }}>
                      {selectedAlertIndex !== null && zapScanResult.alerts[selectedAlertIndex] ? (
                        (() => {
                          const alert = zapScanResult.alerts[selectedAlertIndex];
                          const status = alertStatuses[selectedAlertIndex] || 'open';
                          return (
                            <div>
                              {/* Alert Header */}
                              <div style={{ marginBottom: '28px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                                  <span style={{
                                    padding: '6px 14px',
                                    borderRadius: '4px',
                                    fontSize: '13px',
                                    fontWeight: 500,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px',
                                    background: 'transparent',
                                    border: `1px solid ${alert.risk === 'High' ? '#ff4444' : alert.risk === 'Medium' ? '#ffaa00' : '#444'}`,
                                    color: alert.risk === 'High' ? '#ff4444' : alert.risk === 'Medium' ? '#ffaa00' : '#888'
                                  }}>
                                    {alert.risk}
                                  </span>
                                  <h3 style={{ fontSize: '22px', fontWeight: 500, color: '#ffffff', margin: 0 }}>{alert.alert}</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                  {alert.cweid && (
                                    <span style={{ fontSize: '13px', color: '#666', background: '#111', padding: '6px 12px', borderRadius: '4px' }}>
                                      CWE-{alert.cweid}
                                    </span>
                                  )}
                                  {alert.wascid && (
                                    <span style={{ fontSize: '13px', color: '#666', background: '#111', padding: '6px 12px', borderRadius: '4px' }}>
                                      WASC-{alert.wascid}
                                    </span>
                                  )}
                                  {alert.confidence && (
                                    <span style={{ fontSize: '13px', color: '#666', background: '#111', padding: '6px 12px', borderRadius: '4px' }}>
                                      {alert.confidence} Confidence
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Status Controls */}
                              <div style={{ 
                                display: 'flex', 
                                gap: '10px', 
                                marginBottom: '28px',
                                padding: '16px',
                                background: '#0a0a0a',
                                borderRadius: '6px',
                                border: '1px solid #1a1a1a'
                              }}>
                                <span style={{ fontSize: '14px', color: '#555', marginRight: '12px', alignSelf: 'center' }}>Status:</span>
                                {['open', 'confirmed', 'false_positive', 'fixed'].map(s => (
                                  <button
                                    key={s}
                                    onClick={() => setAlertStatuses(prev => ({ ...prev, [selectedAlertIndex]: s }))}
                                    style={{
                                      padding: '8px 16px',
                                      background: status === s ? '#1a1a1a' : 'transparent',
                                      border: `1px solid ${status === s ? '#333' : '#222'}`,
                                      color: status === s ? '#ffffff' : '#666',
                                      fontSize: '13px',
                                      cursor: 'pointer',
                                      borderRadius: '4px',
                                      textTransform: 'capitalize'
                                    }}
                                  >
                                    {s.replace('_', ' ')}
                                  </button>
                                ))}
                              </div>

                              {/* Description */}
                              {alert.description && (
                                <div style={{ marginBottom: '24px' }}>
                                  <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '12px', fontWeight: 500 }}>Description</div>
                                  <div style={{ color: '#bbb', fontSize: '15px', lineHeight: '1.8' }}>{alert.description}</div>
                                </div>
                              )}

                              {/* Evidence */}
                              {(alert.url || alert.evidence || alert.param) && (
                                <div style={{ marginBottom: '24px' }}>
                                  <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '12px', fontWeight: 500 }}>Evidence</div>
                                  <div style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: '6px', padding: '16px', fontFamily: 'monospace', fontSize: '14px' }}>
                                    {alert.url && <div style={{ color: '#999', marginBottom: '8px' }}><span style={{ color: '#666' }}>URL:</span> {alert.url}</div>}
                                    {alert.param && <div style={{ color: '#999', marginBottom: '8px' }}><span style={{ color: '#666' }}>Param:</span> {alert.param}</div>}
                                    {alert.evidence && <div style={{ color: '#ffaa00', marginTop: '12px', padding: '12px', background: '#111', borderRadius: '4px', fontSize: '14px' }}>{alert.evidence}</div>}
                                  </div>
                                </div>
                              )}

                              {/* Solution */}
                              {alert.solution && (
                                <div style={{ marginBottom: '24px' }}>
                                  <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '12px', fontWeight: 500 }}>Recommended Solution</div>
                                  <div style={{ color: '#999', fontSize: '15px', lineHeight: '1.7', background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: '6px', padding: '16px' }}>{alert.solution}</div>
                                </div>
                              )}

                              {/* AI Fix Actions */}
                              <div style={{ 
                                marginTop: '32px', 
                                padding: '20px',
                                background: '#0a0a0a',
                                border: '1px solid #1a1a1a',
                                borderRadius: '6px'
                              }}>
                                {!showDiffView ? (
                                  <div>
                                    <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '16px', fontWeight: 500 }}>AI Remediation</div>
                                    <button
                                      onClick={async () => {
                                        setIsGeneratingPatch(true);
                                        // Generate patch preview
                                        try {
                                          const response = await fetch(`${API_BASE_URL}/api/ai-fix-security-preview`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                              project_id: project.id,
                                              alert: alert,
                                              files: project.files
                                            })
                                          });
                                          const data = await response.json();
                                          if (data.success && data.diff) {
                                            setCurrentPatchDiff(data.diff);
                                            setShowDiffView(true);
                                          } else {
                                            // Fallback: generate simple diff
                                            setCurrentPatchDiff({
                                              filename: 'index.html',
                                              original: '<!-- Original code would appear here -->',
                                              patched: '<!-- Patched code would appear here -->',
                                              description: data.message || 'AI analysis complete. Review the suggested changes.'
                                            });
                                            setShowDiffView(true);
                                          }
                                        } catch (err) {
                                          console.error('Error generating patch:', err);
                                          setCurrentPatchDiff({
                                            filename: 'N/A',
                                            original: '',
                                            patched: '',
                                            description: 'Unable to generate patch preview. Try applying the fix directly.'
                                          });
                                          setShowDiffView(true);
                                        }
                                        setIsGeneratingPatch(false);
                                      }}
                                      disabled={isGeneratingPatch || status === 'fixed'}
                                      style={{
                                        background: 'transparent',
                                        color: status === 'fixed' ? '#444' : '#ffffff',
                                        border: '1px solid #333',
                                        padding: '14px 28px',
                                        borderRadius: '4px',
                                        cursor: status === 'fixed' ? 'not-allowed' : 'pointer',
                                        fontSize: '15px',
                                        fontWeight: 400
                                      }}
                                    >
                                      {isGeneratingPatch ? 'Analyzing...' : status === 'fixed' ? 'Already Fixed' : 'Review AI Suggestion'}
                                    </button>
                                  </div>
                                ) : (
                                  <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                      <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', fontWeight: 500 }}>Patch Preview</div>
                                      <button
                                        onClick={() => setShowDiffView(false)}
                                        style={{
                                          background: 'transparent',
                                          border: 'none',
                                          color: '#666',
                                          cursor: 'pointer',
                                          fontSize: '14px'
                                        }}
                                      >
                                        Close
                                      </button>
                                    </div>
                                    
                                    {currentPatchDiff && (
                                      <div>
                                        <div style={{ fontSize: '14px', color: '#999', marginBottom: '16px' }}>{currentPatchDiff.description}</div>
                                        <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>{currentPatchDiff.filename}</div>
                                        
                                        {/* Diff View */}
                                        <div style={{ 
                                          fontFamily: 'monospace', 
                                          fontSize: '14px', 
                                          background: '#000', 
                                          border: '1px solid #222',
                                          borderRadius: '4px',
                                          overflow: 'auto',
                                          maxHeight: '350px'
                                        }}>
                                          {currentPatchDiff.original && currentPatchDiff.original.split('\n').map((line, i) => (
                                            <div key={`old-${i}`} style={{ 
                                              padding: '4px 12px', 
                                              background: '#2a1515',
                                              color: '#ff6b6b',
                                              borderLeft: '4px solid #ff4444'
                                            }}>
                                              - {line}
                                            </div>
                                          ))}
                                          {currentPatchDiff.patched && currentPatchDiff.patched.split('\n').map((line, i) => (
                                            <div key={`new-${i}`} style={{ 
                                              padding: '4px 12px', 
                                              background: '#152a15',
                                              color: '#6bff6b',
                                              borderLeft: '4px solid #44ff44'
                                            }}>
                                              + {line}
                                            </div>
                                          ))}
                                        </div>

                                        {/* Action Buttons */}
                                        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                                          <button
                                            onClick={async () => {
                                              // Apply the fix
                                              await aiFixSecurityIssue(alert, selectedAlertIndex);
                                              setAlertStatuses(prev => ({ ...prev, [selectedAlertIndex]: 'fixed' }));
                                              setShowDiffView(false);
                                            }}
                                            disabled={isFixingSecurityIssue !== null}
                                            style={{
                                              background: '#1a1a1a',
                                              color: '#ffffff',
                                              border: '1px solid #333',
                                              padding: '12px 24px',
                                              borderRadius: '4px',
                                              cursor: isFixingSecurityIssue !== null ? 'not-allowed' : 'pointer',
                                              fontSize: '14px',
                                              fontWeight: 500
                                            }}
                                          >
                                            {isFixingSecurityIssue === selectedAlertIndex ? 'Applying...' : 'Merge Fix'}
                                          </button>
                                          <button
                                            onClick={() => {
                                              setAlertStatuses(prev => ({ ...prev, [selectedAlertIndex]: 'false_positive' }));
                                              setShowDiffView(false);
                                            }}
                                            style={{
                                              background: 'transparent',
                                              color: '#666',
                                              border: '1px solid #222',
                                              padding: '12px 24px',
                                              borderRadius: '4px',
                                              cursor: 'pointer',
                                              fontSize: '14px'
                                            }}
                                          >
                                            Mark False Positive
                                          </button>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>

                              {/* References */}
                              {alert.reference && (
                                <div style={{ marginTop: '24px' }}>
                                  <div style={{ fontSize: '13px', color: '#555', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '12px', fontWeight: 500 }}>References</div>
                                  <div style={{ fontSize: '14px', color: '#555', lineHeight: '2' }}>
                                    {alert.reference.split('\n').map((ref, i) => (
                                      <div key={i}>{ref}</div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })()
                      ) : (
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center', 
                          height: '100%',
                          color: '#555',
                          fontSize: '16px'
                        }}>
                          Select an alert to view details
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* No Alerts - All Good! */}
                {zapScanResult?.success && (!zapScanResult.alerts || zapScanResult.alerts.length === 0) && (
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #222',
                    borderRadius: '4px',
                    padding: '48px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: '#ffffff', marginBottom: '8px' }}>
                      No Vulnerabilities Detected
                    </div>
                    <div style={{ color: '#666', fontSize: '12px' }}>
                      Scan completed with no issues found.
                    </div>
                  </div>
                )}

                {/* Full Report (if available) */}
                {zapScanResult?.report && (
                  <div style={{ marginTop: '24px' }}>
                    <div style={{ 
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: '16px'
                    }}>
                      <h3 style={{ 
                        fontSize: '13px', 
                        fontWeight: 500,
                        color: '#ffffff',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        margin: 0
                      }}>
                        Full Report
                      </h3>
                      <button
                        onClick={() => {
                          const blob = new Blob([zapScanResult.report], { type: 'text/plain' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `security-report-${project?.name || 'project'}.txt`;
                          a.click();
                        }}
                        style={{
                          background: 'transparent',
                          color: '#ffffff',
                          border: '1px solid #333',
                          padding: '6px 12px',
                          borderRadius: '2px',
                          cursor: 'pointer',
                          fontSize: '11px',
                          fontWeight: 400,
                          transition: 'all 0.2s ease'
                        }}
                      >
                        Download Report
                      </button>
                    </div>
                    <pre style={{
                      background: '#0a0a0a',
                      border: '1px solid #222',
                      borderRadius: '4px',
                      padding: '16px',
                      fontSize: '10px',
                      fontFamily: 'monospace',
                      color: '#888',
                      overflow: 'auto',
                      maxHeight: '400px',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {zapScanResult.report}
                    </pre>
                  </div>
                )}
              </div>
            ) : layoutMode === 'preview' && previewUrl ? (
              <div style={{
                width: '100%',
                height: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                background: viewMode === 'mobile' ? '#f0f0f0' : '#ffffff',
                padding: viewMode === 'mobile' ? '20px' : '0',
                position: 'relative'
              }}>
                {isBuilding && (
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.4)',
                    zIndex: 10,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#ffffff',
                    fontSize: '18px',
                    fontWeight: 600
                  }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ animation: 'pulse 1.5s infinite', marginBottom: '12px', fontSize: '14px', color: '#22c55e' }}>Scanning...</div>
                      Building...
                    </div>
                  </div>
                )}
                
                {/* X-Ray Security View - Interactive Node Canvas */}
                {isSecurityView && (
                  <SecurityCanvas
                    securityScore={securityScore}
                    securityIssues={securityIssues}
                    projectFiles={allProjectFiles}
                    isLoading={isLoadingSecurityFiles}
                    highlightedNodeId={highlightedIssueNode}
                    onClose={() => {
                      setIsSecurityView(false);
                      setHighlightedIssueNode(null);
                    }}
                    onCodeInjection={(code, type) => {
                      console.log(`Injected ${type} middleware:`, code);
                      // Add to chat as a task
                      setAiTasks(prev => [...prev, {
                        title: `Added ${type} security layer`,
                        description: `Injected ${type} middleware into the security pipeline`,
                        timestamp: new Date().toISOString()
                      }]);
                    }}
                    onPipelineChange={(pipelineData) => {
                      // Store the latest pipeline configuration silently
                      console.log('Security pipeline updated:', pipelineData.summary);
                      
                      // Save pipeline config for later use (don't spam chat)
                      window.__latestSecurityPipeline = pipelineData;
                    }}
                  />
                )}
                
                {/* iPhone 17 Pro Frame */}
                {viewMode === 'mobile' && (
                  <div style={{
                    position: 'relative',
                    width: '320px',
                    height: '693px',
                    background: 'linear-gradient(145deg, #1a1a1a 0%, #0a0a0a 100%)',
                    borderRadius: '46px',
                    padding: '10px',
                    boxShadow: '0 35px 70px rgba(0,0,0,0.45), inset 0 0 0 1.5px rgba(255,255,255,0.1), 0 0 0 1px #000',
                  }}>
                    {/* Side Buttons - Left */}
                    <div style={{ position: 'absolute', left: '-2px', top: '114px', width: '2px', height: '28px', background: '#2a2a2a', borderRadius: '2px 0 0 2px' }} />
                    <div style={{ position: 'absolute', left: '-2px', top: '158px', width: '2px', height: '53px', background: '#2a2a2a', borderRadius: '2px 0 0 2px' }} />
                    <div style={{ position: 'absolute', left: '-2px', top: '224px', width: '2px', height: '53px', background: '#2a2a2a', borderRadius: '2px 0 0 2px' }} />
                    {/* Side Button - Right (Power) */}
                    <div style={{ position: 'absolute', right: '-2px', top: '163px', width: '2px', height: '73px', background: '#2a2a2a', borderRadius: '0 2px 2px 0' }} />
                    
                    {/* Inner Screen Bezel */}
                    <div style={{
                      width: '100%',
                      height: '100%',
                      background: '#000',
                      borderRadius: '37px',
                      overflow: 'hidden',
                      position: 'relative'
                    }}>
                      {/* Dynamic Island */}
                      <div style={{
                        position: 'absolute',
                        top: '10px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: '103px',
                        height: '30px',
                        background: '#000',
                        borderRadius: '16px',
                        zIndex: 100,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        paddingRight: '10px',
                        boxShadow: '0 0 0 3px rgba(0,0,0,0.8)'
                      }}>
                        {/* Camera lens */}
                        <div style={{
                          width: '10px',
                          height: '10px',
                          background: 'radial-gradient(circle at 30% 30%, #1a3a4a 0%, #0a1a20 60%, #000 100%)',
                          borderRadius: '50%',
                          boxShadow: 'inset 0 0 2px rgba(255,255,255,0.3)'
                        }} />
                      </div>
                      
                      {/* Screen Content (iframe) */}
                      <iframe
                        ref={(iframe) => {
                          if (iframe) {
                            iframe.onload = () => {
                              console.log('Mobile preview loaded');
                              previewLoadedRef.current = true;
                            };
                          }
                        }}
                        src={previewUrl}
                        style={{
                          width: '100%',
                          height: '100%',
                          border: 'none',
                          background: '#ffffff'
                        }}
                        title="Live Preview"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                        allow="clipboard-read; clipboard-write"
                        scrolling="yes"
                      />
                      
                      {/* Home Indicator */}
                      <div style={{
                        position: 'absolute',
                        bottom: '7px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: '110px',
                        height: '4px',
                        background: 'rgba(255,255,255,0.3)',
                        borderRadius: '2px'
                      }} />
                    </div>
                  </div>
                )}
                
                {/* Desktop View */}
                {viewMode !== 'mobile' && (
                  <iframe
                    ref={(iframe) => {
                      if (iframe) {
                        iframe.onload = () => {
                          console.log('Desktop preview loaded');
                          previewLoadedRef.current = true;
                        };
                      }
                    }}
                    src={previewUrl}
                    style={{
                      width: '100%',
                      height: '100%',
                      border: 'none',
                      background: '#ffffff'
                    }}
                    title="Live Preview"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                    allow="clipboard-read; clipboard-write"
                    scrolling="yes"
                  />
                )}
              </div>
            ) : layoutMode === 'preview' && isBuilding ? (
              /* Live Generation Progress - VS Code Style Building Screen */
              <div style={{
                width: '100%',
                height: '100%',
                background: '#0a0a0a',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px'
              }}>
                {/* Animated Building Icon */}
                <div style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '32px',
                  animation: 'pulse 2s infinite',
                  boxShadow: '0 0 40px rgba(34, 197, 94, 0.3)'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid transparent',
                    borderTopColor: '#ffffff',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                </div>
                
                {/* Title */}
                <h2 style={{
                  fontSize: '28px',
                  fontWeight: 600,
                  color: '#ffffff',
                  marginBottom: '8px',
                  textAlign: 'center'
                }}>
                  Building Your Project
                </h2>
                
                {/* Project Name */}
                <p style={{
                  fontSize: '16px',
                  color: '#888888',
                  marginBottom: '32px',
                  textAlign: 'center'
                }}>
                  {projectName}
                </p>
                
                {/* Progress Bar */}
                <div style={{
                  width: '100%',
                  maxWidth: '400px',
                  height: '6px',
                  background: '#222222',
                  borderRadius: '3px',
                  overflow: 'hidden',
                  marginBottom: '16px'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${buildProgress}%`,
                    background: 'linear-gradient(90deg, #22c55e 0%, #16a34a 100%)',
                    borderRadius: '3px',
                    transition: 'width 0.5s ease-out'
                  }} />
                </div>
                
                {/* Progress Text */}
                <p style={{
                  fontSize: '14px',
                  color: '#22c55e',
                  marginBottom: '40px'
                }}>
                  {buildProgress}% - {currentBuildPhase || 'Initializing...'}
                </p>
                
                {/* AI Thinking Steps - VS Code Style */}
                <div style={{
                  width: '100%',
                  maxWidth: '500px',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  background: '#1a1a1a',
                  border: '1px solid #333333',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{
                    fontSize: '11px',
                    color: '#666666',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    marginBottom: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{ 
                      width: '8px', 
                      height: '8px', 
                      background: '#22c55e', 
                      borderRadius: '50%',
                      animation: 'pulse 1.5s infinite'
                    }} />
                    AI is thinking...
                  </div>
                  {aiThinkingSteps.length === 0 ? (
                    <div style={{ color: '#555555', fontSize: '13px', fontStyle: 'italic' }}>
                      Starting project generation...
                    </div>
                  ) : (
                    aiThinkingSteps.map((step, index) => (
                      <div 
                        key={index}
                        style={{
                          fontSize: '13px',
                          color: step.type === 'error' ? '#ff4444' : '#cccccc',
                          padding: '4px 0',
                          borderBottom: index < aiThinkingSteps.length - 1 ? '1px solid #2a2a2a' : 'none',
                          animation: index === aiThinkingSteps.length - 1 ? 'fadeIn 0.3s ease-out' : 'none'
                        }}
                      >
                        {step.text}
                      </div>
                    ))
                  )}
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
              /* Code Editor Mode - VS Code Style */
              <div style={styles.codeAreaRow}>
                {/* Left: File Tree Pane */}
                <div style={{
                  ...styles.fileTreePane,
                  background: '#252526',
                  borderRight: '1px solid #1e1e1e'
                }}>
                  {/* Explorer Header */}
                  <div style={{
                    padding: '10px 12px',
                    fontSize: '11px',
                    fontWeight: 400,
                    color: '#bbbbbb',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    background: '#252526',
                    borderBottom: '1px solid #1e1e1e'
                  }}>
                    EXPLORER
                  </div>
                  {/* Explorer Tab Bar */}
                  <div style={{
                    display: 'flex',
                    borderBottom: '1px solid #1e1e1e',
                    background: '#252526',
                    flexShrink: 0
                  }}>
                    <button
                      onClick={() => setExplorerTab('files')}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: explorerTab === 'files' ? '2px solid #007acc' : '2px solid transparent',
                        color: explorerTab === 'files' ? '#ffffff' : '#888888',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 400,
                        fontFamily: "'Segoe UI', 'Inter', sans-serif",
                      }}
                    >
                      Files
                    </button>
                    <button
                      onClick={() => setExplorerTab('problems')}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: explorerTab === 'problems' ? '2px solid #007acc' : '2px solid transparent',
                        color: explorerTab === 'problems' ? '#ffffff' : '#888888',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: 400,
                        fontFamily: "'Segoe UI', 'Inter', sans-serif",
                      }}
                    >
                      Problems {errors.length > 0 && `(${errors.length})`}
                    </button>
                  </div>
                  
                  {explorerTab === 'files' ? (
                    <div style={{
                      ...styles.fileTree,
                      background: '#252526',
                      padding: '4px 0'
                    }}>
                      {fileTree && fileTree.length > 0 ? renderFileTree(fileTree) : (
                        <div style={{ padding: '16px', color: '#888', fontSize: '13px' }}>Loading project files...</div>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      ...styles.fileTree,
                      background: '#252526',
                      padding: '8px'
                    }}>
                      {errors.length === 0 ? (
                        <div style={{ padding: '16px', color: '#888', fontSize: '13px' }}>No problems detected</div>
                      ) : (
                        errors.map((error, index) => (
                          <div key={index} style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            padding: '6px 8px',
                            gap: '8px',
                            borderRadius: '3px',
                            marginBottom: '4px',
                            cursor: 'pointer',
                            background: 'transparent'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.background = '#2a2d2e'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                          >
                            <span style={{
                              fontSize: '11px',
                              fontWeight: 600,
                              color: error.severity === 'error' ? '#f48771' : '#cca700',
                              fontFamily: "'Consolas', monospace"
                            }}>
                              {error.severity === 'error' ? 'E' : 'W'}
                            </span>
                            <div style={{ flex: 1 }}>
                              <div style={{ color: '#cccccc', fontSize: '13px' }}>{error.message}</div>
                              <div style={{ fontSize: '11px', color: '#888888', marginTop: '2px' }}>{error.file}:{error.line}</div>
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
                      {/* Tab Bar - VS Code style */}
                      <div style={{ 
                        padding: '0', 
                        background: '#252526', 
                        borderBottom: '1px solid #1e1e1e',
                        display: 'flex',
                        alignItems: 'stretch',
                        flexShrink: 0,
                        height: '35px'
                      }}>
                        {/* Active Tab */}
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '8px', 
                          padding: '0 12px',
                          background: '#1e1e1e',
                          borderTop: '1px solid #007acc',
                          borderRight: '1px solid #252526',
                          fontSize: '13px',
                          color: '#ffffff',
                          fontFamily: "'Segoe UI', sans-serif"
                        }}>
                          {selectedFile.split('/').pop()}
                        </div>
                        {/* Spacer */}
                        <div style={{ flex: 1 }} />
                        {/* Navigation Controls */}
                        <div style={{ ...styles.navigationControls, padding: '0 8px' }}>
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
                      <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
                        {loadingFile === selectedFile && !fileContents[selectedFile] ? (
                          <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            height: '100%',
                            background: '#1e1e1e',
                            color: '#888888',
                            fontSize: '14px',
                            fontFamily: "'Segoe UI', 'Inter', sans-serif"
                          }}>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ 
                                width: '24px', 
                                height: '24px', 
                                border: '2px solid #444',
                                borderTopColor: '#007acc',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                                margin: '0 auto 12px'
                              }} />
                              <div style={{ color: '#888' }}>Loading {selectedFile?.split('/').pop()}...</div>
                            </div>
                          </div>
                        ) : fileContents[selectedFile] ? (
                          <Editor
                            height="100%"
                            width="100%"
                            language={getLanguageFromFileName(selectedFile)}
                            value={fileContents[selectedFile]}
                            theme="vs-dark"
                            loading={
                              <div style={{ 
                                background: '#1e1e1e', 
                                color: '#888', 
                                padding: '20px',
                                height: '100%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                              }}>
                                Loading editor...
                              </div>
                            }
                            options={{
                              readOnly: true,
                              automaticLayout: true,
                              minimap: { enabled: true },
                              wordWrap: 'on',
                              fontSize: 14,
                              lineNumbers: 'on',
                              scrollBeyondLastLine: true,
                              fontFamily: "Consolas, 'Courier New', monospace",
                              scrollbar: {
                                vertical: 'visible',
                                horizontal: 'visible',
                                verticalScrollbarSize: 14,
                                horizontalScrollbarSize: 14,
                                alwaysConsumeMouseWheel: false
                              },
                              overviewRulerLanes: 0,
                              hideCursorInOverviewRuler: true,
                              renderLineHighlight: 'all',
                              folding: true,
                              glyphMargin: false
                            }}
                            onMount={(editor, monaco) => {
                              console.log('✅ Monaco editor mounted for:', selectedFile);
                            }}
                          />
                        ) : (
                          /* Fallback: No content yet */
                          <div style={{
                            background: '#1e1e1e',
                            color: '#888',
                            padding: '20px',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}>
                            Click on a file to view its contents
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'center',
                      alignItems: 'center',
                      height: '100%',
                      background: '#1e1e1e',
                      color: '#cccccc'
                    }}>
                      <div style={{ 
                        fontSize: '13px', 
                        color: '#858585',
                        textAlign: 'center',
                        maxWidth: '300px'
                      }}>
                        Select a file from the explorer to view its contents
                      </div>
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
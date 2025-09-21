import React, { useState, useEffect, useRef } from 'react';
import MonacoEditor from '@monaco-editor/react';

// Inline styles - moved from MonacoProjectEditor.css
const styles = {
  monacoProjectEditor: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: '#1e1e1e',
    color: '#d4d4d4',
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column'
  },
  editorHeader: {
    background: '#2d2d30',
    borderBottom: '1px solid #3e3e42',
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
    color: '#9cdcfe',
    fontSize: '12px',
    background: 'rgba(156, 220, 254, 0.1)',
    padding: '2px 6px',
    borderRadius: '4px'
  },
  buildingIndicator: {
    color: '#ffcc02',
    fontSize: '12px',
    background: 'rgba(255, 204, 2, 0.1)',
    padding: '2px 6px',
    borderRadius: '4px',
    animation: 'pulse 1.5s infinite'
  },
  editorActions: {
    display: 'flex',
    gap: '8px'
  },
  layoutToggles: {
    display: 'flex',
    gap: '4px',
    marginRight: '12px',
    padding: '4px',
    background: '#2d2d30',
    borderRadius: '6px'
  },
  btnLayoutToggle: {
    background: 'transparent',
    border: 'none',
    color: '#cccccc',
    padding: '6px 10px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s'
  },
  btnLayoutToggleActive: {
    background: '#0e639c',
    color: 'white'
  },
  btnEditorAction: {
    background: '#0e639c',
    color: 'white',
    border: 'none',
    padding: '6px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '4px'
  },
  btnEditorActionPreview: {
    background: '#16825d'
  },
  btnEditorActionStop: {
    background: '#d73027'
  },
  btnEditorActionClose: {
    background: '#c5524a'
  },
  editorLayout: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden'
  },
  editorSidebar: {
    width: '320px',
    background: '#252526',
    borderRight: '1px solid #3e3e42',
    display: 'flex',
    flexDirection: 'column',
    transition: 'width 0.3s ease'
  },
  editorSidebarCollapsed: {
    width: '48px'
  },
  sidebarHeader: {
    background: '#2d2d30',
    borderBottom: '1px solid #3e3e42',
    padding: '8px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  sidebarTabs: {
    display: 'flex',
    gap: '4px'
  },
  sidebarTab: {
    background: 'transparent',
    color: '#cccccc',
    border: 'none',
    padding: '6px 8px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontSize: '11px',
    transition: 'all 0.2s'
  },
  sidebarTabActive: {
    background: '#094771',
    color: '#ffffff'
  },
  sidebarToggle: {
    background: 'transparent',
    color: '#cccccc',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    transition: 'all 0.2s'
  },
  sidebarContent: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px'
  },
  fileTree: {
    fontSize: '13px'
  },
  loadingFiles: {
    color: '#9cdcfe',
    textAlign: 'center',
    padding: '20px',
    fontStyle: 'italic'
  },
  fileTreeItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 6px',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'all 0.2s',
    marginBottom: '1px'
  },
  fileTreeItemSelected: {
    background: '#094771',
    color: '#ffffff'
  },
  fileIcon: {
    fontSize: '14px',
    width: '16px',
    textAlign: 'center',
    flexShrink: 0
  },
  fileName: {
    flex: 1,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis'
  },
  editorMain: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  editorContentContainer: {
    display: 'flex',
    height: '100%',
    overflow: 'hidden'
  },
  monacoContainer: {
    flex: 1,
    overflow: 'hidden'
  },
  monacoContainerWithPreview: {
    width: '50%',
    borderRight: '1px solid #3c3c3c'
  },
  previewContainer: {
    width: '50%',
    display: 'flex',
    flexDirection: 'column',
    background: '#1e1e1e'
  },
  previewHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    background: '#2d2d30',
    borderBottom: '1px solid #3c3c3c',
    minHeight: '32px'
  },
  previewTitle: {
    color: '#cccccc',
    fontSize: '13px',
    fontWeight: 500
  },
  previewContent: {
    flex: 1,
    background: 'white',
    position: 'relative'
  },
  previewIframe: {
    width: '100%',
    height: '100%',
    border: 'none',
    background: 'white'
  },
  previewLoading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#cccccc',
    background: '#1e1e1e'
  },
  previewError: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#f48771',
    background: '#1e1e1e',
    flexDirection: 'column',
    gap: '8px'
  },
  chatContainer: {
    width: '50%',
    minWidth: '300px',
    display: 'flex',
    flexDirection: 'column',
    background: '#1e1e1e',
    borderRight: '1px solid #3c3c3c'
  },
  chatHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    background: '#2d2d30',
    borderBottom: '1px solid #3c3c3c',
    minHeight: '32px'
  },
  chatTitle: {
    color: '#cccccc',
    fontSize: '13px',
    fontWeight: 500
  },
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '12px',
    background: '#1e1e1e'
  },
  chatMessage: {
    marginBottom: '16px',
    padding: '12px',
    borderRadius: '8px',
    background: '#2d2d30'
  },
  chatMessageUser: {
    background: '#0e639c',
    marginLeft: '20px'
  },
  chatMessageAssistant: {
    background: '#2d2d30',
    marginRight: '20px'
  },
  chatMessageError: {
    background: '#5d2d2d',
    borderLeft: '3px solid #f48771'
  },
  messageContent: {
    color: '#cccccc',
    lineHeight: 1.4,
    whiteSpace: 'pre-wrap'
  },
  chatInputContainer: {
    display: 'flex',
    padding: '12px',
    background: '#2d2d30',
    borderTop: '1px solid #3c3c3c',
    gap: '8px'
  },
  chatInput: {
    flex: 1,
    background: '#1e1e1e',
    border: '1px solid #3c3c3c',
    color: '#cccccc',
    padding: '8px 12px',
    borderRadius: '4px',
    fontSize: '13px',
    outline: 'none'
  },
  chatSend: {
    background: '#0e639c',
    border: 'none',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'background-color 0.2s',
    minWidth: '40px'
  },
  editorTerminal: {
    height: '250px',
    background: '#1e1e1e',
    borderTop: '1px solid #3e3e42',
    display: 'flex',
    flexDirection: 'column',
    transition: 'height 0.3s ease'
  },
  editorTerminalCollapsed: {
    height: '32px'
  },
  terminalHeader: {
    background: '#2d2d30',
    borderBottom: '1px solid #3e3e42',
    padding: '6px 12px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '32px'
  },
  terminalTitle: {
    color: '#ffffff',
    fontSize: '12px',
    fontWeight: 500
  },
  terminalContent: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 12px',
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    fontSize: '12px',
    lineHeight: 1.4,
    background: '#1e1e1e'
  },
  terminalLine: {
    marginBottom: '2px',
    display: 'flex',
    gap: '8px'
  },
  terminalTimestamp: {
    color: '#666',
    fontSize: '10px',
    flexShrink: 0
  },
  terminalMessage: {
    flex: 1,
    wordBreak: 'break-word'
  },
  terminalSuccess: {
    color: '#73c991'
  },
  terminalError: {
    color: '#f44747'
  },
  terminalWarning: {
    color: '#ffcc02'
  },
  terminalInfo: {
    color: '#d4d4d4'
  },
  noFileSelected: {
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#1e1e1e'
  },
  welcomeScreen: {
    textAlign: 'center',
    maxWidth: '600px',
    padding: '40px'
  },
  welcomeScreenH2: {
    color: '#ffffff',
    marginBottom: '16px',
    fontSize: '24px'
  },
  welcomeScreenP: {
    color: '#cccccc',
    marginBottom: '12px',
    lineHeight: 1.5
  }
};

const MonacoProjectEditor = ({ project, onClose }) => {
  const [fileTree, setFileTree] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContents, setFileContents] = useState({});
  const [terminalOutput, setTerminalOutput] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [terminalCollapsed, setTerminalCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState('files');
  const [openTabs, setOpenTabs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [currentDirectory, setCurrentDirectory] = useState('/');
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [layoutMode, setLayoutMode] = useState('editor'); // 'editor', 'preview', 'chat', 'split'
  const editorRef = useRef(null);
  const chatEndRef = useRef(null);
  const terminalRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (project?.name) {
      initializeProject();
      setupWebSocket();
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [project]);

  const setupWebSocket = () => {
    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/project/${project.name}`);
      wsRef.current = ws;
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'terminal_output':
            addTerminalOutput(data.message, data.level || 'info');
            break;
          case 'file_changed':
            if (data.file_path && fileContents[data.file_path]) {
              reloadFile(data.file_path);
            }
            break;
          case 'error_detected':
            setErrors(prev => [...prev, data.error]);
            addTerminalOutput(`❌ Error: ${data.error.message}`, 'error');
            break;
          case 'preview_ready':
            setPreviewUrl(data.url);
            addTerminalOutput(`🌐 Preview available: ${data.url}`, 'success');
            break;
          case 'file_creation_start':
            addTerminalOutput(data.message, 'info');
            setIsCreatingProject(true);
            break;
          case 'file_created':
            // Add file to file tree (will trigger re-render)
            loadProjectFiles();
            addTerminalOutput(`📄 Created ${data.file_path}`, 'info');
            break;
          case 'file_content_update':
            // Show real-time typing effect in Monaco Editor
            if (data.file_path && selectedFile === data.file_path) {
              setFileContents(prev => ({
                ...prev,
                [data.file_path]: data.content
              }));
            }
            // Auto-open first created file
            if (data.file_path && !selectedFile && data.content) {
              setSelectedFile(data.file_path);
              setFileContents(prev => ({
                ...prev,
                [data.file_path]: data.content
              }));
            }
            break;
          case 'file_creation_complete':
            addTerminalOutput(data.message, 'success');
            setIsCreatingProject(false);
            loadProjectFiles(); // Refresh file tree
            break;
        }
      };
      
      ws.onopen = () => {
        addTerminalOutput('🔗 Connected to project server', 'success');
      };
      
      ws.onclose = () => {
        addTerminalOutput('🔌 Disconnected from project server', 'warning');
      };
    } catch (error) {
      addTerminalOutput(`❌ WebSocket connection failed: ${error.message}`, 'error');
    }
  };

  const initializeProject = async () => {
    addTerminalOutput('🚀 Initializing project workspace...', 'info');
    
    try {
      // Create project structure
      await createProjectStructure();
      
      // Load file tree
      await loadProjectFiles();
      
      // Install dependencies
      await installDependencies();
      
      addTerminalOutput('✅ Project initialized successfully!', 'success');
    } catch (error) {
      addTerminalOutput(`❌ Project initialization failed: ${error.message}`, 'error');
    }
  };

  const createProjectStructure = async () => {
    addTerminalOutput('📁 Creating project structure...', 'info');
    
    try {
      const response = await fetch('/api/create-project-structure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          idea: project.description,
          tech_stack: project.tech_stack
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput('✅ Project structure created', 'success');
        
        // Log created files
        data.files_created?.forEach(file => {
          addTerminalOutput(`📄 Created: ${file}`, 'info');
        });
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      addTerminalOutput(`❌ Failed to create structure: ${error.message}`, 'error');
      throw error;
    }
  };

  const loadProjectFiles = async () => {
    try {
      const response = await fetch(`/api/project-file-tree?project_name=${encodeURIComponent(project.name)}`);
      const data = await response.json();
      
      if (data.success && data.file_tree) {
        setFileTree(data.file_tree);
        
        // Auto-open main files
        const mainFiles = ['App.jsx', 'index.html', 'main.py', 'package.json', 'README.md'];
        for (const mainFile of mainFiles) {
          const foundFile = findFileInTree(data.file_tree, mainFile);
          if (foundFile) {
            await openFile(foundFile);
            break;
          }
        }
      } else {
        addTerminalOutput(`❌ Failed to load files: ${data.error}`, 'error');
      }
    } catch (error) {
      addTerminalOutput(`❌ Error loading project: ${error.message}`, 'error');
    }
  };

  const installDependencies = async () => {
    addTerminalOutput('📦 Installing dependencies...', 'info');
    
    try {
      const response = await fetch('/api/install-dependencies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          tech_stack: project.tech_stack
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput('✅ Dependencies installed successfully', 'success');
      } else {
        addTerminalOutput(`⚠️ Dependency installation issues: ${data.error}`, 'warning');
      }
    } catch (error) {
      addTerminalOutput(`❌ Failed to install dependencies: ${error.message}`, 'error');
    }
  };

  const findFileInTree = (tree, fileName) => {
    if (!tree || !Array.isArray(tree)) return null;
    
    for (const item of tree) {
      if (item.type === 'file' && item.name === fileName) {
        return item;
      }
      if (item.type === 'dir' && item.children) {
        const found = findFileInTree(item.children, fileName);
        if (found) return found;
      }
    }
    return null;
  };

  const openFile = async (file) => {
    if (file.type !== 'file') return;

    try {
      const response = await fetch(`/api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent(file.path)}`);
      const data = await response.json();
      
      if (data.success) {
        setFileContents(prev => ({
          ...prev,
          [file.path]: data.content
        }));
        
        setSelectedFile(file);
        
        // Add to open tabs if not already open
        if (!openTabs.find(tab => tab.path === file.path)) {
          setOpenTabs(prev => [...prev, file]);
        }
        
        addTerminalOutput(`📄 Opened: ${file.path}`, 'info');
      } else {
        addTerminalOutput(`❌ Failed to open ${file.path}: ${data.error}`, 'error');
      }
    } catch (error) {
      addTerminalOutput(`❌ Error opening file: ${error.message}`, 'error');
    }
  };

  const saveFile = async (filePath, content) => {
    try {
      const response = await fetch('/api/save-project-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          file_path: filePath,
          content: content
        })
      });
      
      const data = await response.json();
      if (data.success) {
        addTerminalOutput(`💾 Saved: ${filePath}`, 'success');
        
        setFileContents(prev => ({
          ...prev,
          [filePath]: content
        }));
        
        // Auto-check for errors after save
        setTimeout(() => checkForErrors(), 1000);
      } else {
        addTerminalOutput(`❌ Failed to save ${filePath}: ${data.error}`, 'error');
      }
    } catch (error) {
      addTerminalOutput(`❌ Error saving file: ${error.message}`, 'error');
    }
  };

  const runProject = async () => {
    if (isRunning) return;
    
    setIsRunning(true);
    setIsBuilding(true);
    addTerminalOutput('🚀 Building and starting project...', 'info');
    
    try {
      const response = await fetch('/api/run-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          tech_stack: project.tech_stack
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput('✅ Project started successfully!', 'success');
        if (data.preview_url) {
          setPreviewLoading(true);
          setPreviewUrl(data.preview_url);
        }
        setIsBuilding(false);
        
        // Start monitoring
        startErrorMonitoring();
      } else {
        addTerminalOutput(`❌ Failed to start project: ${data.error}`, 'error');
        setIsBuilding(false);
        
        // Try to auto-fix build errors
        if (data.errors && data.errors.length > 0) {
          await autoFixErrors(data.errors);
        }
      }
    } catch (error) {
      addTerminalOutput(`❌ Error running project: ${error.message}`, 'error');
      setIsBuilding(false);
    } finally {
      setIsRunning(false);
    }
  };

  const stopProject = async () => {
    try {
      const response = await fetch('/api/stop-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput('🛑 Project stopped', 'info');
        setPreviewUrl(null);
        setPreviewLoading(false);
        setIsBuilding(false);
      }
    } catch (error) {
      addTerminalOutput(`❌ Error stopping project: ${error.message}`, 'error');
    }
  };

  // AI Chat Functions
  const sendChatMessage = async () => {
    if (!chatInput.trim() || isAiThinking) return;
    
    const userMessage = {
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date().toLocaleTimeString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsAiThinking(true);
    
    try {
      const response = await fetch('/api/ai-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          message: userMessage.content,
          file_context: selectedFile ? {
            path: selectedFile.path,
            content: fileContents[selectedFile.path] || ''
          } : null,
          file_tree: fileTree
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        const aiMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toLocaleTimeString(),
          actions: data.actions || []
        };
        
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Apply any file changes suggested by AI
        if (data.file_changes) {
          await applyAiFileChanges(data.file_changes);
        }
      } else {
        const errorMessage = {
          role: 'assistant',
          content: `Sorry, I encountered an error: ${data.error}`,
          timestamp: new Date().toLocaleTimeString(),
          isError: true
        };
        setChatMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I couldn't process your request: ${error.message}`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
    
    setIsAiThinking(false);
  };

  const applyAiFileChanges = async (fileChanges) => {
    for (const change of fileChanges) {
      if (change.type === 'modify' && change.path && change.content) {
        // Update file content in editor
        setFileContents(prev => ({
          ...prev,
          [change.path]: change.content
        }));
        
        // Save the file
        await saveFile(change.path, change.content);
        
        addTerminalOutput(`✏️ AI updated file: ${change.path}`, 'success');
      } else if (change.type === 'create' && change.path && change.content) {
        // Create new file
        await createNewFile(change.path, change.content);
        addTerminalOutput(`📝 AI created file: ${change.path}`, 'success');
      }
    }
    
    // Refresh file tree to show changes
    await loadProjectFiles();
  };

  const createNewFile = async (filePath, content) => {
    try {
      const response = await fetch('/api/create-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          file_path: filePath,
          content: content
        })
      });
      
      if (response.ok) {
        // Add to file contents
        setFileContents(prev => ({
          ...prev,
          [filePath]: content
        }));
      }
    } catch (error) {
      addTerminalOutput(`❌ Error creating file: ${error.message}`, 'error');
    }
  };

  const autoFixErrors = async (errorList) => {
    addTerminalOutput('🔧 Auto-fixing detected errors...', 'info');
    
    try {
      const response = await fetch('/api/auto-fix-errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          errors: errorList,
          tech_stack: project.tech_stack
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput('✅ Errors fixed automatically!', 'success');
        
        // Reload modified files
        if (data.files_modified) {
          for (const filePath of data.files_modified) {
            await reloadFile(filePath);
          }
        }
        
        // Try running again after a delay
        setTimeout(() => {
          addTerminalOutput('🔄 Retrying project build...', 'info');
          runProject();
        }, 2000);
      } else {
        addTerminalOutput(`❌ Auto-fix failed: ${data.error}`, 'error');
        addTerminalOutput('💡 Please fix errors manually', 'info');
      }
    } catch (error) {
      addTerminalOutput(`❌ Auto-fix error: ${error.message}`, 'error');
    }
  };

  const checkForErrors = async () => {
    try {
      const response = await fetch(`/api/check-project-errors?project_name=${encodeURIComponent(project.name)}`);
      const data = await response.json();
      
      if (data.errors && data.errors.length > 0) {
        setErrors(data.errors);
        
        if (data.errors.length > 0) {
          addTerminalOutput(`⚠️ ${data.errors.length} errors detected`, 'warning');
        }
      } else {
        setErrors([]);
      }
    } catch (error) {
      console.error('Error checking for errors:', error);
    }
  };

  const startErrorMonitoring = () => {
    const interval = setInterval(checkForErrors, 3000);
    return () => clearInterval(interval);
  };

  const reloadFile = async (filePath) => {
    try {
      const response = await fetch(`/api/project-file-content?project_name=${encodeURIComponent(project.name)}&file_path=${encodeURIComponent(filePath)}`);
      const data = await response.json();
      
      if (data.success) {
        setFileContents(prev => ({
          ...prev,
          [filePath]: data.content
        }));
        
        addTerminalOutput(`🔄 Reloaded: ${filePath}`, 'info');
      }
    } catch (error) {
      addTerminalOutput(`❌ Error reloading file: ${error.message}`, 'error');
    }
  };

  const executeTerminalCommand = async (command) => {
    addTerminalOutput(`$ ${command}`, 'command');
    
    try {
      const response = await fetch('/api/execute-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: project.name,
          command: command,
          working_directory: currentDirectory
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        addTerminalOutput(data.output, 'output');
        
        // Update current directory if cd command
        if (command.startsWith('cd ')) {
          setCurrentDirectory(data.working_directory || currentDirectory);
        }
      } else {
        addTerminalOutput(data.error, 'error');
      }
    } catch (error) {
      addTerminalOutput(`Error: ${error.message}`, 'error');
    }
  };

  const addTerminalOutput = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalOutput(prev => [...prev, {
      message,
      type,
      timestamp,
      id: Date.now() + Math.random()
    }]);
    
    // Auto-scroll terminal
    setTimeout(() => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }, 100);
  };

  const closeTab = (tabToClose) => {
    setOpenTabs(prev => prev.filter(tab => tab.path !== tabToClose.path));
    
    if (selectedFile?.path === tabToClose.path) {
      const remainingTabs = openTabs.filter(tab => tab.path !== tabToClose.path);
      setSelectedFile(remainingTabs.length > 0 ? remainingTabs[0] : null);
    }
  };

  const getFileLanguage = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'json': 'json',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'dockerfile': 'dockerfile',
      'env': 'shell',
      'gitignore': 'ignore',
      'vue': 'vue'
    };
    return languageMap[ext] || 'plaintext';
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    const iconMap = {
      'js': '🟨',
      'jsx': '⚛️',
      'ts': '🔷',
      'tsx': '⚛️',
      'py': '🐍',
      'html': '🌐',
      'css': '🎨',
      'scss': '🎨',
      'json': '📄',
      'md': '📝',
      'yml': '⚙️',
      'yaml': '⚙️',
      'dockerfile': '🐳',
      'gitignore': '📋',
      'env': '🔐',
      'vue': '💚'
    };
    return iconMap[ext] || '📄';
  };

  const renderFileTree = (items, level = 0) => {
    if (!items || !Array.isArray(items)) return null;
    
    return items.map(item => (
      <div key={item.path} style={{ marginLeft: `${level * 16}px` }}>
        <div 
          className={`file-tree-item ${item.type} ${selectedFile?.path === item.path ? 'selected' : ''}`}
          onClick={() => item.type === 'file' ? openFile(item) : null}
        >
          <span className="file-icon">
            {item.type === 'directory' ? '📁' : getFileIcon(item.name)}
          </span>
          <span className="file-name">{item.name}</span>
        </div>
        
        {item.type === 'directory' && item.children && (
          <div className="file-tree-children">
            {renderFileTree(item.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 's') {
          e.preventDefault();
          if (selectedFile) {
            const content = fileContents[selectedFile.path] || '';
            saveFile(selectedFile.path, content);
          }
        }
      }
      
      if (e.key === 'F5') {
        e.preventDefault();
        runProject();
      }
      
      if (e.key === 'Escape' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        stopProject();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedFile, fileContents]);

  return (
    <div style={styles.monacoProjectEditor}>
      {/* Header */}
      <div style={styles.editorHeader}>
        <div style={styles.editorTitle}>
          <span style={styles.projectIcon}>🚀</span>
          <span style={styles.projectName}>{project.name}</span>
          <span style={styles.projectType}>({project.tech_stack?.join(', ') || 'Mixed'})</span>
          {isBuilding && <span style={styles.buildingIndicator}>⚡ Building...</span>}
        </div>
        
        <div style={styles.editorActions}>
          {/* Layout Toggle Buttons */}
          <div style={styles.layoutToggles}>
            <button 
              style={{
                ...styles.btnLayoutToggle,
                ...(layoutMode === 'editor' ? styles.btnLayoutToggleActive : {})
              }}
              onClick={() => setLayoutMode('editor')}
              title="Editor Only"
            >
              📝
            </button>
            <button 
              style={{
                ...styles.btnLayoutToggle,
                ...(layoutMode === 'chat' ? styles.btnLayoutToggleActive : {})
              }}
              onClick={() => setLayoutMode('chat')}
              title="AI Chat"
            >
              🤖
            </button>
            <button 
              style={{
                ...styles.btnLayoutToggle,
                ...(layoutMode === 'preview' ? styles.btnLayoutToggleActive : {}),
                ...(previewUrl ? {} : styles.btnLayoutToggleDisabled)
              }}
              onClick={() => setLayoutMode('preview')}
              title="Preview Only"
              disabled={!previewUrl}
            >
              🌐
            </button>
            <button 
              style={{
                ...styles.btnLayoutToggle,
                ...(layoutMode === 'split' ? styles.btnLayoutToggleActive : {})
              }}
              onClick={() => setLayoutMode('split')}
              title="Split View"
            >
              ⚡
            </button>
          </div>

          <button 
            style={{
              ...styles.btnEditorAction,
              ...(isRunning || isBuilding ? styles.btnEditorActionDisabled : {})
            }}
            onClick={runProject}
            disabled={isRunning || isBuilding}
            title="Run Project (F5)"
          >
            {isBuilding ? '⚡' : isRunning ? '⏳' : '▶️'} 
            {isBuilding ? 'Building' : 'Run'}
          </button>
          
          {previewUrl && (
            <button 
              style={{...styles.btnEditorAction, ...styles.btnEditorActionPreview}}
              onClick={() => window.open(previewUrl, '_blank')}
              title="Open Preview"
            >
              🌐 Preview
            </button>
          )}
          
          {(isRunning || previewUrl) && (
            <button 
              style={{...styles.btnEditorAction, ...styles.btnEditorActionStop}}
              onClick={stopProject}
              title="Stop Project (Ctrl+Esc)"
            >
              🛑 Stop
            </button>
          )}
          
          <button 
            style={{...styles.btnEditorAction, ...styles.btnEditorActionClose}}
            onClick={onClose}
            title="Close Editor"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Main Layout */}
      <div style={styles.editorLayout}>
        {/* Sidebar */}
        <div style={{
          ...styles.editorSidebar,
          ...(sidebarCollapsed ? styles.editorSidebarCollapsed : {})
        }}>
          <div style={styles.sidebarHeader}>
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
            
            <button 
              style={styles.sidebarToggle}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? '▶️' : '◀️'}
            </button>
          </div>
          
          <div style={styles.sidebarContent}>
            {activeTab === 'files' && (
              <div style={styles.fileTree}>
                {fileTree && fileTree.length > 0 ? renderFileTree(fileTree) : (
                  <div style={styles.loadingFiles}>Loading project files...</div>
                )}
              </div>
            )}
            
            {activeTab === 'errors' && (
              <div style={styles.errorsPanel}>
                {errors.length === 0 ? (
                  <div style={styles.noErrors}>✅ No problems detected</div>
                ) : (
                  errors.map((error, index) => (
                    <div key={index} style={styles.errorItem} onClick={() => {
                      // Jump to error location
                      if (error.file) {
                        const file = findFileInTree(fileTree, error.file);
                        if (file) openFile(file);
                      }
                    }}>
                      <div style={styles.errorSeverity}>{error.severity === 'error' ? '❌' : '⚠️'}</div>
                      <div style={styles.errorDetails}>
                        <div style={styles.errorMessage}>{error.message}</div>
                        <div style={styles.errorLocation}>{error.file}:{error.line}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Editor Area */}
        <div style={styles.editorMain}>
          {/* Tab Bar */}
          {openTabs.length > 0 && (
            <div style={styles.editorTabs}>
              {openTabs.map(tab => (
                <div 
                  key={tab.path}
                  style={{
                    ...styles.editorTab,
                    ...(selectedFile?.path === tab.path ? styles.editorTabActive : {})
                  }}
                  onClick={() => setSelectedFile(tab)}
                >
                  <span style={styles.tabIcon}>{getFileIcon(tab.name)}</span>
                  <span style={styles.tabName}>{tab.name}</span>
                  <button 
                    style={styles.tabClose}
                    onClick={(e) => {
                      e.stopPropagation();
                      closeTab(tab);
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
          
          {/* Dynamic Content Container */}
          <div style={{
            ...styles.editorContentContainer,
            ...styles[`layout${layoutMode.charAt(0).toUpperCase() + layoutMode.slice(1)}`]
          }}>
            {/* Chat Panel */}
            {(layoutMode === 'chat' || layoutMode === 'split') && (
              <div style={styles.chatContainer}>
                <div style={styles.chatHeader}>
                  <span style={styles.chatTitle}>🤖 AI Assistant</span>
                </div>
                <div style={styles.chatMessages}>
                  {chatMessages.map((message, index) => (
                    <div key={index} style={{
                      ...styles.chatMessage,
                      ...styles[`chatMessage${message.role.charAt(0).toUpperCase() + message.role.slice(1)}`],
                      ...(message.isError ? styles.chatMessageError : {})
                    }}>
                      <div style={styles.messageHeader}>
                        <span style={styles.messageRole}>
                          {message.role === 'user' ? '👤' : '🤖'} 
                          {message.role === 'user' ? 'You' : 'AI Assistant'}
                        </span>
                        <span style={styles.messageTime}>{message.timestamp}</span>
                      </div>
                      <div style={styles.messageContent}>{message.content}</div>
                      {message.actions && message.actions.length > 0 && (
                        <div style={styles.messageActions}>
                          {message.actions.map((action, actionIndex) => (
                            <button key={actionIndex} style={styles.actionButton}>
                              {action.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                  {isAiThinking && (
                    <div style={{...styles.chatMessage, ...styles.chatMessageAssistant, ...styles.chatMessageThinking}}>
                      <div style={styles.messageHeader}>
                        <span style={styles.messageRole}>🤖 AI Assistant</span>
                      </div>
                      <div style={styles.messageContent}>
                        <div style={styles.thinkingIndicator}>
                          <span>🧠</span> Thinking...
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
                <div style={styles.chatInputContainer}>
                  <input
                    type="text"
                    style={styles.chatInput}
                    placeholder="Ask AI to modify your code..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                    disabled={isAiThinking}
                  />
                  <button 
                    style={{
                      ...styles.chatSend,
                      ...(!chatInput.trim() || isAiThinking ? styles.chatSendDisabled : {})
                    }}
                    onClick={sendChatMessage}
                    disabled={!chatInput.trim() || isAiThinking}
                  >
                    📤
                  </button>
                </div>
              </div>
            )}

            {/* Monaco Editor */}
            {(layoutMode === 'editor' || layoutMode === 'split') && (
              <div style={{
                ...styles.monacoContainer,
                ...(layoutMode === 'split' ? styles.monacoContainerSplitMode : styles.monacoContainerFullWidth)
              }}>
                {selectedFile ? (
                  <MonacoEditor
                    ref={editorRef}
                    height="100%"
                    language={getFileLanguage(selectedFile.name)}
                    value={fileContents[selectedFile.path] || ''}
                    onChange={(value) => {
                      setFileContents(prev => ({
                        ...prev,
                        [selectedFile.path]: value
                      }));
                    }}
                    theme="vs-dark"
                    options={{
                      fontSize: 14,
                      minimap: { enabled: true },
                      automaticLayout: true,
                      lineNumbers: 'on',
                      renderWhitespace: 'selection',
                      folding: true,
                      bracketPairColorization: { enabled: true },
                      autoIndent: 'full',
                      formatOnType: true,
                      formatOnPaste: true,
                      quickSuggestions: true,
                      parameterHints: { enabled: true },
                      suggestOnTriggerCharacters: true,
                      acceptSuggestionOnEnter: 'on',
                      tabCompletion: 'on',
                      wordBasedSuggestions: true
                    }}
                  />
                ) : (
                  <div style={styles.noFileSelected}>
                    <div style={styles.welcomeScreen}>
                      <h2>🚀 {project.name}</h2>
                      <p>AI-generated {project.tech_stack?.join(' + ') || 'web'} application</p>
                      <p>Select a file from the tree to start editing</p>
                      
                      <div style={styles.quickActions}>
                        <button 
                          onClick={runProject} 
                          style={{
                            ...styles.btnWelcome,
                            ...(isBuilding ? styles.btnWelcomeDisabled : {})
                          }}
                          disabled={isBuilding}
                        >
                          {isBuilding ? '⚡ Building...' : '▶️ Run Project'}
                        </button>
                        {previewUrl && (
                          <button 
                            onClick={() => window.open(previewUrl, '_blank')}
                            style={styles.btnWelcome}
                          >
                            🌐 Open Preview
                          </button>
                        )}
                      </div>
                      
                      <div style={styles.keyboardShortcuts}>
                        <h4>Keyboard Shortcuts:</h4>
                        <div>Ctrl+S - Save file</div>
                        <div>F5 - Run project</div>
                        <div>Ctrl+Esc - Stop project</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Preview Panel */}
            {(layoutMode === 'preview' || (layoutMode === 'split' && previewUrl)) && previewUrl && (
              <div style={styles.previewContainer}>
                <div style={styles.previewHeader}>
                  <span style={styles.previewTitle}>🌐 Live Preview</span>
                  <div style={styles.previewActions}>
                    <button 
                      onClick={() => window.open(previewUrl, '_blank')}
                      style={styles.btnPreviewAction}
                      title="Open in new tab"
                    >
                      ↗️
                    </button>
                    <button 
                      onClick={() => document.getElementById('preview-iframe')?.contentWindow?.location.reload()}
                      style={styles.btnPreviewAction}
                      title="Refresh preview"
                    >
                      🔄
                    </button>
                  </div>
                </div>
                <div style={styles.previewContent}>
                  {previewLoading && (
                    <div style={styles.previewLoading}>
                      <div>🔄 Loading preview...</div>
                    </div>
                  )}
                  <iframe
                    id="preview-iframe"
                    src={previewUrl}
                    style={{
                      ...styles.previewIframe,
                      display: previewLoading ? 'none' : 'block'
                    }}
                    title="Application Preview"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-modals allow-popups"
                    onLoad={() => setPreviewLoading(false)}
                    onError={() => setPreviewLoading(false)}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Terminal */}
      <div style={{
        ...styles.editorTerminal,
        ...(terminalCollapsed ? styles.editorTerminalCollapsed : {})
      }}>
        <div style={styles.terminalHeader}>
          <span style={styles.terminalTitle}>🖥️ Terminal - {currentDirectory}</span>
          <div style={styles.terminalActions}>
            <button 
              style={styles.terminalAction}
              onClick={() => setTerminalOutput([])}
              title="Clear terminal"
            >
              🗑️
            </button>
            <button 
              style={styles.terminalToggle}
              onClick={() => setTerminalCollapsed(!terminalCollapsed)}
            >
              {terminalCollapsed ? '⬆️' : '⬇️'}
            </button>
          </div>
        </div>
        
        <div style={styles.terminalContent} ref={terminalRef}>
          {terminalOutput.map(output => (
            <div key={output.id} style={{
              ...styles.terminalLine,
              ...styles[`terminalLine${output.type.charAt(0).toUpperCase() + output.type.slice(1)}`]
            }}>
              <span style={styles.terminalTimestamp}>[{output.timestamp}]</span>
              <span style={styles.terminalMessage}>{output.message}</span>
            </div>
          ))}
        </div>
        
        <div style={styles.terminalInput}>
          <span style={styles.terminalPrompt}>{currentDirectory}$</span>
          <input 
            type="text"
            placeholder="Type command and press Enter..."
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                executeTerminalCommand(e.target.value);
                e.target.value = '';
              }
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default MonacoProjectEditor;
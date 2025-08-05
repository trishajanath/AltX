import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

const RepoAnalysisPage = () => {
  usePreventZoom();
  const [repoUrl, setRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState('');
  const [analysisLogs, setAnalysisLogs] = useState([]);
  const [modelType, setModelType] = useState('smart');
  const [deepScan, setDeepScan] = useState(true); // This state was declared but not used in the UI, keeping for logic.
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isAskingAI, setIsAskingAI] = useState(false);
  const [showAISidebar, setShowAISidebar] = useState(false);

  const navigate = useNavigate();

  // Clean and validate GitHub repository URLs
  const cleanRepositoryUrl = (url) => {
    try {
      // Remove common GitHub web interface paths
      let cleaned = url
        .replace(/\/tree\/[^\/]+.*$/, '') // Remove /tree/branch-name and everything after
        .replace(/\/blob\/[^\/]+.*$/, '') // Remove /blob/branch-name and everything after
        .replace(/\/commits.*$/, '')     // Remove /commits and everything after
        .replace(/\/issues.*$/, '')      // Remove /issues and everything after
        .replace(/\/pull.*$/, '')        // Remove /pull and everything after
        .replace(/\/releases.*$/, '')    // Remove /releases and everything after
        .replace(/\/wiki.*$/, '')        // Remove /wiki and everything after
        .replace(/\/settings.*$/, '')    // Remove /settings and everything after
        .replace(/\/$/, '');             // Remove trailing slash

      // Validate it's a GitHub URL
      const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+$/;
      if (!urlPattern.test(cleaned)) {
        return null;
      }
      return cleaned;
    } catch (e) {
      return null;
    }
  };

  const analyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    const cleanedUrl = cleanRepositoryUrl(repoUrl.trim());
    if (!cleanedUrl) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)');
      return;
    }

    setIsScanning(true);
    setError('');
    setAnalysisResult(null);
    setAnalysisLogs(['🔄 Starting repository analysis...']);
    setChatMessages([]); // Reset chat on new analysis

    try {
      const response = await fetch('http://localhost:8000/analyze-repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: cleanedUrl,
          model_type: modelType,
          deep_scan: deepScan
        }),
      });

      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setAnalysisLogs(prev => [...prev, `❌ Analysis failed: ${data.error}`]);
      } else {
        setAnalysisResult(data);
        setAnalysisLogs(prev => [...prev, '✅ Repository analysis completed successfully!']);

        if (data.warnings && data.warnings.length > 0) {
          data.warnings.forEach(warning => {
            setAnalysisLogs(prev => [...prev, `⚠️ Warning: ${warning}`]);
          });
        }

        const summary = generateAnalysisSummary(data);
        setChatMessages([{
          type: 'ai',
          message: summary,
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    } catch (err) {
      const errorMsg = 'Failed to analyze repository. Please check your connection and try again.';
      setError(errorMsg);
      setAnalysisLogs(prev => [...prev, `❌ ${errorMsg}`]);
      console.error('Repository analysis error:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const generateAnalysisSummary = (data) => {
    const score = data.overall_security_score || 0;
    const level = data.security_level || 'Unknown';
    const summary = data.security_summary || {};
    
    return `🔍 **Repository Analysis Complete**

📊 **Security Summary:**
• Repository: ${data.repository_info?.name || 'Unknown'}
• Security Score: ${score}/100 (${level})
• Language: ${data.repository_info?.language || 'Unknown'}

🔍 **Scan Results:**
• Files Scanned: ${summary.total_files_scanned || 0}
• Directories Skipped: ${data.file_security_scan?.directories_skipped || 0} (build/dependency dirs)
• Secrets Found: ${summary.secrets_found || 0} 
• Static Issues: ${summary.static_issues_found || 0}
• Vulnerable Dependencies: ${summary.vulnerable_dependencies || 0}
• Code Quality Issues: ${summary.code_quality_issues || 0}

📁 **File Management:**
• Excluded Directories: ${data.file_security_scan?.excluded_directories?.length || 0}
• GitIgnore Recommendations: ${data.file_security_scan?.gitignore_recommendations?.length || 0}

💡 **Ready to answer specific questions about this repository analysis!**`;
  };

  const askAI = async () => {
    if (!currentQuestion.trim() || !analysisResult) return;

    setIsAskingAI(true);
    const userMessage = {
      type: 'user',
      message: currentQuestion,
      timestamp: new Date().toLocaleTimeString()
    };
    
    // Add user message and clear input immediately
    setChatMessages(prev => [...prev, userMessage]);
    const questionToAsk = currentQuestion;
    setCurrentQuestion('');

    try {
      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: questionToAsk,
          context: 'repo_analysis',
          model_type: modelType,
          history: [...chatMessages, userMessage] // Send the latest history
        }),
      });

      const data = await response.json();
      
      const aiMessage = {
        type: 'ai',
        message: data.response || 'Sorry, I could not process your question.',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('AI chat error:', err);
      const errorMessage = {
        type: 'ai',
        message: '❌ **Error:** Could not connect to AI assistant.',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAskingAI(false);
    }
  };
  
  // A wrapper for askAI that also sets the question from quick-links
  const handleQuickQuestion = (question) => {
      if (isAskingAI) return;
      const userMessage = {
        type: 'user',
        message: question,
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, userMessage]);
      setIsAskingAI(true);
      
      // We pass the question directly to askAI logic
      const ask = async () => {
          try {
              const response = await fetch('http://localhost:8000/ai-chat', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                      question: question,
                      context: 'repo_analysis',
                      model_type: modelType,
                      history: [...chatMessages, userMessage]
                  }),
              });
              const data = await response.json();
              const aiMessage = { type: 'ai', message: data.response || 'Sorry, I could not process your question.', timestamp: new Date().toLocaleTimeString() };
              setChatMessages(prev => [...prev, aiMessage]);
          } catch (err) {
              console.error('AI chat error:', err);
              const errorMessage = { type: 'ai', message: '❌ **Error:** Could not connect to AI assistant.', timestamp: new Date().toLocaleTimeString() };
              setChatMessages(prev => [...prev, errorMessage]);
          } finally {
              setIsAskingAI(false);
          }
      };
      ask();
  };

  const formatSecurityScore = (score) => {
    if (score >= 80) return { color: '#22c55e', label: 'High Security' };
    if (score >= 60) return { color: '#f59e0b', label: 'Medium Security' };
    return { color: '#ef4444', label: 'Low Security' };
  };

  return (
    <PageWrapper>
      <style>
        {`
          :root {
            --primary-green: #00f5c3;
            --secondary-blue: #00d4ff;
            --dark-bg: #0a0a0a; 
            --card-bg: rgba(26, 26, 26, 0.8);
            --card-bg-hover: rgba(38, 38, 38, 0.9);
            --card-border: rgba(255, 255, 255, 0.1);
            --card-border-hover: rgba(255, 255, 255, 0.2);
            --text-light: #f8fafc;
            --text-muted: #a1a1aa;
          }
          
          .page-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
          }
          
          .content-wrapper {
            padding: 2rem 0;
          }
          .hero-section {
            min-height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 3rem 0;
          }
          
          .hero-content {
            max-width: 800px;
            margin: 0 auto;
          }
          
          .hero-title {
            font-size: 2.5rem;
            font-weight: 900;
            letter-spacing: -0.05em;
            color: var(--text-light);
            text-shadow: 0 0 15px rgba(0, 245, 195, 0.4), 0 0 30px rgba(0, 245, 195, 0.2);
            margin-bottom: 1.5rem;
            line-height: 1.1;
          }
          
          .hero-subtitle {
            font-size: 1.125rem;
            line-height: 1.75rem;
            color: var(--text-dark);
            margin-bottom: 2rem;
          }
          
          .card {
            background-color: var(--card-bg);
            backdrop-filter: blur(4px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: left; /* Reset text-align for cards */
          }
          
          .card h3 {
            color: var(--text-light);
            margin-bottom: 1rem;
            font-size: 1.25rem;
            font-weight: 700;
          }
          
          .input-group {
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
          }
          
          .input {
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            color: var(--text-light);
            font-size: 1rem;
            transition: all 0.3s ease;
          }
          
          .input:focus {
            outline: none;
            border-color: var(--primary-green);
            box-shadow: 0 0 0 2px rgba(0, 245, 195, 0.2);
          }
          
          .input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            min-width: fit-content;
          }
          
          .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
          }
          
          .btn-primary {
            background-color: var(--primary-green);
            color: #000;
          }
          
          .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 245, 195, 0.3);
          }
          
          .btn-secondary {
            background-color: transparent;
            color: var(--text-light);
            border: 1px solid var(--card-border);
          }
          
          .btn-secondary:hover:not(:disabled) {
            background-color: var(--card-bg-hover);
            border-color: var(--card-border-hover);
          }
          
          .scan-options {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-top: 1.5rem;
          }
          
          .option-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
          }
          
          .analysis-results {
            margin-right: 0; /* No sidebar space by default */
            display: grid;
            gap: 2rem;
            transition: margin-right 0.3s ease;
          }
          
          .analysis-results.with-sidebar {
            margin-right: 420px; /* Add space when sidebar is shown */
          }
          
          @media (max-width: 1200px) {
            .analysis-results, .analysis-results.with-sidebar {
              margin-right: 0 !important; /* Remove margin on smaller screens */
            }
            .ai-chat-sidebar {
                display: none !important; /* Hide fixed sidebar on smaller screens */
            }
          }
          
          .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(0, 245, 195, 0.2);
            border-top: 3px solid var(--primary-green);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
          }
          
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          .repo-info .info-item {
            margin-bottom: 0.75rem;
            line-height: 1.5;
          }
          
          @media (min-width: 640px) {
            .input-group {
              flex-direction: row;
            }
            
            .scan-options {
              flex-direction: row;
              justify-content: space-between;
              align-items: center;
            }
          }
          
          @media (max-width: 639px) {
            .input-group {
              flex-direction: column;
              align-items: stretch;
            }
            
            .input-group .input {
              flex: 1;
              margin-bottom: 0.5rem;
            }
            
            .input-group .btn {
              width: 100%;
            }
          }
        `}
      </style>
      <div className="content-wrapper">
        <div className="hero-section">
          <div className="hero-content">
            <div className="hero-title">
              <h1>Repository Security Analysis</h1>
              <p>Comprehensive security analysis for GitHub repositories</p>
            </div>

            {/* Scan Configuration */}
            <div className="card">
              <h3>Repository Analysis</h3>
              <p style={{ color: '#a1a1aa', marginBottom: '16px', fontSize: '14px' }}>
                Enter a GitHub repository URL. The system will automatically clean common web interface paths.
              </p>
              
              <div className="input-group">
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="Enter GitHub repository URL (e.g., https://github.com/user/repo)"
                  className="input"
                  disabled={isScanning}
                  style={{ flex: 1 }}
                />
                <button 
                  onClick={analyzeRepository} 
                  disabled={isScanning || !repoUrl.trim()}
                  className="btn btn-secondary"
                >
                  {isScanning ? 'Analyzing...' : 'Analyze Repository'}
                </button>
              </div>

              {/* Example URLs */}
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', color: '#a1a1aa', marginBottom: '6px' }}>
                    Example URLs (these will be automatically cleaned):
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280', lineHeight: '1.4' }}>
                  • https://github.com/user/repo<br/>
                  • https://github.com/user/repo/tree/main<br/>
                  • https://github.com/user/repo/blob/main/README.md
                </div>
              </div>

              <div className="scan-options">
                <div className="option-group">
                  <label style={{ color: '#a1a1aa', marginRight: '9px'}}>AI Model:</label>
                  <select 
                    value={modelType} 
                    onChange={(e) => setModelType(e.target.value)}
                    disabled={isScanning}
                    style={{ 
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      background: 'rgba(0, 0, 0, 0.3)',
                      color: '#fafafa'
                    }}
                  >
                    <option value="fast">Fast Model (Quick Analysis)</option>
                    <option value="smart">Smart Model (Detailed Analysis)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {isScanning && (
              <div className="card">
                <h3>🔍 Analysis in Progress</h3>
                <div style={{ textAlign: 'center', padding: '20px 20px 40px' }}>
                  <div className="loading-spinner"></div>
                  <p style={{ color: '#a1a1aa', marginTop: '16px' }}>Analyzing repository... This may take a few minutes.</p>
                </div>
                
                {/* Analysis Logs */}
                {analysisLogs.length > 0 && (
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    padding: '16px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '14px'
                  }}>
                    {analysisLogs.map((log, index) => (
                      <div key={index} style={{
                        color: log.includes('❌') ? '#ef4444' : 
                               log.includes('⚠️') ? '#f59e0b' : 
                               log.includes('✅') ? '#22c55e' : '#a1a1aa',
                        marginBottom: '4px'
                      }}>
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && !isScanning && (
              <div className="card">
                <h3>❌ Analysis Error</h3>
                <p style={{ color: '#ef4444' }}>{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* --- ANALYSIS RESULTS AND CHAT --- */}
        {/* This block renders only when analysis is complete */}
        {analysisResult && !isScanning && (
          <>
            {/* AI Sidebar Toggle Button */}
            <div style={{ 
              position: 'fixed', 
              top: '20px', 
              right: '20px', 
              zIndex: 1001
            }}>
              <button
                onClick={() => setShowAISidebar(!showAISidebar)}
                style={{
                  background: showAISidebar ? '#00f5c3' : 'rgba(0, 245, 195, 0.1)',
                  color: showAISidebar ? '#000' : '#00f5c3',
                  border: '1px solid rgba(0, 245, 195, 0.3)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
                }}
              >
                {showAISidebar ? '❌ Hide AI Chat' : '🤖 Show AI Chat'}
              </button>
            </div>
            
            {/* Main content with conditional margin for sidebar */}
            <div className={`analysis-results ${showAISidebar ? 'with-sidebar' : ''}`}>

              {/* Analysis Status & Warnings */}
              {(analysisResult.warnings && analysisResult.warnings.length > 0) && (
                <div className="card">
                  <h3>⚠️ Analysis Warnings</h3>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {analysisResult.warnings.map((warning, index) => (
                      <div key={index} style={{
                        padding: '12px',
                        background: 'rgba(245, 158, 11, 0.1)',
                        border: '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '6px',
                        borderLeft: '4px solid #f59e0b',
                        fontSize: '14px'
                      }}>
                        {warning}
                      </div>
                    ))}
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '12px', marginTop: '12px', marginBottom: '0' }}>
                    Note: Some analysis tools may have encountered issues, but core security scanning completed successfully.
                  </p>
                </div>
              )}

              {/* Overview */}
              <div className="card">
                <h3>📊 Repository Overview</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '40px', alignItems: 'center' }}>
                  <div className="repo-info">
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Repository:</strong> 
                      <span>{analysisResult.repository_info?.name || 'Unknown'}</span>
                    </div>
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Description:</strong> 
                      <span>{analysisResult.repository_info?.description || 'No description'}</span>
                    </div>
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Language:</strong> 
                      <span>{analysisResult.repository_info?.language || 'Unknown'}</span>
                    </div>
                    <div className="info-item">
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Stars:</strong> 
                      <span>{analysisResult.repository_info?.stars || 0}</span>
                    </div>
                  </div>
                  
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      background: 'rgba(0, 212, 255, 0.1)', 
                      border: '1px solid rgba(0, 212, 255, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      minWidth: '120px'
                    }}>
                      <div style={{ fontSize: '28px', fontWeight: '700', color: '#00d4ff' }}>
                        {analysisResult.overall_security_score || 0}
                      </div>
                      <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Security Score</div>
                    </div>
                    <div style={{ 
                      marginTop: '12px', 
                      fontWeight: '600', 
                      color: formatSecurityScore(analysisResult.overall_security_score).color 
                    }}>
                      {formatSecurityScore(analysisResult.overall_security_score).label}
                    </div>
                  </div>
                </div>
              </div>

              {/* Security Summary */}
              <div className="card">
                <h3>🔍 Security Summary</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px' }}>
                  {analysisResult.security_summary && (
                    <>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(34, 197, 94, 0.1)', 
                          border: '1px solid rgba(34, 197, 94, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>
                            {analysisResult.security_summary.total_files_scanned || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Files Scanned</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(239, 68, 68, 0.1)', 
                          border: '1px solid rgba(239, 68, 68, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>
                            {analysisResult.security_summary.secrets_found || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Secrets Found</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(245, 158, 11, 0.1)', 
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
                            {analysisResult.security_summary.static_issues_found || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Static Issues</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(139, 69, 19, 0.1)', 
                          border: '1px solid rgba(139, 69, 19, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#8b4513' }}>
                            {analysisResult.security_summary.vulnerable_dependencies || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Vulnerable Deps</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(168, 85, 247, 0.1)', 
                          border: '1px solid rgba(168, 85, 247, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#a855f7' }}>
                            {analysisResult.security_summary.code_quality_issues || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Quality Issues</div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* File Analysis & .gitignore Recommendations */}
              {analysisResult.file_security_scan && (
                <div className="card">
                  <h3>📁 File Security Analysis</h3>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.file_security_scan.sensitive_files && analysisResult.file_security_scan.sensitive_files.length > 0 && (
                      <div>
                        <h4 style={{ color: '#ef4444', fontSize: '16px', marginBottom: '12px' }}>
                          🚨 Sensitive Files Found ({analysisResult.file_security_scan.sensitive_files.length})
                        </h4>
                        <div style={{ display: 'grid', gap: '8px' }}>
                          {analysisResult.file_security_scan.sensitive_files.slice(0, 5).map((file, index) => (
                            <div key={index} style={{
                              padding: '12px',
                              background: 'rgba(239, 68, 68, 0.1)',
                              border: '1px solid rgba(239, 68, 68, 0.2)',
                              borderRadius: '8px',
                              fontFamily: 'monospace',
                              fontSize: '13px'
                            }}>
                              📄 {file}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {analysisResult.file_security_scan.excluded_directories && analysisResult.file_security_scan.excluded_directories.length > 0 && (
                      <div>
                        <h4 style={{ color: '#22c55e', fontSize: '16px', marginBottom: '12px' }}>
                          ✅ Excluded Directories ({analysisResult.file_security_scan.excluded_directories.length})
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {analysisResult.file_security_scan.excluded_directories.map((dir, index) => (
                            <span key={index} style={{
                              padding: '4px 8px',
                              background: 'rgba(34, 197, 94, 0.1)',
                              border: '1px solid rgba(34, 197, 94, 0.2)',
                              borderRadius: '12px',
                              fontSize: '12px',
                              fontFamily: 'monospace'
                            }}>
                              📁 {dir}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {analysisResult.file_security_scan.gitignore_recommendations && analysisResult.file_security_scan.gitignore_recommendations.length > 0 && (
                      <div>
                        <h4 style={{ color: '#f59e0b', fontSize: '16px', marginBottom: '12px' }}>
                          💡 GitIgnore Recommendations ({analysisResult.file_security_scan.gitignore_recommendations.length})
                        </h4>
                        <div style={{ 
                          background: 'rgba(245, 158, 11, 0.1)',
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          borderRadius: '8px',
                          padding: '12px',
                          fontFamily: 'monospace',
                          fontSize: '13px'
                        }}>
                          {analysisResult.file_security_scan.gitignore_recommendations.map((rec, index) => (
                            <div key={index} style={{ marginBottom: '4px' }}>
                              + {rec}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                <div className="card">
                  {/* ... recommendations content ... */}
                </div>
              )}

              {/* Secret Scan Results */}
              {analysisResult.secret_scan_results && analysisResult.secret_scan_results.length > 0 && (
                <div className="card">
                  <h3>🔐 Secrets Detection ({analysisResult.secret_scan_results.length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Potential secrets and sensitive information found in code:
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {analysisResult.secret_scan_results.slice(0, 10).map((secret, index) => (
                      <div key={index} style={{
                        padding: '16px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '8px',
                        borderLeft: '4px solid #ef4444'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <div style={{ fontWeight: '600', fontSize: '14px' }}>
                            {secret.type || 'Potential Secret'}
                          </div>
                          <span style={{
                            background: '#dc2626',
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: '600'
                          }}>
                            CRITICAL
                          </span>
                        </div>
                        
                        {secret.file && (
                          <div style={{ 
                            fontFamily: 'monospace', 
                            fontSize: '12px', 
                            color: '#a1a1aa',
                            marginBottom: '8px'
                          }}>
                            📁 {secret.file}
                            {secret.line && ` → Line ${secret.line}`}
                          </div>
                        )}
                        
                        {secret.match && (
                          <div style={{ 
                            fontSize: '12px', 
                            color: '#d1d5db',
                            background: 'rgba(0, 0, 0, 0.3)',
                            padding: '8px',
                            borderRadius: '4px',
                            fontFamily: 'monospace'
                          }}>
                            Found: {secret.match.substring(0, 50)}...
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Static Analysis Results */}
              {analysisResult.static_analysis_results && analysisResult.static_analysis_results.length > 0 && (
                <div className="card">
                  <h3>🔍 Static Analysis ({analysisResult.static_analysis_results.length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Security vulnerabilities detected through static code analysis:
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {analysisResult.static_analysis_results.slice(0, 10).map((issue, index) => (
                      <div key={index} style={{
                        padding: '16px',
                        background: issue.severity === 'HIGH' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: issue.severity === 'HIGH' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '8px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <div style={{ fontWeight: '600', fontSize: '14px' }}>
                            {issue.rule_id || issue.description || 'Static Analysis Issue'}
                          </div>
                          <span style={{
                            background: issue.severity === 'HIGH' ? '#ef4444' : '#f59e0b',
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: '600'
                          }}>
                            {issue.severity || 'MEDIUM'}
                          </span>
                        </div>
                        
                        {issue.filename && (
                          <div style={{ 
                            fontFamily: 'monospace', 
                            fontSize: '12px', 
                            color: '#a1a1aa',
                            marginBottom: '8px'
                          }}>
                            📁 {issue.filename}
                            {issue.line_number && ` → Line ${issue.line_number}`}
                          </div>
                        )}
                        
                        {issue.message && (
                          <div style={{ fontSize: '13px', color: '#d1d5db', lineHeight: '1.4' }}>
                            {issue.message}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Code Quality Issues */}
              {analysisResult.code_quality_results && analysisResult.code_quality_results.length > 0 && (
                <div className="card">
                  <h3>🎯 Code Quality Issues ({analysisResult.code_quality_results.length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Insecure coding patterns and quality issues detected:
                  </p>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.code_quality_results.slice(0, 10).map((issue, index) => (
                      <div key={index} style={{
                        padding: '20px',
                        background: issue.severity === 'Critical' || issue.severity === 'High' ? 
                          'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: issue.severity === 'Critical' || issue.severity === 'High' ? 
                          '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '12px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: '600', marginBottom: '6px', fontSize: '15px' }}>
                              {issue.pattern || issue.description || 'Code Quality Issue'}
                            </div>
                            {issue.file && (
                              <div style={{ 
                                fontFamily: 'monospace', 
                                fontSize: '12px', 
                                color: '#a1a1aa',
                                background: 'rgba(0, 0, 0, 0.2)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'inline-block'
                              }}>
                                📁 {issue.file}
                                {issue.line && ` → Line ${issue.line}`}
                              </div>
                            )}
                          </div>
                          <span style={{
                            background: issue.severity === 'Critical' ? '#dc2626' :
                                       issue.severity === 'High' ? '#ef4444' :
                                       issue.severity === 'Medium' ? '#f59e0b' : '#6b7280',
                            color: 'white',
                            padding: '6px 12px',
                            borderRadius: '16px',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}>
                            {issue.severity || 'Medium'}
                          </span>
                        </div>

                        {issue.code_snippet && (
                          <div style={{ marginTop: '12px' }}>
                            <div style={{ 
                              fontSize: '12px', 
                              color: '#a1a1aa', 
                              marginBottom: '6px',
                              fontWeight: '500'
                            }}>
                              🔍 Code Found:
                            </div>
                            <div style={{
                              background: 'rgba(0, 0, 0, 0.4)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              padding: '12px',
                              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                              fontSize: '13px',
                              color: '#e5e7eb',
                              overflowX: 'auto',
                              whiteSpace: 'pre'
                            }}>
                              {issue.code_snippet && issue.code_snippet.length > 150 ? 
                                `${issue.code_snippet.substring(0, 150)}...` : 
                                issue.code_snippet || 'No code snippet available'
                              }
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependency Vulnerabilities */}
              {analysisResult.dependency_scan_results?.vulnerable_packages && analysisResult.dependency_scan_results.vulnerable_packages.length > 0 && (
                <div className="card">
                  <h3>📦 Vulnerable Dependencies ({analysisResult.dependency_scan_results.vulnerable_packages.length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Dependencies with known security vulnerabilities:
                  </p>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.dependency_scan_results.vulnerable_packages.slice(0, 10).map((pkg, index) => (
                      <div key={index} style={{
                        padding: '20px',
                        background: pkg.severity === 'Critical' || pkg.severity === 'High' ? 
                          'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: pkg.severity === 'Critical' || pkg.severity === 'High' ? 
                          '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '12px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: '700', fontFamily: 'monospace', fontSize: '16px' }}>
                                {pkg.package || pkg.name || 'Unknown Package'}
                              </span>
                              {pkg.current_version && (
                                <span style={{ 
                                  color: '#a1a1aa', 
                                  fontSize: '13px',
                                  background: 'rgba(0, 0, 0, 0.2)',
                                  padding: '2px 6px',
                                  borderRadius: '4px'
                                }}>
                                  v{pkg.current_version.replace(/[>=<]/g, '')}
                                </span>
                              )}
                            </div>
                            {pkg.file && (
                              <div style={{ 
                                fontFamily: 'monospace', 
                                fontSize: '12px', 
                                color: '#a1a1aa',
                                background: 'rgba(0, 0, 0, 0.2)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'inline-block'
                              }}>
                                📄 {pkg.file}
                              </div>
                            )}
                          </div>
                          <span style={{
                            background: pkg.severity === 'Critical' ? '#dc2626' :
                                       pkg.severity === 'High' ? '#ef4444' :
                                       pkg.severity === 'Medium' ? '#f59e0b' : '#6b7280',
                            color: 'white',
                            padding: '6px 14px',
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: '700'
                          }}>
                            {pkg.severity || 'Unknown'}
                          </span>
                        </div>

                        {pkg.advisory && (
                          <div style={{ 
                            color: '#d1d5db', 
                            fontSize: '13px', 
                            marginBottom: '12px',
                            lineHeight: '1.5',
                            background: 'rgba(0, 0, 0, 0.2)',
                            padding: '10px',
                            borderRadius: '6px'
                          }}>
                            ⚠️ <strong>Advisory:</strong> {pkg.advisory}
                          </div>
                        )}

                        {(pkg.package || pkg.name) && (
                          <div style={{ marginTop: '12px' }}>
                            <div style={{ fontSize: '12px', color: '#a1a1aa', marginBottom: '4px' }}>
                              🛠️ Quick Fix:
                            </div>
                            <div style={{
                              background: 'rgba(0, 0, 0, 0.4)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              padding: '8px 12px',
                              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                              fontSize: '12px',
                              color: '#e5e7eb'
                            }}>
                              {pkg.file?.includes('package.json') ? 
                                `npm update ${pkg.package || pkg.name}` : 
                                `pip install --upgrade ${pkg.package || pkg.name}`
                              }
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* --- FIXED AI CHAT SIDEBAR (CONDITIONAL DISPLAY) --- */}
            {showAISidebar && (
              <div className="ai-chat-sidebar" style={{
              position: 'fixed',
              top: '0',
              right: '0',
              width: '400px',
              height: '100vh',
              background: 'linear-gradient(135deg, rgba(15, 15, 15, 0.95) 0%, rgba(25, 25, 25, 0.95) 100%)',
              backdropFilter: 'blur(10px)',
              borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.3)'
            }}>
              {/* AI Chat Header */}
              <div style={{
                padding: '20px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(0, 245, 195, 0.05)'
              }}>
                <h3 style={{ margin: '0', color: '#00f5c3', fontSize: '18px', fontWeight: '700' }}>
                  🤖 AI Security Advisor
                </h3>
                <p style={{ margin: '8px 0 0 0', color: '#a1a1aa', fontSize: '13px' }}>
                  Ask about security findings & get recommendations
                </p>
              </div>

              {/* Quick Questions */}
              <div style={{ padding: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <div style={{ color: '#a1a1aa', fontSize: '12px', marginBottom: '8px' }}>
                  💡 Quick questions:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {[
                    'Fix critical issues',
                    'Explain security score',
                    'GitIgnore help',
                    'Vulnerability details'
                  ].map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickQuestion(question)}
                      disabled={isAskingAI}
                      style={{
                        padding: '4px 8px',
                        background: 'rgba(0, 212, 255, 0.1)',
                        border: '1px solid rgba(0, 212, 255, 0.2)',
                        borderRadius: '12px',
                        color: '#00d4ff',
                        fontSize: '11px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>

              {/* Chat Messages */}
              <div style={{ 
                flex: 1,
                padding: '16px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column'
              }}>
                {chatMessages.length === 0 ? (
                  <div style={{ 
                    color: '#a1a1aa', 
                    fontStyle: 'italic',
                    textAlign: 'center',
                    padding: '40px 20px',
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column'
                  }}>
                    <div style={{ fontSize: '24px', marginBottom: '8px' }}>💬</div>
                    <div>Ask me about security analysis...</div>
                    <div style={{ fontSize: '11px', marginTop: '4px' }}>Try the quick questions above!</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {chatMessages.map((msg, index) => (
                      <div key={index} style={{
                        padding: '12px',
                        borderRadius: '8px',
                        maxWidth: '90%',
                        ...(msg.type === 'user' ? {
                          background: 'rgba(0, 212, 255, 0.1)',
                          border: '1px solid rgba(0, 212, 255, 0.2)',
                          alignSelf: 'flex-end'
                        } : {
                          background: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          alignSelf: 'flex-start'
                        })
                      }}>
                        <div style={{ whiteSpace: 'pre-line', lineHeight: '1.5', fontSize: '13px' }}
                             dangerouslySetInnerHTML={{ __html: msg.message.replace(/\n/g, '<br />') }}>
                        </div>
                        <div style={{ 
                          fontSize: '10px', 
                          color: '#a1a1aa', 
                          marginTop: '6px',
                          opacity: 0.7,
                          textAlign: 'right'
                        }}>
                          {msg.timestamp}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {isAskingAI && (
                  <div style={{ 
                    color: '#a1a1aa', 
                    fontStyle: 'italic', 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    padding: '12px',
                    marginTop: '8px'
                  }}>
                    <div style={{ 
                      width: '14px', 
                      height: '14px', 
                      border: '2px solid rgba(0, 212, 255, 0.2)',
                      borderTop: '2px solid #00d4ff',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></div>
                    <span style={{ fontSize: '12px' }}>AI analyzing...</span>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div style={{ 
                padding: '16px',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                background: 'rgba(0, 0, 0, 0.2)'
              }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    value={currentQuestion}
                    onChange={(e) => setCurrentQuestion(e.target.value)}
                    placeholder="Ask about security..."
                    onKeyPress={(e) => e.key === 'Enter' && askAI()}
                    disabled={!analysisResult || isAskingAI}
                    style={{
                      flex: 1,
                      background: 'rgba(0, 0, 0, 0.3)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      borderRadius: '6px',
                      padding: '8px 12px',
                      color: '#fff',
                      fontSize: '13px'
                    }}
                  />
                  <button 
                    onClick={askAI} 
                    disabled={!analysisResult || isAskingAI || !currentQuestion.trim()}
                    style={{
                      background: 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '8px 16px',
                      color: '#000',
                      fontWeight: '600',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}
                  >
                    {isAskingAI ? '...' : 'Ask'}
                  </button>
                </div>
              </div>
              </div>
            )}
          </>
        )}
      </div>
    </PageWrapper>
  );
};

export default RepoAnalysisPage;
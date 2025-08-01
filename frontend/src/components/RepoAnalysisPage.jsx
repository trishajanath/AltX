import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from './PageWrapper';
import './RepoAnalysisPage.css';

const RepoAnalysisPage = () => {
  const [repoUrl, setRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState('');
  const [modelType, setModelType] = useState('smart');
  const [deepScan, setDeepScan] = useState(true);
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isAskingAI, setIsAskingAI] = useState(false);
  
  const navigate = useNavigate();

  const analyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    setIsScanning(true);
    setError('');
    setAnalysisResult(null);

    try {
      const response = await fetch('http://localhost:8000/analyze-repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          model_type: modelType,
          deep_scan: deepScan
        }),
      });

      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setAnalysisResult(data);
        // Add initial AI summary to chat
        const summary = generateAnalysisSummary(data);
        setChatMessages([{
          type: 'ai',
          message: summary,
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    } catch (err) {
      setError('Failed to analyze repository. Please check your connection.');
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
• Secrets Found: ${summary.secrets_found || 0} 
• Static Issues: ${summary.static_issues_found || 0}
• Vulnerable Dependencies: ${summary.vulnerable_dependencies || 0}
• Code Quality Issues: ${summary.code_quality_issues || 0}

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

    setChatMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: currentQuestion,
          context: 'repo_analysis',
          model_type: modelType,
          history: chatMessages
        }),
      });

      const data = await response.json();
      
      const aiMessage = {
        type: 'ai',
        message: data.response || 'Sorry, I could not process your question.',
        timestamp: new Date().toLocaleTimeString()
      };

      setChatMessages(prev => [...prev, aiMessage]);
      setCurrentQuestion('');
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

  const formatSecurityScore = (score) => {
    if (score >= 80) return { color: '#22c55e', label: 'High Security' };
    if (score >= 60) return { color: '#f59e0b', label: 'Medium Security' };
    return { color: '#ef4444', label: 'Low Security' };
  };

  return (
    <PageWrapper>
      <div className="page-container">
        <div className="content-wrapper">
          <div className="hero">
            <h1>🔍 Repository Security Analysis</h1>
            <p>Comprehensive security analysis for GitHub repositories</p>
          </div>

        {/* Scan Configuration */}
        <div className="card">
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
              className="btn btn-primary"
            >
              {isScanning ? 'Analyzing...' : 'Analyze Repository'}
            </button>
          </div>

          <div className="scan-options">
            <div className="option-group">
              <label style={{ color: '#a1a1aa', marginRight: '8px' }}>AI Model:</label>
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
            
            <div className="option-group">
              <label style={{ color: '#a1a1aa', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  checked={deepScan}
                  onChange={(e) => setDeepScan(e.target.checked)}
                  disabled={isScanning}
                />
                Deep Scan (Includes secret detection & static analysis)
              </label>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isScanning && (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div className="loading-spinner"></div>
              <p style={{ color: '#a1a1aa', marginTop: '16px' }}>Analyzing repository... This may take a few minutes.</p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="card">
            <h3>❌ Analysis Error</h3>
            <p style={{ color: '#ef4444' }}>{error}</p>
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <div className="analysis-results">
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
                <div style={{ 
                  background: 'rgba(0, 212, 255, 0.1)', 
                  border: '1px solid rgba(0, 212, 255, 0.2)',
                  borderRadius: '8px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#00d4ff' }}>
                    {analysisResult.security_summary?.total_files_scanned || 0}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Files Scanned</div>
                </div>
                
                <div style={{ 
                  background: 'rgba(239, 68, 68, 0.1)', 
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: '8px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>
                    {analysisResult.security_summary?.secrets_found || 0}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Secrets Found</div>
                </div>
                
                <div style={{ 
                  background: 'rgba(245, 158, 11, 0.1)', 
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  borderRadius: '8px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
                    {analysisResult.security_summary?.static_issues_found || 0}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Static Issues</div>
                </div>
                
                <div style={{ 
                  background: 'rgba(147, 51, 234, 0.1)', 
                  border: '1px solid rgba(147, 51, 234, 0.2)',
                  borderRadius: '8px',
                  padding: '20px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#9333ea' }}>
                    {analysisResult.security_summary?.vulnerable_dependencies || 0}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Vulnerable Dependencies</div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
              <div className="card">
                <h3>📋 Security Recommendations</h3>
                <div style={{ display: 'grid', gap: '12px' }}>
                  {analysisResult.recommendations.map((rec, index) => (
                    <div key={index} style={{
                      padding: '16px',
                      background: 'rgba(0, 212, 255, 0.1)',
                      border: '1px solid rgba(0, 212, 255, 0.2)',
                      borderRadius: '8px',
                      borderLeft: '4px solid #00d4ff'
                    }}>
                      {rec}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detailed Results Sections */}
            {analysisResult.secret_scan_results && analysisResult.secret_scan_results.length > 0 && (
              <div className="card">
                <h3>🔑 Secrets Detected ({analysisResult.secret_scan_results.length})</h3>
                <div style={{ display: 'grid', gap: '12px' }}>
                  {analysisResult.secret_scan_results.slice(0, 10).map((secret, index) => (
                    <div key={index} style={{
                      padding: '16px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      borderRadius: '8px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{
                          background: '#ef4444',
                          color: 'white',
                          padding: '4px 12px',
                          borderRadius: '20px',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          {secret.secret_type}
                        </span>
                        <span style={{
                          fontFamily: 'monospace',
                          background: 'rgba(0, 0, 0, 0.3)',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          color: '#a1a1aa'
                        }}>
                          {secret.file}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#a1a1aa' }}>Line {secret.line}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Chat Section */}
            <div className="card">
              <h3>🤖 AI Security Advisor</h3>
              
              <div style={{ 
                background: 'rgba(0, 0, 0, 0.3)', 
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '20px',
                maxHeight: '300px',
                overflowY: 'auto',
                marginBottom: '20px'
              }}>
                {chatMessages.length === 0 ? (
                  <div style={{ 
                    color: '#a1a1aa', 
                    fontStyle: 'italic',
                    textAlign: 'center',
                    padding: '40px 20px'
                  }}>
                    💬 Ask me anything about this repository's security analysis...
                  </div>
                ) : (
                  chatMessages.map((msg, index) => (
                    <div key={index} style={{
                      marginBottom: '16px',
                      padding: '12px',
                      borderRadius: '8px',
                      maxWidth: '80%',
                      ...(msg.type === 'user' ? {
                        background: 'rgba(0, 212, 255, 0.1)',
                        border: '1px solid rgba(0, 212, 255, 0.2)',
                        marginLeft: 'auto',
                        textAlign: 'right'
                      } : {
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)'
                      })
                    }}>
                      <div style={{ whiteSpace: 'pre-line', lineHeight: '1.6' }}>
                        {msg.message.split('\n').map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#a1a1aa', 
                        marginTop: '8px',
                        opacity: 0.7
                      }}>
                        {msg.timestamp}
                      </div>
                    </div>
                  ))
                )}
                
                {isAskingAI && (
                  <div style={{ color: '#a1a1aa', fontStyle: 'italic' }}>
                    🤖 AI is analyzing...
                  </div>
                )}
              </div>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <input
                  type="text"
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  placeholder="Ask about this repository's security..."
                  onKeyPress={(e) => e.key === 'Enter' && askAI()}
                  disabled={isAskingAI}
                  className="input"
                  style={{ flex: 1 }}
                />
                <button 
                  onClick={askAI} 
                  disabled={isAskingAI || !currentQuestion.trim()}
                  className="btn btn-primary"
                >
                  {isAskingAI ? '...' : 'Ask'}
                </button>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </PageWrapper>
  );
};

export default RepoAnalysisPage;

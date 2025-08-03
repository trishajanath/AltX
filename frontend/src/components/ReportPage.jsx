import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SecurityIssueFormatter from './SecurityIssueFormatter';
import ChatResponseFormatter from './ChatResponseFormatter';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
const ReportPage = ({ scanResult }) => {
  usePreventZoom();
  const navigate = useNavigate();
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize chat with AI analysis if available
  useEffect(() => {
    if (scanResult?.ai_assistant_advice && chatHistory.length === 0) {
      setChatHistory([{
        type: 'ai',
        message: `🔍 **Initial Security Analysis**\n\n${scanResult.ai_assistant_advice}\n\n💬 Feel free to ask me any questions about your security scan results!`,
        timestamp: new Date()
      }]);
    }
  }, [scanResult, chatHistory.length]);

  const handleChat = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { type: 'user', message: userMessage, timestamp: new Date() }]);
    setIsLoading(true);

    try {
      // Check if user is asking for summary and we have existing summary
      const isAskingForSummary = userMessage.toLowerCase().includes('summar') || 
                                userMessage.toLowerCase().includes('overview') ||
                                userMessage.toLowerCase().includes('report');
      
      if (isAskingForSummary && (scanResult.summary || scanResult.ai_assistant_advice)) {
        // Use existing summary instead of generating new one
        const existingSummary = scanResult.summary || scanResult.ai_assistant_advice;
        setChatHistory(prev => [...prev, { 
          type: 'ai', 
          message: `📋 **Here's your detailed security analysis summary:**\n\n${existingSummary}`, 
          timestamp: new Date() 
        }]);
        setIsLoading(false);
        return;
      }

      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: userMessage, 
          scan_result: scanResult,
          context: 'website_scan'
        }),
      });
      
      const data = await response.json();
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        message: data.response, 
        timestamp: new Date() 
      }]);
    } catch (error) {
      let fallbackResponse = generateSmartResponse(userMessage, scanResult);
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        message: fallbackResponse,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateSmartResponse = (question, result) => {
    const q = question.toLowerCase();
    
    // Handle summary requests with existing data
    if ((q.includes('summar') || q.includes('overview') || q.includes('report')) && 
        (result?.summary || result?.ai_assistant_advice)) {
      return `📋 **Security Analysis Summary:**\n\n${result.summary || result.ai_assistant_advice}`;
    }
    
    if (q.includes('vulnerabilit') || q.includes('security')) {
      const flagsCount = result?.scan_result?.flags?.length || 0;
      return `Based on your scan results, I found ${flagsCount} security issues that need attention. ${flagsCount > 0 ? 'Focus on addressing the most critical ones first.' : 'Great job - no major vulnerabilities detected!'}`;
    }
    if (q.includes('fix') || q.includes('how to')) {
      return `Here are key steps to improve security: 1) Implement missing security headers, 2) Ensure HTTPS is properly configured, 3) Update vulnerable dependencies, 4) Enable proper input validation.`;
    }
    if (q.includes('score') || q.includes('rating')) {
      return `Your security score is ${result?.security_score || result?.scan_result?.security_score || 'not available'}/100. Scores above 85 are considered excellent, 70-85 is good, 50-70 needs improvement.`;
    }
    
    return `I'm here to help you understand your security scan results and provide remediation guidance. Ask me about specific vulnerabilities, how to improve your score, or request a summary of the analysis.`;
  };

  const getVulnerabilityColor = (level) => {
    switch (level) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  if (!scanResult) {
    return (
      <PageWrapper>
        <style>
          {`      
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
            }
          .btn-secondary {
            background-color: transparent;
            color: var(--text-light);
            border: 1px solid var(--card-border);
            padding: 1rem 1.5rem;
            font-size: 1.1rem;
          }
          .btn-secondary:hover:not(:disabled) {
            background-color: var(--card-bg-hover);
            border-color: var(--card-border-hover);
          }
          .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
        `}
        </style>
        <div className="hero-section">
          <div className="hero-content">
            <div className="hero-title">
              <h1>Security Reports</h1>
              <p>No scan results available. Please run a security scan or deployment first.</p>
            </div>
            <div style={{ textAlign: 'center', marginTop: '40px' }}>
              <button className="btn btn-secondary" onClick={() => navigate('/security')}>
                Start New Scan
              </button>
            </div>
          </div>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper>
      <style>
          {`      
          .report-page {
            padding: 2rem 0;
            min-height: 100vh;
          }
          
          .report-hero {
            text-align: center;
            margin-bottom: 2rem;
            padding: 1rem 0;
          }
          
          .report-hero h1 {
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: -0.05em;
            color: var(--text-light);
            text-shadow: 0 0 15px rgba(0, 245, 195, 0.4), 0 0 30px rgba(0, 245, 195, 0.2);
            margin-bottom: 0.5rem;
            line-height: 1.1;
          }
          
          .report-hero p {
            font-size: 1rem;
            color: var(--text-dark);
            margin: 0;
          }
          
          .report-layout {
            display: grid;
            grid-template-columns: 1fr 500px;
            gap: 2rem;
            max-width: 1500px;
            margin: 0 auto;
          }
          
          .report-main {
            min-height: 0;
          }
          
          .report-sidebar {
            position: sticky;
            top: 2rem;
            height: fit-content;
          }
          
          @media (max-width: 1200px) {
            .report-layout {
              grid-template-columns: 1fr;
              gap: 2rem;
            }
            
            .report-sidebar {
              position: static;
            }
          }
          
          .card {
            background: var(--card-bg);
            backdrop-filter: blur(8px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 2rem;
            transition: all 0.3s ease;
          }
          
          .card:hover {
            border-color: var(--card-border-hover);
            background-color: var(--card-bg-hover);
            transform: translateY(-0.25rem);
          }
          
          .card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-light);
            margin: 0 0 1.5rem 0;
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
          
          .btn-ghost {
            background-color: rgba(0, 0, 0, 0.4);
            color: var(--text-light);
            border: 1px solid rgba(0, 245, 195, 0.2);
            backdrop-filter: blur(4px);
          }
          
          .btn-ghost:hover {
            background-color: rgba(0, 245, 195, 0.1);
            border-color: rgba(0, 245, 195, 0.4);
            color: var(--primary-green);
          }
          
          .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          .input {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            color: var(--text-light);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(4px);
          }
          
          .input:focus {
            border-color: var(--primary-green);
            box-shadow: 0 0 0 3px rgba(0, 245, 195, 0.1);
            outline: none;
          }
          
          .input::placeholder {
            color: var(--text-dark);
          }
        `}
      </style>
      
      <div className="page-container">
        <div className="content-wrapper">
          <div className="report-page">
            <div className="report-hero">
              <h1>Security Report</h1>
              <p>Comprehensive analysis for {scanResult.url || scanResult.deploymentUrl}</p>
            </div>

            <div className="report-layout">
              <div className="report-main">
                <div className="card">
                  <h3>Security Overview</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                    <div style={{ 
                      background: 'rgba(0, 212, 255, 0.1)', 
                      border: '1px solid rgba(0, 212, 255, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '28px', fontWeight: '700', color: '#00d4ff' }}>
                        {scanResult.security_score || scanResult.scan_result?.security_score || 'N/A'}
                      </div>
                      <div style={{ color: '#a1a1aa' }}>Security Score</div>
                    </div>
                    
                    <div style={{ 
                      background: 'rgba(34, 197, 94, 0.1)', 
                      border: '1px solid rgba(34, 197, 94, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>
                        {scanResult.scan_result?.https ? '✓' : '✗'}
                      </div>
                      <div style={{ color: '#a1a1aa' }}>HTTPS Status</div>
                    </div>

                    <div style={{ 
                      background: 'rgba(147, 51, 234, 0.1)', 
                      border: '1px solid rgba(147, 51, 234, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '28px', fontWeight: '700', color: '#9333ea' }}>
                        {scanResult.scan_result?.ssl_certificate?.valid ? '✅' : 
                         scanResult.scan_result?.https ? '⚠️' : '❌'}
                      </div>
                      <div style={{ color: '#a1a1aa' }}>SSL Certificate</div>
                      {scanResult.scan_result?.ssl_certificate?.certificate_details && (
                        <div style={{ fontSize: '12px', color: '#a1a1aa', marginTop: '8px' }}>
                          {scanResult.scan_result.ssl_certificate.certificate_details.days_until_expiry !== undefined && (
                            <div>
                              {scanResult.scan_result.ssl_certificate.certificate_details.days_until_expiry > 0 
                                ? `${scanResult.scan_result.ssl_certificate.certificate_details.days_until_expiry} days left`
                                : 'Expired'
                              }
                            </div>
                          )}
                          {scanResult.scan_result.ssl_certificate.cipher_info?.bits && (
                            <div>{scanResult.scan_result.ssl_certificate.cipher_info.bits}-bit encryption</div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* AI Summary Section */}
                {(scanResult.summary || scanResult.ai_assistant_advice) && (
                  <div className="card">
                    <h3>🤖 AI Security Analysis Summary</h3>
                    <div style={{ 
                      background: 'rgba(0, 245, 195, 0.05)', 
                      border: '1px solid rgba(0, 245, 195, 0.1)',
                      borderRadius: '8px',
                      padding: '20px',
                      marginTop: '16px'
                    }}>
                      <ChatResponseFormatter 
                        message={scanResult.summary || scanResult.ai_assistant_advice}
                        type="ai"
                      />
                    </div>
                  </div>
                )}

                {/* Security Issues Formatted Display */}
                {scanResult.scan_result?.flags && (
                  <div className="card">
                    <h3>Security Issues Analysis</h3>
                    <SecurityIssueFormatter 
                      issues={scanResult.scan_result.flags} 
                      scanResult={scanResult.scan_result}
                    />
                  </div>
                )}
              </div>

              <div className="report-sidebar">
                <div className="card">
                  <h3>AI Security Advisor</h3>

                  <div style={{ 
                    background: 'rgba(0, 0, 0, 0.3)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    padding: '20px',
                    height: '400px',
                    overflowY: 'auto',
                    marginBottom: '20px'
                  }}>
                    {chatHistory.length === 0 ? (
                      <div style={{ 
                        color: '#a1a1aa', 
                        fontStyle: 'italic',
                        textAlign: 'center',
                        padding: '50px 20px',
                        fontSize: '16px',
                        lineHeight: '1.5'
                      }}>
                        💬 Ask me anything about your security scan results...
                        <br />
                        <span style={{ fontSize: '14px', opacity: '0.8' }}>
                          I can help explain vulnerabilities, suggest fixes, or provide detailed analysis.
                        </span>
                      </div>
                    ) : (
                      chatHistory.map((chat, index) => (
                        <div key={index} style={{ marginBottom: '20px', fontSize: '15px', lineHeight: '1.5' }}>
                          <ChatResponseFormatter 
                            message={chat.message}
                            type={chat.type}
                          />
                        </div>
                      ))
                    )}
                    {isLoading && (
                      <div style={{ color: '#a1a1aa', fontStyle: 'italic', fontSize: '15px' }}>
                        🤖 AI is analyzing...
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
                    <input
                      type="text"
                      className="input"
                      placeholder="Ask about security issues, vulnerabilities, or how to improve..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleChat()}
                      disabled={isLoading}
                      style={{ flex: 1, fontSize: '15px', padding: '12px 15px', height: '48px' }}
                    />
                    <button 
                      className="btn btn-secondary" 
                      onClick={handleChat}
                      disabled={isLoading || !chatInput.trim()}
                      style={{ fontSize: '14px', padding: '12px 20px', height: '48px' }}
                    >
                      Send
                    </button>
                  </div>

                  {/* Quick Action Buttons */}
                  <div>
                    <div style={{ fontSize: '14px', color: '#a1a1aa', marginBottom: '12px', fontWeight: '500' }}>
                      Quick actions:
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                      {(scanResult.summary || scanResult.ai_assistant_advice) && (
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: '13px', padding: '10px 12px' }}
                          onClick={() => {
                            setChatInput('Summarize the analysis');
                            setTimeout(() => handleChat(), 100);
                          }}
                        >
                          📋 Summary
                        </button>
                      )}
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '13px', padding: '10px 12px' }}
                        onClick={() => {
                          setChatInput('What are the main vulnerabilities?');
                          setTimeout(() => handleChat(), 100);
                        }}
                      >
                        🔍 Issues
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '11px', padding: '6px 8px' }}
                        onClick={() => {
                          setChatInput('How can I improve my security score?');
                          setTimeout(() => handleChat(), 100);
                        }}
                      >
                        🛠️ Fix
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ fontSize: '13px', padding: '10px 12px' }}
                        onClick={() => {
                          setChatInput('Explain my security score');
                          setTimeout(() => handleChat(), 100);
                        }}
                      >
                        📊 Score
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default ReportPage;
import React, { useState } from 'react';
import SecurityIssueFormatter from './SecurityIssueFormatter';
import ChatResponseFormatter from './ChatResponseFormatter';

const ReportPage = ({ scanResult }) => {
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleChat = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { type: 'user', message: userMessage, timestamp: new Date() }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: userMessage, 
          scan_result: scanResult 
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
    
    if (q.includes('vulnerabilit') || q.includes('security')) {
      return `Based on your scan results, I found ${result?.scan_result?.vulnerabilities?.high || 0} high-priority and ${result?.scan_result?.vulnerabilities?.medium || 0} medium-priority vulnerabilities. Focus on addressing the high-priority issues first.`;
    }
    if (q.includes('fix') || q.includes('how to')) {
      return `Here are key steps to improve security: 1) Implement missing security headers, 2) Ensure HTTPS is properly configured, 3) Update vulnerable dependencies, 4) Enable proper input validation.`;
    }
    if (q.includes('score') || q.includes('rating')) {
      return `Your security score is ${result?.security_score || result?.scan_result?.security_score || 'not available'}. Scores above 85 are considered excellent.`;
    }
    
    return `I'm here to help you understand your security scan results and provide remediation guidance.`;
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
      <div className="page">
        <div className="container">
          <div className="hero">
            <h1>Security Reports</h1>
            <p>No scan results available. Please run a security scan or deployment first.</p>
          </div>
          <div style={{ textAlign: 'center', marginTop: '40px' }}>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>
              Start New Scan
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container">
        <div className="hero">
          <h1>Security Report</h1>
          <p>Comprehensive analysis for {scanResult.url || scanResult.deploymentUrl}</p>
        </div>

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
                {scanResult.scan_result?.ssl_valid ? '✓' : '✗'}
              </div>
              <div style={{ color: '#a1a1aa' }}>SSL Certificate</div>
            </div>
          </div>
        </div>

        {/* Security Issues Formatted Display */}
        {scanResult.scan_result?.flags && (
          <div className="card">
            <h3>🔍 Security Issues Analysis</h3>
            <SecurityIssueFormatter 
              issues={scanResult.scan_result.flags} 
              scanResult={scanResult.scan_result}
            />
          </div>
        )}

        <div className="card">
          <h3>AI Security Advisor</h3>
          
          {scanResult.ai_assistant_advice && (
            <div style={{ 
              background: 'rgba(0, 212, 255, 0.1)', 
              border: '1px solid rgba(0, 212, 255, 0.2)',
              borderRadius: '8px',
              padding: '20px',
              marginBottom: '24px'
            }}>
              <h4 style={{ marginBottom: '12px', color: '#00d4ff' }}>Initial Analysis</h4>
              <p>{scanResult.ai_assistant_advice}</p>
            </div>
          )}

          <div style={{ 
            background: 'rgba(0, 0, 0, 0.3)', 
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            padding: '20px',
            maxHeight: '300px',
            overflowY: 'auto',
            marginBottom: '20px'
          }}>
            {chatHistory.length === 0 ? (
              <div style={{ 
                color: '#a1a1aa', 
                fontStyle: 'italic',
                textAlign: 'center',
                padding: '40px 20px'
              }}>
                💬 Ask me anything about your security scan results...
              </div>
            ) : (
              chatHistory.map((chat, index) => (
                <ChatResponseFormatter 
                  key={index}
                  message={chat.message}
                  type={chat.type}
                />
              ))
            )}
            {isLoading && (
              <div style={{ color: '#a1a1aa', fontStyle: 'italic' }}>
                🤖 AI is analyzing...
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              className="input"
              placeholder="Ask about vulnerabilities, security headers, or remediation steps..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleChat()}
              disabled={isLoading}
              style={{ flex: 1 }}
            />
            <button 
              className="btn btn-primary" 
              onClick={handleChat}
              disabled={isLoading || !chatInput.trim()}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportPage;

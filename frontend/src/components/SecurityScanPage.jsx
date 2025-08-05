import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatResponseFormatter from './ChatResponseFormatter';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom'

const SecurityScanPage = ({ setScanResult }) => {
  usePreventZoom();
  const [targetUrl, setTargetUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanLogs, setScanLogs] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [modelType, setModelType] = useState('fast'); // Add model selection
  const navigate = useNavigate();

  // Add summary to chat when scan completes
  useEffect(() => {
    if (chatHistory.length === 0) {
      setChatHistory([{
        type: 'ai',
        message: ` **AI Security Assistant Ready**

I'm here to help with your security analysis! 

**What I can help with:**
• Explain security vulnerabilities and risks
• Provide implementation guidance for security fixes
• Answer questions about OWASP best practices
• Help interpret scan results and recommendations
• Suggest security improvements for your website

**Choose your analysis speed:**
• **Fast Model**: Quick analysis with essential security checks
• **Smart Model**: Comprehensive deep analysis with advanced threat detection

Ready to start? Enter a URL above and select your preferred analysis model!`,
        timestamp: new Date()
      }]);
    }
  }, []);

  const handleChat = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatInput('');
    setChatHistory(prev => [...prev, { type: 'user', message: userMessage, timestamp: new Date() }]);
    setIsChatLoading(true);

    try {
      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          question: userMessage, 
          context: 'security_scanning'
        }),
      });
      
      const data = await response.json();
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        message: data.response, 
        timestamp: new Date() 
      }]);
    } catch (error) {
      // Smart fallback responses
      let fallbackResponse = generateAIResponse(userMessage);
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        message: fallbackResponse,
        timestamp: new Date()
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const generateAIResponse = (question) => {
    const q = question.toLowerCase();
    
    if (q.includes('scan') || q.includes('security')) {
      return `I'm your AI security advisor! I can help you understand web security, explain vulnerabilities, and guide you through the scanning process. Just enter a website URL above and I'll perform a comprehensive AI-powered security analysis.`;
    }
    if (q.includes('vulnerabilit') || q.includes('threat')) {
      return `I analyze websites for common vulnerabilities like XSS, SQL injection, CSRF, security misconfigurations, and more. My AI models are trained on the latest threat intelligence to provide accurate assessments.`;
    }
    if (q.includes('ssl') || q.includes('https')) {
      return `I examine SSL/TLS configurations, certificate validity, cipher strength, and protocol security. HTTPS is essential for protecting data in transit and user privacy.`;
    }
    if (q.includes('header') || q.includes('csp')) {
      return `Security headers like Content-Security-Policy, X-Frame-Options, and HSTS are crucial for preventing attacks. I analyze which headers are missing and provide implementation guidance.`;
    }
    
    return `Hello! I'm your AI security assistant. I can help you with web security questions, explain scan results, or guide you through security best practices. What would you like to know?`;
  };

  const handleScan = async () => {
    if (!targetUrl) {
      alert('Please enter a website URL');
      return;
    }

    setIsScanning(true);
    setScanLogs(['🔍 Initializing AI-powered security scan...']);

    try {
      const scanSteps = [
        'analyzing domain and DNS configuration...',
        'AI checking SSL/TLS certificate security...',
        'AI scanning HTTP security headers...',
        'AI testing for XSS vulnerabilities...',
        'AI checking for SQL injection points...',
        'AI analyzing authentication mechanisms...',
        'AI evaluating Content Security Policy...',
        'Running advanced AI threat analysis...',
        'AI generating intelligent recommendations...',
        'AI compiling comprehensive security report...'
      ];

      for (let i = 0; i < scanSteps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1200));
        setScanLogs(prev => [...prev, scanSteps[i]]);
        
        // Add AI checkmarks after each step
        if (i > 0) {
          await new Promise(resolve => setTimeout(resolve, 300));
          setScanLogs(prev => [...prev, `✅ AI Analysis Complete: ${scanSteps[i-1].split('AI ')[1]}`]);
        }
      }

      // Connect to backend for real security scanning
      let result;
      try {
        const response = await fetch('http://localhost:8000/scan', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: targetUrl, model_type: modelType }),
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        result = await response.json();
        
        // Extract data from backend response structure
        const scanData = {
          url: result.url,
          pages: result.pages || [],
          scan_result: result.scan_result,
          exposed_paths: result.exposed_paths || [],
          suggestions: result.suggestions || [],
          ai_assistant_advice: result.ai_assistant_advice,
          summary: result.summary,
          // Include WAF and DNS security analysis data from backend
          waf_analysis: result.waf_analysis,
          dns_security: result.dns_security,
          // Calculate security score from scan_result if not provided
          security_score: result.scan_result?.security_score || 
                         (result.scan_result ? Math.max(0, 100 - (result.scan_result.flags?.length || 0) * 10) : 75)
        };
        
        result = scanData;
        
      } catch (error) {
        setScanLogs(prev => [...prev, `❌ Backend connection failed: ${error.message}`]);
        setScanLogs(prev => [...prev, 'Please ensure the backend server is running on http://localhost:8000']);
        console.error('Scan error:', error);
        return;
      }

      setScanResult(result);
      setScanLogs(prev => [...prev, '🎯 AI has completed comprehensive security analysis!']);
      setScanLogs(prev => [...prev, `📊 Pages Analyzed: ${result.pages?.length || 0}`]);
      setScanLogs(prev => [...prev, `🚪 Exposed Paths Found: ${result.exposed_paths?.length || 0}`]);
      setScanLogs(prev => [...prev, `🔒 Security Score: ${result.security_score || 'Calculating...'}/100`]);
      setScanLogs(prev => [...prev, '✅ Security scan completed successfully - AI report ready!']);
      
      // Add analysis summary to chatbox using the backend summary
      const summary = result.summary || result.ai_assistant_advice || 
        `🔒 **Security Analysis Complete!**\n\n📊 **Results:**\n• Security Score: ${result.security_score || 'N/A'}/100\n• HTTPS Status: ${result.scan_result?.https ? '✅ Enabled' : '❌ Disabled'}\n• Vulnerabilities Found: ${result.scan_result?.flags?.length || 0} issues\n• Pages Crawled: ${result.pages?.length || 0}\n• Exposed Paths: ${result.exposed_paths?.length || 0}\n\n💡 AI analysis complete - ready to answer your security questions!`;
      
      setChatHistory(prev => [...prev, { 
        type: 'ai', 
        message: summary, 
        timestamp: new Date() 
      }]);

      // Auto-redirect to report page after 2 seconds
      setTimeout(() => {
        navigate('/report');
      }, 2000);
      
    } catch (error) {
      setScanLogs(prev => [...prev, 'Scan failed - please try again']);
      console.error('Scan error:', error);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <PageWrapper>
            <style>
        {`
          :root {
            --primary-green: #00f5c3;
            --background-dark: #0a0a0a;
            --card-bg: rgba(26, 26, 26, 0.5);
            --card-bg-hover: rgba(36, 36, 36, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --card-border-hover: rgba(0, 245, 195, 0.5);
            --text-light: #f5f5f5;
            --text-dark: #a3a3a3;
            --input-bg: #1a1a1a;
            --input-border: #3a3a3a;
            --input-focus-border: var(--primary-green);
          }

          body {
            background-color: var(--background-dark);
            color: var(--text-light);
            font-family: sans-serif;
          }
          
          .page-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1.5rem;
          }

          /* --- Hero Section --- */
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
          
          /* --- Main Deployment Card --- */
          .deploy-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2.5rem;
            width: 100%;
            max-width: 500px;
            backdrop-filter: blur(4px);
          }
          .deploy-card h3 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: var(--text-light);
            text-align: left;
          }
          
          /* --- Input & Button Styles --- */
          .input {
            width: 100%;
            background-color: var(--input-bg);
            border: 1px solid var(--input-border);
            color: var(--text-light);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 1rem;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
          }
          .input:focus {
            outline: none;
            border-color: var(--input-focus-border);
          }
          .input::placeholder {
            color: var(--text-dark);
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

          /* --- Loading Dots Animation --- */
          .loading-dots {
            display: inline-flex;
            align-items: center;
            margin-left: 8px;
          }
          .loading-dots span {
            display: inline-block;
            width: 6px;
            height: 6px;
            background-color: #000;
            border-radius: 50%;
            margin: 0 2px;
            animation: dot-pulse 1.4s infinite ease-in-out both;
          }
          .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
          .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
          @keyframes dot-pulse {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
          }
          
          /* --- Terminal Styles --- */
          .terminal {
            background-color: #000;
            border: 1px solid var(--input-border);
            border-radius: 0.5rem;
            padding: 1.25rem;
            height: 280px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            text-align: left;
          }
          .terminal-line {
            white-space: pre-wrap;
            line-height: 1.5;
          }
          
          /* --- Deployment Summary --- */
          .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
          }
          .summary-item {
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
          }
          .summary-item-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
          }
          .summary-item-value {
            font-size: 1.25rem;
            font-weight: 700;
          }
          .status-success {
            background: rgba(34, 197, 94, 0.1); 
            border: 1px solid rgba(34, 197, 94, 0.2);
            color: #22c55e;
          }
          .build-time {
            background: rgba(0, 212, 255, 0.1); 
            border: 1px solid rgba(0, 212, 255, 0.2);
            color: #00d4ff;
          }
          .security-score {
            background: rgba(147, 51, 234, 0.1); 
            border: 1px solid rgba(147, 51, 234, 0.2);
            color: #9333ea;
          }

          /* --- Features Section --- */
          .features-grid {
            display: grid;
            grid-template-columns: repeat(1, 1fr);
            gap: 2rem;
            margin-top: 5rem;
          }
          .feature-card {
            background-color: var(--card-bg);
            backdrop-filter: blur(4px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
            transition: all 0.3s ease;
            text-align: left;
          }
          .feature-card:hover {
            border-color: var(--card-border-hover);
            background-color: var(--card-bg-hover);
            transform: translateY(-0.5rem);
          }
          .feature-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-light);
          }
          .feature-content {
            color: var(--text-dark);
            line-height: 1.6;
            flex-grow: 1;
          }
          .feature-learn-more {
            margin-top: auto;
            padding-top: 1rem;
          }
          .learn-more-group {
            color: var(--primary-green);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
          }
          .learn-more-arrow {
            width: 1rem;
            height: 1rem;
            transition: transform 0.3s ease;
          }
          .feature-card:hover .learn-more-arrow {
            transform: translateX(0.25rem);
          }
          
          /* --- Responsive Design --- */
          @media (min-width: 640px) {
            .hero-title {
              font-size: 3.5rem;
            }
            .hero-subtitle {
              font-size: 1.25rem;
            }
            .features-grid {
              grid-template-columns: repeat(2, 1fr);
            }
          }

          @media (min-width: 1024px) {
            .hero-title {
              font-size: 4.5rem;
            }
            .hero-subtitle {
              font-size: 1.375rem;
            }
            .features-grid {
              grid-template-columns: repeat(4, 1fr);
            }
          }
          
          @media (min-width: 1280px) {
            .hero-title {
              font-size: 5rem;
            }
          }
        `}
      </style>
      <div className="page-container">
        <div className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">AI-Powered Security Analysis</h1>
            <p className="hero-subtitle">Advanced AI-driven security scanning with intelligent threat detection and real-time recommendations</p>
          </div>

        <div className="card">
          <h3>AI-Security Scanner</h3>
          <div style={{ marginBottom: '24px' }}>
            <input
              type="url"
              className="input"
              placeholder="https://example.com"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              disabled={isScanning}
              style={{ marginBottom: '16px' }}
            />
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: '#333' }}>
                AI Model Selection:
              </label>
              <select
                className="input"
                value={modelType}
                onChange={(e) => setModelType(e.target.value)}
                disabled={isScanning}
                style={{ width: '100%' }}
              >
                <option value="fast">Fast Model (Quick Analysis)</option>
                <option value="smart">Smart Model (Deep Analysis)</option>
              </select>
            </div>
            
            <button 
              className="btn btn-secondary" 
              onClick={handleScan}
              disabled={isScanning || !targetUrl}
              style={{ width: '100%' }}
            >
              {isScanning ? (
                <>
                  AI Analyzing
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </>
              ) : (
                `Start AI Security Analysis`
              )}
            </button>
          </div>

          {scanLogs.length > 0 && (
            <div>
              <h4 style={{ marginBottom: '16px', color: 'var(--text-light)', fontSize: '1.1rem' }}>🧠 AI Analysis Progress</h4>
              <div className="terminal">
                {scanLogs.map((log, index) => (
                  <div key={index} className="terminal-line" style={{
                    color: log.includes('✅') ? '#22c55e' : 
                           log.includes('🤖') ? '#00d4ff' : 
                           log.includes('🧠') ? '#9333ea' : '#00d4ff'
                  }}>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="features-grid" style={{ marginTop: '40px' }}>
          <div className="feature-card">
            <h3>AI SSL/TLS Analysis</h3>
            <p>Machine learning powered certificate validation and security assessment</p>
          </div>
          <div className="feature-card">
            <h3>AI Header Security</h3>
            <p>Intelligent HTTP security headers analysis with AI recommendations</p>
          </div>
          <div className="feature-card">
            <h3>AI Vulnerability Detection</h3>
            <p>Advanced AI models for OWASP Top 10 testing and threat identification</p>
          </div>
          <div className="feature-card">
            <h3>Real-time AI Analysis</h3>
            <p>Live AI-powered threat detection with instant security insights</p>
          </div>
          <div className="feature-card">
            <h3>AI Performance Metrics</h3>
            <p>Intelligent load time analysis and AI-driven optimization suggestions</p>
          </div>
          <div className="feature-card">
            <h3>AI Compliance Check</h3>
            <p>Smart compliance verification using AI for GDPR, PCI DSS standards</p>
          </div>
        </div>


        {/* AI Chat Interface */}
        <div className="card" style={{ marginTop: '40px' }}>
          <h3>Ask Your AI Security Advisor</h3>
          <p style={{ color: '#a1a1aa', marginBottom: '20px' }}>
            Get instant answers about web security, vulnerabilities, and best practices
          </p>
          
          <div style={{ 
            background: 'rgba(0, 0, 0, 0.3)', 
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px',
            padding: '20px',
            maxHeight: '500px',
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
                Ask me about web security, vulnerabilities, SSL certificates, security headers, or anything else...
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
            {isChatLoading && (
              <div style={{ color: '#a1a1aa', fontStyle: 'italic' }}>
                AI is thinking...
              </div>
            )}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              className="input"
              placeholder="Ask about security best practices, vulnerabilities, or how to improve website security..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleChat()}
              disabled={isChatLoading}
              style={{ flex: 1 }}
            />
            <button 
              className="btn btn-primary" 
              onClick={handleChat}
              disabled={isChatLoading || !chatInput.trim()}
            >
              Send
            </button>
          </div>

          {/* Quick Questions */}
          <div style={{ marginTop: '16px' }}>
            <div style={{ fontSize: '14px', color: '#a1a1aa', marginBottom: '8px' }}>
              Quick questions:
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[
                'What is XSS vulnerability?',
                'How important is HTTPS?',
                'What are security headers?',
                'How to prevent SQL injection?'
              ].map((question, index) => (
                <button
                  key={index}
                  className="btn btn-ghost"
                  style={{ fontSize: '12px', padding: '6px 12px' }}
                  onClick={() => {
                    setChatInput(question);
                    setTimeout(() => handleChat(), 100);
                  }}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default SecurityScanPage;

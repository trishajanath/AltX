import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
const DeployPage = ({ setScanResult }) => {
  usePreventZoom();
  const [repoUrl, setRepoUrl] = useState('');
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployLogs, setDeployLogs] = useState([]);
  const [deploymentStatus, setDeploymentStatus] = useState(null);

  const handleDeploy = async () => {
    if (!repoUrl) {
      alert('Please enter a GitHub repository URL');
      return;
    }

    setIsDeploying(true);
    setDeployLogs(['🚀 Starting deployment process...']);
    setDeploymentStatus(null);

    try {
      const deploySteps = [
        '📦 Cloning repository...',
        '🔍 Analyzing project structure...',
        '🛡️ Running security pre-checks...',
        '📋 Installing dependencies...',
        '🏗️ Building application...',
        '🔒 Performing security scan...',
        '🌐 Deploying to edge network...',
        '✅ Deployment complete!'
      ];

      for (let i = 0; i < deploySteps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 1500));
        setDeployLogs(prev => [...prev, deploySteps[i]]);
        
        // Simulate security scan step
        if (i === 5) {
          setDeployLogs(prev => [...prev, '🔍 Scanning for vulnerabilities...']);
          await new Promise(resolve => setTimeout(resolve, 1000));
          setDeployLogs(prev => [...prev, '📊 Generating security report...']);
        }
      }

      // Mock deployment result
      const deployResult = {
        url: repoUrl,
        deploymentUrl: `https://${repoUrl.split('/').pop()}-${Math.random().toString(36).substr(2, 9)}.vercel.app`,
        status: 'success',
        buildTime: '2m 34s',
        securityScore: Math.floor(Math.random() * 20) + 80, // 80-100
        vulnerabilities: {
          critical: 0,
          high: Math.floor(Math.random() * 2),
          medium: Math.floor(Math.random() * 3),
          low: Math.floor(Math.random() * 5)
        },
        recommendations: [
          'Update dependencies to latest versions',
          'Add Content Security Policy headers',
          'Enable HTTPS redirects',
          'Implement rate limiting'
        ]
      };

      setDeploymentStatus(deployResult);
      setScanResult(deployResult);
      setDeployLogs(prev => [...prev, `🌍 Live at: ${deployResult.deploymentUrl}`]);

    } catch (error) {
      setDeployLogs(prev => [...prev, '❌ Deployment failed']);
      console.error('Deploy error:', error);
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <PageWrapper>
      {/* The <style> block contains all the necessary CSS. 
        CSS variables are defined at the top for easy theme management.
      */}
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
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
          }

          /* --- Hero Section --- */
          .hero-section {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 5rem 0;
          }
          .hero-title {
            font-size: 3rem; /* Adjusted for better mobile view */
            font-weight: 900;
            letter-spacing: -0.05em;
            color: var(--text-light);
            text-shadow: 0 0 15px rgba(0, 245, 195, 0.4), 0 0 30px rgba(0, 245, 195, 0.2);
          }
          .hero-title-highlight {
            color: var(--primary-green);
          }
          .hero-subtitle {
            margin-top: 1.5rem;
            max-width: 42rem;
            font-size: 1.125rem;
            line-height: 1.75rem;
            color: var(--text-dark);
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
            padding: 0.5rem 1rem;
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
            padding: 1rem;
            height: 250px;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.875rem;
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
              font-size: 4.5rem;
            }
            .hero-subtitle {
              font-size: 1.25rem;
            }
            .features-grid {
              grid-template-columns: repeat(2, 1fr);
            }
          }

          @media (min-width: 1024px) {
            .features-grid {
              grid-template-columns: repeat(4, 1fr);
            }
            .hero-title {
              font-size: 5rem;
            }
          }
        `}
      </style>
      <div className="page-container">
        <div className="hero-section">
          <h1 className="hero-title">
            Deploy with <span className="hero-title-highlight">Confidence</span>
          </h1>
          <p className="hero-subtitle">
            Deploy your GitHub repository with automatic security analysis and continuous monitoring. One click is all it takes.
          </p>

          <div className="deploy-card">
            <h3>Repository Deployment</h3>
            <div style={{ marginBottom: '24px' }}>
              <input
                type="url"
                className="input"
                placeholder="https://github.com/username/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                disabled={isDeploying}
                style={{ marginBottom: '16px' }}
              />
              <button 
                className="btn btn-secondary" 
                onClick={handleDeploy}
                disabled={isDeploying || !repoUrl}
                style={{ width: '100%' }}
              >
                {isDeploying ? (
                  <>
                    Deploying
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </>
                ) : (
                  'Deploy Now'
                )}
              </button>
            </div>

            {deployLogs.length > 1 && (
              <div>
                <h4 style={{ marginBottom: '16px', textAlign: 'left', fontWeight: '600' }}>Deployment Progress</h4>
                <div className="terminal">
                  {deployLogs.map((log, index) => (
                    <div key={index} className="terminal-line">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {deploymentStatus && (
              <div style={{ marginTop: '32px' }}>
                <h4 style={{ marginBottom: '16px', textAlign: 'left', fontWeight: '600' }}>Deployment Summary</h4>
                <div className="summary-grid">
                  <div className="summary-item status-success">
                    <div className="summary-item-title">Status</div>
                    <div className="summary-item-value">✅ Success</div>
                  </div>
                  <div className="summary-item build-time">
                    <div className="summary-item-title">Build Time</div>
                    <div className="summary-item-value">{deploymentStatus.buildTime}</div>
                  </div>
                  <div className="summary-item security-score">
                    <div className="summary-item-title">Security</div>
                    <div className="summary-item-value">{deploymentStatus.securityScore}/100</div>
                  </div>
                </div>
                
                <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                  <a 
                    href={deploymentStatus.deploymentUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                  >
                    Visit Site
                  </a>
                  <button className="btn btn-secondary" style={{ flex: 1 }}>
                    View Analytics
                  </button>
                </div>
              </div>
            )}
          </div>
          
          <div className="features-grid">
            <div className="feature-card">
              <h3 className="feature-title">Automatic Builds</h3>
              <p className="feature-content">Smart build detection with optimized bundling and compression for any framework.</p>
               <div className="feature-learn-more">
                    <div className="learn-more-group">
                        <span>Learn More</span>
                        <div className="learn-more-arrow"><ArrowRight size={16} /></div>
                    </div>
                </div>
            </div>
            <div className="feature-card">
              <h3 className="feature-title">Edge Deployment</h3>
              <p className="feature-content">Global CDN distribution ensures maximum performance and reliability for your users.</p>
               <div className="feature-learn-more">
                    <div className="learn-more-group">
                        <span>Learn More</span>
                        <div className="learn-more-arrow"><ArrowRight size={16} /></div>
                    </div>
                </div>
            </div>
            <div className="feature-card">
              <h3 className="feature-title">Security Scanning</h3>
              <p className="feature-content">Real-time vulnerability detection and dependency analysis on every single deploy.</p>
               <div className="feature-learn-more">
                    <div className="learn-more-group">
                        <span>Learn More</span>
                        <div className="learn-more-arrow"><ArrowRight size={16} /></div>
                    </div>
                </div>
            </div>
            <div className="feature-card">
              <h3 className="feature-title">Continuous Monitoring</h3>
              <p className="feature-content">24/7 uptime monitoring with instant alerts to keep your application online and healthy.</p>
               <div className="feature-learn-more">
                    <div className="learn-more-group">
                        <span>Learn More</span>
                        <div className="learn-more-arrow"><ArrowRight size={16} /></div>
                    </div>
                </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default DeployPage;

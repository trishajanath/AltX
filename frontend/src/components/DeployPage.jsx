import React, { useState } from 'react';
import PageWrapper from './PageWrapper';

const DeployPage = ({ setScanResult }) => {
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
      <div className="page-container">
        <div className="content-wrapper">
          <div className="hero">
            <h1>Deploy GitHub Project</h1>
            <p>Deploy your GitHub repository with automatic security analysis and monitoring</p>
          </div>

          <div className="card">
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
              className="btn btn-primary" 
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

          {deployLogs.length > 0 && (
            <div>
              <h4 style={{ marginBottom: '16px' }}>Deployment Progress</h4>
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
              <h4 style={{ marginBottom: '16px' }}>Deployment Summary</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div style={{ 
                  background: 'rgba(34, 197, 94, 0.1)', 
                  border: '1px solid rgba(34, 197, 94, 0.2)',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{ color: '#22c55e', fontWeight: '600' }}>Status</div>
                  <div>✅ Deployed Successfully</div>
                </div>
                <div style={{ 
                  background: 'rgba(0, 212, 255, 0.1)', 
                  border: '1px solid rgba(0, 212, 255, 0.2)',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{ color: '#00d4ff', fontWeight: '600' }}>Build Time</div>
                  <div>{deploymentStatus.buildTime}</div>
                </div>
                <div style={{ 
                  background: 'rgba(147, 51, 234, 0.1)', 
                  border: '1px solid rgba(147, 51, 234, 0.2)',
                  borderRadius: '8px',
                  padding: '16px'
                }}>
                  <div style={{ color: '#9333ea', fontWeight: '600' }}>Security Score</div>
                  <div>{deploymentStatus.securityScore}/100</div>
                </div>
              </div>
              
              <div style={{ marginTop: '24px' }}>
                <a 
                  href={deploymentStatus.deploymentUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                  style={{ marginRight: '12px' }}
                >
                  Visit Site
                </a>
                <button className="btn btn-secondary">
                  View Analytics
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="features-grid" style={{ marginTop: '40px' }}>
          <div className="feature-card">
            <h3>Automatic Builds</h3>
            <p>Smart build detection with optimized bundling and compression</p>
          </div>
          <div className="feature-card">
            <h3>Edge Deployment</h3>
            <p>Global CDN distribution for maximum performance</p>
          </div>
          <div className="feature-card">
            <h3>Security Scanning</h3>
            <p>Real-time vulnerability detection and reporting</p>
          </div>
          <div className="feature-card">
            <h3>Continuous Monitoring</h3>
            <p>24/7 uptime monitoring with instant alerts</p>
          </div>
        </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default DeployPage;

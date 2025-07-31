import React from 'react';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="page">
      <div className="container">
        <div className="hero">
          <h1>Deploy with AI Confidence</h1>
          <p>
            One-click GitHub deployments with real-time AI security analysis. 
            Monitor vulnerabilities, get intelligent recommendations, and chat with our AI security advisor.
          </p>
          <div className="hero-buttons">
            <button 
              className="btn btn-primary btn-large"
              onClick={() => navigate('/deploy')}
            >
              🚀 Deploy Project
            </button>
            <button 
              className="btn btn-secondary btn-large"
              onClick={() => navigate('/security')}
            >
              🤖 AI Security Chat
            </button>
          </div>
        </div>

        <div className="features-grid">
          <div className="feature-card" onClick={() => navigate('/deploy')}>
            <span className="feature-icon">🚀</span>
            <h3>One-Click Deploy</h3>
            <p>
              Deploy GitHub repositories instantly with automated builds, optimizations, 
              and real-time security monitoring throughout the process.
            </p>
          </div>

          <div className="feature-card" onClick={() => navigate('/security')}>
            <span className="feature-icon">🔒</span>
            <h3>Security Analysis</h3>
            <p>
              Comprehensive security scanning for any website or application. 
              Get detailed vulnerability reports with actionable insights.
            </p>
          </div>

          <div className="feature-card" onClick={() => navigate('/security')}>
            <span className="feature-icon">🤖</span>
            <h3>AI Security Advisor</h3>
            <p>
              Chat with our intelligent AI security advisor for personalized recommendations, 
              threat analysis, and real-time security guidance.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">📊</span>
            <h3>Real-time Monitoring</h3>
            <p>
              Continuous monitoring with instant alerts, performance metrics, 
              and security status updates for all your deployed projects.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">⚡</span>
            <h3>Edge Deployment</h3>
            <p>
              Global edge network deployment for maximum performance, 
              automatic scaling, and zero-downtime updates.
            </p>
          </div>

          <div className="feature-card">
            <span className="feature-icon">🔍</span>
            <h3>Vulnerability Detection</h3>
            <p>
              Advanced scanning for OWASP Top 10, dependency vulnerabilities, 
              configuration issues, and security misconfigurations.
            </p>
          </div>
        </div>

        <div className="card" style={{ textAlign: 'center', marginTop: '80px' }}>
          <h2 style={{ marginBottom: '16px', fontSize: '32px', fontWeight: '700' }}>
            Trusted by Developers Worldwide
          </h2>
          <p style={{ fontSize: '18px', color: '#a1a1aa', marginBottom: '32px' }}>
            Join thousands of developers who deploy with confidence using our AI-powered security platform.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '48px', flexWrap: 'wrap' }}>
            <div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#00d4ff' }}>10,000+</div>
              <div style={{ fontSize: '14px', color: '#a1a1aa' }}>Projects Deployed</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#00d4ff' }}>50,000+</div>
              <div style={{ fontSize: '14px', color: '#a1a1aa' }}>Security Scans</div>
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#00d4ff' }}>99.9%</div>
              <div style={{ fontSize: '14px', color: '#a1a1aa' }}>Uptime</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;

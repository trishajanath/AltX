import React from 'react';
import PageWrapper from './PageWrapper';

const SecurityIssueFormatter = ({ issues, scanResult }) => {
  // Categorize issues by severity and type
  const categorizeIssues = (flags) => {
    const categories = {
      critical: [],
      high: [],
      medium: [],
      low: [],
      info: []
    };

    flags.forEach(flag => {
      const lowerFlag = flag.toLowerCase();
      
      // Critical issues
      if (lowerFlag.includes('https') || lowerFlag.includes('ssl')) {
        categories.critical.push({
          issue: flag,
          description: 'HTTPS is essential for protecting data in transit and user privacy',
          impact: 'High - Data transmitted in plain text',
          recommendation: 'Enable HTTPS/SSL certificate immediately',
          priority: 'Critical'
        });
      }
      // High priority issues
      else if (lowerFlag.includes('content-security-policy') || lowerFlag.includes('csp')) {
        categories.high.push({
          issue: flag,
          description: 'Content Security Policy prevents XSS attacks by controlling resource loading',
          impact: 'High - Vulnerable to cross-site scripting attacks',
          recommendation: 'Implement Content-Security-Policy header with appropriate directives',
          priority: 'High'
        });
      }
      else if (lowerFlag.includes('x-frame-options')) {
        categories.high.push({
          issue: flag,
          description: 'X-Frame-Options prevents clickjacking attacks',
          impact: 'High - Vulnerable to clickjacking attacks',
          recommendation: 'Add X-Frame-Options header with DENY or SAMEORIGIN value',
          priority: 'High'
        });
      }
      else if (lowerFlag.includes('strict-transport-security') || lowerFlag.includes('hsts')) {
        categories.high.push({
          issue: flag,
          description: 'HSTS forces browsers to use HTTPS connections',
          impact: 'High - Vulnerable to protocol downgrade attacks',
          recommendation: 'Implement Strict-Transport-Security header',
          priority: 'High'
        });
      }
      // Medium priority issues
      else if (lowerFlag.includes('x-content-type-options')) {
        categories.medium.push({
          issue: flag,
          description: 'Prevents MIME type sniffing attacks',
          impact: 'Medium - Vulnerable to MIME confusion attacks',
          recommendation: 'Add X-Content-Type-Options: nosniff header',
          priority: 'Medium'
        });
      }
      else if (lowerFlag.includes('x-xss-protection')) {
        categories.medium.push({
          issue: flag,
          description: 'Enables browser XSS filtering',
          impact: 'Medium - Reduced XSS protection',
          recommendation: 'Add X-XSS-Protection: 1; mode=block header',
          priority: 'Medium'
        });
      }
      else if (lowerFlag.includes('referrer-policy')) {
        categories.medium.push({
          issue: flag,
          description: 'Controls referrer information sent with requests',
          impact: 'Medium - Potential information leakage',
          recommendation: 'Implement Referrer-Policy header',
          priority: 'Medium'
        });
      }
      // Low priority or info
      else {
        categories.low.push({
          issue: flag,
          description: 'General security improvement',
          impact: 'Low - Minor security enhancement',
          recommendation: 'Review and implement as needed',
          priority: 'Low'
        });
      }
    });

    return categories;
  };

  const getSeverityColor = (priority) => {
    switch (priority) {
      case 'Critical': return '#ef4444';
      case 'High': return '#f97316';
      case 'Medium': return '#eab308';
      case 'Low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getSeverityIcon = (priority) => {
    switch (priority) {
      case 'Critical': return '🚨';
      case 'High': return '⚠️';
      case 'Medium': return '🔧';
      case 'Low': return '📝';
      default: return 'ℹ️';
    }
  };

  const categories = categorizeIssues(issues || []);

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
      <div className="security-issues-container">
        {/* Security Score Summary */}
        {scanResult && (
          <div className="security-score-card">
            <h3>Security Overview</h3>
            <div className="score-grid">
              <div className="score-item">
                <div className="score-value">{scanResult.security_score || 'N/A'}</div>
                <div className="score-label">Security Score</div>
              </div>
              <div className="score-item">
                <div className="score-value">{scanResult.https ? '✅' : '❌'}</div>
                <div className="score-label">HTTPS Status</div>
              </div>
              <div className="score-item">
                <div className="score-value">{scanResult.ssl_valid ? '✅' : '❌'}</div>
                <div className="score-label">SSL Certificate</div>
              </div>
            </div>
          </div>
        )}

        {/* Issues by Priority */}
        {Object.entries(categories).map(([priority, issues]) => {
          if (issues.length === 0) return null;
          
          return (
            <div key={priority} className="priority-section">
              <h4 style={{ color: getSeverityColor(priority.charAt(0).toUpperCase() + priority.slice(1)) }}>
                {getSeverityIcon(priority.charAt(0).toUpperCase() + priority.slice(1))} {priority.charAt(0).toUpperCase() + priority.slice(1)} Priority Issues ({issues.length})
              </h4>
              
              <div className="issues-grid">
                {issues.map((issue, index) => (
                  <div key={index} className="issue-card" style={{ borderLeft: `4px solid ${getSeverityColor(issue.priority)}` }}>
                    <div className="issue-header">
                      <span className="issue-priority" style={{ color: getSeverityColor(issue.priority) }}>
                        {getSeverityIcon(issue.priority)} {issue.priority}
                      </span>
                    </div>
                    
                    <div className="issue-title">{issue.issue}</div>
                    
                    <div className="issue-description">
                      <strong>Description:</strong> {issue.description}
                    </div>
                    
                    <div className="issue-impact">
                      <strong>Impact:</strong> {issue.impact}
                    </div>
                    
                    <div className="issue-recommendation">
                      <strong>Recommendation:</strong> {issue.recommendation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {/* Action Plan */}
        {issues && issues.length > 0 && (
          <div className="action-plan-card">
            <h3>🎯 Action Plan</h3>
            <div className="action-steps">
              {categories.critical.length > 0 && (
                <div className="action-step critical">
                  <span className="step-number">1</span>
                  <div className="step-content">
                    <strong>🚨 CRITICAL (Immediate Action Required):</strong>
                    <ul>
                      {categories.critical.map((issue, index) => (
                        <li key={index}>{issue.recommendation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
              
              {categories.high.length > 0 && (
                <div className="action-step high">
                  <span className="step-number">2</span>
                  <div className="step-content">
                    <strong>⚠️ HIGH (Implement This Week):</strong>
                    <ul>
                      {categories.high.map((issue, index) => (
                        <li key={index}>{issue.recommendation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
              
              {categories.medium.length > 0 && (
                <div className="action-step medium">
                  <span className="step-number">3</span>
                  <div className="step-content">
                    <strong>🔧 MEDIUM (Implement This Month):</strong>
                    <ul>
                      {categories.medium.map((issue, index) => (
                        <li key={index}>{issue.recommendation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
              
              {categories.low.length > 0 && (
                <div className="action-step low">
                  <span className="step-number">4</span>
                  <div className="step-content">
                    <strong>📝 LOW (Consider Implementing):</strong>
                    <ul>
                      {categories.low.map((issue, index) => (
                        <li key={index}>{issue.recommendation}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Security Issues by Priority */}
        {issues && issues.length > 0 && (
          <div className="card" style={{ marginBottom: '24px' }}>
            <h3>🚨 Security Issues by Priority</h3>
            
            {/* Critical Issues */}
            {categories.critical.length > 0 && (
              <div className="priority-section">
                <h4 style={{ color: '#ef4444', marginBottom: '12px' }}>
                  🚨 Critical Priority ({categories.critical.length})
                </h4>
                <div className="issues-grid">
                  {categories.critical.map((issue, index) => (
                    <div key={index} className="issue-card" style={{ borderLeft: '4px solid #ef4444' }}>
                      <div className="issue-title">{issue.issue}</div>
                      <div className="issue-description">
                        <strong>Impact:</strong> {issue.impact}
                      </div>
                      <div className="issue-recommendation">
                        <strong>Fix:</strong> {issue.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* High Priority Issues */}
            {categories.high.length > 0 && (
              <div className="priority-section">
                <h4 style={{ color: '#f97316', marginBottom: '12px' }}>
                  ⚠️ High Priority ({categories.high.length})
                </h4>
                <div className="issues-grid">
                  {categories.high.map((issue, index) => (
                    <div key={index} className="issue-card" style={{ borderLeft: '4px solid #f97316' }}>
                      <div className="issue-title">{issue.issue}</div>
                      <div className="issue-description">
                        <strong>Impact:</strong> {issue.impact}
                      </div>
                      <div className="issue-recommendation">
                        <strong>Fix:</strong> {issue.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Medium Priority Issues */}
            {categories.medium.length > 0 && (
              <div className="priority-section">
                <h4 style={{ color: '#eab308', marginBottom: '12px' }}>
                  🔧 Medium Priority ({categories.medium.length})
                </h4>
                <div className="issues-grid">
                  {categories.medium.map((issue, index) => (
                    <div key={index} className="issue-card" style={{ borderLeft: '4px solid #eab308' }}>
                      <div className="issue-title">{issue.issue}</div>
                      <div className="issue-description">
                        <strong>Impact:</strong> {issue.impact}
                      </div>
                      <div className="issue-recommendation">
                        <strong>Fix:</strong> {issue.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Low Priority Issues */}
            {categories.low.length > 0 && (
              <div className="priority-section">
                <h4 style={{ color: '#22c55e', marginBottom: '12px' }}>
                  📝 Low Priority ({categories.low.length})
                </h4>
                <div className="issues-grid">
                  {categories.low.map((issue, index) => (
                    <div key={index} className="issue-card" style={{ borderLeft: '4px solid #22c55e' }}>
                      <div className="issue-title">{issue.issue}</div>
                      <div className="issue-description">
                        <strong>Impact:</strong> {issue.impact}
                      </div>
                      <div className="issue-recommendation">
                        <strong>Fix:</strong> {issue.recommendation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Checklist for Missing Items */}
        {scanResult && (
          <div className="checklist-card">
            <h3>⚡ Action Checklist - Items to Fix</h3>
            <p style={{ color: '#a1a1aa', marginBottom: '16px', fontSize: '14px' }}>
              Check off items as you implement them:
            </p>
            <div className="checklist">
              {/* HTTPS/SSL */}
              {!scanResult.https && (
                <div className="checklist-item critical">
                  <input type="checkbox" />
                  <span>🚨 Enable HTTPS/SSL certificate (Critical)</span>
                </div>
              )}
              
              {/* Content Security Policy */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('content-security-policy')) && (
                <div className="checklist-item high">
                  <input type="checkbox" />
                  <span>⚠️ Add Content-Security-Policy header (High Priority)</span>
                </div>
              )}
              
              {/* Strict Transport Security */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('strict-transport-security')) && (
                <div className="checklist-item high">
                  <input type="checkbox" />
                  <span>⚠️ Set up HSTS header (High Priority)</span>
                </div>
              )}
              
              {/* X-Frame-Options */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-frame-options')) && (
                <div className="checklist-item medium">
                  <input type="checkbox" />
                  <span>🔧 Add X-Frame-Options header (Medium Priority)</span>
                </div>
              )}
              
              {/* X-Content-Type-Options */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-content-type-options')) && (
                <div className="checklist-item medium">
                  <input type="checkbox" />
                  <span>🔧 Configure X-Content-Type-Options header (Medium Priority)</span>
                </div>
              )}
              
              {/* X-XSS-Protection */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-xss-protection')) && (
                <div className="checklist-item medium">
                  <input type="checkbox" />
                  <span>🔧 Add X-XSS-Protection header (Medium Priority)</span>
                </div>
              )}
              
              {/* Referrer-Policy */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('referrer-policy')) && (
                <div className="checklist-item medium">
                  <input type="checkbox" />
                  <span>🔧 Implement Referrer-Policy header (Medium Priority)</span>
                </div>
              )}
              
              {/* Permissions-Policy */}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('permissions-policy')) && (
                <div className="checklist-item low">
                  <input type="checkbox" />
                  <span>📝 Implement Permissions-Policy header (Low Priority)</span>
                </div>
              )}
              
              {/* Always show the test item */}
              <div className="checklist-item">
                <input type="checkbox" />
                <span>✅ Test all security implementations</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  );
};

export default SecurityIssueFormatter; 
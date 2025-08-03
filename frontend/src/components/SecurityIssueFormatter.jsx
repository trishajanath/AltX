import React from 'react';
import PageWrapper from './PageWrapper';

const SecurityIssueFormatter = ({ issues, scanResult }) => {
  // Configuration for severity levels (color and icon)
  const severityConfig = {
    Critical: { color: 'var(--critical-color)', icon: '🚨' },
    High: { color: 'var(--high-color)', icon: '⚠️' },
    Medium: { color: 'var(--medium-color)', icon: '🔧' },
    Low: { color: 'var(--low-color)', icon: '📝' },
    default: { color: 'var(--info-color)', icon: 'ℹ️' },
  };

  const getSeverity = (priority) => {
    const capitalizedPriority = priority.charAt(0).toUpperCase() + priority.slice(1);
    return severityConfig[capitalizedPriority] || severityConfig.default;
  };

  // Categorize issues by severity and type
  const categorizeIssues = (flags) => {
    const categories = {
      critical: [], high: [], medium: [], low: [], info: []
    };

    flags.forEach(flag => {
      const lowerFlag = flag.toLowerCase();
      if (lowerFlag.includes('https') || lowerFlag.includes('ssl')) {
        categories.critical.push({ issue: flag, description: 'HTTPS is essential for protecting data in transit and user privacy.', impact: 'High - Data transmitted in plain text.', recommendation: 'Enable HTTPS/SSL certificate immediately.', priority: 'Critical' });
      } else if (lowerFlag.includes('content-security-policy') || lowerFlag.includes('csp')) {
        categories.high.push({ issue: flag, description: 'Content Security Policy prevents XSS attacks by controlling resource loading.', impact: 'High - Vulnerable to cross-site scripting attacks.', recommendation: 'Implement Content-Security-Policy header with appropriate directives.', priority: 'High' });
      } else if (lowerFlag.includes('x-frame-options')) {
        categories.high.push({ issue: flag, description: 'X-Frame-Options prevents clickjacking attacks.', impact: 'High - Vulnerable to clickjacking attacks.', recommendation: 'Add X-Frame-Options header with DENY or SAMEORIGIN value.', priority: 'High' });
      } else if (lowerFlag.includes('strict-transport-security') || lowerFlag.includes('hsts')) {
        categories.high.push({ issue: flag, description: 'HSTS forces browsers to use HTTPS connections.', impact: 'High - Vulnerable to protocol downgrade attacks.', recommendation: 'Implement Strict-Transport-Security header.', priority: 'High' });
      } else if (lowerFlag.includes('x-content-type-options')) {
        categories.medium.push({ issue: flag, description: 'Prevents MIME type sniffing attacks.', impact: 'Medium - Vulnerable to MIME confusion attacks.', recommendation: 'Add X-Content-Type-Options: nosniff header.', priority: 'Medium' });
      } else if (lowerFlag.includes('x-xss-protection')) {
        categories.medium.push({ issue: flag, description: 'Enables browser XSS filtering.', impact: 'Medium - Reduced XSS protection.', recommendation: 'Add X-XSS-Protection: 1; mode=block header.', priority: 'Medium' });
      } else if (lowerFlag.includes('referrer-policy')) {
        categories.medium.push({ issue: flag, description: 'Controls referrer information sent with requests.', impact: 'Medium - Potential information leakage.', recommendation: 'Implement Referrer-Policy header.', priority: 'Medium' });
      } else {
        categories.low.push({ issue: flag, description: 'General security improvement.', impact: 'Low - Minor security enhancement.', recommendation: 'Review and implement as needed.', priority: 'Low' });
      }
    });
    return categories;
  };

  const categories = categorizeIssues(issues || []);
  const allIssues = Object.values(categories).flat();

  return (
    <PageWrapper>
      <style>
        {`
          :root {
            --critical-color: #ef4444;
            --high-color: #f97316;
            --medium-color: #eab308;
            --low-color: #22c55e;
            --info-color: #6b7280;
          }
          .security-report-container {
            display: flex;
            flex-direction: column;
            gap: 2rem;
            font-family: 'Inter', sans-serif;
            padding: 2rem 1rem;
          }
          .report-card {
            background-color: var(--card-bg) !important;
            backdrop-filter: blur(8px);
            border: 1px solid var(--card-border) !important;
            border-radius: 1rem;
            padding: 1.5rem;
            transition: all 0.3s ease;
          }
          .report-card:hover {
            border-color: var(--card-border-hover) !important;
            background-color: var(--card-bg-hover) !important;
            transform: translateY(-0.25rem);
          }
          .report-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 1.5rem;
            color: var(--text-light);
          }
          .report-card h4 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 1rem;
            color: var(--text-light);
          }

          /* Severity Colors */
          .text-critical { color: var(--critical-color); }
          .text-high { color: var(--high-color); }
          .text-medium { color: var(--medium-color); }
          .text-low { color: var(--low-color); }

          .border-critical { border-left: 4px solid var(--critical-color); }
          .border-high { border-left: 4px solid var(--high-color); }
          .border-medium { border-left: 4px solid var(--medium-color); }
          .border-low { border-left: 4px solid var(--low-color); }

          /* Overview Score Card */
          .score-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1.5rem;
            text-align: center;
          }
          .score-item .score-value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
            color: var(--primary-green);
          }
          .score-item .score-label {
            font-size: 0.875rem;
            color: var(--text-dark);
            margin-top: 0.5rem;
          }

          /* Issues by Priority Section */
          .priority-section { margin-bottom: 2rem; }
          .priority-section:last-child { margin-bottom: 0; }
          .issues-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
          }
          .issue-card {
            background-color: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(4px);
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(0, 245, 195, 0.1);
            transition: all 0.3s ease;
          }
          .issue-card:hover {
            background-color: rgba(0, 0, 0, 0.6);
            border-color: rgba(0, 245, 195, 0.3);
          }
          .issue-card .issue-title {
            font-weight: 600;
            color: var(--text-light);
            margin-bottom: 0.75rem;
          }
          .issue-card div {
            font-size: 0.875rem;
            line-height: 1.5;
            color: var(--text-dark);
          }
          .issue-card div strong {
            color: var(--text-light);
            font-weight: 500;
          }
          .issue-card div:not(:last-child) { margin-bottom: 0.5rem; }

          /* Action Plan Card */
          .action-steps { display: flex; flex-direction: column; gap: 1.5rem; }
          .action-step { display: flex; align-items: flex-start; gap: 1rem; }
          .action-step .step-number {
            flex-shrink: 0;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: #fff;
          }
          .action-step.critical .step-number { background-color: var(--critical-color); }
          .action-step.high .step-number { background-color: var(--high-color); }
          .action-step.medium .step-number { background-color: var(--medium-color); }
          .action-step.low .step-number { background-color: var(--low-color); }
          .action-step-content strong { color: var(--text-light); }
          .action-step-content ul { padding-left: 1.25rem; margin: 0.5rem 0 0; color: var(--text-dark); }
          .action-step-content li { margin-bottom: 0.25rem; }

          /* SSL Analysis Card */
          .ssl-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            text-align: center;
            padding: 1.5rem;
            background-color: rgba(147, 51, 234, 0.1);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(147, 51, 234, 0.2);
            border-radius: 0.5rem;
            margin-bottom: 1.5rem;
          }
          .ssl-summary-item .icon { font-size: 1.75rem; margin-bottom: 0.5rem; }
          .ssl-summary-item .label { 
            font-weight: 600; 
            color: var(--text-light);
          }
          .ssl-summary-item .score-value { 
            font-size: 1.75rem; 
            color: #c084fc;
          }
          .ssl-details-grid, .ssl-issues-list, .ssl-warnings-list { margin-top: 1.5rem; }
          .ssl-details-grid h4, .ssl-issues-list h4, .ssl-warnings-list h4 { 
            margin-top: 0; 
            margin-bottom: 1rem; 
            color: var(--text-light);
          }
          .ssl-details-grid-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.75rem;
            font-size: 0.875rem;
            padding: 1rem;
            background-color: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(4px);
            border-radius: 0.5rem;
            border: 1px solid rgba(0, 245, 195, 0.1);
          }
          .ssl-details-grid-content div { color: var(--text-dark); }
          .ssl-details-grid-content strong { color: var(--text-light); font-weight: 500; }
          .ssl-issue, .ssl-warning {
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            backdrop-filter: blur(4px);
          }
          .ssl-issue { 
            background: rgba(239, 68, 68, 0.15); 
            border: 1px solid rgba(239, 68, 68, 0.3); 
            color: #fca5a5;
          }
          .ssl-warning { 
            background: rgba(234, 179, 8, 0.15); 
            border: 1px solid rgba(234, 179, 8, 0.3); 
            color: #fde047;
          }

          /* Checklist Card */
          .checklist p { 
            color: var(--text-dark); 
            margin: -1rem 0 1.5rem; 
            font-size: 0.875rem; 
          }
          .checklist-items { display: flex; flex-direction: column; gap: 0.75rem; }
          .checklist-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background-color: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(4px);
            border-radius: 0.5rem;
            border-left: 3px solid var(--info-color);
            border: 1px solid rgba(0, 245, 195, 0.1);
            transition: all 0.3s ease;
          }
          .checklist-item:hover {
            background-color: rgba(0, 0, 0, 0.6);
            border-color: rgba(0, 245, 195, 0.3);
          }
          .checklist-item input[type="checkbox"] { 
            width: 1rem; 
            height: 1rem; 
            accent-color: var(--primary-green);
          }
          .checklist-item span {
            color: var(--text-light);
          }
          .checklist-item.critical { border-left-color: var(--critical-color); }
          .checklist-item.high { border-left-color: var(--high-color); }
          .checklist-item.medium { border-left-color: var(--medium-color); }
          .checklist-item.low { border-left-color: var(--low-color); }
        `}
      </style>
      <div className="page-container">
        <div className="content-wrapper">
          <div className="security-report-container">
        
        {/* Security Score Summary */}
        {scanResult && (
          <div className="report-card">
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
                <div className="score-value">{scanResult.ssl_certificate?.valid ? '✅' : scanResult.https ? '⚠️' : '❌'}</div>
                <div className="score-label">SSL Certificate</div>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Report Section */}
        {allIssues.length > 0 && (
          <div className="report-card">
            <h3>Detailed Security Report</h3>
            {Object.entries(categories).map(([priority, issues]) => {
              if (issues.length === 0) return null;
              const severity = getSeverity(priority);
              return (
                <div key={priority} className="priority-section">
                  <h4 className={`text-${priority}`}>
                    {severity.icon} {priority.charAt(0).toUpperCase() + priority.slice(1)} Priority Issues ({issues.length})
                  </h4>
                  <div className="issues-grid">
                    {issues.map((issue, index) => (
                      <div key={index} className={`issue-card border-${issue.priority.toLowerCase()}`}>
                        <div className="issue-title">{issue.issue}</div>
                        <div><strong>Description:</strong> {issue.description}</div>
                        <div><strong>Impact:</strong> {issue.impact}</div>
                        <div><strong>Recommendation:</strong> {issue.recommendation}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Action Plan */}
        {allIssues.length > 0 && (
          <div className="report-card">
            <h3>🎯 Action Plan</h3>
            <div className="action-steps">
              {Object.entries(categories).map(([priority, issues], index) => {
                 if (issues.length === 0) return null;
                 const priorityCapitalized = priority.charAt(0).toUpperCase() + priority.slice(1);
                 return (
                    <div key={priority} className={`action-step ${priority}`}>
                      <span className="step-number">{index + 1}</span>
                      <div className="action-step-content">
                        <strong>{getSeverity(priority).icon} {priorityCapitalized} (Priority)</strong>
                        <ul>
                          {issues.map((issue, i) => <li key={i}>{issue.recommendation}</li>)}
                        </ul>
                      </div>
                    </div>
                 );
              })}
            </div>
          </div>
        )}

        {/* Detailed SSL Certificate Analysis */}
        {scanResult?.https && scanResult.ssl_certificate && (
          <div className="report-card">
            <h3>🔐 SSL Certificate Analysis</h3>
            <div className="ssl-summary-grid">
              <div className="ssl-summary-item">
                <div className="icon">{scanResult.ssl_certificate.valid ? '✅' : '❌'}</div>
                <div className={`label ${scanResult.ssl_certificate.valid ? 'text-low' : 'text-critical'}`}>
                  {scanResult.ssl_certificate.valid ? 'Valid' : 'Invalid'}
                </div>
              </div>

              {scanResult.ssl_certificate.certificate_details?.days_until_expiry !== undefined && (
                <div className="ssl-summary-item">
                  <div className="icon">
                    {scanResult.ssl_certificate.certificate_details.days_until_expiry > 30 ? '🟢' :
                     scanResult.ssl_certificate.certificate_details.days_until_expiry > 0 ? '🟡' : '🔴'}
                  </div>
                  <div className="label">
                    {scanResult.ssl_certificate.certificate_details.days_until_expiry > 0
                      ? `${scanResult.ssl_certificate.certificate_details.days_until_expiry} Days Left`
                      : 'Expired'}
                  </div>
                </div>
              )}

              {scanResult.ssl_certificate.cipher_info?.bits && (
                <div className="ssl-summary-item">
                  <div className="icon">
                    {scanResult.ssl_certificate.cipher_info.bits >= 256 ? '🔒' : '⚠️'}
                  </div>
                  <div className="label">{scanResult.ssl_certificate.cipher_info.bits}-bit Encryption</div>
                </div>
              )}

              {scanResult.ssl_certificate.ssl_score !== undefined && (
                <div className="ssl-summary-item">
                  <div className="score-value">{scanResult.ssl_certificate.ssl_score}</div>
                  <div className="label">SSL Score</div>
                </div>
              )}
            </div>

            {scanResult.ssl_certificate.certificate_details && (
              <div className="ssl-details-grid">
                <h4 style={{ color: 'var(--purple-text)'}}>Certificate Details</h4>
                <div className="ssl-details-grid-content">
                  <div><strong>Issued by:</strong> {scanResult.ssl_certificate.certificate_details.issuer?.commonName || 'N/A'}</div>
                  <div><strong>Subject:</strong> {scanResult.ssl_certificate.certificate_details.subject?.commonName || 'N/A'}</div>
                  <div><strong>Valid From:</strong> {new Date(scanResult.ssl_certificate.certificate_details.valid_from).toLocaleDateString()}</div>
                  <div><strong>Valid Until:</strong> {new Date(scanResult.ssl_certificate.certificate_details.valid_until).toLocaleDateString()}</div>
                  <div><strong>Cipher Suite:</strong> {scanResult.ssl_certificate.cipher_info?.name || 'N/A'}</div>
                  <div><strong>TLS Version:</strong> {scanResult.ssl_certificate.cipher_info?.version || 'N/A'}</div>
                </div>
              </div>
            )}

            {scanResult.ssl_certificate.security_issues?.length > 0 && (
              <div className="ssl-issues-list">
                <h4 className="text-critical">SSL Security Issues</h4>
                {scanResult.ssl_certificate.security_issues.map((issue, index) => (
                  <div key={index} className="ssl-issue">⚠️ {issue}</div>
                ))}
              </div>
            )}
            
            {(scanResult.ssl_certificate.self_signed || scanResult.ssl_certificate.expires_soon || scanResult.ssl_certificate.weak_cipher) && (
              <div className="ssl-warnings-list">
                <h4 className="text-medium">SSL Warnings</h4>
                {scanResult.ssl_certificate.self_signed && <div className="ssl-warning">⚠️ Self-signed certificate detected</div>}
                {scanResult.ssl_certificate.expires_soon && <div className="ssl-warning">⚠️ Certificate expires within 30 days</div>}
                {scanResult.ssl_certificate.weak_cipher && <div className="ssl-warning">⚠️ Weak cipher suite detected</div>}
              </div>
            )}
          </div>
        )}

        {/* Action Checklist for Missing Items */}
        {scanResult && (
          <div className="report-card checklist">
            <h3>⚡ Action Checklist - Items to Fix</h3>
            <p>A prioritized checklist based on your scan results. Check off items as you implement them.</p>
            <div className="checklist-items">
              {!scanResult.https && (
                <div className="checklist-item critical"><input type="checkbox" /><span>🚨 Enable HTTPS/SSL certificate</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('content-security-policy')) && (
                <div className="checklist-item high"><input type="checkbox" /><span>⚠️ Add Content-Security-Policy header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('strict-transport-security')) && (
                <div className="checklist-item high"><input type="checkbox" /><span>⚠️ Set up HSTS header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-frame-options')) && (
                <div className="checklist-item medium"><input type="checkbox" /><span>🔧 Add X-Frame-Options header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-content-type-options')) && (
                <div className="checklist-item medium"><input type="checkbox" /><span>🔧 Configure X-Content-Type-Options header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-xss-protection')) && (
                <div className="checklist-item medium"><input type="checkbox" /><span>🔧 Add X-XSS-Protection header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('referrer-policy')) && (
                <div className="checklist-item medium"><input type="checkbox" /><span>🔧 Implement Referrer-Policy header</span></div>
              )}
              {scanResult.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('permissions-policy')) && (
                <div className="checklist-item low"><input type="checkbox" /><span>📝 Implement Permissions-Policy header</span></div>
              )}
              <div className="checklist-item"><input type="checkbox" /><span>✅ Test all security implementations</span></div>
            </div>
          </div>
        )}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
};

export default SecurityIssueFormatter;
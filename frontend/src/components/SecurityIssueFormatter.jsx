import React from 'react';

const SecurityIssueFormatter = ({ issues, scanResult }) => {
    // This logic remains to categorize and add context to raw issue flags.
    const categorizeIssues = (flags) => {
        const categories = { critical: [], high: [], medium: [], low: [], info: [] };
        if (!flags || flags.length === 0) return categories;

        flags.forEach(flag => {
            const lowerFlag = flag.toLowerCase();
            // Your categorization logic remains the same...
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

    const getStatusTextAndClass = (value) => {
        if (value) return { text: 'Enabled', className: 'status-enabled' };
        return { text: 'Missing', className: 'status-missing' };
    };

    const httpsStatus = getStatusTextAndClass(scanResult?.https);
    const sslStatus = getStatusTextAndClass(scanResult?.ssl_certificate?.valid);

    return (
        <>
            <style>
                {`
                /* General Styles */
                .security-issue-formatter { font-family: sans-serif; }
                .report-section { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; }
                .report-section h3 { font-size: 1rem; font-weight: 500; color: #a1a1aa; margin: 0 0 2rem 0; text-transform: uppercase; letter-spacing: 1px; }
                .report-section h4 { font-size: 1.1rem; font-weight: 600; color: #ffffff; margin: 0 0 1rem 0; }
                .info-text { color: #a1a1aa; text-align: center; padding: 2rem 0; }

                /* Overview Section */
                .overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; }
                .overview-item .label { font-size: 0.8rem; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
                .overview-item .value { font-size: 1.75rem; font-weight: 600; color: #ffffff; }
                .overview-item .status-enabled { color: #ffffff; }
                .overview-item .status-missing { color: #a1a1aa; }

                /* Detailed Report Section */
                .severity-group { margin-bottom: 2rem; }
                .severity-group:last-child { margin-bottom: 0; }
                .issues-grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }
                .issue-card { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; padding: 1.5rem; }
                .issue-card .issue-title { font-weight: 600; color: #ffffff; margin-bottom: 1rem; }
                .issue-card .detail-grid { display: grid; grid-template-columns: 1fr; gap: 0.75rem; font-size: 0.9rem; line-height: 1.6; color: #a1a1aa; }
                .issue-card .detail-grid strong { color: #ffffff; font-weight: 500; }

                /* Action Plan */
                .action-list { padding-left: 1.25rem; margin: 0; display: flex; flex-direction: column; gap: 1rem; }
                .action-list li { line-height: 1.5; }
                .action-list .priority-label { font-weight: 600; color: #ffffff; text-transform: capitalize; }
                .action-list .recommendation-text { color: #a1a1aa; }

                /* SSL Analysis */
                .ssl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
                .ssl-item { text-align: center; }
                .ssl-details-list { font-size: 0.9rem; line-height: 1.8; }
                .ssl-details-list div { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
                .ssl-details-list div:last-child { border-bottom: none; }
                .ssl-details-list strong { color: #a1a1aa; font-weight: 500; }
                .ssl-issues-list { margin-top: 2rem; }
                .ssl-issue-item { background: rgba(0,0,0,0.2); border-left: 3px solid #a1a1aa; padding: 0.75rem 1rem; margin-bottom: 0.5rem; border-radius: 0.25rem; font-size: 0.9rem; }

                /* Checklist */
                .checklist-item { display: flex; align-items: center; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
                .checklist-item:last-child { border-bottom: none; }
                .checklist-progress-container { width: 32px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; }
                .checklist-item-text { flex-grow: 1; }
                `}
            </style>
            <div className="security-issue-formatter">
                {/* Security Overview */}
                <div className="report-section">
                    <h3>Security Overview</h3>
                    <div className="overview-grid">
                        <div className="overview-item">
                            <div className="label">Security Score</div>
                            <div className="value">{scanResult?.security_score || 'N/A'}</div>
                        </div>
                        <div className="overview-item">
                            <div className="label">HTTPS Status</div>
                            <div className={`value ${httpsStatus.className}`}>{httpsStatus.text}</div>
                        </div>
                        <div className="overview-item">
                            <div className="label">SSL Certificate</div>
                            <div className={`value ${sslStatus.className}`}>{sslStatus.text}</div>
                        </div>
                    </div>
                </div>

                {/* Detailed Report Section */}
                {allIssues.length > 0 && (
                    <div className="report-section">
                        <h3>Vulnerability Details</h3>
                        {Object.entries(categories).map(([priority, issues]) => {
                            if (issues.length === 0) return null;
                            return (
                                <div key={priority} className="severity-group">
                                    <h4>{priority.charAt(0).toUpperCase() + priority.slice(1)} Priority Issues</h4>
                                    <div className="issues-grid">
                                        {issues.map((issue, index) => (
                                            <div key={index} className="issue-card">
                                                <div className="issue-title">{issue.issue}</div>
                                                <div className="detail-grid">
                                                    <div><strong>Description:</strong> {issue.description}</div>
                                                    <div><strong>Impact:</strong> {issue.impact}</div>
                                                    <div><strong>Recommendation:</strong> {issue.recommendation}</div>
                                                </div>
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
                    <div className="report-section">
                        <h3>Action Plan</h3>
                        <ol className="action-list">
                            {Object.entries(categories).map(([priority, issues]) => {
                                if (issues.length === 0) return null;
                                return (
                                    <li key={priority}>
                                        <span className="priority-label">{priority} Priority:</span>
                                        <span className="recommendation-text"> {issues.map(i => i.issue).join(', ')}</span>
                                    </li>
                                );
                            })}
                        </ol>
                    </div>
                )}

                {/* Detailed SSL Certificate Analysis */}
                {scanResult?.https && scanResult.ssl_certificate && (
                    <div className="report-section">
                        <h3>SSL Certificate Analysis</h3>
                        <div className="ssl-grid">
                            <div className="overview-item">
                                <div className="label">Days Until Expiry</div>
                                <div className="value">{scanResult.ssl_certificate.certificate_details?.days_until_expiry ?? 'N/A'}</div>
                            </div>
                            <div className="overview-item">
                                <div className="label">Encryption Strength</div>
                                <div className="value">{scanResult.ssl_certificate.cipher_info?.bits ? `${scanResult.ssl_certificate.cipher_info.bits}-bit` : 'N/A'}</div>
                            </div>
                            <div className="overview-item">
                                <div className="label">TLS Version</div>
                                <div className="value">{scanResult.ssl_certificate.cipher_info?.version || 'N/A'}</div>
                            </div>
                        </div>
                        <div className="ssl-details-list">
                            <h4>Certificate Details</h4>
                            <div><strong>Issued by:</strong><span>{scanResult.ssl_certificate.certificate_details.issuer?.commonName || 'N/A'}</span></div>
                            <div><strong>Issued to:</strong><span>{scanResult.ssl_certificate.certificate_details.subject?.commonName || 'N/A'}</span></div>
                            <div><strong>Valid From:</strong><span>{new Date(scanResult.ssl_certificate.certificate_details.valid_from).toLocaleDateString()}</span></div>
                            <div><strong>Valid Until:</strong><span>{new Date(scanResult.ssl_certificate.certificate_details.valid_until).toLocaleDateString()}</span></div>
                        </div>

                        {scanResult.ssl_certificate.security_issues?.length > 0 && (
                            <div className="ssl-issues-list">
                                <h4>SSL Security Issues</h4>
                                {scanResult.ssl_certificate.security_issues.map((issue, index) => (
                                    <div key={index} className="ssl-issue-item">{issue}</div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Action Checklist */}
                <div className="report-section">
                    <h3>Action Checklist</h3>
                    <p>A prioritized list of actions based on your scan results.</p>
                    <div className="checklist-items">
                        {!scanResult?.https && (
                            <div className="checklist-item"><div className="checklist-progress-container"></div><span className="checklist-item-text">Enable HTTPS/SSL certificate</span></div>
                        )}
                        {scanResult?.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('content-security-policy')) && (
                            <div className="checklist-item"><div className="checklist-progress-container"></div><span className="checklist-item-text">Add Content-Security-Policy header</span></div>
                        )}
                        {scanResult?.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('strict-transport-security')) && (
                            <div className="checklist-item"><div className="checklist-progress-container"></div><span className="checklist-item-text">Set up HSTS header</span></div>
                        )}
                         {scanResult?.headers && !Object.keys(scanResult.headers).some(h => h.toLowerCase().includes('x-frame-options')) && (
                            <div className="checklist-item"><div className="checklist-progress-container"></div><span className="checklist-item-text">Add X-Frame-Options header</span></div>
                        )}
                        {/* Add other checklist items as needed */}
                    </div>
                </div>
            </div>
        </>
    );
};

export default SecurityIssueFormatter;
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SecurityIssueFormatter from './SecurityIssueFormatter';
import ChatResponseFormatter from './ChatResponseFormatter';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// OWASP Top 10 Mapping Component
const OwaspMappingSection = ({ scanResult }) => {
  const [owaspData, setOwaspData] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchOwaspMapping = async () => {
      try {
        setIsLoading(true);
        
        const response = await fetch('http://localhost:8000/owasp-mapping', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        const data = await response.json();
        
        if (data.success) {
          setOwaspData(data.owasp_mapping);
        } else {
          setError(data.error || 'Failed to process OWASP mapping');
        }
      } catch (err) {
        setError('Failed to fetch OWASP mapping');
        console.error('OWASP mapping error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    // Fetch OWASP mapping when component mounts
    if (scanResult) {
      fetchOwaspMapping();
    } else {
      setIsLoading(false);
      setError('No scan result data available for OWASP mapping');
    }
  }, [scanResult]);

  if (isLoading) {
    return (
      <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(255, 193, 7, 0.1)', borderRadius: '8px' }}>
        <h4>🏆 OWASP Top 10 Mapping</h4>
        <p>🔄 Analyzing security issues against OWASP Top 10 framework...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(220, 53, 69, 0.1)', borderRadius: '8px' }}>
        <h4>🏆 OWASP Top 10 Mapping</h4>
        <p>❌ {error}</p>
      </div>
    );
  }

  if (!owaspData || !owaspData.categories || Object.keys(owaspData.categories).length === 0) {
    return (
      <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(40, 167, 69, 0.1)', borderRadius: '8px' }}>
        <h4>🏆 OWASP Top 10 Mapping</h4>
        <p>✅ No OWASP Top 10 vulnerabilities detected</p>
        <p style={{ fontSize: '0.9em', color: '#666', marginTop: '8px' }}>
          🛡️ Your application appears to be secure against the OWASP Top 10 2021 security risks.
        </p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(255, 193, 7, 0.1)', borderRadius: '8px' }}>
      <h4>🏆 OWASP Top 10 Mapping</h4>
      <div style={{ marginTop: '12px' }}>
        <div style={{ display: 'flex', gap: '20px', marginBottom: '16px', fontSize: '0.9em' }}>
          <span><strong>Total Issues:</strong> {owaspData.total_issues || 0}</span>
          <span><strong>Risk Level:</strong> <span style={{ 
            color: owaspData.risk_score === 'Critical' ? '#dc3545' : 
                  owaspData.risk_score === 'High' ? '#fd7e14' : 
                  owaspData.risk_score === 'Medium' ? '#ffc107' : '#28a745',
            fontWeight: 'bold'
          }}>{owaspData.risk_score || 'Low'}</span></span>
        </div>

        {Object.entries(owaspData.categories).map(([categoryId, categoryData]) => (
          <div key={categoryId} style={{
            border: '1px solid rgba(255, 193, 7, 0.3)',
            borderRadius: '6px',
            padding: '12px',
            marginBottom: '12px',
            background: 'rgba(255, 255, 255, 0.5)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <h5 style={{ margin: 0, color: '#d63384' }}>{categoryData.name}</h5>
              <span style={{ 
                background: '#dc3545', 
                color: 'white', 
                padding: '2px 8px', 
                borderRadius: '12px', 
                fontSize: '0.8em',
                fontWeight: 'bold'
              }}>
                {categoryData.count} issue{categoryData.count !== 1 ? 's' : ''}
              </span>
            </div>
            <p style={{ margin: '0 0 12px 0', fontSize: '0.9em', color: '#666' }}>
              {categoryData.description}
            </p>
            <div>
              <strong>Issues found:</strong>
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                {categoryData.issues.map((issue, index) => (
                  <li key={index} style={{ marginBottom: '4px', fontSize: '0.9em' }}>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}

        {owaspData.recommendations && owaspData.recommendations.length > 0 && (
          <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(23, 162, 184, 0.1)', borderRadius: '6px' }}>
            <h5>💡 Recommendations:</h5>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
              {owaspData.recommendations.map((rec, index) => (
                <li key={index} style={{ marginBottom: '4px', fontSize: '0.9em' }}>
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

// OWASP Top 10 Card Component - Always Visible
const OwaspMappingCardSection = ({ scanResult }) => {
  const [owaspData, setOwaspData] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    const fetchOwaspMapping = async () => {
      try {
        setIsLoading(true);
        
        const response = await fetch('http://localhost:8000/owasp-mapping', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ scan_result: scanResult }),
        });
        
        const data = await response.json();
        
        if (data.success && data.owasp_mapping) {
          const owaspMapping = data.owasp_mapping.owasp_mapping;
          const summary = data.owasp_mapping.summary;
          
          // Transform the data to match our component expectations
          const transformedData = {
            categories: owaspMapping,
            total_issues: summary.total_issues,
            categories_affected: summary.categories_affected,
            risk_score: summary.total_issues > 10 ? 'High' : summary.total_issues > 5 ? 'Medium' : summary.total_issues > 0 ? 'Low' : 'Low',
            top_categories: summary.top_categories,
            recommendations: []
          };
          
          // Generate recommendations based on issues found
          if (summary.total_issues > 0) {
            summary.top_categories.forEach(category => {
              if (category.category.includes('Security Misconfiguration')) {
                transformedData.recommendations.push('Implement missing security headers (X-Frame-Options, X-Content-Type-Options, etc.)');
              }
              if (category.category.includes('Cryptographic Failures')) {
                transformedData.recommendations.push('Enable HSTS, configure DNSSEC and DMARC for better cryptographic security');
              }
              if (category.category.includes('Injection')) {
                transformedData.recommendations.push('Implement Content Security Policy and XSS protection headers');
              }
            });
          }
          
          setOwaspData(transformedData);
        } else {
          setError(data.error || 'Failed to process OWASP mapping');
        }
      } catch (err) {
        setError('Failed to fetch OWASP mapping');
        console.error('OWASP mapping error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    // Fetch OWASP mapping when component mounts
    if (scanResult) {
      fetchOwaspMapping();
    } else {
      setIsLoading(false);
    }
  }, [scanResult]);

  if (!scanResult) {
    return (
      <div className="card">
        <h3>🏆 OWASP Top 10 Security Analysis</h3>
        <div style={{ 
          background: 'rgba(156, 163, 175, 0.1)', 
          border: '1px solid rgba(156, 163, 175, 0.2)',
          borderRadius: '8px',
          padding: '20px',
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
          <h4 style={{ color: '#9ca3af', margin: '0 0 8px 0' }}>OWASP Analysis Pending</h4>
          <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
            OWASP Top 10 security analysis will be performed during the next security scan. This analysis categorizes vulnerabilities against the industry-standard OWASP framework.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>🏆 OWASP Top 10 Security Analysis</h3>
      {isLoading ? (
        <div style={{ 
          background: 'rgba(255, 193, 7, 0.1)', 
          border: '1px solid rgba(255, 193, 7, 0.2)',
          borderRadius: '8px',
          padding: '20px',
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>🔄</div>
          <h4 style={{ color: '#ffc107', margin: '0 0 8px 0' }}>Analyzing Security Framework</h4>
          <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
            Mapping security issues against OWASP Top 10 2021 framework...
          </p>
        </div>
      ) : error ? (
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.1)', 
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: '8px',
          padding: '20px',
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>❌</div>
          <h4 style={{ color: '#ef4444', margin: '0 0 8px 0' }}>Analysis Error</h4>
          <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
            {error}
          </p>
        </div>
      ) : !owaspData || !owaspData.categories || Object.keys(owaspData.categories).length === 0 ? (
        <div style={{ 
          background: 'rgba(34, 197, 94, 0.1)', 
          border: '1px solid rgba(34, 197, 94, 0.2)',
          borderRadius: '8px',
          padding: '20px' 
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>✅</div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Security Status</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>No Issues Found</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>0</div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Vulnerabilities</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>OWASP Top 10</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>Low</div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Risk Level</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Excellent</div>
            </div>
          </div>
          <div style={{ padding: '12px', background: 'rgba(34, 197, 94, 0.1)', borderRadius: '6px' }}>
            <h5 style={{ color: '#22c55e', margin: '0 0 8px 0' }}>🛡️ Excellent Security Posture</h5>
            <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
              Your application appears to be secure against the OWASP Top 10 2021 security risks. Continue following security best practices to maintain this excellent posture.
            </p>
          </div>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{ 
              background: 'rgba(239, 68, 68, 0.1)', 
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>
                {owaspData.total_issues || 0}
              </div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Total Issues</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>OWASP Categories</div>
            </div>

            <div style={{ 
              background: owaspData.risk_score === 'Critical' ? 'rgba(220, 38, 127, 0.1)' : 
                         owaspData.risk_score === 'High' ? 'rgba(239, 68, 68, 0.1)' : 
                         owaspData.risk_score === 'Medium' ? 'rgba(255, 193, 7, 0.1)' : 'rgba(34, 197, 94, 0.1)',
              border: owaspData.risk_score === 'Critical' ? '1px solid rgba(220, 38, 127, 0.2)' : 
                     owaspData.risk_score === 'High' ? '1px solid rgba(239, 68, 68, 0.2)' : 
                     owaspData.risk_score === 'Medium' ? '1px solid rgba(255, 193, 7, 0.2)' : '1px solid rgba(34, 197, 94, 0.2)',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center'
            }}>
              <div style={{ 
                fontSize: '24px', 
                fontWeight: '700', 
                color: owaspData.risk_score === 'Critical' ? '#dc267f' : 
                       owaspData.risk_score === 'High' ? '#ef4444' : 
                       owaspData.risk_score === 'Medium' ? '#ffc107' : '#22c55e'
              }}>
                {owaspData.risk_score === 'Critical' ? '🚨' : 
                 owaspData.risk_score === 'High' ? '⚠️' : 
                 owaspData.risk_score === 'Medium' ? '🔶' : '✅'}
              </div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Risk Level</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {owaspData.risk_score || 'Low'}
              </div>
            </div>

            <div style={{ 
              background: 'rgba(147, 51, 234, 0.1)', 
              border: '1px solid rgba(147, 51, 234, 0.2)',
              borderRadius: '8px',
              padding: '16px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#9333ea' }}>
                {Object.keys(owaspData.categories).length}
              </div>
              <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Categories</div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Affected</div>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <h5 style={{ margin: '0 0 12px 0', color: '#a1a1aa' }}>OWASP Top 10 Categories Found:</h5>
            <div style={{ display: 'grid', gap: '12px' }}>
              {Object.entries(owaspData.categories).filter(([, categoryData]) => categoryData.count > 0).map(([categoryId, categoryData]) => (
                <div key={categoryId} style={{
                  border: '1px solid rgba(255, 193, 7, 0.3)',
                  borderRadius: '8px',
                  padding: '12px',
                  background: 'rgba(255, 193, 7, 0.05)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h6 style={{ margin: 0, color: '#d63384', fontSize: '14px', fontWeight: '600' }}>
                      {categoryId}
                    </h6>
                    <span style={{ 
                      background: '#dc3545', 
                      color: 'white', 
                      padding: '2px 8px', 
                      borderRadius: '12px', 
                      fontSize: '0.75em',
                      fontWeight: 'bold'
                    }}>
                      {categoryData.count} issue{categoryData.count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8em', color: '#888', marginBottom: '8px' }}>
                    <strong>Issues:</strong> {categoryData.issues.slice(0, 2).map(issue => issue.description).join(', ')}
                    {categoryData.issues.length > 2 && ` +${categoryData.issues.length - 2} more`}
                  </div>
                  <div style={{ fontSize: '0.75em', color: '#999' }}>
                    <strong>Sources:</strong> {categoryData.sources.join(', ')}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {owaspData.recommendations && owaspData.recommendations.length > 0 && (
            <div style={{ padding: '12px', background: 'rgba(23, 162, 184, 0.1)', borderRadius: '6px' }}>
              <h5 style={{ color: '#17a2b8', margin: '0 0 8px 0' }}>💡 Priority Recommendations:</h5>
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '0.9em' }}>
                {owaspData.recommendations.slice(0, 3).map((rec, index) => (
                  <li key={index} style={{ marginBottom: '4px', color: '#666' }}>
                    {rec}
                  </li>
                ))}
                {owaspData.recommendations.length > 3 && (
                  <li style={{ fontStyle: 'italic', color: '#888' }}>
                    +{owaspData.recommendations.length - 3} more recommendations available
                  </li>
                )}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

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
    
    // WAF Analysis
    if (q.includes('waf') || q.includes('firewall')) {
      const wafData = result?.waf_analysis || 
                     result?.scan_result?.waf_analysis ||
                     result?.security_analysis?.waf_analysis ||
                     result?.analysis?.waf ||
                     result?.waf;
      
      const wafDetected = wafData?.waf_detected;
      const wafType = wafData?.waf_type;
      const protectionLevel = wafData?.protection_level;
      
      return `🛡️ **WAF Analysis:**\n\n` +
             `• **Status:** ${wafDetected ? '✅ Protected' : '❌ Not Protected'}\n` +
             `• **Type:** ${wafType || 'None detected'}\n` +
             `• **Protection Level:** ${protectionLevel || 'Unknown'}\n` +
             `• **Blocked Requests:** ${wafData?.blocked_requests || 0}/${wafData?.total_requests || 0}\n\n` +
             `${!wafDetected ? '⚠️ **Recommendation:** Consider implementing a Web Application Firewall to protect against common attacks.' : '✅ Your application is protected by a WAF.'}`;
    }
    
    // DNS Security Analysis
    if (q.includes('dns') || q.includes('dnssec') || q.includes('dmarc') || q.includes('dkim')) {
      const dnsData = result?.dns_security || 
                     result?.scan_result?.dns_security ||
                     result?.security_analysis?.dns_security ||
                     result?.analysis?.dns ||
                     result?.dns;
      
      const dnssec = dnsData?.dnssec?.enabled;
      const dmarc = dnsData?.dmarc?.enabled;
      const dkim = dnsData?.dkim?.selectors_found?.length > 0;
      
      return `🔐 **DNS Security Analysis:**\n\n` +
             `• **DNSSEC:** ${dnssec ? '✅ Enabled' : '❌ Disabled'} - ${dnsData?.dnssec?.status || 'Not configured'}\n` +
             `• **DMARC:** ${dmarc ? '✅ Enabled' : '❌ Not configured'} - ${dnsData?.dmarc?.policy || 'No policy'}\n` +
             `• **DKIM:** ${dkim ? '✅ Found' : '❌ Not found'} - ${dnsData?.dkim?.selectors_found?.length || 0} selectors\n\n` +
             `**Recommendations:**\n` +
             `${!dnssec ? '• Enable DNSSEC to prevent DNS spoofing attacks\n' : ''}` +
             `${!dmarc ? '• Configure DMARC to prevent email spoofing\n' : ''}` +
             `${!dkim ? '• Set up DKIM signing for email authenticity\n' : ''}` +
             `${dnssec && dmarc && dkim ? '✅ Your DNS security configuration is excellent!' : ''}`;
    }
    
    // OWASP Analysis
    if (q.includes('owasp') || q.includes('top 10')) {
      return `🏆 **OWASP Top 10 Analysis:**\n\n` +
             `I'm analyzing your security issues against the OWASP Top 10 framework. ` +
             `This helps categorize vulnerabilities by their risk level and provides targeted remediation guidance.\n\n` +
             `The OWASP mapping section shows:\n` +
             `• Categories of vulnerabilities found\n` +
             `• Risk assessment for each category\n` +
             `• Specific recommendations for remediation\n\n` +
             `Check the OWASP Top 10 Mapping section above for detailed analysis.`;
    }
    
    if (q.includes('vulnerabilit') || q.includes('security')) {
      const flagsCount = result?.scan_result?.flags?.length || 0;
      const wafData = result?.waf_analysis || 
                     result?.scan_result?.waf_analysis ||
                     result?.security_analysis?.waf_analysis ||
                     result?.analysis?.waf ||
                     result?.waf;
      const dnsData = result?.dns_security || 
                     result?.scan_result?.dns_security ||
                     result?.security_analysis?.dns_security ||
                     result?.analysis?.dns ||
                     result?.dns;
      
      const wafStatus = wafData?.waf_detected ? 'protected by WAF' : 'not protected by WAF';
      const dnsIssues = [
        !dnsData?.dnssec?.enabled && 'DNSSEC disabled',
        !dnsData?.dmarc?.enabled && 'DMARC not configured',
        !dnsData?.dkim?.selectors_found?.length && 'DKIM not found'
      ].filter(Boolean);
      
      return `🔍 **Security Overview:**\n\n` +
             `• **Security Issues:** ${flagsCount} vulnerabilities detected\n` +
             `• **WAF Protection:** ${wafStatus}\n` +
             `• **DNS Security:** ${dnsIssues.length > 0 ? `${dnsIssues.length} issues found` : 'All configured'}\n\n` +
             `${flagsCount > 0 ? '⚠️ Focus on addressing the most critical vulnerabilities first.' : '✅ Great job - no major vulnerabilities detected!'}\n\n` +
             `Check the detailed analysis cards above for comprehensive security information.`;
    }
    
    if (q.includes('fix') || q.includes('how to')) {
      const recommendations = [];
      
      const wafData = result?.waf_analysis || 
                     result?.scan_result?.waf_analysis ||
                     result?.security_analysis?.waf_analysis ||
                     result?.analysis?.waf ||
                     result?.waf;
      const dnsData = result?.dns_security || 
                     result?.scan_result?.dns_security ||
                     result?.security_analysis?.dns_security ||
                     result?.analysis?.dns ||
                     result?.dns;
      
      // Basic security recommendations
      recommendations.push('1) Implement missing security headers');
      recommendations.push('2) Ensure HTTPS is properly configured');
      
      // WAF recommendations
      if (!wafData?.waf_detected) {
        recommendations.push('3) Deploy a Web Application Firewall (WAF)');
      }
      
      // DNS security recommendations
      if (!dnsData?.dnssec?.enabled) {
        recommendations.push('4) Enable DNSSEC for DNS security');
      }
      if (!dnsData?.dmarc?.enabled) {
        recommendations.push('5) Configure DMARC email protection');
      }
      
      recommendations.push('6) Update vulnerable dependencies');
      recommendations.push('7) Enable proper input validation');
      
      return `🛠️ **Security Improvement Steps:**\n\n${recommendations.join('\n')}\n\n` +
             `💡 **Priority:** Focus on critical vulnerabilities first, then implement additional security layers.`;
    }
    
    if (q.includes('score') || q.includes('rating')) {
      const score = result?.security_score || result?.scan_result?.security_score || 'not available';
      const wafData = result?.waf_analysis || 
                     result?.scan_result?.waf_analysis ||
                     result?.security_analysis?.waf_analysis ||
                     result?.analysis?.waf ||
                     result?.waf;
      const dnsData = result?.dns_security || 
                     result?.scan_result?.dns_security ||
                     result?.security_analysis?.dns_security ||
                     result?.analysis?.dns ||
                     result?.dns;
      
      const wafBonus = wafData?.waf_detected ? '+10 for WAF protection' : '-10 for no WAF';
      const dnsSecure = dnsData?.dnssec?.enabled && dnsData?.dmarc?.enabled;
      const dnsBonus = dnsSecure ? '+5 for DNS security' : '-5 for DNS issues';
      
      return `📊 **Security Score Analysis:**\n\n` +
             `• **Current Score:** ${score}/100\n` +
             `• **WAF Impact:** ${wafBonus}\n` +
             `• **DNS Security Impact:** ${dnsBonus}\n\n` +
             `**Score Ranges:**\n` +
             `• 85-100: Excellent security posture\n` +
             `• 70-85: Good security, minor improvements needed\n` +
             `• 50-70: Moderate security, improvements required\n` +
             `• Below 50: Significant security issues present\n\n` +
             `💡 **Tip:** Implementing WAF and DNS security can significantly boost your score.`;
    }
    
    return `🤖 **AI Security Assistant**\n\n` +
           `I'm here to help you understand your comprehensive security analysis:\n\n` +
           `• **Security Issues:** Vulnerability analysis and remediation\n` +
           `• **WAF Protection:** Web Application Firewall status\n` +
           `• **DNS Security:** DNSSEC, DMARC, and DKIM configuration\n` +
           `• **OWASP Mapping:** Risk categorization and recommendations\n\n` +
           `Ask me about specific topics like "WAF analysis", "DNS security", "OWASP mapping", or "how to fix vulnerabilities".`;
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

                {/* WAF Analysis Card - Always Visible */}
                <div className="card">
                  <h3>🛡️ Web Application Firewall (WAF) Analysis</h3>
                  {(() => {
                    // Check data locations in priority order - top level first (matches backend structure)
                    const wafData = scanResult.waf_analysis || 
                                   scanResult.scan_result?.waf_analysis ||
                                   scanResult.security_analysis?.waf_analysis ||
                                   scanResult.analysis?.waf ||
                                   scanResult.waf;
                    
                    // Make sure we have actual data, not just an empty object
                    return wafData && (wafData.waf_detected !== undefined || Object.keys(wafData).length > 0);
                  })() ? (
                    <>
                      {(() => {
                        const wafData = scanResult.waf_analysis || 
                                       scanResult.scan_result?.waf_analysis ||
                                       scanResult.security_analysis?.waf_analysis ||
                                       scanResult.analysis?.waf ||
                                       scanResult.waf;
                        return (
                          <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                              <div style={{ 
                                background: wafData.waf_detected ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                                border: wafData.waf_detected ? '1px solid rgba(34, 197, 94, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '24px', fontWeight: '700', color: wafData.waf_detected ? '#22c55e' : '#ef4444' }}>
                                  {wafData.waf_detected ? '✅' : '❌'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>WAF Detection</div>
                                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                  {wafData.waf_detected ? 'Protected' : 'Not Protected'}
                                </div>
                              </div>

                              <div style={{ 
                                background: 'rgba(147, 51, 234, 0.1)', 
                                border: '1px solid rgba(147, 51, 234, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '20px', fontWeight: '700', color: '#9333ea' }}>
                                  {wafData.waf_type || 'None'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>WAF Type</div>
                              </div>

                              <div style={{ 
                                background: 'rgba(255, 193, 7, 0.1)', 
                                border: '1px solid rgba(255, 193, 7, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '20px', fontWeight: '700', color: '#ffc107' }}>
                                  {wafData.protection_level || 'Unknown'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Protection Level</div>
                              </div>

                              <div style={{ 
                                background: 'rgba(23, 162, 184, 0.1)', 
                                border: '1px solid rgba(23, 162, 184, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '20px', fontWeight: '700', color: '#17a2b8' }}>
                                  {wafData.blocked_requests || 0}/{wafData.total_requests || 0}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>Blocked/Total</div>
                                <div style={{ fontSize: '12px', color: '#17a2b8', marginTop: '4px', fontWeight: '600' }}>
                                  {wafData.total_requests > 0 
                                    ? `${Math.round((wafData.blocked_requests / wafData.total_requests) * 100)}% blocked`
                                    : 'No data'
                                  }
                                </div>
                              </div>
                            </div>

                            {!wafData.waf_detected && (
                              <div style={{ 
                                marginTop: '16px', 
                                padding: '12px', 
                                background: 'rgba(239, 68, 68, 0.1)', 
                                borderRadius: '6px',
                                border: '1px solid rgba(239, 68, 68, 0.2)'
                              }}>
                                <h5 style={{ color: '#ef4444', margin: '0 0 8px 0' }}>⚠️ No WAF Protection Detected</h5>
                                <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
                                  Consider implementing a Web Application Firewall to protect against common attacks like SQL injection, XSS, and other OWASP Top 10 vulnerabilities.
                                </p>
                              </div>
                            )}

                            {/* Enhanced Detection Details - Show evidence and methods */}
                            {wafData.waf_detected && (wafData.evidence || wafData.detection_summary) && (
                              <div style={{ marginTop: '16px' }}>
                                <h5 style={{ margin: '0 0 12px 0', color: '#a1a1aa' }}>🔍 Detection Evidence:</h5>
                                
                                {/* Evidence List */}
                                {wafData.evidence && wafData.evidence.length > 0 && (
                                  <div style={{ marginBottom: '12px' }}>
                                    <div style={{ display: 'grid', gap: '6px' }}>
                                      {wafData.evidence.slice(0, 5).map((evidence, index) => (
                                        <div key={index} style={{ 
                                          padding: '6px 10px', 
                                          background: 'rgba(34, 197, 94, 0.1)', 
                                          borderRadius: '4px', 
                                          fontSize: '0.85em',
                                          color: '#22c55e',
                                          border: '1px solid rgba(34, 197, 94, 0.2)'
                                        }}>
                                          ✓ {evidence}
                                        </div>
                                      ))}
                                      {wafData.evidence.length > 5 && (
                                        <div style={{ 
                                          padding: '6px 10px', 
                                          background: 'rgba(147, 51, 234, 0.1)', 
                                          borderRadius: '4px', 
                                          fontSize: '0.85em',
                                          color: '#9333ea',
                                          textAlign: 'center'
                                        }}>
                                          +{wafData.evidence.length - 5} more evidence found
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Detection Methods and Manual Verification */}
                                {wafData.detection_summary && (
                                  <div style={{ 
                                    padding: '12px', 
                                    background: 'rgba(0, 245, 195, 0.05)', 
                                    borderRadius: '6px',
                                    border: '1px solid rgba(0, 245, 195, 0.1)'
                                  }}>
                                    <div style={{ display: 'grid', gap: '8px', fontSize: '0.9em' }}>
                                      {wafData.detection_summary.primary_detection_method && wafData.detection_summary.primary_detection_method !== 'unknown' && (
                                        <div>
                                          <strong>Primary Detection:</strong> {wafData.detection_summary.primary_detection_method.replace(/_/g, ' ')}
                                        </div>
                                      )}
                                      
                                      {wafData.confidence && (
                                        <div>
                                          <strong>Confidence Score:</strong> {wafData.confidence}% 
                                          {wafData.confidence >= 80 ? ' (Very High)' : 
                                           wafData.confidence >= 60 ? ' (High)' : 
                                           wafData.confidence >= 40 ? ' (Medium)' : ' (Low)'}
                                        </div>
                                      )}
                                      
                                      {wafData.detection_summary.manual_verification_method && (
                                        <div>
                                          <strong>Manual Verification:</strong> {wafData.detection_summary.manual_verification_method}
                                        </div>
                                      )}
                                      
                                      {wafData.detection_summary.recommended_tools && wafData.detection_summary.recommended_tools.length > 0 && (
                                        <div>
                                          <strong>Compatible Tools:</strong> {wafData.detection_summary.recommended_tools.slice(0, 2).join(', ')}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </>
                  ) : (
                    <div style={{ 
                      background: 'rgba(156, 163, 175, 0.1)', 
                      border: '1px solid rgba(156, 163, 175, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      textAlign: 'center' 
                    }}>
                      <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                      <h4 style={{ color: '#9ca3af', margin: '0 0 8px 0' }}>WAF Analysis Pending</h4>
                      <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
                        WAF detection will be performed during the next security scan. This analysis checks for Web Application Firewall protection against common attacks.
                      </p>
                    </div>
                  )}
                </div>

                {/* DNS Security Analysis Card - Always Visible */}
                <div className="card">
                  <h3>🔐 DNS Security Analysis</h3>
                  {(() => {
                    // Check data locations in priority order - top level first (matches backend structure)
                    const dnsData = scanResult.dns_security || 
                                   scanResult.scan_result?.dns_security ||
                                   scanResult.security_analysis?.dns_security ||
                                   scanResult.analysis?.dns ||
                                   scanResult.dns;
                    
                    // Make sure we have actual data, not just an empty object
                    return dnsData && (dnsData.dnssec !== undefined || dnsData.dmarc !== undefined || Object.keys(dnsData).length > 0);
                  })() ? (
                    <>
                      {(() => {
                        const dnsData = scanResult.dns_security || 
                                       scanResult.scan_result?.dns_security ||
                                       scanResult.security_analysis?.dns_security ||
                                       scanResult.analysis?.dns ||
                                       scanResult.dns;
                        return (
                          <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                              <div style={{ 
                                background: dnsData.dnssec?.enabled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                                border: dnsData.dnssec?.enabled ? '1px solid rgba(34, 197, 94, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '24px', fontWeight: '700', color: dnsData.dnssec?.enabled ? '#22c55e' : '#ef4444' }}>
                                  {dnsData.dnssec?.enabled ? '✅' : '❌'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>DNSSEC</div>
                                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                  {dnsData.dnssec?.status || 'Not configured'}
                                </div>
                              </div>

                              <div style={{ 
                                background: dnsData.dmarc?.enabled ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                                border: dnsData.dmarc?.enabled ? '1px solid rgba(34, 197, 94, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '24px', fontWeight: '700', color: dnsData.dmarc?.enabled ? '#22c55e' : '#ef4444' }}>
                                  {dnsData.dmarc?.enabled ? '✅' : '❌'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>DMARC</div>
                                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                  {dnsData.dmarc?.policy || 'No policy'}
                                </div>
                              </div>

                              <div style={{ 
                                background: dnsData.dkim?.selectors_found?.length > 0 ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                                border: dnsData.dkim?.selectors_found?.length > 0 ? '1px solid rgba(34, 197, 94, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                                borderRadius: '8px',
                                padding: '16px',
                                textAlign: 'center'
                              }}>
                                <div style={{ fontSize: '24px', fontWeight: '700', color: dnsData.dkim?.selectors_found?.length > 0 ? '#22c55e' : '#ef4444' }}>
                                  {dnsData.dkim?.selectors_found?.length > 0 ? '✅' : '❌'}
                                </div>
                                <div style={{ color: '#a1a1aa', marginTop: '8px' }}>DKIM</div>
                                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                  {dnsData.dkim?.selectors_found?.length || 0} selectors
                                </div>
                              </div>
                            </div>

                            <div style={{ marginTop: '16px' }}>
                              <h5 style={{ margin: '0 0 12px 0', color: '#a1a1aa' }}>DNS Security Recommendations:</h5>
                              <div style={{ display: 'grid', gap: '8px' }}>
                                {!dnsData.dnssec?.enabled && (
                                  <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '0.9em' }}>
                                    <strong>DNSSEC:</strong> Enable DNSSEC to prevent DNS spoofing and cache poisoning attacks
                                  </div>
                                )}
                                {!dnsData.dmarc?.enabled && (
                                  <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '0.9em' }}>
                                    <strong>DMARC:</strong> Configure DMARC policy to prevent email spoofing and phishing
                                  </div>
                                )}
                                {(!dnsData.dkim?.selectors_found || dnsData.dkim.selectors_found.length === 0) && (
                                  <div style={{ padding: '8px 12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '4px', fontSize: '0.9em' }}>
                                    <strong>DKIM:</strong> Set up DKIM signing to verify email authenticity
                                  </div>
                                )}
                                {dnsData.dnssec?.enabled && dnsData.dmarc?.enabled && dnsData.dkim?.selectors_found?.length > 0 && (
                                  <div style={{ padding: '8px 12px', background: 'rgba(34, 197, 94, 0.1)', borderRadius: '4px', fontSize: '0.9em' }}>
                                    <strong>✅ Excellent:</strong> All DNS security features are properly configured!
                                  </div>
                                )}
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </>
                  ) : (
                    <div style={{ 
                      background: 'rgba(156, 163, 175, 0.1)', 
                      border: '1px solid rgba(156, 163, 175, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      textAlign: 'center' 
                    }}>
                      <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                      <h4 style={{ color: '#9ca3af', margin: '0 0 8px 0' }}>DNS Security Analysis Pending</h4>
                      <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
                        DNS security analysis (DNSSEC, DMARC, DKIM) will be performed during the next security scan. These features help protect against DNS spoofing and email attacks.
                      </p>
                    </div>
                  )}
                </div>

                {/* OWASP Top 10 Analysis Card - Always Visible */}
                <OwaspMappingCardSection scanResult={scanResult} />

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

                    {/* OWASP Top 10 Mapping Integration */}
                    <OwaspMappingSection scanResult={scanResult} />
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
                      {scanResult.waf_analysis && (
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: '13px', padding: '10px 12px' }}
                          onClick={() => {
                            setChatInput('WAF analysis');
                            setTimeout(() => handleChat(), 100);
                          }}
                        >
                          🛡️ WAF
                        </button>
                      )}
                      {scanResult.dns_security && (
                        <button
                          className="btn btn-ghost"
                          style={{ fontSize: '13px', padding: '10px 12px' }}
                          onClick={() => {
                            setChatInput('DNS security');
                            setTimeout(() => handleChat(), 100);
                          }}
                        >
                          🔐 DNS
                        </button>
                      )}
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
                          setChatInput('OWASP mapping');
                          setTimeout(() => handleChat(), 100);
                        }}
                      >
                        🏆 OWASP
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
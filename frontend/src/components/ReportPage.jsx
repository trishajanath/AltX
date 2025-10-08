import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Make sure these component paths are correct for your project structure
import SecurityIssueFormatter from './SecurityIssueFormatter';
import ChatResponseFormatter from './ChatResponseFormatter';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// --- Sub-component: Security Score Gauge ---
const SecurityScoreGauge = ({ score }) => {
    const scoreValue = score || 0;
    const circumference = 2 * Math.PI * 54;
    const strokeDashoffset = circumference - (scoreValue / 100) * circumference;
    const getScoreColorClass = (s) => {
        if (s >= 80) return 'score-high';
        if (s >= 50) return 'score-medium';
        return 'score-low';
    };

    return (
        <div className="score-gauge-container">
            <svg viewBox="0 0 120 120" className="score-gauge-svg">
                <circle className="gauge-background" cx="60" cy="60" r="54" />
                <circle
                    className={`gauge-progress ${getScoreColorClass(scoreValue)}`}
                    cx="60" cy="60" r="54"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                />
            </svg>
            <div className="score-text">
                <div className="score-value">{scoreValue}</div>
                <div className="score-label">Security Score</div>
            </div>
        </div>
    );
};

// --- Sub-component: OWASP Top 10 Card ---
const OwaspMappingCardSection = ({ scanResult }) => {
    const [owaspData, setOwaspData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOwaspMapping = async () => {
            if (!scanResult) {
                console.log('🚫 OWASP Mapping - No scan result provided');
                setIsLoading(false);
                return;
            }
            try {
                setIsLoading(true);
                console.log('🎯 OWASP Mapping - Starting request...');
                console.log('OWASP Mapping - scanResult data:', scanResult);
                console.log('OWASP Mapping - scanResult type:', typeof scanResult);
                console.log('OWASP Mapping - scanResult keys:', Object.keys(scanResult || {}));
                
                const response = await fetch('http://localhost:8000/owasp-mapping', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        scan_result: scanResult,
                        exclude_repo: true  // Only analyze website scan data, not repository data
                    }),
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                console.log('OWASP Mapping - API response:', data);
                console.log('OWASP Mapping - API success:', data.success);
                console.log('OWASP Mapping - API owasp_mapping:', data.owasp_mapping);
                
                if (data.success && data.owasp_mapping) {
                    const { owasp_mapping, summary } = data.owasp_mapping;
                    console.log('✅ OWASP Mapping - Processing successful response');
                    console.log('OWASP categories:', owasp_mapping);
                    console.log('OWASP summary:', summary);
                    
                    setOwaspData({
                        categories: owasp_mapping,
                        total_issues: summary.total_issues,
                        risk_score: summary.total_issues > 15 ? 'Critical' : summary.total_issues > 8 ? 'High' : summary.total_issues > 3 ? 'Medium' : 'Low',
                    });
                } else {
                    console.log('❌ OWASP Mapping - API returned failure or no data');
                    setError(data.error || 'Failed to process mapping');
                }
            } catch (err) {
                console.error('❌ OWASP Mapping error:', err);
                setError(`Could not connect to the analysis server: ${err.message}`);
            } finally {
                setIsLoading(false);
            }
        };
        fetchOwaspMapping();
    }, [scanResult]);

    if (isLoading) return <div className="info-text" style={{padding: '2rem', fontSize: '1.1rem', color: '#ffc107'}}>🔄 Analyzing OWASP vulnerabilities...</div>;
    if (error) return <div className="info-text" style={{padding: '2rem', fontSize: '1.1rem', color: '#dc3545'}}>❌ OWASP analysis unavailable: {error}</div>;
    if (!owaspData || !owaspData.categories || Object.keys(owaspData.categories).length === 0) {
        return <div className="info-text" style={{padding: '2rem', fontSize: '1.1rem', color: '#6c757d'}}>ℹ️ No OWASP Top 10 vulnerabilities detected.</div>;
    }

    return (
        <>
            <div className="owasp-grid">
                <div className="owasp-stat">
                    <span className="owasp-value">{owaspData.total_issues || 0}</span>
                    <span className="owasp-label">Total Issues</span>
                </div>
                <div className="owasp-stat">
                    <span className="owasp-value">{owaspData.risk_score || 'Low'}</span>
                    <span className="owasp-label">Risk Level</span>
                </div>
                <div className="owasp-stat">
                    <span className="owasp-value">{Object.keys(owaspData.categories).length}</span>
                    <span className="owasp-label">Categories Affected</span>
                </div>
            </div>
            <div className="owasp-list">
                {Object.entries(owaspData.categories).filter(([, c]) => c.count > 0).map(([id, data]) => (
                    <div key={id} className="owasp-item">
                        <span>{id.replace('A0', 'A').replace(':', ' - ')}</span>
                        <span className="issue-count">{data.count} Issues</span>
                    </div>
                ))}
            </div>
        </>
    );
};

// --- Main Page Component ---
const ReportPage = ({ scanResult }) => {
    usePreventZoom();
    const navigate = useNavigate();
    const [chatInput, setChatInput] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (scanResult?.ai_assistant_advice && chatHistory.length === 0) {
            setChatHistory([{ type: 'ai', message: `**Initial Security Analysis**\n\n${scanResult.ai_assistant_advice}` }]);
        }
    }, [scanResult, chatHistory.length]);

    const handleChat = async (message) => {
        const userMessage = message || chatInput;
        if (!userMessage.trim()) return;

        setChatInput('');
        setChatHistory(prev => [...prev, { type: 'user', message: userMessage }]);
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8000/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: userMessage,
                    scan_result: scanResult,
                    context: 'website_scan'
                }),
            });
            const data = await response.json();
            setChatHistory(prev => [...prev, { type: 'ai', message: data.response }]);
        } catch (error) {
            setChatHistory(prev => [...prev, { type: 'ai', message: "Sorry, I couldn't connect to the AI assistant. Please try again later." }]);
        } finally {
            setIsLoading(false);
        }
    };

    if (!scanResult) {
        return (
            <PageWrapper>
                <style>{`
                    :root {
                        --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                        --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                    }
                    .report-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                    .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                    .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                    .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }
                `}</style>
                <div className="report-page">
                    <div className="hero-section">
                        <h1 className="hero-title">Security Report</h1>
                        <p className="hero-subtitle">No scan results available. Please run a security scan first.</p>
                    </div>
                </div>
            </PageWrapper>
        );
    }

    const { scan_result = {}, url, deploymentUrl, security_score, summary } = scanResult;

    // Debug logging to understand data structure
    console.log('ReportPage scanResult:', scanResult);
    console.log('Security score:', security_score);
    console.log('WAF Analysis:', scan_result.waf_analysis);
    console.log('Scan result keys:', Object.keys(scan_result));

    // Enhanced data extraction with fallbacks
    const actualSecurityScore = security_score || 
                               scan_result.security_score || 
                               scan_result.overall_score || 
                               scan_result.score ||
                               (scan_result.analysis && scan_result.analysis.security_score) ||
                               (scan_result.summary && scan_result.summary.security_score) ||
                               0;
                               
    // More comprehensive WAF detection - check multiple possible locations
    const wafDetected = scan_result.waf_analysis?.waf_detected || 
                       scan_result.waf?.detected || 
                       scan_result.waf_detected ||
                       scan_result.waf_protection ||
                       scan_result.cloudflare_detected ||
                       scan_result.firewall_detected ||
                       (scan_result.waf_analysis?.waf_type && scan_result.waf_analysis.waf_type !== 'none' && scan_result.waf_analysis.waf_type !== 'unknown') ||
                       (scan_result.waf_type && scan_result.waf_type !== 'none' && scan_result.waf_type !== 'unknown') ||
                       // Check if cloudflare is explicitly mentioned
                       (scan_result.waf_analysis?.waf_type === 'cloudflare') ||
                       (scan_result.waf_type === 'cloudflare') ||
                       // Check in security headers for cloudflare indicators
                       (scan_result.security_headers && Object.keys(scan_result.security_headers).some(header => 
                           header.toLowerCase().includes('cloudflare') || 
                           header.toLowerCase().includes('cf-')
                       )) ||
                       false;
                       
    const wafType = scan_result.waf_analysis?.waf_type || 
                   scan_result.waf?.type || 
                   scan_result.waf_type ||
                   (scan_result.waf_analysis?.waf_type === 'cloudflare' ? 'cloudflare' : null) ||
                   (scan_result.security_headers && Object.keys(scan_result.security_headers).some(header => 
                       header.toLowerCase().includes('cloudflare')
                   ) ? 'cloudflare' : null) ||
                   'unknown';

    console.log('Extracted actualSecurityScore:', actualSecurityScore);
    console.log('Extracted wafDetected:', wafDetected);
    console.log('Extracted wafType:', wafType);
    console.log('WAF analysis object:', scan_result.waf_analysis);
    console.log('Security headers:', scan_result.security_headers);
    console.log('Summary content:', summary);

    // Check if WAF info is mentioned in the AI summary as fallback
    let finalWafDetected = wafDetected;
    let finalWafType = wafType;
    
    if (!wafDetected && summary && typeof summary === 'string') {
        const summaryLower = summary.toLowerCase();
        if (summaryLower.includes('waf detected') || summaryLower.includes('cloudflare')) {
            finalWafDetected = true;
            if (summaryLower.includes('cloudflare')) {
                finalWafType = 'cloudflare';
            }
        }
    }

    console.log('Final WAF status - detected:', finalWafDetected, 'type:', finalWafType);

    return (
        <PageWrapper>
            <style>{`
                /* Enhanced styles matching RepoAnalysisPage design system */
                :root {
                    --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                    --input-bg: rgba(0,0,0,0.2);
                }
                .report-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                .layout-container { max-width: 1600px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                
                /* Sidebar Layout */
                .report-layout { display: grid; grid-template-columns: 1fr 450px; gap: 2rem; margin-top: 2rem; }
                .report-sidebar { position: sticky; top: 2rem; height: calc(100vh - 4rem); }
                @media (max-width: 1200px) { 
                    .report-layout { grid-template-columns: 1fr; } 
                    .report-sidebar { position: static; height: auto; } 
                }
                
                .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }
                .card { width: 100%; box-sizing: border-box; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.3s ease; }
                .card:hover { border-color: var(--card-border-hover); box-shadow: 0 0 25px rgba(255, 255, 255, 0.08); }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 1.5rem 0; text-transform: uppercase; letter-spacing: 1px; }
                .input { flex-grow: 1; background: var(--input-bg); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; transition: border-color 0.3s; }
                .input:focus { border-color: var(--text-primary); outline: none; }
                .btn { background: var(--text-primary); border: 1px solid var(--text-primary); color: var(--bg-black); padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s; }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .btn:hover:not(:disabled) { box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
                .btn-secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--card-border); }
                .btn-secondary:hover:not(:disabled) { border-color: var(--text-primary); color: var(--text-primary); }
                
                /* Results Grid and Score Gauge */
                .results-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; align-items: center; }
                .score-gauge-container { position: relative; display: flex; align-items: center; justify-content: center; }
                .score-gauge-svg { transform: rotate(-90deg); width: 140px; height: 140px; }
                .gauge-background { fill: none; stroke: rgba(255, 255, 255, 0.1); stroke-width: 12; }
                .gauge-progress { fill: none; stroke-width: 12; stroke-linecap: round; transition: stroke-dashoffset 1s ease-out; }
                .gauge-progress.score-high { stroke: #ffffff; } .gauge-progress.score-medium { stroke: #bbbbbb; } .gauge-progress.score-low { stroke: #666666; }
                .score-text { position: absolute; text-align: center; }
                .score-value { font-size: 2.5rem; font-weight: 600; color: var(--text-primary); }
                .score-label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
                .info-list { display: flex; flex-direction: column; gap: 1rem; }
                .info-item { display: flex; justify-content: space-between; font-size: 0.9rem; padding-bottom: 1rem; border-bottom: 1px solid var(--card-border); }
                .info-item:last-child { border-bottom: none; }
                .info-item .label { color: var(--text-secondary); }
                .info-item .value { color: var(--text-primary); font-weight: 500; }
                
                /* Enhanced Status Grid */
                .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
                .status-item { background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1rem; transition: all 0.3s ease; }
                .status-item:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.04); }
                .status-item .status-label { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }
                .status-item .status-value { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }
                
                /* Enhanced OWASP Section */
                .owasp-summary { margin-bottom: 2rem; }
                .owasp-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }
                .owasp-stat { text-align: center; padding: 1.5rem 1rem; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; transition: all 0.3s ease; }
                .owasp-stat:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.04); }
                .owasp-value { display: block; font-size: 2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem; }
                .owasp-label { display: block; font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
                .owasp-list { display: flex; flex-direction: column; gap: 0.75rem; }
                .owasp-item { display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; font-size: 0.9rem; transition: all 0.3s ease; }
                .owasp-item:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.04); }
                .owasp-item span:first-child { color: var(--text-primary); font-weight: 500; }
                .issue-count { color: var(--text-secondary); background: rgba(255,255,255,0.1); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 600; }
                
                /* AI Chat Sidebar Styles */
                .ai-chat-container { height: 100%; display: flex; flex-direction: column; }
                .ai-chat-history { flex-grow: 1; overflow-y: auto; padding-right: 1rem; margin-bottom: 1.5rem; max-height: calc(100vh - 12rem); }
                .chat-message { max-width: 90%; margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5; word-wrap: break-word; }
                .ai-message { background: rgba(255, 255, 255, 0.1); border-bottom-left-radius: 0; }
                .user-message { background: var(--card-bg); border: 1px solid var(--card-border); border-bottom-right-radius: 0; margin-left: auto; }
                .ai-chat-input-area { display: flex; gap: 0.75rem; align-items: center; margin-top: auto; }
                .info-text { color: var(--text-secondary); text-align: center; padding: 2rem 0; }
                .loading-text { color: var(--text-secondary); text-align: center; padding: 1rem 0; font-style: italic; }
                .formatted-content code { background: rgba(255, 255, 255, 0.1); padding: 0.1em 0.3em; border-radius: 4px; }
                .formatted-content ul { padding-left: 1.25rem; margin: 0.5rem 0; }
                .formatted-content p { margin: 0 0 0.5rem 0; } .formatted-content p:last-child { margin-bottom: 0; }
                
                /* Enhanced scrollbars */
                .ai-chat-history::-webkit-scrollbar { width: 8px; }
                .ai-chat-history::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
                .ai-chat-history::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
                .ai-chat-history::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
                
                /* Enhanced header section */
                .report-header { margin-bottom: 0; }
                .report-header h1 { margin-bottom: 0.5rem; }
                .report-header p { margin: 0; font-size: 1rem; }
                
                /* Enhanced vulnerability details */
                .vulnerability-section { }
                .vulnerability-section .formatted-content { background: rgba(255, 255, 255, 0.01); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; }
                
                /* Enhanced AI Analysis Styling */
                .ai-analysis-content { 
                    line-height: 1.8; 
                    font-size: 0.95rem;
                }
                .ai-analysis-content .formatted-content {
                    background: transparent;
                    border: none;
                    padding: 0;
                }
                .ai-analysis-content h1, .ai-analysis-content h2, .ai-analysis-content h3 {
                    color: var(--text-primary);
                    font-weight: 600;
                    margin: 2rem 0 1rem 0;
                    padding-bottom: 0.75rem;
                    border-bottom: 1px solid var(--card-border);
                    font-size: 1.1rem;
                }
                .ai-analysis-content h1:first-child, .ai-analysis-content h2:first-child, .ai-analysis-content h3:first-child {
                    margin-top: 0;
                }
                .ai-analysis-content p {
                    margin: 1rem 0;
                    color: var(--text-secondary);
                    line-height: 1.7;
                }
                .ai-analysis-content ul {
                    margin: 1.25rem 0;
                    padding-left: 1.5rem;
                    background: rgba(255, 255, 255, 0.02);
                    border-radius: 0.5rem;
                    padding: 1rem 1rem 1rem 2.5rem;
                    border-left: 3px solid var(--card-border);
                }
                .ai-analysis-content li {
                    margin: 0.75rem 0;
                    color: var(--text-secondary);
                    line-height: 1.6;
                }
                .ai-analysis-content strong {
                    color: var(--text-primary);
                    font-weight: 600;
                }
                .ai-analysis-content code {
                    background: rgba(255, 255, 255, 0.1);
                    color: var(--text-primary);
                    padding: 0.2rem 0.5rem;
                    border-radius: 0.3rem;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 0.9rem;
                    border: 1px solid var(--card-border);
                }
                /* Enhanced formatting for sections */
                .ai-analysis-content p:has(strong) {
                    background: rgba(255, 255, 255, 0.03);
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border-left: 3px solid var(--text-primary);
                    margin: 1.5rem 0;
                }
                /* Better spacing for analysis sections */
                .ai-analysis-content p + ul {
                    margin-top: 0.5rem;
                }
                .ai-analysis-content ul + p {
                    margin-top: 1.5rem;
                }
                /* Status indicators in AI content */
                .ai-analysis-content .status-indicator {
                    display: inline-block;
                    margin-right: 0.5rem;
                    font-size: 1.1rem;
                }
                .ai-analysis-content .security-metric {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid var(--card-border);
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin: 1rem 0;
                    display: grid;
                    grid-template-columns: auto 1fr;
                    gap: 1rem;
                    align-items: center;
                }
                .ai-analysis-content .metric-icon {
                    font-size: 1.5rem;
                }
                .ai-analysis-content .metric-details {
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                }
                .ai-analysis-content .metric-title {
                    font-weight: 600;
                    color: var(--text-primary);
                    font-size: 1rem;
                }
                .ai-analysis-content .metric-value {
                    color: var(--text-secondary);
                    font-size: 0.9rem;
                }
            `}</style>

            <div className="report-page">
                <div className="layout-container">
                    <div className="hero-section">
                        <h1 className="hero-title">Website Security Report</h1>
                        <p className="hero-subtitle">Comprehensive security analysis and OWASP compliance assessment for {url || deploymentUrl}</p>
                    </div>

                    <div className="report-layout">
                        <main>
                            <div className="card">
                                <h3>📊 Security Overview</h3>
                                <div className="results-grid">
                                    <SecurityScoreGauge score={actualSecurityScore} />
                                    <div className="info-list">
                                        <div className="info-item">
                                            <span className="label">Target URL</span>
                                            <span className="value">{url || deploymentUrl || 'N/A'}</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="label">Security Score</span>
                                            <span className="value">{actualSecurityScore}/100</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="label">HTTPS Status</span>
                                            <span className="value">{scan_result.https ? 'Enabled' : 'Disabled'}</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="label">SSL Certificate</span>
                                            <span className="value">{scan_result.ssl_certificate?.valid ? 'Valid' : 'Invalid'}</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="label">WAF Protection</span>
                                            <span className="value">{finalWafDetected ? (finalWafType !== 'unknown' ? `Detected (${finalWafType})` : 'Detected') : 'Not Detected'}</span>
                                        </div>
                                        <div className="info-item">
                                            <span className="label">DNSSEC</span>
                                            <span className="value">{scan_result.dns_security?.dnssec?.enabled ? 'Enabled' : 'Disabled'}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="card">
                                <h3>🛡️ Security Configuration Status</h3>
                                <div className="status-grid">
                                    <div className="status-item">
                                        <div className="status-label">HTTPS Protocol</div>
                                        <div className="status-value" style={{ color: scan_result.https ? '#28a745' : '#dc3545' }}>
                                            {scan_result.https ? '✅ Enabled' : '❌ Disabled'}
                                        </div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">SSL Certificate</div>
                                        <div className="status-value" style={{ color: scan_result.ssl_certificate?.valid ? '#28a745' : '#dc3545' }}>
                                            {scan_result.ssl_certificate?.valid ? '✅ Valid' : '❌ Invalid'}
                                        </div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">Web Application Firewall</div>
                                        <div className="status-value" style={{ color: finalWafDetected ? '#28a745' : '#ffc107' }}>
                                            {finalWafDetected ? `✅ Protected ${finalWafType !== 'unknown' ? `(${finalWafType})` : ''}` : '⚠️ Not Detected'}
                                        </div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">DNS Security</div>
                                        <div className="status-value" style={{ color: scan_result.dns_security?.dnssec?.enabled ? '#28a745' : '#ffc107' }}>
                                            {scan_result.dns_security?.dnssec?.enabled ? '✅ DNSSEC Enabled' : '⚠️ DNSSEC Disabled'}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="card">
                                <h3>🎯 OWASP Top 10 Analysis</h3>
                                <div className="owasp-summary">
                                    <OwaspMappingCardSection scanResult={scan_result} />
                                </div>
                            </div>

                            {summary && (
                                <div className="card">
                                    <h3>🧠 AI Security Analysis</h3>
                                    <div className="vulnerability-section">
                                        <div className="ai-analysis-content">
                                            <ChatResponseFormatter message={summary} type="ai" />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {scan_result.flags && scan_result.flags.length > 0 && (
                                <div className="card">
                                    <h3>🚨 Vulnerability Details</h3>
                                    <div className="vulnerability-section">
                                        <SecurityIssueFormatter issues={scan_result.flags} scanResult={scan_result} />
                                    </div>
                                </div>
                            )}
                        </main>

                        <aside className="report-sidebar">
                            <div className="card ai-chat-container">
                                <h3>🤖 AI Security Advisor</h3>
                                <div className="ai-chat-history">
                                    {chatHistory.map((chat, index) => (
                                        <div key={index} className={`chat-message ${chat.type}-message`}>
                                            <ChatResponseFormatter message={chat.message} type={chat.type} />
                                        </div>
                                    ))}
                                    {isLoading && <div className="loading-text">🔍 Analyzing your question...</div>}
                                    {chatHistory.length === 0 && !isLoading && (
                                        <div className="info-text">👋 Ask me anything about your security report!</div>
                                    )}
                                </div>
                                <div className="ai-chat-input-area">
                                    <input
                                        type="text"
                                        className="input"
                                        placeholder="Ask about security findings..."
                                        value={chatInput}
                                        onChange={(e) => setChatInput(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleChat()}
                                        disabled={isLoading}
                                    />
                                    <button 
                                        className="btn" 
                                        onClick={() => handleChat()} 
                                        disabled={isLoading || !chatInput.trim()}
                                    >
                                        Send
                                    </button>
                                </div>
                            </div>
                        </aside>
                    </div>
                </div>
            </div>
        </PageWrapper>
    );
};

export default ReportPage;

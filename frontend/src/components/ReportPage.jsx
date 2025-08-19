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

    const getColor = (s) => {
        if (s >= 85) return '#ffffff'; // Excellent
        if (s >= 70) return '#cccccc'; // Good
        if (s >= 50) return '#999999'; // Medium
        return '#666666'; // Low
    };

    return (
        <div className="score-gauge-container">
            <svg viewBox="0 0 120 120" className="score-gauge-svg">
                <circle className="gauge-background" cx="60" cy="60" r="54" />
                <circle
                    className="gauge-progress"
                    cx="60" cy="60" r="54"
                    stroke={getColor(scoreValue)}
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
                setIsLoading(false);
                return;
            }
            try {
                setIsLoading(true);
                const response = await fetch('http://localhost:8000/owasp-mapping', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scan_result: scanResult }),
                });
                const data = await response.json();
                if (data.success && data.owasp_mapping) {
                    const { owasp_mapping, summary } = data.owasp_mapping;
                    setOwaspData({
                        categories: owasp_mapping,
                        total_issues: summary.total_issues,
                        risk_score: summary.total_issues > 15 ? 'Critical' : summary.total_issues > 8 ? 'High' : summary.total_issues > 3 ? 'Medium' : 'Low',
                    });
                } else {
                    setError(data.error || 'Failed to process mapping');
                }
            } catch (err) {
                setError('Could not connect to the analysis server.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchOwaspMapping();
    }, [scanResult]);

    if (isLoading) return <p className="info-text">Analyzing OWASP vulnerabilities...</p>;
    if (error) return <p className="info-text">OWASP analysis unavailable: {error}</p>;
    if (!owaspData || !owaspData.categories || Object.keys(owaspData.categories).length === 0) {
        return <p className="info-text">No OWASP Top 10 vulnerabilities detected.</p>;
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
                <div className="hero-section">
                    <h1 className="hero-title">Security Report</h1>
                    <p className="hero-subtitle">No scan results available. Please run a security scan first.</p>
                </div>
            </PageWrapper>
        );
    }

    const { scan_result = {}, url, deploymentUrl, security_score, summary } = scanResult;

    return (
        <PageWrapper>
            <style>{`
                :root {
                    --bg-black: #000000;
                    --card-bg: rgba(255, 255, 255, 0.05);
                    --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3);
                    --text-primary: #ffffff;
                    --text-secondary: #a1a1aa;
                    --input-bg: rgba(255, 255, 255, 0.03);
                }
                .report-page { background: var(--bg-black); color: var(--text-primary); min-height: 100vh; }

                /* Layout & Typography */
                .hero-section, .report-header { text-align: center; padding: 3rem 1rem; }
                .hero-title, .report-header h1 { font-size: 2.5rem; font-weight: 700; margin: 0; letter-spacing: -1px; }
                .hero-subtitle, .report-header p { color: var(--text-secondary); margin-top: 0.5rem; font-size: 1.1rem; }

                .report-layout { display: grid; grid-template-columns: 1fr 450px; gap: 2rem; max-width: 1600px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                .report-sidebar { position: sticky; top: 2rem; height: calc(100vh - 4rem); }
                @media (max-width: 1200px) { .report-layout { grid-template-columns: 1fr; } .report-sidebar { position: static; height: auto; } }

                /* Card Styling */
                .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); transition: border-color 0.3s ease; }
                .card:hover { border-color: var(--card-border-hover); }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 2rem 0; text-transform: uppercase; letter-spacing: 1px; }

                /* At a Glance Section & Score Gauge */
                .at-a-glance-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; align-items: center; }
                .score-gauge-container { position: relative; display: flex; align-items: center; justify-content: center; }
                .score-gauge-svg { transform: rotate(-90deg); width: 140px; height: 140px; }
                .gauge-background { fill: none; stroke: rgba(255, 255, 255, 0.1); stroke-width: 12; }
                .gauge-progress { fill: none; stroke-width: 12; stroke-linecap: round; transition: stroke-dashoffset 1s ease-out; }
                .score-text { position: absolute; text-align: center; }
                .score-value { font-size: 2.5rem; font-weight: 600; color: var(--text-primary); }
                .score-label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
                .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
                .status-item .status-label { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.5px; }
                .status-item .status-value { font-size: 1.1rem; font-weight: 500; color: var(--text-primary); }

                /* OWASP Section */
                .owasp-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; text-align: center; }
                .owasp-value { display: block; font-size: 1.75rem; font-weight: 600; color: var(--text-primary); }
                .owasp-label { display: block; font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
                .owasp-list { display: flex; flex-direction: column; gap: 0.75rem; }
                .owasp-item { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--card-border); font-size: 0.9rem; }
                .owasp-item:last-child { border-bottom: none; }
                .issue-count { color: var(--text-secondary); background: rgba(255,255,255,0.1); padding: 0.2rem 0.5rem; border-radius: 0.25rem; font-size: 0.8rem;}

                /* AI Chat Advisor */
                .ai-chat-container { height: 100%; display: flex; flex-direction: column; }
                .ai-chat-history { flex-grow: 1; overflow-y: auto; padding-right: 1rem; margin-bottom: 1.5rem; }
                .chat-message { max-width: 90%; margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5; word-wrap: break-word; }
                .ai-message { background: rgba(255, 255, 255, 0.1); border-bottom-left-radius: 0; }
                .user-message { background: var(--card-bg); border: 1px solid var(--card-border); border-bottom-right-radius: 0; margin-left: auto; }
                .ai-chat-input-area { display: flex; gap: 0.75rem; align-items: center; margin-top: auto; }
                .input { flex-grow: 1; background: var(--input-bg); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; transition: border-color 0.3s; }
                .input:focus { border-color: var(--text-primary); outline: none; }
                .btn { background: transparent; border: 1px solid var(--card-border); color: var(--text-secondary); padding: 0.75rem; border-radius: 0.5rem; cursor: pointer; transition: all 0.3s; }
                .btn:hover:not(:disabled) { border-color: var(--text-primary); color: var(--text-primary); }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .info-text, .loading-text { color: var(--text-secondary); text-align: center; padding: 2rem 0; }
            `}</style>

            <div className="report-page">
                <header className="report-header">
                    <h1>Security Report</h1>
                    <p>{url || deploymentUrl}</p>
                </header>

                <div className="report-layout">
                    <main className="report-main">
                        <div className="card">
                            <h3>At a Glance</h3>
                            <div className="at-a-glance-grid">
                                <SecurityScoreGauge score={security_score} />
                                <div className="status-grid">
                                    <div className="status-item">
                                        <div className="status-label">HTTPS</div>
                                        <div className="status-value">{scan_result.https ? 'Enabled' : 'Disabled'}</div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">Valid SSL</div>
                                        <div className="status-value">{scan_result.ssl_certificate?.valid ? 'Active' : 'Invalid'}</div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">WAF</div>
                                        <div className="status-value">{scan_result.waf_analysis?.waf_detected ? 'Protected' : 'Not Found'}</div>
                                    </div>
                                    <div className="status-item">
                                        <div className="status-label">DNSSEC</div>
                                        <div className="status-value">{scan_result.dns_security?.dnssec?.enabled ? 'Enabled' : 'Not Found'}</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <h3>OWASP Top 10 Analysis</h3>
                            <OwaspMappingCardSection scanResult={scanResult} />
                        </div>

                        {summary && (
                            <div className="card">
                                <h3>AI Analysis Summary</h3>
                                <ChatResponseFormatter message={summary} type="ai" />
                            </div>
                        )}

                        {scan_result.flags && scan_result.flags.length > 0 && (
                            <div className="card">
                                <h3>Vulnerability Details</h3>
                                <SecurityIssueFormatter issues={scan_result.flags} scanResult={scan_result} />
                            </div>
                        )}
                    </main>

                    <aside className="report-sidebar">
                        <div className="card ai-chat-container">
                            <h3>AI Security Advisor</h3>
                            <div className="ai-chat-history">
                                {chatHistory.map((chat, index) => (
                                    <div key={index} className={`chat-message ${chat.type}-message`}>
                                        <ChatResponseFormatter message={chat.message} type={chat.type} />
                                    </div>
                                ))}
                                {isLoading && <div className="loading-text">Analyzing...</div>}
                            </div>
                            <div className="ai-chat-input-area">
                                <input
                                    type="text"
                                    className="input"
                                    placeholder="Ask a question..."
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleChat()}
                                    disabled={isLoading}
                                />
                                <button className="btn" onClick={() => handleChat()} disabled={isLoading || !chatInput.trim()}>Send</button>
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </PageWrapper>
    );
};

export default ReportPage;
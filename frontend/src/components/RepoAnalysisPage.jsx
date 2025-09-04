import React, { useState, useEffect } from 'react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
import ChatResponseFormatter from './ChatResponseFormatter';

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


// --- Main Page Component ---
const RepoAnalysisPage = ({ setScanResult }) => { // Assuming setScanResult is passed for consistency
    usePreventZoom();
    const [repoUrl, setRepoUrl] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [error, setError] = useState('');
    const [analysisLogs, setAnalysisLogs] = useState([]);
    const [modelType, setModelType] = useState('smart');
    const [chatMessages, setChatMessages] = useState([]);
    const [currentQuestion, setCurrentQuestion] = useState('');
    const [isAskingAI, setIsAskingAI] = useState(false);
    const [fixingIssues, setFixingIssues] = useState({});
    const [fixedIssues, setFixedIssues] = useState(new Set());
    const [isFixingAll, setIsFixingAll] = useState(false);
    
    // --- Core Logic Functions (Restored) ---

    const cleanRepositoryUrl = (url) => {
        try {
            let cleaned = url.replace(/\/tree\/[^\/]+.*$/, '').replace(/\/blob\/[^\/]+.*$/, '').replace(/\/$/, '');
            const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+$/;
            if (!urlPattern.test(cleaned)) return null;
            return cleaned;
        } catch (e) { return null; }
    };

    const analyzeRepository = async () => {
        const cleanedUrl = cleanRepositoryUrl(repoUrl.trim());
        if (!cleanedUrl) {
            setError('Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)');
            return;
        }
        setIsScanning(true);
        setError('');
        setAnalysisResult(null);
        setAnalysisLogs(['[INIT] Starting repository analysis...']);
        setChatMessages([]);
        setFixedIssues(new Set());
        setFixingIssues({});
        try {
            const response = await fetch('http://localhost:8000/analyze-repo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: cleanedUrl, model_type: modelType }),
            });
            const data = await response.json();
            if (data.error) {
                setError(data.error);
                setAnalysisLogs(prev => [...prev, `[ERROR] Analysis failed: ${data.error}`]);
            } else {
                setAnalysisResult(data);
                setAnalysisLogs(prev => [...prev, '[OK] Repository analysis completed successfully!']);
                const summary = generateAnalysisSummary(data);
                setChatMessages([{ type: 'ai', message: summary }]);
            }
        } catch (err) {
            const errorMsg = 'Failed to connect to the analysis server. Please ensure it is running.';
            setError(errorMsg);
            setAnalysisLogs(prev => [...prev, `[ERROR] ${errorMsg}`]);
        } finally {
            setIsScanning(false);
        }
    };

    const generateAnalysisSummary = (data) => {
        const score = data.overall_security_score || 0;
        const level = data.security_level || 'Unknown';
        const summary = data.security_summary || {};
        return `**Repository Analysis Complete**\n\n- **Repository:** ${data.repository_info?.name || 'Unknown'}\n- **Security Score:** ${score}/100 (${level})\n- **Language:** ${data.repository_info?.language || 'N/A'}\n\n**Scan Results:**\n- **Secrets Found:** ${summary.secrets_found || 0}\n- **Static Issues:** ${summary.static_issues_found || 0}\n- **Vulnerable Dependencies:** ${summary.vulnerable_dependencies || 0}\n\nI am ready to answer specific questions about these findings.`;
    };
    
    const askAI = async () => {
        if (!currentQuestion.trim() || !analysisResult) return;
        setIsAskingAI(true);
        const userMessage = { type: 'user', message: currentQuestion };
        setChatMessages(prev => [...prev, userMessage]);
        const questionToAsk = currentQuestion;
        setCurrentQuestion('');
        try {
            // Format chat history for backend compatibility
            const formattedHistory = [...chatMessages, userMessage].map(msg => ({
                type: msg.type === 'ai' ? 'assistant' : 'user',
                parts: [typeof msg.message === 'string' ? msg.message : JSON.stringify(msg.message)]
            }));
            
            const response = await fetch('http://localhost:8000/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: questionToAsk,
                    context: 'repo_analysis',
                    history: formattedHistory
                }),
            });
            const data = await response.json();
            setChatMessages(prev => [...prev, { type: 'ai', message: data.response || 'Sorry, I could not process your question.' }]);
        } catch (err) {
            setChatMessages(prev => [...prev, { type: 'ai', message: 'Error: Could not connect to AI assistant.' }]);
        } finally {
            setIsAskingAI(false);
        }
    };
    
    const isIssueFixed = (issueType, issueIndex) => fixedIssues.has(`${issueType}-${issueIndex}`);
    
    const fixIssue = async (issue, issueType, issueIndex) => {
        const issueId = `${issueType}-${issueIndex}`;
        if (fixingIssues[issueId] || isFixingAll) return;
        setFixingIssues(prev => ({ ...prev, [issueId]: true }));
        try {
            const issueData = {
                type: issueType,
                description: issue.description || issue.title || issue.pattern || issue.message || 'Security issue',
                file: issue.file || issue.filename || null,
                line: issue.line || issue.line_number || null,
                severity: issue.severity || 'Medium',
            };
            const response = await fetch('http://localhost:8000/propose-fix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl.trim(), issue: issueData, branch_name: "main" }),
            });
            const data = await response.json();
            if (response.ok && data.success) {
                setFixedIssues(prev => new Set(prev).add(issueId));
                let successMessage = `**Issue Fixed Successfully!**\n\n- **Issue:** ${issueData.description}\n- **File:** ${issueData.file || 'Multiple files'}`;
                if (data.pull_request?.url) {
                    successMessage += `\n- **Action:** Pull Request created at [${data.pull_request.url}](${data.pull_request.url})`;
                }
                setChatMessages(prev => [...prev, { type: 'ai', message: successMessage }]);
            } else {
                throw new Error(data.error || 'Failed to fix issue');
            }
        } catch (error) {
            setChatMessages(prev => [...prev, {
                type: 'ai',
                message: `**Failed to fix issue:** ${issue.description || 'Security issue'}\n- **Error:** ${error.message}`
            }]);
        } finally {
            setFixingIssues(prev => ({ ...prev, [issueId]: false }));
        }
    };

    const fixAllIssues = async () => {
        setIsFixingAll(true);
        const allUnfixedIssues = [
            ...(analysisResult.secret_scan_results?.map((issue, index) => ({ issue, type: 'secret', index })) || []),
            ...(analysisResult.static_analysis_results?.map((issue, index) => ({ issue, type: 'static_analysis', index })) || []),
            ...(analysisResult.dependency_scan_results?.vulnerable_packages?.map((issue, index) => ({ issue, type: 'dependency', index })) || [])
        ].filter(({ type, index }) => !isIssueFixed(type, index));

        for (const { issue, type, index } of allUnfixedIssues) {
            await fixIssue(issue, type, index);
            await new Promise(resolve => setTimeout(resolve, 1000)); // Delay between fixes
        }
        setIsFixingAll(false);
    };

    const renderIssueRow = (issue, type, index) => {
        const issueId = `${type}-${index}`;
        if (isIssueFixed(type, index)) return null;
        const details = {
            filePath: issue.file || issue.filename || 'N/A',
            severity: issue.severity || 'Medium',
            description: issue.description || issue.pattern || issue.rule_id || 'N/A',
            line: issue.line || issue.line_number || '-',
        };
        return (
            <tr key={issueId}>
                <td>{details.filePath}</td>
                <td><span className={`severity-badge severity-${details.severity.toLowerCase()}`}>{details.severity}</span></td>
                <td>{details.description}</td>
                <td>{details.line}</td>
                <td>
                    <button className="btn-fix" onClick={() => fixIssue(issue, type, index)} disabled={fixingIssues[issueId] || isFixingAll}>
                        {fixingIssues[issueId] ? 'Fixing...' : 'Fix'}
                    </button>
                </td>
            </tr>
        );
    };

    return (
        <PageWrapper>
            <style>{`
                /* All styles from the previous final version are included here */
                :root {
                    --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                }
                .repo-analysis-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                .layout-container { max-width: 900px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }
                .card { width: 100%; box-sizing: border-box; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.3s ease; }
                .card:hover { border-color: var(--card-border-hover); box-shadow: 0 0 25px rgba(255, 255, 255, 0.08); }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 1.5rem 0; text-transform: uppercase; letter-spacing: 1px; }
                .input-group { display: flex; gap: 1rem; }
                .input { flex-grow: 1; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; }
                .btn { background: var(--text-primary); border: 1px solid var(--text-primary); color: var(--bg-black); padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s; }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .btn:hover:not(:disabled) { box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
                .btn-secondary { background: transparent; color: var(--text-secondary); border: 1px solid var(--card-border); }
                .btn-secondary:hover:not(:disabled) { border-color: var(--text-primary); color: var(--text-primary); }
                .error-message { color: var(--text-secondary); background: rgba(255, 77, 77, 0.1); border-left: 3px solid #ff4d4d; padding: 1rem; margin-top: 1rem; }
                .terminal { background: #000; border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; height: 250px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9rem; }
                .terminal-line { line-height: 1.6; color: var(--text-secondary); }
                .terminal-line .log-prefix { display: inline-block; margin-right: 0.75rem; color: var(--text-primary); font-weight: 600; }
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
                .issues-table { width: 100%; border-collapse: collapse; }
                .issues-table th, .issues-table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--card-border); }
                .issues-table th { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; font-weight: 500; }
                .issues-table tr:last-child td { border-bottom: none; }
                .severity-badge { padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; background: rgba(255,255,255,0.1); color: var(--text-secondary); }
                .severity-critical, .severity-high { color: var(--text-primary); background: rgba(255,255,255,0.15); }
                .btn-fix { background: rgba(255,255,255,0.1); color: var(--text-primary); border: 1px solid transparent; padding: 0.4rem 0.8rem; border-radius: 0.5rem; font-size: 0.8rem; cursor: pointer; transition: all 0.2s; }
                .btn-fix:hover:not(:disabled) { background: var(--text-primary); color: var(--bg-black); }
                .card-header-action { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
                .card-header-action h3 { margin: 0; }
                .ai-chat-history { max-height: 400px; overflow-y: auto; padding-right: 1rem; margin-bottom: 1.5rem; }
                .ai-chat-input-area { display: flex; gap: 0.75rem; align-items: center; margin-top: auto; }
                .formatted-content code { background: rgba(255, 255, 255, 0.1); padding: 0.1em 0.3em; border-radius: 4px; }
                .formatted-content ul { padding-left: 1.25rem; margin: 0.5rem 0; }
                .formatted-content p { margin: 0 0 0.5rem 0; } .formatted-content p:last-child { margin-bottom: 0; }
            `}</style>
            
            <div className="repo-analysis-page">
                <div className="layout-container">
                    <div className="hero-section">
                        <h1 className="hero-title">Repository AI Auditor</h1>
                        <p className="hero-subtitle">Submit any public GitHub repository to receive a comprehensive security audit, vulnerability analysis, and AI-powered recommendations.</p>
                    </div>

                    {!analysisResult && (
                        <div className="card">
                            <h3>Analysis Target</h3>
                            <div className="input-group">
                                <input type="text" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="Enter public GitHub repository URL" className="input" disabled={isScanning} />
                                <button onClick={analyzeRepository} disabled={isScanning || !repoUrl.trim()} className="btn">{isScanning ? 'Analyzing...' : 'Analyze'}</button>
                            </div>
                            {error && <p className="error-message">{error}</p>}
                        </div>
                    )}

                    {isScanning && (
                         <div className="card">
                            <h3>Live Analysis Log</h3>
                            <div className="terminal">
                                {analysisLogs.map((log, index) => (
                                    <div key={index} className="terminal-line">
                                        <span className="log-prefix">[{log.match(/^\[(.*?)\]/)?.[1] || 'INFO'}]</span>
                                        {log.replace(/^\[.*?\]\s/, '')}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {analysisResult && !isScanning && (
                        <>
                            <div className="card">
                                <h3>Analysis Overview</h3>
                                <div className="results-grid">
                                    <SecurityScoreGauge score={analysisResult.overall_security_score} />
                                    <div className="info-list">
                                        <div className="info-item"><span className="label">Repository</span><span className="value">{analysisResult.repository_info?.name || 'N/A'}</span></div>
                                        <div className="info-item"><span className="label">Language</span><span className="value">{analysisResult.repository_info?.language || 'N/A'}</span></div>
                                        <div className="info-item"><span className="label">Secrets Found</span><span className="value">{analysisResult.security_summary?.secrets_found || 0}</span></div>
                                        <div className="info-item"><span className="label">Dependencies</span><span className="value">{analysisResult.security_summary?.vulnerable_dependencies || 0}</span></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="card">
                                <div className="card-header-action">
                                    <h3>Vulnerabilities Detected</h3>
                                    <button onClick={fixAllIssues} disabled={isFixingAll} className="btn btn-secondary">{isFixingAll ? 'Fixing All...' : 'Fix All Issues'}</button>
                                </div>
                                <div style={{ overflowX: 'auto' }}>
                                    <table className="issues-table">
                                        <thead><tr><th>File Path</th><th>Severity</th><th>Description</th><th>Line</th><th>Action</th></tr></thead>
                                        <tbody>
                                            {analysisResult.secret_scan_results?.map((issue, index) => renderIssueRow(issue, 'secret', index))}
                                            {analysisResult.static_analysis_results?.map((issue, index) => renderIssueRow(issue, 'static_analysis', index))}
                                            {analysisResult.dependency_scan_results?.vulnerable_packages?.map((issue, index) => renderIssueRow(issue, 'dependency', index))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="card">
                                <h3>AI Security Advisor</h3>
                                <div className="ai-chat-history">
                                    {chatMessages.map((msg, index) => (
                                        <div key={index} className={`chat-message ${msg.type}-message`}>
                                            <ChatResponseFormatter message={msg.message} />
                                        </div>
                                    ))}
                                    {isAskingAI && <div className="info-text">AI is thinking...</div>}
                                </div>
                                <div className="ai-chat-input-area">
                                    <input className="input" placeholder="Ask about these findings..." value={currentQuestion} onChange={(e) => setCurrentQuestion(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && askAI()} disabled={isAskingAI} />
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
};

export default RepoAnalysisPage;
import React, { useState, useEffect } from 'react';
import { API_BASE_URL, apiUrl } from '../config/api';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
import ChatResponseFormatter from './ChatResponseFormatter';
import CodePreviewTester from './CodePreviewTester';

// --- Sub-component: Diff Viewer ---
const DiffViewer = ({ original, fixed, filename, diffStats, unifiedDiff }) => {
    const [showDiff, setShowDiff] = useState(false);
    const [viewMode, setViewMode] = useState('unified'); // 'unified', 'split', 'raw'
    
    if (!diffStats?.has_changes) {
        return (
            <div className="diff-viewer">
                <div className="diff-header">
                    <span className="diff-filename">{filename}</span>
                    <span className="no-changes">No changes detected</span>
                </div>
            </div>
        );
    }
    
    const renderUnifiedDiff = () => {
        if (!unifiedDiff) return <div>No diff available</div>;
        
        const lines = unifiedDiff.split('\n');
        return (
            <div className="unified-diff">
                {lines.map((line, index) => {
                    let className = 'diff-line';
                    if (line.startsWith('+++') || line.startsWith('---')) {
                        className += ' diff-file-header';
                    } else if (line.startsWith('@@')) {
                        className += ' diff-hunk-header';
                    } else if (line.startsWith('+')) {
                        className += ' diff-addition';
                    } else if (line.startsWith('-')) {
                        className += ' diff-deletion';
                    } else {
                        className += ' diff-context';
                    }
                    
                    return (
                        <div key={index} className={className}>
                            <code>{line}</code>
                        </div>
                    );
                })}
            </div>
        );
    };
    
    const renderSplitDiff = () => {
        const originalLines = (original || '').split('\n');
        const fixedLines = (fixed || '').split('\n');
        const maxLines = Math.max(originalLines.length, fixedLines.length);
        
        return (
            <div className="split-diff">
                <div className="split-diff-pane">
                    <div className="pane-header">Original</div>
                    <div className="pane-content">
                        {originalLines.map((line, index) => (
                            <div key={index} className="diff-line">
                                <span className="line-number">{index + 1}</span>
                                <code>{line}</code>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="split-diff-pane">
                    <div className="pane-header">Fixed</div>
                    <div className="pane-content">
                        {fixedLines.map((line, index) => (
                            <div key={index} className="diff-line">
                                <span className="line-number">{index + 1}</span>
                                <code>{line}</code>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    };
    
    return (
        <div className="diff-viewer">
            <div className="diff-header" onClick={() => setShowDiff(!showDiff)}>
                <div className="diff-title">
                    <span className="diff-filename">{filename}</span>
                    <div className="diff-stats">
                        {diffStats.lines_added > 0 && <span className="stat-added">+{diffStats.lines_added}</span>}
                        {diffStats.lines_removed > 0 && <span className="stat-removed">-{diffStats.lines_removed}</span>}
                        {diffStats.lines_modified > 0 && <span className="stat-modified">~{diffStats.lines_modified}</span>}
                    </div>
                </div>
                <button className="diff-toggle">
                    {showDiff ? '−' : '+'}
                </button>
            </div>
            
            {showDiff && (
                <div className="diff-content">
                    <div className="diff-controls">
                        <button 
                            className={`control-btn ${viewMode === 'unified' ? 'active' : ''}`}
                            onClick={() => setViewMode('unified')}
                        >
                            Unified
                        </button>
                        <button 
                            className={`control-btn ${viewMode === 'split' ? 'active' : ''}`}
                            onClick={() => setViewMode('split')}
                        >
                            Split
                        </button>
                    </div>
                    
                    <div className="diff-display">
                        {viewMode === 'unified' ? renderUnifiedDiff() : renderSplitDiff()}
                    </div>
                </div>
            )}
        </div>
    );
};
// --- Sub-component: Rate Limit Indicator ---
const RateLimitIndicator = ({ rateLimitStatus }) => {
    if (!rateLimitStatus) return null;
    
    const getStatusColor = () => {
        if (rateLimitStatus.is_blocked) return '#ef4444';
        if (rateLimitStatus.requests_remaining_this_minute <= 2) return '#f59e0b';
        return '#22c55e';
    };
    
    const getStatusText = () => {
        if (rateLimitStatus.is_blocked) return 'Rate Limited';
        if (rateLimitStatus.requests_remaining_this_minute <= 2) return 'Low Quota';
        return 'API OK';
    };
    
    return (
        <div className="rate-limit-indicator">
            <div className="rate-limit-status" style={{ color: getStatusColor() }}>
                <div className="status-dot" style={{ backgroundColor: getStatusColor() }}></div>
                <span className="status-text">{getStatusText()}</span>
            </div>
            <div className="rate-limit-details">
                <small>
                    {rateLimitStatus.is_blocked ? (
                        `Blocked for ${Math.max(0, rateLimitStatus.blocked_until - Date.now() / 1000).toFixed(0)}s`
                    ) : (
                        `${rateLimitStatus.requests_remaining_this_minute}/8 requests left`
                    )}
                </small>
            </div>
        </div>
    );
};

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
    
    // Helper function to safely render file paths
    const safeRenderFilePath = (file) => {
        if (typeof file === 'string') return file;
        if (typeof file === 'object' && file !== null) {
            return file.path || file.file || file.filename || 'Unknown file';
        }
        return 'Unknown file';
    };
    
    // Helper function to safely render file reason/pattern
    const safeRenderFileReason = (file) => {
        if (typeof file === 'object' && file !== null) {
            return file.reason || file.pattern || file.risk || '';
        }
        return '';
    };
    
    const [repoUrl, setRepoUrl] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [error, setError] = useState('');
    const [analysisLogs, setAnalysisLogs] = useState([]);
    const [modelType, setModelType] = useState('smart');
    const [chatMessages, setChatMessages] = useState([]);
    const [fixDetails, setFixDetails] = useState({}); // Store fix details with diffs
    const [expandedDiffs, setExpandedDiffs] = useState({}); // Track which diffs are expanded
    const [rateLimitStatus, setRateLimitStatus] = useState(null); // Track API rate limits
    const [currentQuestion, setCurrentQuestion] = useState('');
    const [isAskingAI, setIsAskingAI] = useState(false);
    const [fixingIssues, setFixingIssues] = useState({});
    const [fixedIssues, setFixedIssues] = useState(new Set());
    const [isFixingAll, setIsFixingAll] = useState(false);
    const [showAllIssues, setShowAllIssues] = useState(false); // Toggle for showing low priority issues
    const [pentestResult, setPentestResult] = useState(null);
    const [isPentesting, setIsPentesting] = useState(false);
    const [pentestProgress, setPentestProgress] = useState('');
    const [pentestError, setPentestError] = useState('');
    const [expandedFindings, setExpandedFindings] = useState({});
    
    // --- Core Logic Functions (Restored) ---

    const cleanRepositoryUrl = (url) => {
        try {
            let cleaned = url.replace(/\/tree\/[^\/]+.*$/, '').replace(/\/blob\/[^\/]+.*$/, '').replace(/\/$/, '');
            const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+$/;
            if (!urlPattern.test(cleaned)) return null;
            return cleaned;
        } catch (e) { return null; }
    };

    const runDeepPentest = async () => {
        const cleanedUrl = cleanRepositoryUrl(repoUrl.trim());
        if (!cleanedUrl) {
            setPentestError('Please enter a valid GitHub repository URL');
            return;
        }
        setIsPentesting(true);
        setPentestError('');
        setPentestResult(null);
        setPentestProgress('Cloning repository & uploading to S3...');
        try {
            const response = await fetch(apiUrl('api/pentest-repo'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: cleanedUrl, deep_scan: true }),
            });
            const data = await response.json();
            if (data.error && !data.success) {
                setPentestError(data.error);
            } else {
                setPentestResult(data);
                setPentestProgress('');
            }
        } catch (err) {
            setPentestError('Failed to connect to pentest service. Ensure backend is running.');
        } finally {
            setIsPentesting(false);
            setPentestProgress('');
        }
    };

    const toggleFinding = (id) => {
        setExpandedFindings(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const getSeverityColor = (severity) => {
        const colors = { Critical: '#dc2626', High: '#ea580c', Medium: '#d97706', Low: '#2563eb', Informational: '#6b7280' };
        return colors[severity] || '#6b7280';
    };

    const getSeverityIcon = (severity) => {
        const icons = { Critical: '🔴', High: '🟠', Medium: '🟡', Low: '🔵', Informational: 'ℹ️' };
        return icons[severity] || 'ℹ️';
    };

    const getCategoryIcon = (category) => {
        const icons = {
            'Injection': '💉', 'Authentication Bypass': '🔓', 'Authorization Bypass': '🛡️',
            'Cross-Site Scripting': '⚡', 'Server-Side Request Forgery': '🌐', 'Path Traversal': '📂',
            'Insecure Direct Object Reference': '🎯', 'Security Misconfiguration': '⚙️',
            'Sensitive Data Exposure': '📋', 'Rate Limiting': '⏱️', 'CORS Misconfiguration': '🔗',
            'Security Headers': '🏷️', 'File Upload': '📤', 'Insecure Deserialization': '📦',
            'Endpoint Enumeration': '🔍'
        };
        return icons[category] || '🔒';
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
            const response = await fetch(apiUrl('analyze-repo'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: cleanedUrl, model_type: modelType }),
            });
            const data = await response.json();
            if (data.error) {
                setError(data.error);
                setAnalysisLogs(prev => [...prev, `[ERROR] Analysis failed: ${data.error}`]);
            } else {
                console.log('Analysis result received:', data);
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
        const repoInfo = data.repository_info || {};
        
        // Debug log to check what data we're receiving
        console.log('Analysis data received:', data);
        console.log('Repository info:', repoInfo);
        
        // Extract repo name with better logic
        let repoName = 'Unknown Repository';
        
        // First, try to get from repoInfo.name if it's a valid repo name format
        if (repoInfo.name && repoInfo.name !== 'Unknown' && repoInfo.name.includes('/')) {
            repoName = repoInfo.name;
        } else {
            // Try to extract from URLs with better parsing
            let urlToUse = repoInfo.url || data.repository_url || repoUrl;
            if (urlToUse) {
                try {
                    // Clean the URL and extract owner/repo
                    let cleanUrl = urlToUse.replace(/\.git$/, '').replace(/\/$/, '');
                    
                    // Handle different GitHub URL formats
                    if (cleanUrl.includes('github.com/')) {
                        const githubIndex = cleanUrl.indexOf('github.com/');
                        const pathPart = cleanUrl.substring(githubIndex + 11); // 11 = length of 'github.com/'
                        const pathParts = pathPart.split('/');
                        
                        if (pathParts.length >= 2) {
                            repoName = `${pathParts[0]}/${pathParts[1]}`;
                        }
                    }
                } catch (e) {
                    console.warn('Failed to parse repository URL:', e);
                }
            }
        }
        
        return `**🔍 Repository Analysis Complete**

**📊 Repository Overview:**
- **Name:** ${repoName}
- **Language:** ${repoInfo.language && repoInfo.language !== 'Unknown' ? repoInfo.language : 'N/A'}
- **Stars:** ${repoInfo.stars || 0} ⭐
- **Forks:** ${repoInfo.forks || 0} 🍴
- **Open Issues:** ${repoInfo.open_issues || 0} 📋

**🛡️ Security Assessment:**
- **Security Score:** ${score}/100 (${level})
- **Files Scanned:** ${summary.total_files_scanned || 0}
- **Sensitive Files:** ${summary.sensitive_files_found || 0}
- **Risky Files:** ${summary.risky_files_found || 0}
- **Security Files Present:** ${summary.security_files_present || 0}

**🚨 Issues Detected:**
- **Secrets Found:** ${summary.secrets_found || 0}
- **Static Analysis Issues:** ${summary.static_issues_found || 0}
- **Vulnerable Dependencies:** ${summary.vulnerable_dependencies || 0}
- **Code Quality Issues:** ${summary.code_quality_issues || 0}

I'm ready to answer specific questions about these findings, provide detailed explanations, or help you fix any issues detected!`;
    };
    
   const askAI = async () => {
    if (!currentQuestion.trim() || !analysisResult) return;
    
    // Check rate limits before making request
    if (rateLimitStatus && !rateLimitStatus.can_make_request) {
        setChatMessages(prev => [...prev, { 
            type: 'ai', 
            message: `⏱️ **Rate Limit:** ${rateLimitStatus.message}\n\nPlease wait a moment before asking another question.` 
        }]);
        return;
    }
    
    setIsAskingAI(true);
    const userMessage = { type: 'user', message: currentQuestion };
    setChatMessages(prev => [...prev, userMessage]);
    const questionToAsk = currentQuestion;
    setCurrentQuestion('');
    try {
        // Format chat history properly - ensure all parts are strings
        const formattedHistory = [...chatMessages, userMessage].map(msg => {
            let messageContent = '';
            if (typeof msg.message === 'string') {
                messageContent = msg.message;
            } else if (typeof msg.message === 'object') {
                messageContent = JSON.stringify(msg.message);
            } else {
                messageContent = String(msg.message);
            }
            
            return {
                type: msg.type === 'ai' ? 'assistant' : 'user',
                parts: [messageContent] // Ensure this is always a string
            };
        });
        
        const response = await fetch(apiUrl('ai-chat'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: questionToAsk,
                context: 'repo_analysis',
                history: formattedHistory
            }),
        });
        
        const data = await response.json();
        
        // Handle the response properly
        let aiResponse = '';
        if (data.response) {
            aiResponse = data.response;
        } else if (data.error) {
            aiResponse = `Error: ${data.error}`;
        } else {
            aiResponse = 'Sorry, I could not process your question.';
        }
        
        setChatMessages(prev => [...prev, { type: 'ai', message: aiResponse }]);
        
        // Update rate limit status after successful request
        checkRateLimitStatus();
        
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
                // Add more context for better fix generation
                vulnerable_code: issue.code || issue.vulnerable_code || issue.pattern || null,
                rule_id: issue.rule_id || issue.cwe || null,
                advisory: issue.advisory || null,
                package: issue.package || null,
                version: issue.version || null,
                // Include full issue object for additional context
                context: {
                    full_issue: issue,
                    issue_type: issueType,
                    repo_url: repoUrl.trim()
                }
            };
            const response = await fetch(apiUrl('propose-fix'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl.trim(), issue: issueData, branch_name: "main" }),
            });
            const data = await response.json();
            if (response.ok && data.success) {
                setFixedIssues(prev => new Set(prev).add(issueId));
                
                // Store fix details with diff information
                setFixDetails(prev => ({
                    ...prev,
                    [issueId]: {
                        ...data,
                        timestamp: new Date().toISOString()
                    }
                }));
                
                let successMessage = `**Issue Fixed Successfully!**\n\n- **Issue:** ${issueData.description}\n- **File:** ${issueData.file || 'Multiple files'}`;
                
                // Add diff statistics to the message
                if (data.code_comparison?.diff_statistics) {
                    const stats = data.code_comparison.diff_statistics;
                    successMessage += `\n- **Changes:** `;
                    if (stats.lines_added > 0) successMessage += `+${stats.lines_added} `;
                    if (stats.lines_removed > 0) successMessage += `-${stats.lines_removed} `;
                    if (stats.lines_modified > 0) successMessage += `~${stats.lines_modified} `;
                    successMessage += `lines`;
                }
                
                if (data.pull_request?.url) {
                    successMessage += `\n- **Action:** Pull Request created at [${data.pull_request.url}](${data.pull_request.url})`;
                }
                
                successMessage += `\n\n*Click "View Diff" next to the fixed issue to see the exact changes made.*`;
                
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

    const renderFixedIssueWithDiff = (issue, type, index) => {
        const issueId = `${type}-${index}`;
        const fixData = fixDetails[issueId];
        
        if (!isIssueFixed(type, index) || !fixData) return null;
        
        const details = {
            filePath: issue.file || issue.filename || 'N/A',
            severity: issue.severity || 'Medium',
            description: issue.description || issue.pattern || issue.rule_id || 'N/A',
            line: issue.line || issue.line_number || '-',
        };
        
        return (
            <div key={`fixed-${issueId}`} className="fixed-issue-container">
                <div className="fixed-issue-header">
                    <span className="fixed-badge">✅ Fixed</span>
                    <span className="fixed-issue-title">{details.description}</span>
                    <span className="fixed-issue-file">{details.filePath}</span>
                    {fixData.pull_request?.url && (
                        <a href={fixData.pull_request.url} target="_blank" rel="noopener noreferrer" className="pr-link">
                            View PR #{fixData.pull_request.number}
                        </a>
                    )}
                </div>
                
                {fixData.code_comparison && (
                    <DiffViewer
                        original={fixData.code_comparison.original_content}
                        fixed={fixData.code_comparison.fixed_content}
                        filename={details.filePath}
                        diffStats={fixData.code_comparison.diff_statistics}
                        unifiedDiff={fixData.code_comparison.diff_statistics?.unified_diff}
                    />
                )}
                
                {fixData.fix_details && (
                    <div className="fix-summary">
                        <h4>Fix Summary</h4>
                        <p>{fixData.fix_details.fix_summary}</p>
                        {fixData.fix_details.changes_made && fixData.fix_details.changes_made.length > 0 && (
                            <div className="changes-made">
                                <h5>Changes Made:</h5>
                                <ul>
                                    {fixData.fix_details.changes_made.map((change, idx) => (
                                        <li key={idx}>{change}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}
            </div>
        );
    };

    // Function to toggle diff visibility
    const toggleDiffView = (issueType, index) => {
        const issueId = `${issueType}-${index}`;
        setExpandedDiffs(prev => ({
            ...prev,
            [issueId]: !prev[issueId]
        }));
    };

    // Function to check rate limit status
    const checkRateLimitStatus = async () => {
        try {
            const response = await fetch(apiUrl('api/rate-limit-status'));
            const data = await response.json();
            setRateLimitStatus(data);
        } catch (error) {
            console.warn('Could not fetch rate limit status:', error);
        }
    };

    // Check rate limits periodically
    useEffect(() => {
        checkRateLimitStatus();
        const interval = setInterval(checkRateLimitStatus, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
    }, []);

    return (
        <PageWrapper>
            <RateLimitIndicator rateLimitStatus={rateLimitStatus} />
            <style>{`
                /* Enhanced styles with sidebar layout */
                :root {
                    --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                    --input-bg: rgba(0,0,0,0.2);
                }
                .repo-analysis-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                .layout-container { max-width: 1600px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                
                /* Sidebar Layout */
                .report-layout { display: grid; grid-template-columns: 1fr 450px; gap: 2rem; margin-top: 2rem; }
                .report-sidebar { position: sticky; top: 2rem; height: calc(100vh - 4rem); }
                @media (max-width: 1200px) { 
                    .report-layout { grid-template-columns: 1fr; } 
                    .report-sidebar { position: static; height: auto; } 
                }

                /* Diff Viewer Styles */
                .fixed-issue-container {
                    background: var(--card-bg);
                    border: 1px solid var(--card-border);
                    border-radius: 8px;
                    margin: 1rem 0;
                    padding: 1rem;
                }
                
                .fixed-issue-header {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    margin-bottom: 1rem;
                    flex-wrap: wrap;
                }
                
                .fixed-badge {
                    background: #22c55e;
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.875rem;
                    font-weight: 600;
                }
                
                .fixed-issue-title {
                    font-weight: 600;
                    color: var(--text-primary);
                }
                
                .fixed-issue-file {
                    color: var(--text-secondary);
                    font-family: monospace;
                    font-size: 0.875rem;
                }
                
                .pr-link {
                    background: #3b82f6;
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    text-decoration: none;
                    font-size: 0.875rem;
                    margin-left: auto;
                }
                
                .pr-link:hover {
                    background: #2563eb;
                }
                
                .diff-viewer {
                    border: 1px solid var(--card-border);
                    border-radius: 6px;
                    margin: 1rem 0;
                    overflow: hidden;
                }
                
                .diff-header {
                    background: rgba(255, 255, 255, 0.05);
                    padding: 0.75rem 1rem;
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    user-select: none;
                }
                
                .diff-header:hover {
                    background: rgba(255, 255, 255, 0.08);
                }
                
                .diff-title {
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                
                .diff-filename {
                    font-family: monospace;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                
                .diff-stats {
                    display: flex;
                    gap: 0.5rem;
                    font-size: 0.875rem;
                }
                
                .stat-added {
                    color: #22c55e;
                    font-weight: 600;
                }
                
                .stat-removed {
                    color: #ef4444;
                    font-weight: 600;
                }
                
                .stat-modified {
                    color: #f59e0b;
                    font-weight: 600;
                }
                
                .diff-toggle {
                    background: none;
                    border: none;
                    color: var(--text-primary);
                    font-size: 1.25rem;
                    cursor: pointer;
                    padding: 0.25rem;
                    border-radius: 4px;
                }
                
                .diff-toggle:hover {
                    background: rgba(255, 255, 255, 0.1);
                }
                
                .diff-content {
                    border-top: 1px solid var(--card-border);
                }
                
                .diff-controls {
                    background: rgba(255, 255, 255, 0.02);
                    padding: 0.5rem 1rem;
                    display: flex;
                    gap: 0.5rem;
                    border-bottom: 1px solid var(--card-border);
                }
                
                .control-btn {
                    background: none;
                    border: 1px solid var(--card-border);
                    color: var(--text-secondary);
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.875rem;
                }
                
                .control-btn:hover {
                    border-color: var(--card-border-hover);
                    color: var(--text-primary);
                }
                
                .control-btn.active {
                    background: #3b82f6;
                    border-color: #3b82f6;
                    color: white;
                }
                
                .diff-display {
                    max-height: 400px;
                    overflow-y: auto;
                }
                
                .unified-diff {
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 0.875rem;
                    line-height: 1.4;
                }
                
                .diff-line {
                    padding: 0.125rem 1rem;
                    white-space: pre-wrap;
                    word-break: break-all;
                }
                
                .diff-line code {
                    background: none;
                    padding: 0;
                    font-family: inherit;
                }
                
                .diff-file-header {
                    background: rgba(255, 255, 255, 0.05);
                    color: var(--text-secondary);
                    font-weight: 600;
                }
                
                .diff-hunk-header {
                    background: rgba(59, 130, 246, 0.1);
                    color: #60a5fa;
                }
                
                .diff-addition {
                    background: rgba(34, 197, 94, 0.1);
                    color: #4ade80;
                }
                
                .diff-deletion {
                    background: rgba(239, 68, 68, 0.1);
                    color: #f87171;
                }
                
                .diff-context {
                    color: var(--text-primary);
                }
                
                .split-diff {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    height: 400px;
                }
                
                .split-diff-pane {
                    border-right: 1px solid var(--card-border);
                }
                
                .split-diff-pane:last-child {
                    border-right: none;
                }
                
                .pane-header {
                    background: rgba(255, 255, 255, 0.05);
                    padding: 0.5rem 1rem;
                    font-weight: 600;
                    border-bottom: 1px solid var(--card-border);
                }
                
                .pane-content {
                    height: calc(400px - 3rem);
                    overflow-y: auto;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 0.875rem;
                    line-height: 1.4;
                }
                
                .pane-content .diff-line {
                    display: flex;
                    align-items: flex-start;
                    padding: 0.125rem 0;
                }
                
                .line-number {
                    display: inline-block;
                    width: 3rem;
                    padding: 0 0.5rem;
                    color: var(--text-secondary);
                    background: rgba(255, 255, 255, 0.02);
                    text-align: right;
                    user-select: none;
                    border-right: 1px solid var(--card-border);
                    margin-right: 0.5rem;
                }
                
                .fix-summary {
                    margin-top: 1rem;
                    padding: 1rem;
                    background: rgba(255, 255, 255, 0.02);
                    border-radius: 6px;
                    border: 1px solid var(--card-border);
                }
                
                .fix-summary h4 {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-primary);
                    font-size: 1rem;
                }
                
                .fix-summary h5 {
                    margin: 1rem 0 0.5rem 0;
                    color: var(--text-primary);
                    font-size: 0.875rem;
                }
                
                .fix-summary p {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-secondary);
                    line-height: 1.5;
                }
                
                .changes-made ul {
                    margin: 0;
                    padding-left: 1.5rem;
                }
                
                .changes-made li {
                    color: var(--text-secondary);
                    margin-bottom: 0.25rem;
                    line-height: 1.4;
                }
                
                .no-changes {
                    color: var(--text-secondary);
                    font-style: italic;
                }
                
                /* Fixed Issues Section */
                .fixed-issues-section {
                    margin: 2rem 0;
                    padding: 1.5rem;
                    background: var(--card-bg);
                    border: 1px solid var(--card-border);
                    border-radius: 8px;
                }
                
                .fixed-issues-section h3 {
                    margin: 0 0 1.5rem 0;
                    color: var(--text-primary);
                    font-size: 1.25rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                
                /* Inline diff styles */
                .fixed-actions {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    flex-wrap: wrap;
                }
                
                .btn-view-diff {
                    background: #3b82f6;
                    color: white;
                    border: none;
                    padding: 0.25rem 0.75rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 0.875rem;
                    transition: background-color 0.2s;
                }
                
                .btn-view-diff:hover {
                    background: #2563eb;
                }
                
                .diff-row {
                    background: rgba(255, 255, 255, 0.02);
                }
                
                .diff-cell {
                    padding: 0 !important;
                    border-top: 1px solid var(--card-border);
                }
                
                .inline-diff-container {
                    padding: 1rem;
                    background: var(--card-bg);
                    border-radius: 0 0 6px 6px;
                }
                
                .fix-summary-inline {
                    margin-bottom: 1rem;
                    padding: 1rem;
                    background: rgba(255, 255, 255, 0.03);
                    border-radius: 6px;
                    border: 1px solid var(--card-border);
                }
                
                .fix-summary-inline h4 {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-primary);
                    font-size: 1rem;
                }
                
                .fix-summary-inline p {
                    margin: 0 0 0.5rem 0;
                    color: var(--text-secondary);
                    line-height: 1.5;
                }
                
                .pr-link-inline {
                    color: #3b82f6;
                    text-decoration: none;
                    font-weight: 500;
                }
                
                .pr-link-inline:hover {
                    color: #2563eb;
                    text-decoration: underline;
                }
                
                /* Rate Limit Indicator */
                .rate-limit-indicator {
                    position: fixed;
                    top: 1rem;
                    right: 1rem;
                    background: var(--card-bg);
                    border: 1px solid var(--card-border);
                    border-radius: 8px;
                    padding: 0.75rem;
                    z-index: 1000;
                    min-width: 120px;
                    backdrop-filter: blur(10px);
                }
                
                .rate-limit-status {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-weight: 600;
                    font-size: 0.875rem;
                }
                
                .status-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    flex-shrink: 0;
                }
                
                .rate-limit-details {
                    margin-top: 0.25rem;
                    color: var(--text-secondary);
                    font-size: 0.75rem;
                }
                
                .rate-limit-details small {
                    display: block;
                    line-height: 1.2;
                }
                
                .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }
                .card { width: 100%; box-sizing: border-box; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.3s ease; }
                .card:hover { border-color: var(--card-border-hover); box-shadow: 0 0 25px rgba(255, 255, 255, 0.08); }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 1.5rem 0; text-transform: uppercase; letter-spacing: 1px; }
                .input-group { display: flex; gap: 1rem; }
                .input { flex-grow: 1; background: var(--input-bg); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; transition: border-color 0.3s; }
                .input:focus { border-color: var(--text-primary); outline: none; }
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
                /* Enhanced Issues Table */
                .issues-summary { margin-bottom: 2rem; }
                .summary-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem; }
                .summary-stat { text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.02); border-radius: 0.5rem; border: 1px solid var(--card-border); }
                .summary-stat.critical { border-color: rgba(220, 53, 69, 0.3); background: rgba(220, 53, 69, 0.02); }
                .summary-stat.high { border-color: rgba(255, 99, 71, 0.3); background: rgba(255, 99, 71, 0.02); }
                .summary-stat.medium { border-color: rgba(255, 193, 7, 0.3); background: rgba(255, 193, 7, 0.02); }
                
                .issues-table-container { overflow-x: auto; }
                .issues-table { width: 100%; border-collapse: collapse; }
                .issues-table th, .issues-table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--card-border); }
                .issues-table th { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; font-weight: 500; background: rgba(255, 255, 255, 0.02); }
                .issues-table tr:last-child td { border-bottom: none; }
                .issues-table tr:hover { background: rgba(255, 255, 255, 0.01); }
                .issues-table tr.issue-fixed { opacity: 0.6; background: rgba(40, 167, 69, 0.05); }
                
                .issue-type { padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
                .issue-type.secret { background: rgba(220, 53, 69, 0.2); color: #dc3545; }
                .issue-type.static { background: rgba(255, 99, 71, 0.2); color: #ff6347; }
                .issue-type.dependency { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
                .issue-type.quality { background: rgba(52, 144, 220, 0.2); color: #3490dc; }
                
                .file-path { font-family: 'Courier New', monospace; font-size: 0.9rem; color: var(--text-primary); word-break: break-all; }
                .issue-description { color: var(--text-secondary); line-height: 1.4; max-width: 300px; }
                
                .fixed-badge { background: rgba(40, 167, 69, 0.2); color: #28a745; padding: 0.25rem 0.5rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 600; }
                
                .no-issues-message { text-align: center; padding: 3rem 2rem; background: rgba(40, 167, 69, 0.05); border: 1px solid rgba(40, 167, 69, 0.2); border-radius: 0.75rem; margin-top: 2rem; }
                .no-issues-icon { font-size: 3rem; margin-bottom: 1rem; }
                .no-issues-text h4 { color: var(--text-primary); margin: 0 0 0.5rem 0; font-size: 1.2rem; }
                .no-issues-text p { color: var(--text-secondary); margin: 0; }
                
                .header-actions { display: flex; gap: 1rem; align-items: center; }
                
                /* AI Chat Sidebar Styles */
                .ai-chat-container { height: 100%; display: flex; flex-direction: column; }
                .ai-chat-history { flex-grow: 1; overflow-y: auto; padding-right: 1rem; margin-bottom: 1.5rem; max-height: calc(100vh - 12rem); }
                .chat-message { max-width: 90%; margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5; word-wrap: break-word; }
                .ai-message { background: rgba(255, 255, 255, 0.1); border-bottom-left-radius: 0; }
                .user-message { background: var(--card-bg); border: 1px solid var(--card-border); border-bottom-right-radius: 0; margin-left: auto; }
                .ai-chat-input-area { display: flex; gap: 0.75rem; align-items: center; margin-top: auto; }
                .info-text { color: var(--text-secondary); text-align: center; padding: 2rem 0; }
                .formatted-content code { background: rgba(255, 255, 255, 0.1); padding: 0.1em 0.3em; border-radius: 4px; }
                .formatted-content ul { padding-left: 1.25rem; margin: 0.5rem 0; }
                .formatted-content p { margin: 0 0 0.5rem 0; } .formatted-content p:last-child { margin-bottom: 0; }
                
                /* Security Stats Grid */
                .security-stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
                .stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem 1rem; text-align: center; transition: all 0.3s ease; }
                .stat-card:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.05); }
                .stat-number { font-size: 2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem; }
                .stat-label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
                
                /* Scoring Breakdown */
                .scoring-breakdown { display: flex; flex-direction: column; gap: 1.5rem; }
                .score-category { background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; }
                .category-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
                .category-name { color: var(--text-primary); font-weight: 600; text-transform: capitalize; }
                .category-score { color: var(--text-primary); font-weight: 700; font-size: 1.1rem; }
                .category-progress { background: rgba(255, 255, 255, 0.1); border-radius: 1rem; height: 8px; overflow: hidden; margin-bottom: 0.5rem; }
                .progress-bar { background: linear-gradient(90deg, #ff6b6b 0%, #ffd93d 50%, #6bcf7f 100%); height: 100%; border-radius: 1rem; transition: width 1s ease-out; }
                .category-details { color: var(--text-secondary); font-size: 0.9rem; }
                
                /* Enhanced Security Scan Results */
                .security-scan-container { display: flex; flex-direction: column; gap: 2rem; }
                .security-scan-section { border: 2px solid var(--card-border); border-radius: 0.75rem; padding: 1.5rem; background: rgba(255, 255, 255, 0.01); transition: all 0.3s ease; }
                .security-scan-section:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.02); }
                .security-scan-section.danger { border-color: rgba(220, 53, 69, 0.3); background: rgba(220, 53, 69, 0.02); }
                .security-scan-section.warning { border-color: rgba(255, 193, 7, 0.3); background: rgba(255, 193, 7, 0.02); }
                .security-scan-section.success { border-color: rgba(40, 167, 69, 0.3); background: rgba(40, 167, 69, 0.02); }
                .security-scan-section.missing { border-color: rgba(108, 117, 125, 0.3); background: rgba(108, 117, 125, 0.02); }
                
                .scan-section-header { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1.5rem; }
                .section-icon { font-size: 1.5rem; line-height: 1; }
                .section-title h4 { color: var(--text-primary); margin: 0 0 0.25rem 0; font-size: 1.1rem; font-weight: 600; }
                .section-subtitle { color: var(--text-secondary); margin: 0; font-size: 0.9rem; }
                
                .files-container { display: flex; flex-direction: column; gap: 0.75rem; }
                .file-card { display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; transition: all 0.2s ease; }
                .file-card:hover { background: rgba(255, 255, 255, 0.04); border-color: var(--card-border-hover); }
                .file-card.sensitive { border-left: 3px solid #dc3545; }
                .file-card.risky { border-left: 3px solid #ffc107; }
                
                .file-icon { font-size: 1.2rem; color: var(--text-secondary); }
                .file-details { flex-grow: 1; min-width: 0; }
                .file-details .file-path { color: var(--text-primary); font-family: 'Courier New', monospace; font-size: 0.9rem; word-break: break-all; }
                .file-details .file-reason { color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem; }
                
                .file-badge { padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
                .sensitive-badge { background: rgba(220, 53, 69, 0.2); color: #dc3545; border: 1px solid rgba(220, 53, 69, 0.3); }
                .risky-badge { background: rgba(255, 193, 7, 0.2); color: #ffc107; border: 1px solid rgba(255, 193, 7, 0.3); }
                
                .more-files-indicator { text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--card-border); border-radius: 0.5rem; }
                .more-count { color: var(--text-secondary); font-style: italic; font-size: 0.9rem; }
                
                .security-files-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
                .simple-files-list { display: flex; flex-direction: column; gap: 0.5rem; }
                .simple-file-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; }
                .simple-file-item.present .file-check { color: #28a745; font-weight: bold; }
                .simple-file-item.missing .file-check { color: #dc3545; font-weight: bold; }
                .simple-file-item .file-name { color: var(--text-primary); font-family: 'Courier New', monospace; font-size: 0.9rem; }
                
                /* Enhanced AI Analysis */
                .ai-analysis-container { }
                .analysis-header { margin-bottom: 1.5rem; }
                .analysis-model-info { display: flex; align-items: center; gap: 1rem; }
                .model-badge { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 1rem; border-radius: 1rem; font-size: 0.9rem; font-weight: 600; }
                
                .ai-analysis-content { background: rgba(255, 255, 255, 0.01); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 0; overflow: hidden; }
                
                /* Enhanced markdown formatting for AI analysis */
                .ai-analysis-content .formatted-content { padding: 2rem; }
                .ai-analysis-content .formatted-content h1 { color: var(--text-primary); font-size: 1.8rem; font-weight: 700; margin: 0 0 1.5rem 0; padding-bottom: 1rem; border-bottom: 2px solid var(--card-border); }
                .ai-analysis-content .formatted-content h2 { color: var(--text-primary); font-size: 1.4rem; font-weight: 600; margin: 2rem 0 1rem 0; padding: 1rem; background: rgba(255, 255, 255, 0.03); border-left: 4px solid #667eea; border-radius: 0.5rem; }
                .ai-analysis-content .formatted-content h3 { color: var(--text-primary); font-size: 1.2rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0; }
                .ai-analysis-content .formatted-content h4 { color: var(--text-primary); font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem 0; }
                
                .ai-analysis-content .formatted-content p { color: var(--text-secondary); line-height: 1.7; margin: 0 0 1rem 0; }
                .ai-analysis-content .formatted-content p:last-child { margin-bottom: 0; }
                
                .ai-analysis-content .formatted-content ul, .ai-analysis-content .formatted-content ol { color: var(--text-secondary); line-height: 1.6; margin: 0.5rem 0 1rem 0; padding-left: 1.5rem; }
                .ai-analysis-content .formatted-content li { margin-bottom: 0.5rem; }
                .ai-analysis-content .formatted-content li:last-child { margin-bottom: 0; }
                
                .ai-analysis-content .formatted-content blockquote { background: rgba(255, 255, 255, 0.02); border-left: 4px solid var(--card-border); padding: 1rem 1.5rem; margin: 1rem 0; border-radius: 0.5rem; color: var(--text-secondary); font-style: italic; }
                
                .ai-analysis-content .formatted-content code { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); padding: 0.2em 0.4em; border-radius: 0.25rem; font-family: 'Courier New', monospace; font-size: 0.9em; }
                
                .ai-analysis-content .formatted-content pre { background: rgba(0, 0, 0, 0.3); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0; overflow-x: auto; }
                .ai-analysis-content .formatted-content pre code { background: none; padding: 0; color: var(--text-primary); font-size: 0.85rem; }
                
                .ai-analysis-content .formatted-content strong { color: var(--text-primary); font-weight: 600; }
                .ai-analysis-content .formatted-content em { color: var(--text-primary); font-style: italic; }
                
                .ai-analysis-content .formatted-content table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: rgba(255, 255, 255, 0.02); border-radius: 0.5rem; overflow: hidden; }
                .ai-analysis-content .formatted-content th, .ai-analysis-content .formatted-content td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--card-border); }
                .ai-analysis-content .formatted-content th { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); font-weight: 600; font-size: 0.9rem; }
                .ai-analysis-content .formatted-content td { color: var(--text-secondary); }
                .ai-analysis-content .formatted-content tr:last-child td { border-bottom: none; }
                
                .ai-analysis-content .formatted-content a { color: #667eea; text-decoration: none; border-bottom: 1px solid transparent; transition: all 0.2s ease; }
                .ai-analysis-content .formatted-content a:hover { border-bottom-color: #667eea; }
                
                /* Enhanced markdown content spacing and readability */
                .ai-analysis-content .formatted-content { line-height: 1.6; }
                .ai-analysis-content .formatted-content > *:first-child { margin-top: 0; }
                .ai-analysis-content .formatted-content > *:last-child { margin-bottom: 0; }
                
                /* Section dividers */
                .ai-analysis-content .formatted-content hr { border: none; height: 2px; background: linear-gradient(90deg, transparent, var(--card-border), transparent); margin: 2rem 0; }
                
                /* Enhanced list styling */
                .ai-analysis-content .formatted-content ul ul, .ai-analysis-content .formatted-content ol ul { margin-top: 0.5rem; margin-bottom: 0.5rem; }
                .ai-analysis-content .formatted-content li > p { margin: 0.25rem 0; }
                
                /* Step-by-step instructions */
                .ai-analysis-content .formatted-content ol li { background: rgba(255, 255, 255, 0.01); margin-bottom: 0.75rem; padding: 0.75rem; border-radius: 0.5rem; border-left: 3px solid var(--card-border); }
                .ai-analysis-content .formatted-content ol li:hover { background: rgba(255, 255, 255, 0.02); border-left-color: var(--card-border-hover); }
                
                /* Enhanced readability for long content */
                .ai-analysis-content { max-height: 80vh; overflow-y: auto; }
                .ai-analysis-content::-webkit-scrollbar { width: 8px; }
                .ai-analysis-content::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
                .ai-analysis-content::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
                .ai-analysis-content::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
                
                .ai-analysis-content { background: rgba(255, 255, 255, 0.01); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 0; overflow: hidden; }
                
                /* Enhanced markdown formatting for AI analysis */
                .ai-analysis-content .formatted-content { padding: 2rem; }
                .ai-analysis-content .formatted-content h1 { color: var(--text-primary); font-size: 1.8rem; font-weight: 700; margin: 0 0 1.5rem 0; padding-bottom: 1rem; border-bottom: 2px solid var(--card-border); }
                .ai-analysis-content .formatted-content h2 { color: var(--text-primary); font-size: 1.4rem; font-weight: 600; margin: 2rem 0 1rem 0; padding: 1rem; background: rgba(255, 255, 255, 0.03); border-left: 4px solid #667eea; border-radius: 0.5rem; }
                .ai-analysis-content .formatted-content h3 { color: var(--text-primary); font-size: 1.2rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0; }
                .ai-analysis-content .formatted-content h4 { color: var(--text-primary); font-size: 1rem; font-weight: 600; margin: 1rem 0 0.5rem 0; }
                
                .ai-analysis-content .formatted-content p { color: var(--text-secondary); line-height: 1.7; margin: 0 0 1rem 0; }
                .ai-analysis-content .formatted-content p:last-child { margin-bottom: 0; }
                
                .ai-analysis-content .formatted-content ul, .ai-analysis-content .formatted-content ol { color: var(--text-secondary); line-height: 1.6; margin: 0.5rem 0 1rem 0; padding-left: 1.5rem; }
                .ai-analysis-content .formatted-content li { margin-bottom: 0.5rem; }
                .ai-analysis-content .formatted-content li:last-child { margin-bottom: 0; }
                
                .ai-analysis-content .formatted-content blockquote { background: rgba(255, 255, 255, 0.02); border-left: 4px solid var(--card-border); padding: 1rem 1.5rem; margin: 1rem 0; border-radius: 0.5rem; color: var(--text-secondary); font-style: italic; }
                
                .ai-analysis-content .formatted-content code { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); padding: 0.2em 0.4em; border-radius: 0.25rem; font-family: 'Courier New', monospace; font-size: 0.9em; }
                
                .ai-analysis-content .formatted-content pre { background: rgba(0, 0, 0, 0.3); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; margin: 1rem 0; overflow-x: auto; }
                .ai-analysis-content .formatted-content pre code { background: none; padding: 0; color: var(--text-primary); font-size: 0.85rem; }
                
                .ai-analysis-content .formatted-content strong { color: var(--text-primary); font-weight: 600; }
                .ai-analysis-content .formatted-content em { color: var(--text-primary); font-style: italic; }
                
                .ai-analysis-content .formatted-content table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: rgba(255, 255, 255, 0.02); border-radius: 0.5rem; overflow: hidden; }
                .ai-analysis-content .formatted-content th, .ai-analysis-content .formatted-content td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--card-border); }
                .ai-analysis-content .formatted-content th { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); font-weight: 600; font-size: 0.9rem; }
                .ai-analysis-content .formatted-content td { color: var(--text-secondary); }
                .ai-analysis-content .formatted-content tr:last-child td { border-bottom: none; }
                
                .ai-analysis-content .formatted-content a { color: #667eea; text-decoration: none; border-bottom: 1px solid transparent; transition: all 0.2s ease; }
                .ai-analysis-content .formatted-content a:hover { border-bottom-color: #667eea; }
                
                /* Special styling for security analysis sections */
                .ai-analysis-content .formatted-content h2:contains("Executive"), .ai-analysis-content .formatted-content h2:contains("Summary") { background: linear-gradient(135deg, rgba(220, 53, 69, 0.1) 0%, rgba(220, 53, 69, 0.05) 100%); border-left-color: #dc3545; }
                .ai-analysis-content .formatted-content h2:contains("Critical"), .ai-analysis-content .formatted-content h2:contains("Vulnerabilities") { background: linear-gradient(135deg, rgba(255, 99, 71, 0.1) 0%, rgba(255, 99, 71, 0.05) 100%); border-left-color: #ff6347; }
                .ai-analysis-content .formatted-content h2:contains("Technical"), .ai-analysis-content .formatted-content h2:contains("Risk") { background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%); border-left-color: #ffc107; }
                .ai-analysis-content .formatted-content h2:contains("Remediation"), .ai-analysis-content .formatted-content h2:contains("Roadmap") { background: linear-gradient(135deg, rgba(40, 167, 69, 0.1) 0%, rgba(40, 167, 69, 0.05) 100%); border-left-color: #28a745; }
                .ai-analysis-content .formatted-content h2:contains("Advanced"), .ai-analysis-content .formatted-content h2:contains("Recommendations") { background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(102, 126, 234, 0.05) 100%); border-left-color: #667eea; }
                
                /* Risk rating and CVSS styling */
                .ai-analysis-content .formatted-content p:contains("Risk Rating"), .ai-analysis-content .formatted-content p:contains("CVSS") { background: rgba(220, 53, 69, 0.05); border: 1px solid rgba(220, 53, 69, 0.2); border-radius: 0.5rem; padding: 1rem; margin: 1rem 0; font-weight: 600; }
                
                /* Action items and implementation blocks */
                .ai-analysis-content .formatted-content li:contains("Action:"), .ai-analysis-content .formatted-content li:contains("Implementation:") { background: rgba(255, 255, 255, 0.02); border-radius: 0.25rem; padding: 0.5rem; margin: 0.5rem 0; }
                
                /* Time-bound sections */
                .ai-analysis-content .formatted-content h3:contains("Immediate"), .ai-analysis-content .formatted-content h3:contains("0 - 24") { color: #dc3545; }
                .ai-analysis-content .formatted-content h3:contains("Short-Term"), .ai-analysis-content .formatted-content h3:contains("1 - 4") { color: #ffc107; }
                .ai-analysis-content .formatted-content h3:contains("Long-Term"), .ai-analysis-content .formatted-content h3:contains("1 - 6") { color: #28a745; }
                
                /* Enhanced Code Quality Analysis */
                .quality-summary-header { margin-bottom: 2rem; padding: 1.5rem; background: rgba(255, 255, 255, 0.02); border-radius: 0.75rem; border: 1px solid var(--card-border); }
                .quality-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1.5rem; }
                .quality-stat { text-align: center; }
                .quality-stat .stat-number { display: block; font-size: 2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.5rem; }
                .quality-stat .stat-label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }
                
                .quality-issues-container { display: flex; flex-direction: column; gap: 1.5rem; }
                .severity-group { border: 2px solid var(--card-border); border-radius: 0.75rem; padding: 1.5rem; background: rgba(255, 255, 255, 0.01); }
                .severity-group.severity-critical { border-color: rgba(220, 53, 69, 0.4); background: rgba(220, 53, 69, 0.03); }
                .severity-group.severity-high { border-color: rgba(255, 99, 71, 0.4); background: rgba(255, 99, 71, 0.03); }
                .severity-group.severity-medium { border-color: rgba(255, 193, 7, 0.4); background: rgba(255, 193, 7, 0.03); }
                .severity-group.severity-low { border-color: rgba(52, 144, 220, 0.4); background: rgba(52, 144, 220, 0.03); }
                
                .severity-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
                .severity-title { display: flex; align-items: center; gap: 0.75rem; margin: 0; color: var(--text-primary); font-size: 1.1rem; font-weight: 600; }
                .severity-icon { font-size: 1.2rem; }
                .severity-count { background: rgba(255, 255, 255, 0.1); color: var(--text-primary); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.9rem; font-weight: 600; }
                
                .quality-issues-list { display: flex; flex-direction: column; gap: 1rem; }
                .quality-issue { background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.25rem; transition: all 0.2s ease; }
                .quality-issue:hover { background: rgba(255, 255, 255, 0.04); border-color: var(--card-border-hover); }
                
                .quality-issue .issue-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; gap: 1rem; }
                .issue-file-info { display: flex; flex-direction: column; gap: 0.25rem; flex-grow: 1; min-width: 0; }
                .quality-issue .issue-file { color: var(--text-primary); font-family: 'Courier New', monospace; font-size: 0.9rem; word-break: break-all; }
                .quality-issue .issue-line { color: var(--text-secondary); font-size: 0.8rem; }
                
                .issue-severity-badge { padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; flex-shrink: 0; }
                .issue-severity-badge.severity-critical { background: rgba(220, 53, 69, 0.2); color: #dc3545; border: 1px solid rgba(220, 53, 69, 0.3); }
                .issue-severity-badge.severity-high { background: rgba(255, 99, 71, 0.2); color: #ff6347; border: 1px solid rgba(255, 99, 71, 0.3); }
                .issue-severity-badge.severity-medium { background: rgba(255, 193, 7, 0.2); color: #ffc107; border: 1px solid rgba(255, 193, 7, 0.3); }
                .issue-severity-badge.severity-low { background: rgba(52, 144, 220, 0.2); color: #3490dc; border: 1px solid rgba(52, 144, 220, 0.3); }
                
                .quality-issue .issue-description { color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5; margin: 0; }
                
                .more-issues { text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--card-border); border-radius: 0.5rem; margin-top: 0.5rem; }
                .more-issues-text { color: var(--text-secondary); font-style: italic; font-size: 0.9rem; }
                
                /* Enhanced Recommendations */
                .recommendations-container { display: flex; flex-direction: column; gap: 1.5rem; }
                .recommendation-card { background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); border-radius: 0.75rem; padding: 1.5rem; transition: all 0.3s ease; }
                .recommendation-card:hover { border-color: var(--card-border-hover); background: rgba(255, 255, 255, 0.03); }
                .recommendation-card.priority-critical { border-color: rgba(220, 53, 69, 0.4); background: rgba(220, 53, 69, 0.02); }
                
                .recommendation-header { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
                .recommendation-priority { flex-shrink: 0; }
                .recommendation-title { color: var(--text-primary); margin: 0; font-size: 1.1rem; font-weight: 600; }
                
                .recommendation-content { }
                .recommendation-description { color: var(--text-secondary); line-height: 1.6; margin: 0 0 1rem 0; }
                .recommendation-action, .recommendation-impact { background: rgba(255, 255, 255, 0.02); border-left: 3px solid var(--card-border); padding: 0.75rem 1rem; margin: 0.75rem 0; border-radius: 0.25rem; font-size: 0.9rem; }
                .recommendation-action { border-left-color: #28a745; }
                .recommendation-impact { border-left-color: #ffc107; }
                
                .recommendation-action ul, .recommendation-impact ul { margin: 0.5rem 0 0 0; padding-left: 1.5rem; }
                .recommendation-action li, .recommendation-impact li { margin-bottom: 0.5rem; color: var(--text-secondary); }
                
                .recommendation-references { margin-top: 1rem; }
                .recommendation-references ul { margin: 0.5rem 0 0 0; padding-left: 1.5rem; }
                .recommendation-references li { margin-bottom: 0.25rem; }
                .recommendation-references a { color: #667eea; text-decoration: none; }
                .recommendation-references a:hover { text-decoration: underline; }
                
                .smart-recommendations { margin-top: 1rem; }
                .recommendations-header { text-align: center; margin-bottom: 2rem; padding: 1.5rem; background: rgba(102, 126, 234, 0.05); border: 1px solid rgba(102, 126, 234, 0.2); border-radius: 0.75rem; }
                .recommendations-header h4 { color: var(--text-primary); margin: 0 0 0.5rem 0; font-size: 1.2rem; }
                .recommendations-header p { color: var(--text-secondary); margin: 0; font-size: 0.9rem; }
                
                .priority-badge { padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
                .priority-critical { background: rgba(139, 0, 0, 0.3); color: #dc143c; border: 1px solid rgba(139, 0, 0, 0.4); }
                .priority-high { background: rgba(220, 53, 69, 0.2); color: #dc3545; border: 1px solid rgba(220, 53, 69, 0.3); }
                .priority-medium { background: rgba(255, 193, 7, 0.2); color: #ffc107; border: 1px solid rgba(255, 193, 7, 0.3); }
                .priority-low { background: rgba(40, 167, 69, 0.2); color: #28a745; border: 1px solid rgba(40, 167, 69, 0.3); }
                
                .severity-badge { padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600; background: rgba(255,255,255,0.1); color: var(--text-secondary); }
                .severity-critical, .severity-high { color: var(--text-primary); background: rgba(255,255,255,0.15); }
                .btn-fix { background: rgba(255,255,255,0.1); color: var(--text-primary); border: 1px solid transparent; padding: 0.4rem 0.8rem; border-radius: 0.5rem; font-size: 0.8rem; cursor: pointer; transition: all 0.2s; }
                .btn-fix:hover:not(:disabled) { background: var(--text-primary); color: var(--bg-black); }
                .card-header-action { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
                .card-header-action h3 { margin: 0; }
                
                /* Warnings and Errors */
                .warnings-section, .errors-section { margin-bottom: 1.5rem; }
                .warnings-section:last-child, .errors-section:last-child { margin-bottom: 0; }
                .warnings-list, .errors-list { list-style: none; margin: 0; padding: 0; }
                .warning-item, .error-item { padding: 0.75rem; margin-bottom: 0.5rem; border-radius: 0.5rem; font-size: 0.9rem; }
                .warning-item { background: rgba(255, 193, 7, 0.1); border-left: 3px solid #ffc107; color: #ffc107; }
                .error-item { background: rgba(220, 53, 69, 0.1); border-left: 3px solid #dc3545; color: #dc3545; }
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
                                <input type="text" value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="Enter public GitHub repository URL" className="input" disabled={isScanning || isPentesting} />
                                <button onClick={analyzeRepository} disabled={isScanning || isPentesting || !repoUrl.trim()} className="btn">{isScanning ? 'Analyzing...' : 'Analyze'}</button>
                                <button onClick={runDeepPentest} disabled={isScanning || isPentesting || !repoUrl.trim()} className="btn" style={{background: 'linear-gradient(135deg, #dc2626, #991b1b)', marginLeft: '8px'}}>{isPentesting ? 'Pentesting...' : '🔒 Deep Pentest'}</button>
                            </div>
                            {error && <p className="error-message">{error}</p>}
                            {pentestError && <p className="error-message">{pentestError}</p>}
                            {isPentesting && (
                                <div style={{marginTop: '12px', padding: '12px', background: 'rgba(220, 38, 38, 0.1)', borderRadius: '8px', border: '1px solid rgba(220, 38, 38, 0.3)'}}>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                                        <div className="spinner" style={{width: '16px', height: '16px', border: '2px solid rgba(220,38,38,0.3)', borderTop: '2px solid #dc2626', borderRadius: '50%', animation: 'spin 1s linear infinite'}}></div>
                                        <span style={{color: '#dc2626', fontSize: '14px', fontWeight: 500}}>Deep Penetration Test Running...</span>
                                    </div>
                                    <p style={{color: '#9ca3af', fontSize: '13px', margin: '8px 0 0'}}>Cloning repo → S3 upload → Sandbox deploy → Endpoint discovery → Running attack payloads (SQL injection, XSS, auth bypass, IDOR, SSRF, command injection...)</p>
                                    {pentestProgress && <p style={{color: '#f59e0b', fontSize: '12px', margin: '6px 0 0'}}>{pentestProgress}</p>}
                                </div>
                            )}
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
                        <div className="report-layout">
                            <main>
                                <div className="card">
                                    <h3>Analysis Overview</h3>
                                    <div className="results-grid">
                                        <SecurityScoreGauge score={analysisResult.overall_security_score} />
                                        <div className="info-list">
                                            <div className="info-item">
                                                <span className="label">Repository</span>
                                                <span className="value">
                                                    {(() => {
                                                        let name = analysisResult.repository_info?.name;
                                                        
                                                        // If name is valid and contains a slash, use it directly
                                                        if (name && name !== 'Unknown' && name.includes('/')) {
                                                            return name;
                                                        }
                                                        
                                                        // Otherwise, try to extract from URL
                                                        let urlToUse = analysisResult.repository_info?.url || repoUrl;
                                                        if (urlToUse) {
                                                            try {
                                                                let cleanUrl = urlToUse.replace(/\.git$/, '').replace(/\/$/, '');
                                                                
                                                                if (cleanUrl.includes('github.com/')) {
                                                                    const githubIndex = cleanUrl.indexOf('github.com/');
                                                                    const pathPart = cleanUrl.substring(githubIndex + 11);
                                                                    const pathParts = pathPart.split('/');
                                                                    
                                                                    if (pathParts.length >= 2) {
                                                                        return `${pathParts[0]}/${pathParts[1]}`;
                                                                    }
                                                                }
                                                            } catch (e) {
                                                                console.warn('Failed to parse URL:', e);
                                                            }
                                                        }
                                                        
                                                        return 'Unknown Repository';
                                                    })()}
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Description</span>
                                                <span className="value">
                                                    {analysisResult.repository_info?.description && 
                                                     analysisResult.repository_info.description !== 'No description' ? 
                                                     analysisResult.repository_info.description : 'No description'}
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Language</span>
                                                <span className="value">
                                                    {analysisResult.repository_info?.language && 
                                                     analysisResult.repository_info.language !== 'Unknown' ? 
                                                     analysisResult.repository_info.language : 'N/A'}
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Stars</span>
                                                <span className="value">
                                                    {analysisResult.repository_info?.stars || 0} ⭐
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Forks</span>
                                                <span className="value">
                                                    {analysisResult.repository_info?.forks || 0} 🍴
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Open Issues</span>
                                                <span className="value">
                                                    {analysisResult.repository_info?.open_issues || 0} 📋
                                                </span>
                                            </div>
                                            <div className="info-item">
                                                <span className="label">Security Level</span>
                                                <span className="value">
                                                    {analysisResult.security_level || 'Unknown'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                {analysisResult.scoring_breakdown && (
                                    <div className="card">
                                        <h3>Security Score Breakdown</h3>
                                        <div className="scoring-breakdown">
                                            {Object.entries(analysisResult.scoring_breakdown).map(([category, details]) => (
                                                <div key={category} className="score-category">
                                                    <div className="category-header">
                                                        <span className="category-name">{category.charAt(0).toUpperCase() + category.slice(1)}</span>
                                                        <span className="category-score">{details.score || 0}/100</span>
                                                    </div>
                                                    <div className="category-progress">
                                                        <div 
                                                            className="progress-bar" 
                                                            style={{width: `${details.score || 0}%`}}
                                                        ></div>
                                                    </div>
                                                    {details.issues_count !== undefined && (
                                                        <div className="category-details">
                                                            {details.issues_count} issues found
                                                            {details.weight && ` (Weight: ${details.weight}x)`}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                
                                <div className="card">
                                    <h3>Security Summary</h3>
                                    <div className="security-stats-grid">
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.total_files_scanned || 0}</div>
                                            <div className="stat-label">Files Scanned</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.sensitive_files_found || 0}</div>
                                            <div className="stat-label">Sensitive Files</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.risky_files_found || 0}</div>
                                            <div className="stat-label">Risky Files</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.secrets_found || 0}</div>
                                            <div className="stat-label">Secrets Found</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.static_issues_found || 0}</div>
                                            <div className="stat-label">Static Issues</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.vulnerable_dependencies || 0}</div>
                                            <div className="stat-label">Vulnerable Dependencies</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.code_quality_issues || 0}</div>
                                            <div className="stat-label">Code Quality Issues</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.security_files_present || 0}</div>
                                            <div className="stat-label">Security Files Present</div>
                                        </div>
                                        <div className="stat-card">
                                            <div className="stat-number">{analysisResult.security_summary?.missing_security_files || 0}</div>
                                            <div className="stat-label">Missing Security Files</div>
                                        </div>
                                    </div>
                                </div>

                                {analysisResult.file_security_scan && (
                                    <div className="card">
                                        <h3>📂 File Security Scan Results</h3>
                                        <div className="security-scan-container">
                                            {analysisResult.file_security_scan.sensitive_files && analysisResult.file_security_scan.sensitive_files.length > 0 && (
                                                <div className="security-scan-section danger">
                                                    <div className="scan-section-header">
                                                        <div className="section-icon">🚨</div>
                                                        <div className="section-title">
                                                            <h4>Sensitive Files Detected</h4>
                                                            <p className="section-subtitle">{analysisResult.file_security_scan.sensitive_files.length} files contain sensitive patterns</p>
                                                        </div>
                                                    </div>
                                                    <div className="files-container">
                                                        {analysisResult.file_security_scan.sensitive_files.slice(0, 15).map((file, index) => (
                                                            <div key={index} className="file-card sensitive">
                                                                <div className="file-icon">📄</div>
                                                                <div className="file-details">
                                                                    <div className="file-path">{safeRenderFilePath(file)}</div>
                                                                    {safeRenderFileReason(file) && (
                                                                        <div className="file-reason">{safeRenderFileReason(file)}</div>
                                                                    )}
                                                                </div>
                                                                <div className="file-badge sensitive-badge">Sensitive</div>
                                                            </div>
                                                        ))}
                                                        {analysisResult.file_security_scan.sensitive_files.length > 15 && (
                                                            <div className="more-files-indicator">
                                                                <span className="more-count">+{analysisResult.file_security_scan.sensitive_files.length - 15} more files</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            {analysisResult.file_security_scan.risky_files && analysisResult.file_security_scan.risky_files.length > 0 && (
                                                <div className="security-scan-section warning">
                                                    <div className="scan-section-header">
                                                        <div className="section-icon">⚠️</div>
                                                        <div className="section-title">
                                                            <h4>Risky Files Detected</h4>
                                                            <p className="section-subtitle">{analysisResult.file_security_scan.risky_files.length} files pose potential security risks</p>
                                                        </div>
                                                    </div>
                                                    <div className="files-container">
                                                        {analysisResult.file_security_scan.risky_files.slice(0, 15).map((file, index) => (
                                                            <div key={index} className="file-card risky">
                                                                <div className="file-icon">📄</div>
                                                                <div className="file-details">
                                                                    <div className="file-path">{safeRenderFilePath(file)}</div>
                                                                    {safeRenderFileReason(file) && (
                                                                        <div className="file-reason">{safeRenderFileReason(file)}</div>
                                                                    )}
                                                                </div>
                                                                <div className="file-badge risky-badge">Risky</div>
                                                            </div>
                                                        ))}
                                                        {analysisResult.file_security_scan.risky_files.length > 15 && (
                                                            <div className="more-files-indicator">
                                                                <span className="more-count">+{analysisResult.file_security_scan.risky_files.length - 15} more files</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                            
                                            <div className="security-files-grid">
                                                {analysisResult.file_security_scan.security_files_found && analysisResult.file_security_scan.security_files_found.length > 0 && (
                                                    <div className="security-scan-section success">
                                                        <div className="scan-section-header">
                                                            <div className="section-icon">✅</div>
                                                            <div className="section-title">
                                                                <h4>Security Files Present</h4>
                                                                <p className="section-subtitle">{analysisResult.file_security_scan.security_files_found.length} security configurations found</p>
                                                            </div>
                                                        </div>
                                                        <div className="simple-files-list">
                                                            {analysisResult.file_security_scan.security_files_found.map((file, index) => (
                                                                <div key={index} className="simple-file-item present">
                                                                    <span className="file-check">✓</span>
                                                                    <span className="file-name">{safeRenderFilePath(file)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {analysisResult.file_security_scan.missing_security_files && analysisResult.file_security_scan.missing_security_files.length > 0 && (
                                                    <div className="security-scan-section missing">
                                                        <div className="scan-section-header">
                                                            <div className="section-icon">❌</div>
                                                            <div className="section-title">
                                                                <h4>Missing Security Files</h4>
                                                                <p className="section-subtitle">{analysisResult.file_security_scan.missing_security_files.length} recommended files not found</p>
                                                            </div>
                                                        </div>
                                                        <div className="simple-files-list">
                                                            {analysisResult.file_security_scan.missing_security_files.map((file, index) => (
                                                                <div key={index} className="simple-file-item missing">
                                                                    <span className="file-check">✗</span>
                                                                    <span className="file-name">{safeRenderFilePath(file)}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {analysisResult.code_quality_results && analysisResult.code_quality_results.length > 0 && (
                                    <div className="card">
                                        <h3>🔍 Code Quality Analysis</h3>
                                        <div className="code-quality-section">
                                            <div className="quality-summary-header">
                                                <div className="quality-stats">
                                                    <div className="quality-stat">
                                                        <span className="stat-number">{analysisResult.code_quality_results.length}</span>
                                                        <span className="stat-label">Total Issues</span>
                                                    </div>
                                                    <div className="quality-stat">
                                                        <span className="stat-number">
                                                            {analysisResult.code_quality_results.filter(issue => 
                                                                (issue.severity || 'medium').toLowerCase() === 'high' || 
                                                                (issue.severity || 'medium').toLowerCase() === 'critical'
                                                            ).length}
                                                        </span>
                                                        <span className="stat-label">High Priority</span>
                                                    </div>
                                                    <div className="quality-stat">
                                                        <span className="stat-number">
                                                            {analysisResult.code_quality_results.filter(issue => 
                                                                (issue.severity || 'medium').toLowerCase() === 'medium'
                                                            ).length}
                                                        </span>
                                                        <span className="stat-label">Medium Priority</span>
                                                    </div>
                                                    <div className="quality-stat">
                                                        <span className="stat-number">
                                                            {analysisResult.code_quality_results.filter(issue => 
                                                                (issue.severity || 'medium').toLowerCase() === 'low'
                                                            ).length}
                                                        </span>
                                                        <span className="stat-label">Low Priority</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <div className="quality-issues-container">
                                                {['Critical', 'High', 'Medium', 'Low'].map(severityLevel => {
                                                    const issuesForSeverity = analysisResult.code_quality_results.filter(issue => 
                                                        (issue.severity || 'Medium').toLowerCase() === severityLevel.toLowerCase()
                                                    );
                                                    
                                                    if (issuesForSeverity.length === 0) return null;
                                                    
                                                    return (
                                                        <div key={severityLevel} className={`severity-group severity-${severityLevel.toLowerCase()}`}>
                                                            <div className="severity-header">
                                                                <h4 className="severity-title">
                                                                    <span className={`severity-icon severity-${severityLevel.toLowerCase()}`}>
                                                                        {severityLevel === 'Critical' ? '🔴' : 
                                                                         severityLevel === 'High' ? '🟠' : 
                                                                         severityLevel === 'Medium' ? '🟡' : '🔵'}
                                                                    </span>
                                                                    {severityLevel} Priority Issues
                                                                </h4>
                                                                <span className="severity-count">{issuesForSeverity.length}</span>
                                                            </div>
                                                            <div className="quality-issues-list">
                                                                {issuesForSeverity.slice(0, severityLevel === 'Critical' || severityLevel === 'High' ? 10 : 5).map((issue, index) => (
                                                                    <div key={index} className="quality-issue">
                                                                        <div className="issue-header">
                                                                            <div className="issue-file-info">
                                                                                <span className="issue-file">
                                                                                    {typeof (issue.file || issue.filename) === 'string' 
                                                                                        ? (issue.file || issue.filename || 'N/A')
                                                                                        : 'N/A'
                                                                                    }
                                                                                </span>
                                                                                {issue.line && <span className="issue-line">Line {issue.line}</span>}
                                                                            </div>
                                                                            <span className={`issue-severity-badge severity-${severityLevel.toLowerCase()}`}>
                                                                                {severityLevel}
                                                                            </span>
                                                                        </div>
                                                                        <div className="issue-description">
                                                                            {issue.description || issue.message || issue.rule_id || 'Code quality issue'}
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                                {issuesForSeverity.length > (severityLevel === 'Critical' || severityLevel === 'High' ? 10 : 5) && (
                                                                    <div className="more-issues">
                                                                        <span className="more-issues-text">
                                                                            +{issuesForSeverity.length - (severityLevel === 'Critical' || severityLevel === 'High' ? 10 : 5)} more {severityLevel.toLowerCase()} priority issues
                                                                        </span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {analysisResult.ai_analysis && (
                                    <div className="card">
                                        <h3>🧠 AI Security Analysis</h3>
                                        <div className="ai-analysis-container">
                                            <div className="analysis-header">
                                                <div className="analysis-model-info">
                                                    <span className="model-badge">Comprehensive Analysis (Smart Model)</span>
                                                </div>
                                            </div>
                                            <div className="ai-analysis-content">
                                                <ChatResponseFormatter message={analysisResult.ai_analysis} />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {(analysisResult.recommendations && analysisResult.recommendations.length > 0) || true ? (
                                    <div className="card">
                                        <h3>💡 Security Recommendations</h3>
                                        <div className="recommendations-container">
                                            {/* Show backend recommendations if they have meaningful content */}
                                            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && 
                                             analysisResult.recommendations.some(rec => {
                                                 const description = typeof rec === 'string' ? rec : 
                                                     (rec.description || rec.message || rec.text || '');
                                                 return description && description !== 'No description available' && description.trim().length > 10;
                                             }) ? (
                                                analysisResult.recommendations.map((recommendation, index) => {
                                                    const rec = typeof recommendation === 'string' ? 
                                                        { description: recommendation, priority: 'Medium', title: 'Security Recommendation' } : 
                                                        recommendation;
                                                    
                                                    const description = rec.description || rec.message || rec.text || '';
                                                    
                                                    // Skip recommendations with no meaningful content
                                                    if (!description || description === 'No description available' || description.trim().length <= 10) {
                                                        return null;
                                                    }
                                                    
                                                    return (
                                                        <div key={`backend-${index}`} className="recommendation-card">
                                                            <div className="recommendation-header">
                                                                <div className="recommendation-priority">
                                                                    <span className={`priority-badge priority-${(rec.priority || 'medium').toLowerCase()}`}>
                                                                        {rec.priority || 'Medium'}
                                                                    </span>
                                                                </div>
                                                                <h4 className="recommendation-title">
                                                                    {rec.title || rec.category || `Security Recommendation #${index + 1}`}
                                                                </h4>
                                                            </div>
                                                            <div className="recommendation-content">
                                                                <p className="recommendation-description">
                                                                    {description}
                                                                </p>
                                                                {rec.action && (
                                                                    <div className="recommendation-action">
                                                                        <strong>Recommended Action:</strong> {rec.action}
                                                                    </div>
                                                                )}
                                                                {rec.impact && (
                                                                    <div className="recommendation-impact">
                                                                        <strong>Impact:</strong> {rec.impact}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    );
                                                }).filter(Boolean)
                                            ) : null}
                                            
                                            {/* Always show smart default recommendations based on analysis results */}
                                            <div className="smart-recommendations">
                                                <div className="recommendations-header">
                                                    <h4>🎯 Intelligent Recommendations Based on Your Analysis</h4>
                                                    <p>Generated based on the security issues found in your repository</p>
                                                </div>
                                                
                                                {/* Recommendations based on detected secrets */}
                                                {analysisResult.secret_scan_results && analysisResult.secret_scan_results.length > 0 && (
                                                    <div className="recommendation-card priority-critical">
                                                        <div className="recommendation-header">
                                                            <div className="recommendation-priority">
                                                                <span className="priority-badge priority-critical">Critical</span>
                                                            </div>
                                                            <h4 className="recommendation-title">🚨 Immediate Secret Remediation Required</h4>
                                                        </div>
                                                        <div className="recommendation-content">
                                                            <p className="recommendation-description">
                                                                We detected <strong>{analysisResult.secret_scan_results.length} hardcoded secret(s)</strong> in your repository. This is a critical security risk that needs immediate attention.
                                                            </p>
                                                            <div className="recommendation-action">
                                                                <strong>Immediate Actions:</strong>
                                                                <ul>
                                                                    <li>Rotate all exposed API keys and secrets immediately</li>
                                                                    <li>Remove secrets from git history using tools like BFG Repo-Cleaner</li>
                                                                    <li>Implement environment variables for secret management</li>
                                                                    <li>Set up secret scanning in your CI/CD pipeline</li>
                                                                </ul>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {/* Recommendations based on code quality issues */}
                                                {analysisResult.code_quality_results && analysisResult.code_quality_results.length > 0 && (
                                                    <div className="recommendation-card">
                                                        <div className="recommendation-header">
                                                            <div className="recommendation-priority">
                                                                <span className="priority-badge priority-high">High</span>
                                                            </div>
                                                            <h4 className="recommendation-title">🔧 Code Quality & Security Issues</h4>
                                                        </div>
                                                        <div className="recommendation-content">
                                                            <p className="recommendation-description">
                                                                Found <strong>{analysisResult.code_quality_results.length} code quality issues</strong> including potential security vulnerabilities like function constructors that can lead to code injection.
                                                            </p>
                                                            <div className="recommendation-action">
                                                                <strong>Recommended Actions:</strong>
                                                                <ul>
                                                                    <li>Replace dynamic function constructors with safer alternatives</li>
                                                                    <li>Implement proper input validation and sanitization</li>
                                                                    <li>Use static analysis tools in your development workflow</li>
                                                                    <li>Enable ESLint security rules for JavaScript code</li>
                                                                </ul>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {/* Recommendations based on dependency vulnerabilities */}
                                                {analysisResult.dependency_scan_results?.vulnerable_packages && analysisResult.dependency_scan_results.vulnerable_packages.length > 0 && (
                                                    <div className="recommendation-card">
                                                        <div className="recommendation-header">
                                                            <div className="recommendation-priority">
                                                                <span className="priority-badge priority-high">High</span>
                                                            </div>
                                                            <h4 className="recommendation-title">📦 Vulnerable Dependencies</h4>
                                                        </div>
                                                        <div className="recommendation-content">
                                                            <p className="recommendation-description">
                                                                Detected <strong>{analysisResult.dependency_scan_results.vulnerable_packages.length} vulnerable dependencies</strong> that could expose your application to security risks.
                                                            </p>
                                                            <div className="recommendation-action">
                                                                <strong>Recommended Actions:</strong>
                                                                <ul>
                                                                    <li>Update vulnerable packages to their latest secure versions</li>
                                                                    <li>Enable GitHub Dependabot for automated dependency updates</li>
                                                                    <li>Regularly audit dependencies with npm audit or similar tools</li>
                                                                    <li>Consider using alternative packages if updates aren't available</li>
                                                                </ul>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {/* File security recommendations */}
                                                {analysisResult.file_security_scan && (
                                                    <>
                                                        {analysisResult.file_security_scan.sensitive_files && analysisResult.file_security_scan.sensitive_files.length > 0 && (
                                                            <div className="recommendation-card">
                                                                <div className="recommendation-header">
                                                                    <div className="recommendation-priority">
                                                                        <span className="priority-badge priority-medium">Medium</span>
                                                                    </div>
                                                                    <h4 className="recommendation-title">📁 Sensitive File Management</h4>
                                                                </div>
                                                                <div className="recommendation-content">
                                                                    <p className="recommendation-description">
                                                                        Found <strong>{analysisResult.file_security_scan.sensitive_files.length} sensitive files</strong> that may contain configuration or environment data.
                                                                    </p>
                                                                    <div className="recommendation-action">
                                                                        <strong>Recommended Actions:</strong>
                                                                        <ul>
                                                                            <li>Review sensitive files to ensure no secrets are exposed</li>
                                                                            <li>Add appropriate files to .gitignore</li>
                                                                            <li>Use environment-specific configuration files</li>
                                                                            <li>Implement proper file access controls</li>
                                                                        </ul>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
                                                        
                                                        {analysisResult.file_security_scan.missing_security_files && analysisResult.file_security_scan.missing_security_files.length > 0 && (
                                                            <div className="recommendation-card">
                                                                <div className="recommendation-header">
                                                                    <div className="recommendation-priority">
                                                                        <span className="priority-badge priority-medium">Medium</span>
                                                                    </div>
                                                                    <h4 className="recommendation-title">🛡️ Security Configuration Files</h4>
                                                                </div>
                                                                <div className="recommendation-content">
                                                                    <p className="recommendation-description">
                                                                        Missing <strong>{analysisResult.file_security_scan.missing_security_files.length} recommended security files</strong> that help protect your repository and deployments.
                                                                    </p>
                                                                    <div className="recommendation-action">
                                                                        <strong>Recommended Actions:</strong>
                                                                        <ul>
                                                                            <li>Add a SECURITY.md file with vulnerability reporting procedures</li>
                                                                            <li>Create a .gitignore file to exclude sensitive files</li>
                                                                            <li>Add security headers configuration</li>
                                                                            <li>Implement proper dependency management files</li>
                                                                        </ul>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                                
                                                {/* General security recommendations */}
                                                <div className="recommendation-card">
                                                    <div className="recommendation-header">
                                                        <div className="recommendation-priority">
                                                            <span className="priority-badge priority-medium">Medium</span>
                                                        </div>
                                                        <h4 className="recommendation-title">🔐 General Security Best Practices</h4>
                                                    </div>
                                                    <div className="recommendation-content">
                                                        <p className="recommendation-description">
                                                            Implement these security best practices to improve your overall security posture.
                                                        </p>
                                                        <div className="recommendation-action">
                                                            <strong>Recommended Actions:</strong>
                                                            <ul>
                                                                <li>Enable two-factor authentication for all team members</li>
                                                                <li>Set up branch protection rules for main/master branches</li>
                                                                <li>Implement security headers (HTTPS, CSP, HSTS)</li>
                                                                <li>Regular security training for development team</li>
                                                                <li>Implement automated security testing in CI/CD</li>
                                                            </ul>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : null}

                                {(analysisResult.analysis_warnings && analysisResult.analysis_warnings.length > 0) || 
                                 (analysisResult.analysis_errors && analysisResult.analysis_errors.length > 0) && (
                                    <div className="card">
                                        <h3>Analysis Notes</h3>
                                        {analysisResult.analysis_warnings && analysisResult.analysis_warnings.length > 0 && (
                                            <div className="warnings-section">
                                                <h4>⚠️ Warnings</h4>
                                                <ul className="warnings-list">
                                                    {analysisResult.analysis_warnings.map((warning, index) => (
                                                        <li key={index} className="warning-item">{warning}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        {analysisResult.analysis_errors && analysisResult.analysis_errors.length > 0 && (
                                            <div className="errors-section">
                                                <h4>❌ Errors</h4>
                                                <ul className="errors-list">
                                                    {analysisResult.analysis_errors.map((error, index) => (
                                                        <li key={index} className="error-item">{error}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}
                                
                                <div className="card">
                                    <div className="card-header-action">
                                        <h3>🔍 All Security Issues Detected</h3>
                                        <div className="header-actions">
                                            <button 
                                                onClick={() => setShowAllIssues(!showAllIssues)} 
                                                className="btn btn-outline"
                                            >
                                                {showAllIssues ? 'Show High Priority Only' : 'Show All Issues'}
                                            </button>
                                            <button onClick={fixAllIssues} disabled={isFixingAll} className="btn btn-secondary">
                                                {isFixingAll ? 'Fixing All...' : 'Fix All Issues'}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    {/* Issues Summary */}
                                    <div className="issues-summary">
                                        <div className="summary-stats">
                                            <div className="summary-stat">
                                                <span className="stat-number">
                                                    {(analysisResult.secret_scan_results?.length || 0) + 
                                                     (analysisResult.static_analysis_results?.length || 0) + 
                                                     (analysisResult.dependency_scan_results?.vulnerable_packages?.length || 0) +
                                                     (analysisResult.code_quality_results?.length || 0)}
                                                </span>
                                                <span className="stat-label">Total Issues</span>
                                            </div>
                                            <div className="summary-stat critical">
                                                <span className="stat-number">
                                                    {[
                                                        ...(analysisResult.secret_scan_results || []),
                                                        ...(analysisResult.static_analysis_results || []),
                                                        ...(analysisResult.dependency_scan_results?.vulnerable_packages || []),
                                                        ...(analysisResult.code_quality_results || [])
                                                    ].filter(issue => (issue.severity || '').toLowerCase() === 'critical').length}
                                                </span>
                                                <span className="stat-label">Critical</span>
                                            </div>
                                            <div className="summary-stat high">
                                                <span className="stat-number">
                                                    {[
                                                        ...(analysisResult.secret_scan_results || []),
                                                        ...(analysisResult.static_analysis_results || []),
                                                        ...(analysisResult.dependency_scan_results?.vulnerable_packages || []),
                                                        ...(analysisResult.code_quality_results || [])
                                                    ].filter(issue => (issue.severity || '').toLowerCase() === 'high').length}
                                                </span>
                                                <span className="stat-label">High</span>
                                            </div>
                                            <div className="summary-stat medium">
                                                <span className="stat-number">
                                                    {[
                                                        ...(analysisResult.secret_scan_results || []),
                                                        ...(analysisResult.static_analysis_results || []),
                                                        ...(analysisResult.dependency_scan_results?.vulnerable_packages || []),
                                                        ...(analysisResult.code_quality_results || [])
                                                    ].filter(issue => (issue.severity || '').toLowerCase() === 'medium').length}
                                                </span>
                                                <span className="stat-label">Medium</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* Display Filter Info */}
                                    {!showAllIssues && (analysisResult.code_quality_results?.length || 0) > 0 && (
                                        <div className="issues-filter-info">
                                            <span className="filter-indicator">
                                                Showing high priority issues only. 
                                                <button onClick={() => setShowAllIssues(true)} className="text-link">
                                                    Show all {analysisResult.code_quality_results.length} issues
                                                </button>
                                            </span>
                                        </div>
                                    )}
                                    
                                    {/* All Issues Table */}
                                    <div className="issues-table-container">
                                        <table className="issues-table">
                                            <thead>
                                                <tr>
                                                    <th>Type</th>
                                                    <th>File Path</th>
                                                    <th>Severity</th>
                                                    <th>Description</th>
                                                    <th>Line</th>
                                                    <th>Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {/* Secret Scan Results */}
                                                {analysisResult.secret_scan_results?.map((issue, index) => (
                                                    <React.Fragment key={`secret-${index}`}>
                                                        <tr className={isIssueFixed('secret', index) ? 'issue-fixed' : ''}>
                                                            <td><span className="issue-type secret">Secret</span></td>
                                                            <td className="file-path">{issue.file || issue.filename || 'N/A'}</td>
                                                            <td><span className={`severity-badge severity-${(issue.severity || 'critical').toLowerCase()}`}>{issue.severity || 'Critical'}</span></td>
                                                            <td className="issue-description">{issue.description || issue.pattern || issue.rule_id || 'Hardcoded secret detected'}</td>
                                                            <td>{issue.line || issue.line_number || '-'}</td>
                                                            <td>
                                                                {!isIssueFixed('secret', index) && (
                                                                    <button 
                                                                        className="btn-fix" 
                                                                        onClick={() => fixIssue(issue, 'secret', index)} 
                                                                        disabled={fixingIssues[`secret-${index}`] || isFixingAll}
                                                                    >
                                                                        {fixingIssues[`secret-${index}`] ? 'Fixing...' : 'Fix'}
                                                                    </button>
                                                                )}
                                                                {isIssueFixed('secret', index) && (
                                                                    <div className="fixed-actions">
                                                                        <span className="fixed-badge">✓ Fixed</span>
                                                                        {fixDetails[`secret-${index}`] && (
                                                                            <button 
                                                                                className="btn-view-diff" 
                                                                                onClick={() => toggleDiffView('secret', index)}
                                                                            >
                                                                                {expandedDiffs[`secret-${index}`] ? 'Hide Diff' : 'View Diff'}
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </td>
                                                        </tr>
                                                        {/* Diff viewer row */}
                                                        {isIssueFixed('secret', index) && expandedDiffs[`secret-${index}`] && fixDetails[`secret-${index}`] && (
                                                            <tr className="diff-row">
                                                                <td colSpan="6" className="diff-cell">
                                                                    <div className="inline-diff-container">
                                                                        {fixDetails[`secret-${index}`].fix_details && (
                                                                            <div className="fix-summary-inline">
                                                                                <h4>Fix Summary</h4>
                                                                                <p>{fixDetails[`secret-${index}`].fix_details.fix_summary}</p>
                                                                                {fixDetails[`secret-${index}`].pull_request?.url && (
                                                                                    <p>
                                                                                        <a href={fixDetails[`secret-${index}`].pull_request.url} target="_blank" rel="noopener noreferrer" className="pr-link-inline">
                                                                                            View Pull Request #{fixDetails[`secret-${index}`].pull_request.number}
                                                                                        </a>
                                                                                    </p>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        {fixDetails[`secret-${index}`].code_comparison && (
                                                                            <>
                                                                                <DiffViewer
                                                                                    original={fixDetails[`secret-${index}`].code_comparison.original_content}
                                                                                    fixed={fixDetails[`secret-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    diffStats={fixDetails[`secret-${index}`].code_comparison.diff_statistics}
                                                                                    unifiedDiff={fixDetails[`secret-${index}`].code_comparison.diff_statistics?.unified_diff}
                                                                                />
                                                                                <CodePreviewTester
                                                                                    originalCode={fixDetails[`secret-${index}`].code_comparison.original_content}
                                                                                    fixedCode={fixDetails[`secret-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    issue={issue}
                                                                                    onTestComplete={(results) => {
                                                                                        console.log('Test results for secret issue:', results);
                                                                                    }}
                                                                                />
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                ))}
                                                
                                                {/* Static Analysis Results */}
                                                {analysisResult.static_analysis_results?.map((issue, index) => (
                                                    <React.Fragment key={`static-${index}`}>
                                                        <tr className={isIssueFixed('static_analysis', index) ? 'issue-fixed' : ''}>
                                                            <td><span className="issue-type static">Static Analysis</span></td>
                                                            <td className="file-path">{issue.file || issue.filename || 'N/A'}</td>
                                                            <td><span className={`severity-badge severity-${(issue.severity || 'high').toLowerCase()}`}>{issue.severity || 'High'}</span></td>
                                                            <td className="issue-description">{issue.description || issue.message || issue.rule_id || 'Security vulnerability detected'}</td>
                                                            <td>{issue.line || issue.line_number || '-'}</td>
                                                            <td>
                                                                {!isIssueFixed('static_analysis', index) && (
                                                                    <button 
                                                                        className="btn-fix" 
                                                                        onClick={() => fixIssue(issue, 'static_analysis', index)} 
                                                                        disabled={fixingIssues[`static_analysis-${index}`] || isFixingAll}
                                                                    >
                                                                        {fixingIssues[`static_analysis-${index}`] ? 'Fixing...' : 'Fix'}
                                                                    </button>
                                                                )}
                                                                {isIssueFixed('static_analysis', index) && (
                                                                    <div className="fixed-actions">
                                                                        <span className="fixed-badge">✓ Fixed</span>
                                                                        {fixDetails[`static_analysis-${index}`] && (
                                                                            <button 
                                                                                className="btn-view-diff" 
                                                                                onClick={() => toggleDiffView('static_analysis', index)}
                                                                            >
                                                                                {expandedDiffs[`static_analysis-${index}`] ? 'Hide Diff' : 'View Diff'}
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </td>
                                                        </tr>
                                                        {/* Diff viewer row */}
                                                        {isIssueFixed('static_analysis', index) && expandedDiffs[`static_analysis-${index}`] && fixDetails[`static_analysis-${index}`] && (
                                                            <tr className="diff-row">
                                                                <td colSpan="6" className="diff-cell">
                                                                    <div className="inline-diff-container">
                                                                        {fixDetails[`static_analysis-${index}`].fix_details && (
                                                                            <div className="fix-summary-inline">
                                                                                <h4>Fix Summary</h4>
                                                                                <p>{fixDetails[`static_analysis-${index}`].fix_details.fix_summary}</p>
                                                                                {fixDetails[`static_analysis-${index}`].pull_request?.url && (
                                                                                    <p>
                                                                                        <a href={fixDetails[`static_analysis-${index}`].pull_request.url} target="_blank" rel="noopener noreferrer" className="pr-link-inline">
                                                                                            View Pull Request #{fixDetails[`static_analysis-${index}`].pull_request.number}
                                                                                        </a>
                                                                                    </p>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        {fixDetails[`static_analysis-${index}`].code_comparison && (
                                                                            <>
                                                                                <DiffViewer
                                                                                    original={fixDetails[`static_analysis-${index}`].code_comparison.original_content}
                                                                                    fixed={fixDetails[`static_analysis-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    diffStats={fixDetails[`static_analysis-${index}`].code_comparison.diff_statistics}
                                                                                    unifiedDiff={fixDetails[`static_analysis-${index}`].code_comparison.diff_statistics?.unified_diff}
                                                                                />
                                                                                <CodePreviewTester
                                                                                    originalCode={fixDetails[`static_analysis-${index}`].code_comparison.original_content}
                                                                                    fixedCode={fixDetails[`static_analysis-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    issue={issue}
                                                                                    onTestComplete={(results) => {
                                                                                        console.log('Test results for static analysis issue:', results);
                                                                                    }}
                                                                                />
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                ))}
                                                
                                                {/* Dependency Vulnerabilities */}
                                                {analysisResult.dependency_scan_results?.vulnerable_packages?.map((issue, index) => (
                                                    <React.Fragment key={`dependency-${index}`}>
                                                        <tr className={isIssueFixed('dependency', index) ? 'issue-fixed' : ''}>
                                                            <td><span className="issue-type dependency">Dependency</span></td>
                                                            <td className="file-path">{issue.file || issue.package_name || 'Package Dependencies'}</td>
                                                            <td><span className={`severity-badge severity-${(issue.severity || 'medium').toLowerCase()}`}>{issue.severity || 'Medium'}</span></td>
                                                            <td className="issue-description">{issue.description || issue.vulnerability || (issue.package_name ? `Vulnerable dependency: ${issue.package_name}` : 'Vulnerable dependency detected')}</td>
                                                            <td>{issue.line || '-'}</td>
                                                            <td>
                                                                {!isIssueFixed('dependency', index) && (
                                                                    <button 
                                                                        className="btn-fix" 
                                                                        onClick={() => fixIssue(issue, 'dependency', index)} 
                                                                        disabled={fixingIssues[`dependency-${index}`] || isFixingAll}
                                                                    >
                                                                        {fixingIssues[`dependency-${index}`] ? 'Fixing...' : 'Fix'}
                                                                    </button>
                                                                )}
                                                                {isIssueFixed('dependency', index) && (
                                                                    <div className="fixed-actions">
                                                                        <span className="fixed-badge">✓ Fixed</span>
                                                                        {fixDetails[`dependency-${index}`] && (
                                                                            <button 
                                                                                className="btn-view-diff" 
                                                                                onClick={() => toggleDiffView('dependency', index)}
                                                                            >
                                                                                {expandedDiffs[`dependency-${index}`] ? 'Hide Diff' : 'View Diff'}
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </td>
                                                        </tr>
                                                        {/* Diff viewer row */}
                                                        {isIssueFixed('dependency', index) && expandedDiffs[`dependency-${index}`] && fixDetails[`dependency-${index}`] && (
                                                            <tr className="diff-row">
                                                                <td colSpan="6" className="diff-cell">
                                                                    <div className="inline-diff-container">
                                                                        {fixDetails[`dependency-${index}`].fix_details && (
                                                                            <div className="fix-summary-inline">
                                                                                <h4>Fix Summary</h4>
                                                                                <p>{fixDetails[`dependency-${index}`].fix_details.fix_summary}</p>
                                                                                {fixDetails[`dependency-${index}`].pull_request?.url && (
                                                                                    <p>
                                                                                        <a href={fixDetails[`dependency-${index}`].pull_request.url} target="_blank" rel="noopener noreferrer" className="pr-link-inline">
                                                                                            View Pull Request #{fixDetails[`dependency-${index}`].pull_request.number}
                                                                                        </a>
                                                                                    </p>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        {fixDetails[`dependency-${index}`].code_comparison && (
                                                                            <>
                                                                                <DiffViewer
                                                                                    original={fixDetails[`dependency-${index}`].code_comparison.original_content}
                                                                                    fixed={fixDetails[`dependency-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.package_name || 'Package Dependencies'}
                                                                                    diffStats={fixDetails[`dependency-${index}`].code_comparison.diff_statistics}
                                                                                    unifiedDiff={fixDetails[`dependency-${index}`].code_comparison.diff_statistics?.unified_diff}
                                                                                />
                                                                                <CodePreviewTester
                                                                                    originalCode={fixDetails[`dependency-${index}`].code_comparison.original_content}
                                                                                    fixedCode={fixDetails[`dependency-${index}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.package_name || 'Package Dependencies'}
                                                                                    issue={issue}
                                                                                    onTestComplete={(results) => {
                                                                                        console.log('Test results for dependency issue:', results);
                                                                                    }}
                                                                                />
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                ))}
                                                
                                                {/* Code Quality Issues */}
                                                {analysisResult.code_quality_results?.filter(issue => 
                                                    showAllIssues || 
                                                    (issue.severity || '').toLowerCase() === 'critical' || 
                                                    (issue.severity || '').toLowerCase() === 'high'
                                                ).map((issue, index) => {
                                                    // Find the original index in the full array for proper key generation
                                                    const originalIndex = analysisResult.code_quality_results.findIndex(originalIssue => 
                                                        originalIssue.file === issue.file && 
                                                        originalIssue.line === issue.line && 
                                                        originalIssue.description === issue.description
                                                    );
                                                    return (
                                                    <React.Fragment key={`quality-${originalIndex}`}>
                                                        <tr className={isIssueFixed('code_quality', originalIndex) ? 'issue-fixed' : ''}>
                                                            <td><span className="issue-type quality">Code Quality</span></td>
                                                            <td className="file-path">{issue.file || issue.filename || 'N/A'}</td>
                                                            <td><span className={`severity-badge severity-${(issue.severity || 'medium').toLowerCase()}`}>{issue.severity || 'Medium'}</span></td>
                                                            <td className="issue-description">{issue.description || issue.message || issue.rule_id || 'Code quality issue'}</td>
                                                            <td>{issue.line || issue.line_number || '-'}</td>
                                                            <td>
                                                                {!isIssueFixed('code_quality', originalIndex) && (
                                                                    <button 
                                                                        className="btn-fix" 
                                                                        onClick={() => fixIssue(issue, 'code_quality', originalIndex)} 
                                                                        disabled={fixingIssues[`code_quality-${originalIndex}`] || isFixingAll}
                                                                    >
                                                                        {fixingIssues[`code_quality-${originalIndex}`] ? 'Fixing...' : 'Fix'}
                                                                    </button>
                                                                )}
                                                                {isIssueFixed('code_quality', originalIndex) && (
                                                                    <div className="fixed-actions">
                                                                        <span className="fixed-badge">✓ Fixed</span>
                                                                        {fixDetails[`code_quality-${originalIndex}`] && (
                                                                            <button 
                                                                                className="btn-view-diff" 
                                                                                onClick={() => toggleDiffView('code_quality', originalIndex)}
                                                                            >
                                                                                {expandedDiffs[`code_quality-${originalIndex}`] ? 'Hide Diff' : 'View Diff'}
                                                                            </button>
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </td>
                                                        </tr>
                                                        {/* Diff viewer row */}
                                                        {isIssueFixed('code_quality', originalIndex) && expandedDiffs[`code_quality-${originalIndex}`] && fixDetails[`code_quality-${originalIndex}`] && (
                                                            <tr className="diff-row">
                                                                <td colSpan="6" className="diff-cell">
                                                                    <div className="inline-diff-container">
                                                                        {fixDetails[`code_quality-${originalIndex}`].fix_details && (
                                                                            <div className="fix-summary-inline">
                                                                                <h4>Fix Summary</h4>
                                                                                <p>{fixDetails[`code_quality-${originalIndex}`].fix_details.fix_summary}</p>
                                                                                {fixDetails[`code_quality-${originalIndex}`].pull_request?.url && (
                                                                                    <p>
                                                                                        <a href={fixDetails[`code_quality-${originalIndex}`].pull_request.url} target="_blank" rel="noopener noreferrer" className="pr-link-inline">
                                                                                            View Pull Request #{fixDetails[`code_quality-${originalIndex}`].pull_request.number}
                                                                                        </a>
                                                                                    </p>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                        {fixDetails[`code_quality-${originalIndex}`].code_comparison && (
                                                                            <>
                                                                                <DiffViewer
                                                                                    original={fixDetails[`code_quality-${originalIndex}`].code_comparison.original_content}
                                                                                    fixed={fixDetails[`code_quality-${originalIndex}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    diffStats={fixDetails[`code_quality-${originalIndex}`].code_comparison.diff_statistics}
                                                                                    unifiedDiff={fixDetails[`code_quality-${originalIndex}`].code_comparison.diff_statistics?.unified_diff}
                                                                                />
                                                                                <CodePreviewTester
                                                                                    originalCode={fixDetails[`code_quality-${originalIndex}`].code_comparison.original_content}
                                                                                    fixedCode={fixDetails[`code_quality-${originalIndex}`].code_comparison.fixed_content}
                                                                                    filename={issue.file || issue.filename || 'N/A'}
                                                                                    issue={issue}
                                                                                    onTestComplete={(results) => {
                                                                                        console.log('Test results for code quality issue:', results);
                                                                                    }}
                                                                                />
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                            </tr>
                                                        )}
                                                    </React.Fragment>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                        
                                        {/* Show message if no issues */}
                                        {(!analysisResult.secret_scan_results?.length && 
                                          !analysisResult.static_analysis_results?.length && 
                                          !analysisResult.dependency_scan_results?.vulnerable_packages?.length &&
                                          !(showAllIssues ? analysisResult.code_quality_results?.length : analysisResult.code_quality_results?.filter(issue => 
                                            (issue.severity || '').toLowerCase() === 'critical' || 
                                            (issue.severity || '').toLowerCase() === 'high'
                                          ).length)) && (
                                            <div className="no-issues-message">
                                                <div className="no-issues-icon">✅</div>
                                                <div className="no-issues-text">
                                                    <h4>{showAllIssues ? 'No Security Issues Found' : 'No Critical or High Severity Issues Found'}</h4>
                                                    <p>Great! This repository appears to be well-maintained from a security perspective.</p>
                                                    {!showAllIssues && analysisResult.code_quality_results?.length > 0 && (
                                                        <p><button onClick={() => setShowAllIssues(true)} className="text-link">Show all {analysisResult.code_quality_results.length} code quality issues</button></p>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                {/* ============================================================ */}
                                {/* DEEP PENETRATION TEST RESULTS */}
                                {/* ============================================================ */}
                                {pentestResult && (
                                    <div className="card" style={{marginTop: '20px', border: '1px solid rgba(220, 38, 38, 0.3)'}}>
                                        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px'}}>
                                            <h3 style={{margin: 0, color: '#f87171'}}>🔒 Deep Penetration Test Results</h3>
                                            {!isPentesting && <button onClick={runDeepPentest} className="btn" style={{background: 'linear-gradient(135deg, #dc2626, #991b1b)', fontSize: '12px', padding: '6px 14px'}}>Re-run Pentest</button>}
                                        </div>

                                        {/* Scan Metadata */}
                                        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginBottom: '16px'}}>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Framework</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: '#e5e7eb'}}>{pentestResult.framework_detected || 'Unknown'}</div>
                                            </div>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Language</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: '#e5e7eb'}}>{pentestResult.language_detected || 'Unknown'}</div>
                                            </div>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Endpoints Found</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: '#e5e7eb'}}>{pentestResult.endpoints_discovered?.length || 0}</div>
                                            </div>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Tests Run</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: '#e5e7eb'}}>{pentestResult.total_tests_run || 0}</div>
                                            </div>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Duration</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: '#e5e7eb'}}>{(pentestResult.duration_seconds || 0).toFixed(1)}s</div>
                                            </div>
                                            <div style={{padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px'}}>
                                                <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase'}}>Risk Score</div>
                                                <div style={{fontSize: '16px', fontWeight: 600, color: (pentestResult.overall_risk_score || 0) > 50 ? '#ef4444' : (pentestResult.overall_risk_score || 0) > 20 ? '#f59e0b' : '#22c55e'}}>{pentestResult.overall_risk_score || 0}/100</div>
                                            </div>
                                        </div>

                                        {/* Severity Summary */}
                                        <div style={{display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap'}}>
                                            {pentestResult.summary?.critical > 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(220,38,38,0.2)', color: '#ef4444', fontWeight: 600, fontSize: '13px'}}>🔴 {pentestResult.summary.critical} Critical</span>}
                                            {pentestResult.summary?.high > 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(234,88,12,0.2)', color: '#fb923c', fontWeight: 600, fontSize: '13px'}}>🟠 {pentestResult.summary.high} High</span>}
                                            {pentestResult.summary?.medium > 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(217,119,6,0.2)', color: '#fbbf24', fontWeight: 600, fontSize: '13px'}}>🟡 {pentestResult.summary.medium} Medium</span>}
                                            {pentestResult.summary?.low > 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(37,99,235,0.2)', color: '#60a5fa', fontWeight: 600, fontSize: '13px'}}>🔵 {pentestResult.summary.low} Low</span>}
                                            {pentestResult.summary?.info > 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(107,114,128,0.2)', color: '#9ca3af', fontWeight: 600, fontSize: '13px'}}>ℹ️ {pentestResult.summary.info} Info</span>}
                                            {pentestResult.summary?.total_findings === 0 && <span style={{padding: '4px 12px', borderRadius: '20px', background: 'rgba(34,197,94,0.2)', color: '#22c55e', fontWeight: 600, fontSize: '13px'}}>✅ No vulnerabilities found</span>}
                                        </div>

                                        {/* Discovered Endpoints */}
                                        {pentestResult.endpoints_discovered?.length > 0 && (
                                            <div style={{marginBottom: '16px'}}>
                                                <h4 style={{color: '#d1d5db', fontSize: '14px', marginBottom: '8px'}}>📡 Discovered Endpoints ({pentestResult.endpoints_discovered.length})</h4>
                                                <div style={{maxHeight: '200px', overflowY: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '8px'}}>
                                                    {pentestResult.endpoints_discovered.map((ep, idx) => (
                                                        <div key={idx} style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 8px', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '13px'}}>
                                                            <span style={{padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700, fontFamily: 'monospace',
                                                                background: ep.method === 'GET' ? 'rgba(34,197,94,0.2)' : ep.method === 'POST' ? 'rgba(59,130,246,0.2)' : ep.method === 'PUT' ? 'rgba(245,158,11,0.2)' : ep.method === 'DELETE' ? 'rgba(239,68,68,0.2)' : 'rgba(107,114,128,0.2)',
                                                                color: ep.method === 'GET' ? '#22c55e' : ep.method === 'POST' ? '#3b82f6' : ep.method === 'PUT' ? '#f59e0b' : ep.method === 'DELETE' ? '#ef4444' : '#9ca3af'
                                                            }}>{ep.method}</span>
                                                            <code style={{color: '#e5e7eb', flex: 1}}>{ep.path}</code>
                                                            {ep.auth_required && <span style={{fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: 'rgba(245,158,11,0.2)', color: '#fbbf24'}}>AUTH</span>}
                                                            <span style={{color: '#6b7280', fontSize: '11px'}}>{ep.file}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Auth Mechanisms */}
                                        {pentestResult.auth_mechanisms?.length > 0 && (
                                            <div style={{marginBottom: '16px'}}>
                                                <h4 style={{color: '#d1d5db', fontSize: '14px', marginBottom: '8px'}}>🔐 Authentication Mechanisms</h4>
                                                <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
                                                    {pentestResult.auth_mechanisms.map((auth, idx) => (
                                                        <span key={idx} style={{padding: '4px 12px', borderRadius: '6px', background: 'rgba(139,92,246,0.15)', color: '#a78bfa', fontSize: '13px'}}>{auth}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Technologies */}
                                        {pentestResult.technologies?.length > 0 && (
                                            <div style={{marginBottom: '20px'}}>
                                                <h4 style={{color: '#d1d5db', fontSize: '14px', marginBottom: '8px'}}>🛠️ Technologies Detected</h4>
                                                <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
                                                    {pentestResult.technologies.map((tech, idx) => (
                                                        <span key={idx} style={{padding: '4px 12px', borderRadius: '6px', background: 'rgba(6,182,212,0.15)', color: '#22d3ee', fontSize: '13px'}}>{tech}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Findings List */}
                                        {pentestResult.findings?.length > 0 && (
                                            <div>
                                                <h4 style={{color: '#d1d5db', fontSize: '14px', marginBottom: '12px'}}>⚠️ Vulnerability Findings ({pentestResult.findings.length})</h4>
                                                {pentestResult.findings.map((finding, idx) => (
                                                    <div key={finding.id || idx} style={{marginBottom: '8px', border: `1px solid ${getSeverityColor(finding.severity)}33`, borderRadius: '8px', overflow: 'hidden'}}>
                                                        <div onClick={() => toggleFinding(finding.id || idx)} style={{display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', cursor: 'pointer', background: 'rgba(0,0,0,0.2)', transition: 'background 0.2s'}}>
                                                            <span style={{fontSize: '16px'}}>{getCategoryIcon(finding.category)}</span>
                                                            <span style={{fontSize: '14px'}}>{getSeverityIcon(finding.severity)}</span>
                                                            <span style={{flex: 1, color: '#e5e7eb', fontSize: '13px', fontWeight: 500}}>{finding.title}</span>
                                                            <span style={{padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, background: `${getSeverityColor(finding.severity)}22`, color: getSeverityColor(finding.severity)}}>{finding.severity}</span>
                                                            <span style={{padding: '2px 8px', borderRadius: '4px', fontSize: '11px', background: 'rgba(255,255,255,0.05)', color: '#9ca3af'}}>{finding.method} {finding.endpoint}</span>
                                                            <span style={{color: '#6b7280', fontSize: '14px'}}>{expandedFindings[finding.id || idx] ? '▼' : '▶'}</span>
                                                        </div>
                                                        {expandedFindings[finding.id || idx] && (
                                                            <div style={{padding: '14px', background: 'rgba(0,0,0,0.15)', borderTop: '1px solid rgba(255,255,255,0.05)'}}>
                                                                <div style={{marginBottom: '10px'}}>
                                                                    <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px'}}>Description</div>
                                                                    <div style={{color: '#d1d5db', fontSize: '13px', lineHeight: '1.5'}}>{finding.description}</div>
                                                                </div>
                                                                {finding.evidence && (
                                                                    <div style={{marginBottom: '10px'}}>
                                                                        <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px'}}>Evidence</div>
                                                                        <pre style={{background: 'rgba(0,0,0,0.4)', padding: '10px', borderRadius: '6px', color: '#fbbf24', fontSize: '12px', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '200px', overflowY: 'auto'}}>{finding.evidence}</pre>
                                                                    </div>
                                                                )}
                                                                {finding.payload_used && (
                                                                    <div style={{marginBottom: '10px'}}>
                                                                        <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px'}}>Payload Used</div>
                                                                        <code style={{background: 'rgba(220,38,38,0.15)', padding: '4px 10px', borderRadius: '4px', color: '#f87171', fontSize: '12px', fontFamily: 'monospace'}}>{finding.payload_used}</code>
                                                                    </div>
                                                                )}
                                                                {finding.response_snippet && (
                                                                    <div style={{marginBottom: '10px'}}>
                                                                        <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px'}}>Response Snippet</div>
                                                                        <pre style={{background: 'rgba(0,0,0,0.4)', padding: '10px', borderRadius: '6px', color: '#94a3b8', fontSize: '11px', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '150px', overflowY: 'auto'}}>{finding.response_snippet}</pre>
                                                                    </div>
                                                                )}
                                                                <div style={{marginBottom: '10px'}}>
                                                                    <div style={{fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px'}}>Remediation</div>
                                                                    <div style={{color: '#86efac', fontSize: '13px', lineHeight: '1.5', background: 'rgba(34,197,94,0.1)', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid #22c55e'}}>{finding.remediation}</div>
                                                                </div>
                                                                <div style={{display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: '8px'}}>
                                                                    {finding.cwe_id && <span style={{fontSize: '11px', color: '#a78bfa', background: 'rgba(139,92,246,0.1)', padding: '2px 8px', borderRadius: '4px'}}>{finding.cwe_id}</span>}
                                                                    {finding.owasp_category && <span style={{fontSize: '11px', color: '#f59e0b', background: 'rgba(245,158,11,0.1)', padding: '2px 8px', borderRadius: '4px'}}>{finding.owasp_category}</span>}
                                                                    {finding.cvss_score > 0 && <span style={{fontSize: '11px', color: finding.cvss_score >= 7 ? '#ef4444' : '#fbbf24', background: finding.cvss_score >= 7 ? 'rgba(239,68,68,0.1)' : 'rgba(251,191,36,0.1)', padding: '2px 8px', borderRadius: '4px'}}>CVSS: {finding.cvss_score}</span>}
                                                                    {finding.response_code > 0 && <span style={{fontSize: '11px', color: '#6b7280', background: 'rgba(107,114,128,0.1)', padding: '2px 8px', borderRadius: '4px'}}>HTTP {finding.response_code}</span>}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* S3 & Sandbox Info */}
                                        <div style={{marginTop: '16px', padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', fontSize: '12px', color: '#6b7280'}}>
                                            <div>Scan ID: {pentestResult.scan_id}</div>
                                            {pentestResult.s3_key && <div>S3: {pentestResult.s3_key}</div>}
                                            {pentestResult.sandbox_url && <div>Sandbox: {pentestResult.sandbox_url}</div>}
                                            {pentestResult.errors?.length > 0 && (
                                                <div style={{marginTop: '8px', color: '#f87171'}}>
                                                    {pentestResult.errors.map((err, idx) => <div key={idx}>⚠️ {err}</div>)}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Pentest in progress indicator (when triggered from results page) */}
                                {isPentesting && analysisResult && (
                                    <div className="card" style={{marginTop: '20px', border: '1px solid rgba(220, 38, 38, 0.3)'}}>
                                        <h3 style={{color: '#f87171'}}>🔒 Deep Penetration Test Running...</h3>
                                        <div style={{padding: '16px 0'}}>
                                            <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px'}}>
                                                <div style={{width: '18px', height: '18px', border: '3px solid rgba(220,38,38,0.3)', borderTop: '3px solid #dc2626', borderRadius: '50%', animation: 'spin 1s linear infinite'}}></div>
                                                <span style={{color: '#dc2626', fontWeight: 600}}>Running attack payloads against sandbox...</span>
                                            </div>
                                            <div style={{color: '#9ca3af', fontSize: '13px'}}>
                                                <p>• Cloning repo & storing in S3 bucket</p>
                                                <p>• Deploying in isolated Docker sandbox</p>
                                                <p>• Testing {'>'}20 SQL injection payloads</p>
                                                <p>• Testing XSS (reflected + stored)</p>
                                                <p>• Testing authentication bypass (JWT none, empty token, default creds)</p>
                                                <p>• Testing authorization bypass (IDOR, forced browsing, privilege escalation)</p>
                                                <p>• Testing SSRF, command injection, path traversal</p>
                                                <p>• Checking CORS, rate limiting, security headers</p>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Run Pentest button when analysis results are shown but no pentest yet */}
                                {analysisResult && !pentestResult && !isPentesting && (
                                    <div className="card" style={{marginTop: '20px', textAlign: 'center', padding: '24px', border: '1px dashed rgba(220,38,38,0.3)'}}>
                                        <h4 style={{color: '#f87171', marginBottom: '8px'}}>🔒 Want to go deeper?</h4>
                                        <p style={{color: '#9ca3af', fontSize: '14px', marginBottom: '16px'}}>Run a full penetration test — clones the repo into a sandbox container, discovers all API endpoints, and attacks them with real payloads (SQL injection, XSS, auth bypass, IDOR, and more).</p>
                                        <button onClick={runDeepPentest} disabled={isPentesting} className="btn" style={{background: 'linear-gradient(135deg, #dc2626, #991b1b)', padding: '10px 32px', fontSize: '15px'}}>🔒 Run Deep Penetration Test</button>
                                    </div>
                                )}

                            </main>

                            <aside className="report-sidebar">
                                <div className="card ai-chat-container">
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
                                        <button className="btn" onClick={askAI} disabled={isAskingAI || !currentQuestion.trim()}>Send</button>
                                    </div>
                                </div>
                            </aside>
                        </div>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
};

export default RepoAnalysisPage;
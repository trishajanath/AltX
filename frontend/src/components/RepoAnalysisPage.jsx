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
                                                    <tr key={`secret-${index}`} className={isIssueFixed('secret', index) ? 'issue-fixed' : ''}>
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
                                                            {isIssueFixed('secret', index) && <span className="fixed-badge">✓ Fixed</span>}
                                                        </td>
                                                    </tr>
                                                ))}
                                                
                                                {/* Static Analysis Results */}
                                                {analysisResult.static_analysis_results?.map((issue, index) => (
                                                    <tr key={`static-${index}`} className={isIssueFixed('static_analysis', index) ? 'issue-fixed' : ''}>
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
                                                            {isIssueFixed('static_analysis', index) && <span className="fixed-badge">✓ Fixed</span>}
                                                        </td>
                                                    </tr>
                                                ))}
                                                
                                                {/* Dependency Vulnerabilities */}
                                                {analysisResult.dependency_scan_results?.vulnerable_packages?.map((issue, index) => (
                                                    <tr key={`dependency-${index}`} className={isIssueFixed('dependency', index) ? 'issue-fixed' : ''}>
                                                        <td><span className="issue-type dependency">Dependency</span></td>
                                                        <td className="file-path">{issue.file || issue.package_name || 'Package Dependencies'}</td>
                                                        <td><span className={`severity-badge severity-${(issue.severity || 'medium').toLowerCase()}`}>{issue.severity || 'Medium'}</span></td>
                                                        <td className="issue-description">{issue.description || issue.vulnerability || `Vulnerable dependency: ${issue.package_name}` || 'Vulnerable dependency detected'}</td>
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
                                                            {isIssueFixed('dependency', index) && <span className="fixed-badge">✓ Fixed</span>}
                                                        </td>
                                                    </tr>
                                                ))}
                                                
                                                {/* High Priority Code Quality Issues */}
                                                {analysisResult.code_quality_results?.filter(issue => 
                                                    (issue.severity || '').toLowerCase() === 'critical' || 
                                                    (issue.severity || '').toLowerCase() === 'high'
                                                ).map((issue, index) => (
                                                    <tr key={`quality-${index}`} className={isIssueFixed('code_quality', index) ? 'issue-fixed' : ''}>
                                                        <td><span className="issue-type quality">Code Quality</span></td>
                                                        <td className="file-path">{issue.file || issue.filename || 'N/A'}</td>
                                                        <td><span className={`severity-badge severity-${(issue.severity || 'medium').toLowerCase()}`}>{issue.severity || 'Medium'}</span></td>
                                                        <td className="issue-description">{issue.description || issue.message || issue.rule_id || 'Code quality issue'}</td>
                                                        <td>{issue.line || issue.line_number || '-'}</td>
                                                        <td>
                                                            {!isIssueFixed('code_quality', index) && (
                                                                <button 
                                                                    className="btn-fix" 
                                                                    onClick={() => fixIssue(issue, 'code_quality', index)} 
                                                                    disabled={fixingIssues[`code_quality-${index}`] || isFixingAll}
                                                                >
                                                                    {fixingIssues[`code_quality-${index}`] ? 'Fixing...' : 'Fix'}
                                                                </button>
                                                            )}
                                                            {isIssueFixed('code_quality', index) && <span className="fixed-badge">✓ Fixed</span>}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                        
                                        {/* Show message if no issues */}
                                        {(!analysisResult.secret_scan_results?.length && 
                                          !analysisResult.static_analysis_results?.length && 
                                          !analysisResult.dependency_scan_results?.vulnerable_packages?.length &&
                                          !analysisResult.code_quality_results?.filter(issue => 
                                            (issue.severity || '').toLowerCase() === 'critical' || 
                                            (issue.severity || '').toLowerCase() === 'high'
                                          ).length) && (
                                            <div className="no-issues-message">
                                                <div className="no-issues-icon">✅</div>
                                                <div className="no-issues-text">
                                                    <h4>No Critical or High Severity Issues Found</h4>
                                                    <p>Great! This repository appears to be well-maintained from a security perspective.</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
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
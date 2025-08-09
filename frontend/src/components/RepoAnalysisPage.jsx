import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// Add CSS animations
const spinKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// Inject the keyframes into the document head
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.innerHTML = spinKeyframes;
  document.head.appendChild(style);
}

const RepoAnalysisPage = () => {
  usePreventZoom();
  const [repoUrl, setRepoUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState('');
  const [analysisLogs, setAnalysisLogs] = useState([]);
  const [modelType, setModelType] = useState('smart');
  const [deepScan, setDeepScan] = useState(true); // This state was declared but not used in the UI, keeping for logic.
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isAskingAI, setIsAskingAI] = useState(false);
  const [showAISidebar, setShowAISidebar] = useState(false);
  const [fixingIssues, setFixingIssues] = useState({}); // Track which issues are being fixed
  const [fixedIssues, setFixedIssues] = useState(new Set()); // Track successfully fixed issues

  const navigate = useNavigate();

  // Safe render function to handle any type of data
  const safeRender = (data) => {
    if (data === null || data === undefined) return '';
    if (typeof data === 'string' || typeof data === 'number') return data;
    if (typeof data === 'object') {
      try {
        return JSON.stringify(data);
      } catch (e) {
        return '[Object]';
      }
    }
    return String(data);
  };

  // Clean and validate GitHub repository URLs
  const cleanRepositoryUrl = (url) => {
    try {
      // Remove common GitHub web interface paths
      let cleaned = url
        .replace(/\/tree\/[^\/]+.*$/, '') // Remove /tree/branch-name and everything after
        .replace(/\/blob\/[^\/]+.*$/, '') // Remove /blob/branch-name and everything after
        .replace(/\/commits.*$/, '')     // Remove /commits and everything after
        .replace(/\/issues.*$/, '')      // Remove /issues and everything after
        .replace(/\/pull.*$/, '')        // Remove /pull and everything after
        .replace(/\/releases.*$/, '')    // Remove /releases and everything after
        .replace(/\/wiki.*$/, '')        // Remove /wiki and everything after
        .replace(/\/settings.*$/, '')    // Remove /settings and everything after
        .replace(/\/$/, '');             // Remove trailing slash

      // Validate it's a GitHub URL
      const urlPattern = /^https:\/\/github\.com\/[^\/]+\/[^\/]+$/;
      if (!urlPattern.test(cleaned)) {
        return null;
      }
      return cleaned;
    } catch (e) {
      return null;
    }
  };

  const analyzeRepository = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    const cleanedUrl = cleanRepositoryUrl(repoUrl.trim());
    if (!cleanedUrl) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo)');
      return;
    }

    setIsScanning(true);
    setError('');
    setAnalysisResult(null);
    setAnalysisLogs(['🔄 Starting repository analysis...']);
    setChatMessages([]); // Reset chat on new analysis

    try {
      const response = await fetch('http://localhost:8000/analyze-repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: cleanedUrl,
          model_type: modelType,
          deep_scan: deepScan
        }),
      });

      const data = await response.json();
      
      // Debug log to see the data structure
      console.log('Analysis result data:', data);
      if (data.recommendations) {
        console.log('Recommendations structure:', data.recommendations);
        data.recommendations.forEach((rec, i) => {
          console.log(`Recommendation ${i}:`, rec, typeof rec);
        });
      }

      if (data.error) {
        setError(data.error);
        setAnalysisLogs(prev => [...prev, `❌ Analysis failed: ${data.error}`]);
      } else {
        // Check if we have partial results even with some errors
        const hasPartialResults = data.repository_info || data.security_summary || 
                                 data.file_security_scan || data.secret_scan_results ||
                                 data.static_analysis_results || data.dependency_scan_results;

        if (hasPartialResults) {
          setAnalysisResult(data);
          
          // Show completion message based on whether there were critical errors
          if (data.analysis_errors && data.analysis_errors.length > 0) {
            setAnalysisLogs(prev => [...prev, '⚠️ Repository analysis completed with some errors - partial results available']);
            
            // Log specific analysis errors
            data.analysis_errors.forEach(error => {
              setAnalysisLogs(prev => [...prev, `❌ Analysis Error: ${error}`]);
            });
          } else {
            setAnalysisLogs(prev => [...prev, '✅ Repository analysis completed successfully!']);
          }

          if (data.warnings && data.warnings.length > 0) {
            data.warnings.forEach(warning => {
              setAnalysisLogs(prev => [...prev, `⚠️ Warning: ${warning}`]);
            });
          }
        } else {
          setError('Analysis completed but no results were returned. Please try again.');
          setAnalysisLogs(prev => [...prev, '❌ No analysis results received']);
        }

        // Generate AI summary if we have any results
        if (hasPartialResults) {
          const summary = generateAnalysisSummary(data);
          setChatMessages([{
            type: 'ai',
            message: summary,
            timestamp: new Date().toLocaleTimeString()
          }]);
        }
      }
    } catch (err) {
      console.error('Full error details:', err);
      console.error('Error name:', err.name);
      console.error('Error message:', err.message);
      let errorMsg = 'Failed to analyze repository. ';
      
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        errorMsg += 'Unable to connect to analysis server. Please ensure the backend is running on http://localhost:8000';
      } else if (err.message.includes('JSON')) {
        errorMsg += 'Server returned invalid response. The analysis may have partially completed.';
      } else if (err.message.includes('network') || err.message.includes('ECONNREFUSED')) {
        errorMsg += 'Network connection failed. Please check your connection and ensure the backend server is running.';
      } else {
        errorMsg += 'Please check your connection and try again.';
      }
      
      setError(errorMsg);
      setAnalysisLogs(prev => [...prev, `❌ ${errorMsg}`]);
      setAnalysisLogs(prev => [...prev, `🔍 Technical Error: ${err.message}`]);
      console.error('Repository analysis error:', err);
    } finally {
      setIsScanning(false);
    }
  };

  const generateAnalysisSummary = (data) => {
    const score = data.overall_security_score || 0;
    const level = data.security_level || 'Unknown';
    const summary = data.security_summary || {};
    
    // Check if analysis had errors
    const hasErrors = data.analysis_errors && data.analysis_errors.length > 0;
    const analysisStatus = hasErrors ? '⚠️ **Repository Analysis Complete (with warnings)**' : '🔍 **Repository Analysis Complete**';
    
    let analysisNote = '';
    if (hasErrors) {
      analysisNote = `\n⚠️ **Note:** Some analysis tools encountered issues but core security scanning completed successfully.\n`;
    }
    
    return `${analysisStatus}${analysisNote}

📊 **Security Summary:**
• Repository: ${data.repository_info?.name || 'Unknown'}
• Security Score: ${score}/100 (${level})
• Language: ${data.repository_info?.language || 'Unknown'}${data.repository_info?.stars ? `\n• Stars: ${data.repository_info.stars}` : ''}

🔍 **Scan Results:**
• Files Scanned: ${summary.total_files_scanned || 0}
• Directories Skipped: ${data.file_security_scan?.directories_skipped || 0} (build/dependency dirs)
• Secrets Found: ${summary.secrets_found || 0} 
• Static Issues: ${summary.static_issues_found || 0}
• Vulnerable Dependencies: ${summary.vulnerable_dependencies || 0}
• Code Quality Issues: ${summary.code_quality_issues || 0}

📁 **File Management:**
• Excluded Directories: ${data.file_security_scan?.excluded_directories?.length || 0}
• GitIgnore Recommendations: ${data.file_security_scan?.gitignore_recommendations?.length || 0}

💡 **Ready to answer specific questions about this repository analysis!**${hasErrors ? '\n\n🛠️ **Tip:** Some advanced features may have been limited due to system compatibility issues.' : ''}`;
  };

  const askAI = async () => {
    if (!currentQuestion.trim() || !analysisResult) return;

    setIsAskingAI(true);
    const userMessage = {
      type: 'user',
      message: currentQuestion,
      timestamp: new Date().toLocaleTimeString()
    };
    
    // Add user message and clear input immediately
    setChatMessages(prev => [...prev, userMessage]);
    const questionToAsk = currentQuestion;
    setCurrentQuestion('');

    try {
      const response = await fetch('http://localhost:8000/ai-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: questionToAsk,
          context: 'repo_analysis',
          model_type: modelType,
          history: [...chatMessages, userMessage] // Send the latest history
        }),
      });

      const data = await response.json();
      
      const aiMessage = {
        type: 'ai',
        message: data.response || 'Sorry, I could not process your question.',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      console.error('AI chat error:', err);
      const errorMessage = {
        type: 'ai',
        message: '❌ **Error:** Could not connect to AI assistant.',
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsAskingAI(false);
    }
  };
  
  // A wrapper for askAI that also sets the question from quick-links
  const handleQuickQuestion = (question) => {
      if (isAskingAI) return;
      const userMessage = {
        type: 'user',
        message: question,
        timestamp: new Date().toLocaleTimeString()
      };
      setChatMessages(prev => [...prev, userMessage]);
      setIsAskingAI(true);
      
      // We pass the question directly to askAI logic
      const ask = async () => {
          try {
              const response = await fetch('http://localhost:8000/ai-chat', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                      question: question,
                      context: 'repo_analysis',
                      model_type: modelType,
                      history: [...chatMessages, userMessage]
                  }),
              });
              const data = await response.json();
              const aiMessage = { type: 'ai', message: data.response || 'Sorry, I could not process your question.', timestamp: new Date().toLocaleTimeString() };
              setChatMessages(prev => [...prev, aiMessage]);
          } catch (err) {
              console.error('AI chat error:', err);
              const errorMessage = { type: 'ai', message: '❌ **Error:** Could not connect to AI assistant.', timestamp: new Date().toLocaleTimeString() };
              setChatMessages(prev => [...prev, errorMessage]);
          } finally {
              setIsAskingAI(false);
          }
      };
      ask();
  };

  // Helper function to check if an issue is fixed
  const isIssueFixed = (issueType, issueIndex) => {
    const issueId = `${issueType}-${issueIndex}`;
    return fixedIssues.has(issueId);
  };

  // Function to fix an individual issue
  const fixIssue = async (issue, issueType, issueIndex) => {
    const issueId = `${issueType}-${issueIndex}`;
    
    if (fixingIssues[issueId]) {
      return; // Already fixing this issue
    }

    setFixingIssues(prev => ({ ...prev, [issueId]: true }));

    try {
      console.log('Fixing issue:', issue);
      
      // Prepare the issue data for the API
      const issueData = {
        type: issueType,
        description: typeof issue === 'string' ? issue : 
                    issue.description || issue.title || issue.pattern || issue.message || 'Security issue',
        file: issue.file || issue.filename || null,
        line: issue.line || issue.line_number || null,
        severity: issue.severity || 'Medium',
        code_snippet: issue.code_snippet || issue.match || null,
        rule_id: issue.rule_id || null,
        category: issue.category || issueType
      };

      const response = await fetch('http://localhost:8000/propose-fix', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo_url: repoUrl.trim(),
          issue: issueData,
          branch_name: "main"
        }),
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        // Add the issue to fixed issues set to remove it from display
        setFixedIssues(prev => new Set(prev).add(issueId));
        
        let successMessage = '';
        
        if (data.pull_request && data.pull_request.url) {
          // Successful pull request created
          successMessage = `✅ **Pull Request Created!**\n\n🔧 **Fixed:** ${issueData.description}\n📁 **File:** ${issueData.file || 'Multiple files'}\n\n🔗 **Pull Request:** [#${data.pull_request.number} - ${data.pull_request.title}](${data.pull_request.url})\n📝 **Branch:** ${data.pull_request.branch}\n\n💾 **Changes Applied:**\n${data.fix_details?.changes_made?.join('\n') || 'Security fix applied'}\n\n🎯 **Next Steps:**\n- Review the pull request\n- Test the changes\n- Merge when ready`;
        } else if (data.fix_type === 'fork_required') {
          // Fork workflow required
          successMessage = `🍴 **Fork Required for Contribution**\n\n🔧 **Fix Generated:** ${issueData.description}\n📁 **File:** ${issueData.file || 'Multiple files'}\n\n⚠️ **Action Required:** Repository requires forking to contribute\n\n📋 **Fork Instructions:**\n${data.fork_instructions?.join('\n') || ''}\n\n💾 **Proposed Changes:**\n${data.fix_details?.changes_made?.join('\n') || 'Security fix generated'}\n\n📝 **Manual Fix Instructions:**\n${data.manual_fix_instructions || 'Apply the fix manually'}`;
        } else if (data.fix_type === 'local_suggestion') {
          // Local fix suggestion only
          successMessage = `🔧 **Fix Generated (Local)**\n\n⚠️ **Read-only Repository:** ${data.access_limitation}\n📁 **File:** ${issueData.file || 'Multiple files'}\n\n💾 **Suggested Changes:**\n${data.fix_details?.changes_made?.join('\n') || 'Security fix generated'}\n\n📋 **Manual Steps:**\n${data.suggested_actions?.join('\n') || ''}\n\n📝 **Instructions:**\n${data.manual_fix_instructions || 'Apply the fix manually'}`;
        } else {
          // Default success message
          successMessage = `✅ **Issue Fixed Successfully!**\n\n🔧 **Fixed:** ${issueData.description}\n📁 **File:** ${issueData.file || 'Multiple files'}\n\n💾 **Changes Applied:**\n${data.fix_details?.changes_made?.join('\n') || 'Security fix applied'}\n\n🌐 **View changes:** The fix has been applied to your repository files.\n\n🎯 **Issue removed from display**`;
        }
        
        // Show success message
        setChatMessages(prev => [...prev, {
          type: 'ai',
          message: successMessage,
          timestamp: new Date().toLocaleTimeString()
        }]);

        // Show code comparison if available
        if (data.code_comparison && (data.code_comparison.original_content || data.code_comparison.fixed_content)) {
          setChatMessages(prev => [...prev, {
            type: 'ai',
            message: `📊 **Code Comparison**\n\n**Original Content:**\n\`\`\`\n${data.code_preview?.original_preview || data.code_comparison.original_content.substring(0, 500)}\n\`\`\`\n\n**Fixed Content:**\n\`\`\`\n${data.code_preview?.fixed_preview || data.code_comparison.fixed_content.substring(0, 500)}\n\`\`\`\n\n📈 **Statistics:**\n- Length: ${data.code_comparison.content_length_before} → ${data.code_comparison.content_length_after} characters\n- Change: ${data.code_comparison.character_changes >= 0 ? '+' : ''}${data.code_comparison.character_changes} characters`,
            timestamp: new Date().toLocaleTimeString()
          }]);
        }

        // Optionally show the AI sidebar to display the success message
        setShowAISidebar(true);
      } else {
        throw new Error(data.error || 'Failed to fix issue');
      }
    } catch (error) {
      console.error('Error fixing issue:', error);
      
      // Show error message in chat
      setChatMessages(prev => [...prev, {
        type: 'ai', 
        message: `❌ **Failed to fix issue**\n\n🔧 **Issue:** ${typeof issue === 'string' ? issue : issue.description || 'Security issue'}\n📁 **File:** ${issue.file || issue.filename || 'Unknown'}\n\n⚠️ **Error:** ${error.message}\n\n💡 **Tip:** Try asking me how to manually fix this issue.`,
        timestamp: new Date().toLocaleTimeString()
      }]);

      setShowAISidebar(true);
    } finally {
      setFixingIssues(prev => ({ ...prev, [issueId]: false }));
    }
  };

  const formatSecurityScore = (score) => {
    if (score >= 80) return { color: '#22c55e', label: 'High Security' };
    if (score >= 60) return { color: '#f59e0b', label: 'Medium Security' };
    return { color: '#ef4444', label: 'Low Security' };
  };

  return (
    <PageWrapper>
      <style>
        {`
          :root {
            --primary-green: #00f5c3;
            --background-dark: #0a0a0a;
            --card-bg: rgba(26, 26, 26, 0.5);
            --card-bg-hover: rgba(36, 36, 36, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --card-border-hover: rgba(0, 245, 195, 0.5);
            --text-light: #f5f5f5;
            --text-dark: #a3a3a3;
            --input-bg: #1a1a1a;
            --input-border: #3a3a3a;
            --input-focus-border: var(--primary-green);
          }

          body {
            background-color: var(--background-dark);
            color: var(--text-light);
            font-family: sans-serif;
          }
          
          .page-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 1.5rem;
          }
          
          .content-wrapper {
            padding: 2rem 0;
          }
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
            font-size: 5rem;
            font-weight: 900;
            letter-spacing: -0.05em;
            color: var(--text-light);
            text-shadow: 0 0 15px rgba(0, 245, 195, 0.4), 0 0 30px rgba(0, 245, 195, 0.2);
            margin-bottom: 1.5rem;
            line-height: 1.1;
          }
          
          .hero-subtitle {
            font-size: 1.45rem;
            line-height: 1.75rem;
            color: var(--text-dark);
            margin-bottom: 2rem;
          }
          
          .card {
            background-color: var(--card-bg);
            backdrop-filter: blur(4px);
            border: 1px solid var(--card-border);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: left; /* Reset text-align for cards */
          }
          
          .card h3 {
            color: var(--text-light);
            margin-bottom: 1rem;
            font-size: 1.25rem;
            font-weight: 700;
          }
          
          .input-group {
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 1rem;
          }
          
          .input {
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            color: var(--text-light);
            font-size: 1rem;
            transition: all 0.3s ease;
          }
          
          .input:focus {
            outline: none;
            border-color: var(--primary-green);
            box-shadow: 0 0 0 2px rgba(0, 245, 195, 0.2);
          }
          
          .input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
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
            white-space: nowrap;
            min-width: fit-content;
          }
          
          .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
          }
          
          .btn-primary {
            background-color: var(--primary-green);
            color: #000;
          }
          
          .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 245, 195, 0.3);
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
          
          .scan-options {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-top: 1.5rem;
          }
          
          .option-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
          }
          
          .analysis-results {
            margin-right: 0; /* No sidebar space by default */
            display: grid;
            gap: 2rem;
            transition: margin-right 0.3s ease;
          }
          
          .analysis-results.with-sidebar {
            margin-right: 420px; /* Add space when sidebar is shown */
          }
          
          @media (max-width: 1200px) {
            .analysis-results, .analysis-results.with-sidebar {
              margin-right: 0 !important; /* Remove margin on smaller screens */
            }
            .ai-chat-sidebar {
                display: none !important; /* Hide fixed sidebar on smaller screens */
            }
          }
          
          .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(0, 245, 195, 0.2);
            border-top: 3px solid var(--primary-green);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
          }
          
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          
          .repo-info .info-item {
            margin-bottom: 0.75rem;
            line-height: 1.5;
          }
          
          @media (min-width: 640px) {
            .input-group {
              flex-direction: row;
            }
            
            .scan-options {
              flex-direction: row;
              justify-content: space-between;
              align-items: center;
            }
          }
          
          @media (max-width: 639px) {
            .input-group {
              flex-direction: column;
              align-items: stretch;
            }
            
            .input-group .input {
              flex: 1;
              margin-bottom: 0.5rem;
            }
            
            .input-group .btn {
              width: 100%;
            }
          }
        `}
      </style>
      <div className="content-wrapper">
        <div className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">Repository Security Analysis</h1>
            <p className="hero-subtitle">Comprehensive security analysis for GitHub repositories</p>
            
            {/* Repository Input Section - Only show when no analysis result */}
            {!analysisResult && (
              <div className="card">
                <h3>Repository Analysis</h3>
                <p style={{ color: '#a1a1aa', marginBottom: '16px', fontSize: '14px' }}>
                  Enter a GitHub repository URL. The system will automatically clean common web interface paths.
                </p>
                
                <div className="input-group">
                  <input
                    type="text"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="Enter GitHub repository URL (e.g., https://github.com/user/repo)"
                    className="input"
                    disabled={isScanning}
                    style={{ flex: 1 }}
                  />
                  <button 
                    onClick={analyzeRepository} 
                    disabled={isScanning || !repoUrl.trim()}
                    className="btn btn-secondary"
                  >
                    {isScanning ? 'Analyzing...' : 'Analyze Repository'}
                  </button>
                </div>

                {/* Example URLs */}
                <div style={{ marginTop: '12px' }}>
                  <div style={{ fontSize: '12px', color: '#a1a1aa', marginBottom: '6px' }}>
                      Example URLs (these will be automatically cleaned):
                  </div>
                  <div style={{ fontSize: '11px', color: '#6b7280', lineHeight: '1.4' }}>
                    • https://github.com/user/repo<br/>
                    • https://github.com/user/repo/tree/main<br/>
                    • https://github.com/user/repo/blob/main/README.md
                  </div>
                </div>

                <div className="scan-options">
                  <div className="option-group">
                    <label style={{ color: '#a1a1aa', marginRight: '9px'}}>AI Model:</label>
                    <select 
                      value={modelType} 
                      onChange={(e) => setModelType(e.target.value)}
                      disabled={isScanning}
                      style={{ 
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        background: 'rgba(0, 0, 0, 0.3)',
                        color: '#fafafa'
                      }}
                    >
                      <option value="fast">Fast Model (Quick Analysis)</option>
                      <option value="smart">Smart Model (Detailed Analysis)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Analyze New Repository Button - Show when analysis is complete */}
            {analysisResult && !isScanning && (
              <div className="card" style={{ textAlign: 'center', padding: '20px' }}>
                <button 
                  onClick={() => {
                    setAnalysisResult(null);
                    setRepoUrl('');
                    setError('');
                    setAnalysisLogs([]);
                    setChatMessages([]);
                    setFixedIssues(new Set());
                    setFixingIssues({});
                  }}
                  className="btn btn-secondary"
                  style={{
                    background: 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                    color: '#000',
                    fontWeight: '600',
                    padding: '12px 24px',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 8px 25px rgba(0, 245, 195, 0.4)';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = 'none';
                  }}
                >
                  🔍 Analyze New Repository
                </button>
                <p style={{ color: '#a1a1aa', fontSize: '12px', marginTop: '8px', margin: '8px 0 0 0' }}>
                  Click to analyze a different GitHub repository
                </p>
              </div>
            )}

            {/* Loading State */}
            {isScanning && (
              <div className="card">
                <h3>🔍 Analysis in Progress</h3>
                <div style={{ textAlign: 'center', padding: '20px 20px 40px' }}>
                  <div className="loading-spinner"></div>
                  <p style={{ color: '#a1a1aa', marginTop: '16px' }}>Analyzing repository... This may take a few minutes.</p>
                </div>
                
                {/* Analysis Logs */}
                {analysisLogs.length > 0 && (
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    padding: '16px',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '14px'
                  }}>
                    {analysisLogs.map((log, index) => (
                      <div key={index} style={{
                        color: log.includes('❌') ? '#ef4444' : 
                               log.includes('⚠️') ? '#f59e0b' : 
                               log.includes('✅') ? '#22c55e' : '#a1a1aa',
                        marginBottom: '4px'
                      }}>
                        {log}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && !isScanning && (
              <div className="card">
                <h3>❌ Analysis Error</h3>
                <p style={{ color: '#ef4444' }}>{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* --- ANALYSIS RESULTS AND CHAT --- */}
        {/* This block renders only when analysis is complete */}
        {analysisResult && !isScanning && (
          <>
            {/* Main content with conditional margin for sidebar */}
            <div className={`analysis-results ${showAISidebar ? 'with-sidebar' : ''}`}>

              {/* Analysis Status & Warnings */}
              {(analysisResult.warnings && Array.isArray(analysisResult.warnings) && analysisResult.warnings.length > 0) && (
                <div className="card">
                  <h3>⚠️ Analysis Warnings</h3>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {analysisResult.warnings.map((warning, index) => (
                      <div key={index} style={{
                        padding: '12px',
                        background: 'rgba(245, 158, 11, 0.1)',
                        border: '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '6px',
                        borderLeft: '4px solid #f59e0b',
                        fontSize: '14px'
                      }}>
                        {typeof warning === 'string' ? warning : 
                         typeof warning === 'object' ? JSON.stringify(warning) : 
                         String(warning)}
                      </div>
                    ))}
                  </div>
                  <p style={{ color: '#a1a1aa', fontSize: '12px', marginTop: '12px', marginBottom: '0' }}>
                    Note: Some analysis tools may have encountered issues, but core security scanning completed successfully.
                  </p>
                </div>
              )}

              {/* Analysis Errors */}
              {(analysisResult.analysis_errors && Array.isArray(analysisResult.analysis_errors) && analysisResult.analysis_errors.length > 0) && (
                <div className="card">
                  <h3>🔧 Analysis Issues</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    The following analysis tools encountered issues but partial results are still available:
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {analysisResult.analysis_errors.map((error, index) => (
                      <div key={index} style={{
                        padding: '16px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '8px',
                        borderLeft: '4px solid #ef4444'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                          <span style={{ fontSize: '16px' }}>🛠️</span>
                          <div>
                            <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>
                              Analysis Tool Error
                            </div>
                            <div style={{ fontSize: '13px', color: '#d1d5db', fontFamily: 'monospace', lineHeight: '1.4' }}>
                              {typeof error === 'string' ? error : 
                               typeof error === 'object' ? JSON.stringify(error) : 
                               String(error)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div style={{ 
                    marginTop: '16px', 
                    padding: '12px', 
                    background: 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '8px',
                    fontSize: '13px'
                  }}>
                    <strong style={{ color: '#3b82f6' }}>💡 Troubleshooting Tips:</strong>
                    <ul style={{ marginTop: '8px', paddingLeft: '20px', color: '#a1a1aa' }}>
                      <li>Windows path compatibility issues are common - this doesn't affect core scanning</li>
                      <li>Some advanced analysis features may be limited on Windows systems</li>
                      <li>Core security scanning (secrets, dependencies, file analysis) completed successfully</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Overview */}
              <div className="card">
                <h3>📊 Repository Overview</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '40px', alignItems: 'center' }}>
                  <div className="repo-info">
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Repository:</strong> 
                      <span>{analysisResult.repository_info?.name || 'Unknown'}</span>
                    </div>
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Description:</strong> 
                      <span>{analysisResult.repository_info?.description || 'No description'}</span>
                    </div>
                    <div className="info-item" style={{ marginBottom: '12px' }}>
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Language:</strong> 
                      <span>{analysisResult.repository_info?.language || 'Unknown'}</span>
                    </div>
                    <div className="info-item">
                      <strong style={{ color: '#00d4ff', minWidth: '120px', display: 'inline-block' }}>Stars:</strong> 
                      <span>{analysisResult.repository_info?.stars || 0}</span>
                    </div>
                  </div>
                  
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      background: 'rgba(0, 212, 255, 0.1)', 
                      border: '1px solid rgba(0, 212, 255, 0.2)',
                      borderRadius: '8px',
                      padding: '20px',
                      minWidth: '120px'
                    }}>
                      <div style={{ fontSize: '28px', fontWeight: '700', color: '#00d4ff' }}>
                        {analysisResult.overall_security_score || 0}
                      </div>
                      <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Security Score</div>
                    </div>
                    <div style={{ 
                      marginTop: '12px', 
                      fontWeight: '600', 
                      color: formatSecurityScore(analysisResult.overall_security_score).color 
                    }}>
                      {formatSecurityScore(analysisResult.overall_security_score).label}
                    </div>
                  </div>
                </div>
              </div>

              {/* Security Summary */}
              <div className="card">
                <h3>🔍 Security Summary</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '20px' }}>
                  {analysisResult.security_summary && (
                    <>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(34, 197, 94, 0.1)', 
                          border: '1px solid rgba(34, 197, 94, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#22c55e' }}>
                            {analysisResult.security_summary.total_files_scanned || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Files Scanned</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(239, 68, 68, 0.1)', 
                          border: '1px solid rgba(239, 68, 68, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>
                            {analysisResult.security_summary.secrets_found || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Secrets Found</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(245, 158, 11, 0.1)', 
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
                            {analysisResult.security_summary.static_issues_found || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Static Issues</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(139, 69, 19, 0.1)', 
                          border: '1px solid rgba(139, 69, 19, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#8b4513' }}>
                            {analysisResult.security_summary.vulnerable_dependencies || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Vulnerable Deps</div>
                        </div>
                      </div>
                      
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ 
                          background: 'rgba(168, 85, 247, 0.1)', 
                          border: '1px solid rgba(168, 85, 247, 0.2)',
                          borderRadius: '8px',
                          padding: '20px'
                        }}>
                          <div style={{ fontSize: '28px', fontWeight: '700', color: '#a855f7' }}>
                            {analysisResult.security_summary.code_quality_issues || 0}
                          </div>
                          <div style={{ color: '#a1a1aa', fontSize: '14px' }}>Quality Issues</div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* File Analysis & .gitignore Recommendations */}
              {analysisResult.file_security_scan && (
                <div className="card">
                  <h3>📁 File Security Analysis</h3>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.file_security_scan.sensitive_files && analysisResult.file_security_scan.sensitive_files.length > 0 && (
                      <div>
                        <h4 style={{ color: '#ef4444', fontSize: '16px', marginBottom: '12px' }}>
                          🚨 Sensitive Files Found ({analysisResult.file_security_scan.sensitive_files.length})
                        </h4>
                        <div style={{ display: 'grid', gap: '8px' }}>
                          {analysisResult.file_security_scan.sensitive_files.slice(0, 5).map((file, index) => (
                            <div key={index} style={{
                              padding: '12px',
                              background: 'rgba(239, 68, 68, 0.1)',
                              border: '1px solid rgba(239, 68, 68, 0.2)',
                              borderRadius: '8px',
                              fontFamily: 'monospace',
                              fontSize: '13px'
                            }}>
                              📄 {safeRender(file)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {analysisResult.file_security_scan.excluded_directories && analysisResult.file_security_scan.excluded_directories.length > 0 && (
                      <div>
                        <h4 style={{ color: '#22c55e', fontSize: '16px', marginBottom: '12px' }}>
                          ✅ Excluded Directories ({analysisResult.file_security_scan.excluded_directories.length})
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {analysisResult.file_security_scan.excluded_directories.map((dir, index) => (
                            <span key={index} style={{
                              padding: '4px 8px',
                              background: 'rgba(34, 197, 94, 0.1)',
                              border: '1px solid rgba(34, 197, 94, 0.2)',
                              borderRadius: '12px',
                              fontSize: '12px',
                              fontFamily: 'monospace'
                            }}>
                              📁 {safeRender(dir)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {analysisResult.file_security_scan.gitignore_recommendations && analysisResult.file_security_scan.gitignore_recommendations.length > 0 && (
                      <div>
                        <h4 style={{ color: '#f59e0b', fontSize: '16px', marginBottom: '12px' }}>
                          💡 GitIgnore Recommendations ({analysisResult.file_security_scan.gitignore_recommendations.length})
                        </h4>
                        <div style={{ 
                          background: 'rgba(245, 158, 11, 0.1)',
                          border: '1px solid rgba(245, 158, 11, 0.2)',
                          borderRadius: '8px',
                          padding: '12px',
                          fontFamily: 'monospace',
                          fontSize: '13px'
                        }}>
                          {analysisResult.file_security_scan.gitignore_recommendations.map((rec, index) => (
                            <div key={index} style={{ marginBottom: '4px' }}>
                              + {safeRender(rec)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analysisResult.recommendations && Array.isArray(analysisResult.recommendations) && analysisResult.recommendations.length > 0 && (
                <div className="card">
                  <h3>💡 Security Recommendations ({analysisResult.recommendations.length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    AI-generated security improvement suggestions:
                  </p>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.recommendations.slice(0, 10).map((rec, index) => {
                      // Ensure rec is properly handled
                      if (!rec) return null;
                      
                      return (
                        <div key={index} style={{
                          padding: '20px',
                          background: 'rgba(59, 130, 246, 0.1)',
                          border: '1px solid rgba(59, 130, 246, 0.2)',
                          borderRadius: '12px',
                          borderLeft: '4px solid #3b82f6'
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontWeight: '600', marginBottom: '8px', fontSize: '15px' }}>
                                {typeof rec === 'string' ? rec : 
                                 typeof rec === 'object' ? (rec.title || rec.description || JSON.stringify(rec).substring(0, 50) + '...') : 
                                 'Security Recommendation'}
                              </div>
                              {rec && typeof rec === 'object' && rec.file && (
                                <div style={{ 
                                  fontFamily: 'monospace', 
                                  fontSize: '12px', 
                                  color: '#a1a1aa',
                                  background: 'rgba(0, 0, 0, 0.2)',
                                  padding: '4px 8px',
                                  borderRadius: '4px',
                                  display: 'inline-block'
                                }}>
                                  📁 {String(rec.file)}
                                </div>
                              )}
                            </div>
                            {rec && typeof rec === 'object' && rec.risk && (
                              <span style={{
                                background: rec.risk === 'High' ? '#ef4444' :
                                           rec.risk === 'Medium' ? '#f59e0b' : '#6b7280',
                                color: 'white',
                                padding: '6px 12px',
                                borderRadius: '16px',
                                fontSize: '12px',
                                fontWeight: '600'
                              }}>
                                {String(rec.risk)} Risk
                              </span>
                            )}
                          </div>

                          {rec && typeof rec === 'object' && rec.pattern && (
                            <div style={{ 
                              fontSize: '13px', 
                              color: '#d1d5db', 
                              marginBottom: '8px',
                              background: 'rgba(0, 0, 0, 0.2)',
                              padding: '8px',
                              borderRadius: '6px',
                              fontFamily: 'monospace'
                            }}>
                              <strong>Pattern:</strong> {String(rec.pattern)}
                            </div>
                          )}

                          {rec && typeof rec === 'object' && rec.fix && (
                            <div style={{ 
                              fontSize: '13px', 
                              color: '#22c55e',
                              background: 'rgba(34, 197, 94, 0.1)',
                              padding: '8px',
                              borderRadius: '6px',
                              marginTop: '8px'
                            }}>
                              <strong>💡 Suggested Fix:</strong> {String(rec.fix)}
                            </div>
                          )}
                        </div>
                      );
                    }).filter(Boolean)}
                  </div>
                </div>
              )}

              {/* Secret Scan Results */}
              {analysisResult.secret_scan_results && analysisResult.secret_scan_results.filter((secret, index) => !isIssueFixed('secret', index)).length > 0 && (
                <div className="card">
                  <h3>🔐 Secrets Detection ({analysisResult.secret_scan_results.filter((secret, index) => !isIssueFixed('secret', index)).length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Potential secrets and sensitive information found in code:
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {analysisResult.secret_scan_results
                      .map((secret, index) => ({ secret, originalIndex: index }))
                      .filter(({ originalIndex }) => !isIssueFixed('secret', originalIndex))
                      .slice(0, 10)
                      .map(({ secret, originalIndex }) => (
                      <div key={originalIndex} style={{
                        padding: '16px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        borderRadius: '8px',
                        borderLeft: '4px solid #ef4444'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <div style={{ fontWeight: '600', fontSize: '14px', flex: 1 }}>
                            {secret.type || 'Potential Secret'}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              background: '#dc2626',
                              color: 'white',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: '600'
                            }}>
                              CRITICAL
                            </span>
                            <button
                              onClick={() => fixIssue(secret, 'secret', originalIndex)}
                              disabled={fixingIssues[`secret-${originalIndex}`]}
                              style={{
                                background: fixingIssues[`secret-${originalIndex}`] ? '#6b7280' : 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                                color: fixingIssues[`secret-${originalIndex}`] ? '#fff' : '#000',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '6px 12px',
                                fontSize: '11px',
                                fontWeight: '600',
                                cursor: fixingIssues[`secret-${originalIndex}`] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s ease',
                                opacity: fixingIssues[`secret-${originalIndex}`] ? 0.6 : 1
                              }}
                            >
                              {fixingIssues[`secret-${originalIndex}`] ? '🔧 Fixing...' : '🔧 Fix Issue'}
                            </button>
                          </div>
                        </div>
                        
                        {secret.file && (
                          <div style={{ 
                            fontFamily: 'monospace', 
                            fontSize: '12px', 
                            color: '#a1a1aa',
                            marginBottom: '8px'
                          }}>
                            📁 {secret.file}
                            {secret.line && ` → Line ${secret.line}`}
                          </div>
                        )}
                        
                        {secret.match && (
                          <div style={{ 
                            fontSize: '12px', 
                            color: '#d1d5db',
                            background: 'rgba(0, 0, 0, 0.3)',
                            padding: '8px',
                            borderRadius: '4px',
                            fontFamily: 'monospace'
                          }}>
                            Found: {typeof secret.match === 'string' ? 
                              secret.match.substring(0, 50) + '...' : 
                              String(secret.match).substring(0, 50) + '...'}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Static Analysis Results */}
              {analysisResult.static_analysis_results && analysisResult.static_analysis_results.filter((issue, index) => !isIssueFixed('static_analysis', index)).length > 0 && (
                <div className="card">
                  <h3>🔍 Static Analysis ({analysisResult.static_analysis_results.filter((issue, index) => !isIssueFixed('static_analysis', index)).length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Security vulnerabilities detected through static code analysis:
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    {analysisResult.static_analysis_results
                      .map((issue, index) => ({ issue, originalIndex: index }))
                      .filter(({ originalIndex }) => !isIssueFixed('static_analysis', originalIndex))
                      .slice(0, 10)
                      .map(({ issue, originalIndex }) => (
                      <div key={originalIndex} style={{
                        padding: '16px',
                        background: issue.severity === 'HIGH' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: issue.severity === 'HIGH' ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '8px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                          <div style={{ fontWeight: '600', fontSize: '14px', flex: 1 }}>
                            {safeRender(issue.rule_id || issue.description || 'Static Analysis Issue')}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              background: issue.severity === 'HIGH' ? '#ef4444' : '#f59e0b',
                              color: 'white',
                              padding: '4px 8px',
                              borderRadius: '12px',
                              fontSize: '11px',
                              fontWeight: '600'
                            }}>
                              {safeRender(issue.severity || 'MEDIUM')}
                            </span>
                            <button
                              onClick={() => fixIssue(issue, 'static_analysis', originalIndex)}
                              disabled={fixingIssues[`static_analysis-${originalIndex}`]}
                              style={{
                                background: fixingIssues[`static_analysis-${originalIndex}`] ? '#6b7280' : 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                                color: fixingIssues[`static_analysis-${originalIndex}`] ? '#fff' : '#000',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '6px 12px',
                                fontSize: '11px',
                                fontWeight: '600',
                                cursor: fixingIssues[`static_analysis-${originalIndex}`] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s ease',
                                opacity: fixingIssues[`static_analysis-${originalIndex}`] ? 0.6 : 1
                              }}
                            >
                              {fixingIssues[`static_analysis-${originalIndex}`] ? '🔧 Fixing...' : '🔧 Fix Issue'}
                            </button>
                          </div>
                        </div>
                        
                        {issue.filename && (
                          <div style={{ 
                            fontFamily: 'monospace', 
                            fontSize: '12px', 
                            color: '#a1a1aa',
                            marginBottom: '8px'
                          }}>
                            📁 {safeRender(issue.filename)}
                            {issue.line_number && ` → Line ${safeRender(issue.line_number)}`}
                          </div>
                        )}
                        
                        {issue.message && (
                          <div style={{ fontSize: '13px', color: '#d1d5db', lineHeight: '1.4' }}>
                            {safeRender(issue.message)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Code Quality Issues */}
              {analysisResult.code_quality_results && analysisResult.code_quality_results.filter((issue, index) => !isIssueFixed('code_quality', index)).length > 0 && (
                <div className="card">
                  <h3>🎯 Code Quality Issues ({analysisResult.code_quality_results.filter((issue, index) => !isIssueFixed('code_quality', index)).length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Insecure coding patterns and quality issues detected:
                  </p>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.code_quality_results
                      .map((issue, index) => ({ issue, originalIndex: index }))
                      .filter(({ originalIndex }) => !isIssueFixed('code_quality', originalIndex))
                      .slice(0, 10)
                      .map(({ issue, originalIndex }) => (
                      <div key={originalIndex} style={{
                        padding: '20px',
                        background: issue.severity === 'Critical' || issue.severity === 'High' ? 
                          'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: issue.severity === 'Critical' || issue.severity === 'High' ? 
                          '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '12px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontWeight: '600', marginBottom: '6px', fontSize: '15px' }}>
                              {safeRender(issue.pattern || issue.description || 'Code Quality Issue')}
                            </div>
                            {issue.file && (
                              <div style={{ 
                                fontFamily: 'monospace', 
                                fontSize: '12px', 
                                color: '#a1a1aa',
                                background: 'rgba(0, 0, 0, 0.2)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'inline-block'
                              }}>
                                📁 {safeRender(issue.file)}
                                {issue.line && ` → Line ${safeRender(issue.line)}`}
                              </div>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              background: issue.severity === 'Critical' ? '#dc2626' :
                                         issue.severity === 'High' ? '#ef4444' :
                                         issue.severity === 'Medium' ? '#f59e0b' : '#6b7280',
                              color: 'white',
                              padding: '6px 12px',
                              borderRadius: '16px',
                              fontSize: '12px',
                              fontWeight: '600'
                            }}>
                              {safeRender(issue.severity || 'Medium')}
                            </span>
                            <button
                              onClick={() => fixIssue(issue, 'code_quality', originalIndex)}
                              disabled={fixingIssues[`code_quality-${originalIndex}`]}
                              style={{
                                background: fixingIssues[`code_quality-${originalIndex}`] ? '#6b7280' : 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                                color: fixingIssues[`code_quality-${originalIndex}`] ? '#fff' : '#000',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '8px 12px',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: fixingIssues[`code_quality-${originalIndex}`] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s ease',
                                opacity: fixingIssues[`code_quality-${originalIndex}`] ? 0.6 : 1
                              }}
                            >
                              {fixingIssues[`code_quality-${originalIndex}`] ? '🔧 Fixing...' : '🔧 Fix Issue'}
                            </button>
                          </div>
                        </div>

                        {issue.code_snippet && (
                          <div style={{ marginTop: '12px' }}>
                            <div style={{ 
                              fontSize: '12px', 
                              color: '#a1a1aa', 
                              marginBottom: '6px',
                              fontWeight: '500'
                            }}>
                              🔍 Code Found:
                            </div>
                            <div style={{
                              background: 'rgba(0, 0, 0, 0.4)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              padding: '12px',
                              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                              fontSize: '13px',
                              color: '#e5e7eb',
                              overflowX: 'auto',
                              whiteSpace: 'pre'
                            }}>
                              {safeRender(issue.code_snippet && issue.code_snippet.length > 150 ? 
                                `${issue.code_snippet.substring(0, 150)}...` : 
                                issue.code_snippet || 'No code snippet available'
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependency Vulnerabilities */}
              {analysisResult.dependency_scan_results?.vulnerable_packages && analysisResult.dependency_scan_results.vulnerable_packages.filter((pkg, index) => !isIssueFixed('dependency', index)).length > 0 && (
                <div className="card">
                  <h3>📦 Vulnerable Dependencies ({analysisResult.dependency_scan_results.vulnerable_packages.filter((pkg, index) => !isIssueFixed('dependency', index)).length})</h3>
                  <p style={{ color: '#a1a1aa', fontSize: '14px', marginBottom: '16px' }}>
                    Dependencies with known security vulnerabilities:
                  </p>
                  <div style={{ display: 'grid', gap: '16px' }}>
                    {analysisResult.dependency_scan_results.vulnerable_packages
                      .map((pkg, index) => ({ pkg, originalIndex: index }))
                      .filter(({ originalIndex }) => !isIssueFixed('dependency', originalIndex))
                      .slice(0, 10)
                      .map(({ pkg, originalIndex }) => (
                      <div key={originalIndex} style={{
                        padding: '20px',
                        background: pkg.severity === 'Critical' || pkg.severity === 'High' ? 
                          'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                        border: pkg.severity === 'Critical' || pkg.severity === 'High' ? 
                          '1px solid rgba(239, 68, 68, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                        borderRadius: '12px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: '700', fontFamily: 'monospace', fontSize: '16px' }}>
                                {pkg.package || pkg.name || 'Unknown Package'}
                              </span>
                              {pkg.current_version && (
                                <span style={{ 
                                  color: '#a1a1aa', 
                                  fontSize: '13px',
                                  background: 'rgba(0, 0, 0, 0.2)',
                                  padding: '2px 6px',
                                  borderRadius: '4px'
                                }}>
                                  v{pkg.current_version.replace(/[>=<]/g, '')}
                                </span>
                              )}
                            </div>
                            {pkg.file && (
                              <div style={{ 
                                fontFamily: 'monospace', 
                                fontSize: '12px', 
                                color: '#a1a1aa',
                                background: 'rgba(0, 0, 0, 0.2)',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                display: 'inline-block'
                              }}>
                                📄 {pkg.file}
                              </div>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span style={{
                              background: pkg.severity === 'Critical' ? '#dc2626' :
                                         pkg.severity === 'High' ? '#ef4444' :
                                         pkg.severity === 'Medium' ? '#f59e0b' : '#6b7280',
                              color: 'white',
                              padding: '6px 14px',
                              borderRadius: '20px',
                              fontSize: '12px',
                              fontWeight: '700'
                            }}>
                              {pkg.severity || 'Unknown'}
                            </span>
                            <button
                              onClick={() => fixIssue(pkg, 'dependency', originalIndex)}
                              disabled={fixingIssues[`dependency-${originalIndex}`]}
                              style={{
                                background: fixingIssues[`dependency-${originalIndex}`] ? '#6b7280' : 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                                color: fixingIssues[`dependency-${originalIndex}`] ? '#fff' : '#000',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '8px 12px',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: fixingIssues[`dependency-${originalIndex}`] ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s ease',
                                opacity: fixingIssues[`dependency-${originalIndex}`] ? 0.6 : 1
                              }}
                            >
                              {fixingIssues[`dependency-${originalIndex}`] ? '🔧 Fixing...' : '🔧 Fix Issue'}
                            </button>
                          </div>
                        </div>

                        {pkg.advisory && (
                          <div style={{ 
                            color: '#d1d5db', 
                            fontSize: '13px', 
                            marginBottom: '12px',
                            lineHeight: '1.5',
                            background: 'rgba(0, 0, 0, 0.2)',
                            padding: '10px',
                            borderRadius: '6px'
                          }}>
                            ⚠️ <strong>Advisory:</strong> {pkg.advisory}
                          </div>
                        )}

                        {(pkg.package || pkg.name) && (
                          <div style={{ marginTop: '12px' }}>
                            <div style={{ fontSize: '12px', color: '#a1a1aa', marginBottom: '4px' }}>
                              🛠️ Quick Fix:
                            </div>
                            <div style={{
                              background: 'rgba(0, 0, 0, 0.4)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              padding: '8px 12px',
                              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                              fontSize: '12px',
                              color: '#e5e7eb'
                            }}>
                              {pkg.file?.includes('package.json') ? 
                                `npm update ${pkg.package || pkg.name}` : 
                                `pip install --upgrade ${pkg.package || pkg.name}`
                              }
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* --- ALWAYS VISIBLE AI CHAT SIDEBAR --- */}
            <div className="ai-chat-sidebar" style={{
              position: 'fixed',
              top: '120px', // Moved further down to avoid overlap with buttons
              right: '20px',
              width: window.innerWidth < 768 ? '90vw' : 'min(450px, 40vw)',
              height: '60vh', // Reduced height to 60% of viewport
              background: 'linear-gradient(135deg, rgba(10, 10, 10, 0.98) 0%, rgba(20, 20, 20, 0.98) 100%)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(0, 245, 195, 0.2)',
              borderRadius: '12px',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)'
            }}>
                {/* Compact AI Chat Header */}
                <div style={{
                  padding: '16px 16px 14px 16px',
                  borderBottom: '1px solid rgba(0, 245, 195, 0.2)',
                  background: 'linear-gradient(135deg, rgba(0, 245, 195, 0.08) 0%, rgba(0, 212, 255, 0.08) 100%)',
                  borderRadius: '12px 12px 0 0',
                  position: 'relative'
                }}>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      background: 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px'
                    }}>
                      🤖
                    </div>
                    <div>
                      <h3 style={{ margin: '0', color: '#fff', fontSize: '16px', fontWeight: '700' }}>
                        AI Security Advisor
                      </h3>
                      <p style={{ margin: '2px 0 0 0', color: '#a1a1aa', fontSize: '11px' }}>
                        Powered by RAG + Gemini AI
                      </p>
                    </div>
                  </div>
                  <p style={{ margin: '0', color: '#b1b5c3', fontSize: '10px', fontStyle: 'italic' }}>
                    💡 Ask about security findings & get fix recommendations
                  </p>
                </div>

              {/* Compact Quick Questions */}
              <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(0, 245, 195, 0.2)' }}>
                <div style={{ 
                  color: '#a1a1aa', 
                  fontSize: '10px', 
                  marginBottom: '8px',
                  fontWeight: '500',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  💡 Quick Questions
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {[
                    'Fix critical issues',
                    'Security score', 
                    'GitIgnore help',
                    'Vulnerabilities'
                  ].map((question, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickQuestion(question)}
                      disabled={isAskingAI}
                      style={{
                        padding: '4px 8px',
                        background: 'rgba(0, 245, 195, 0.1)',
                        border: '1px solid rgba(0, 245, 195, 0.3)',
                        borderRadius: '12px',
                        color: '#00f5c3',
                        fontSize: '10px',
                        fontWeight: '500',
                        cursor: isAskingAI ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s ease',
                        opacity: isAskingAI ? '0.5' : '1'
                      }}
                      onMouseEnter={(e) => {
                        if (!isAskingAI) {
                          e.target.style.background = 'rgba(0, 245, 195, 0.2)';
                          e.target.style.borderColor = 'rgba(0, 245, 195, 0.5)';
                          e.target.style.transform = 'translateY(-1px)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = 'rgba(0, 245, 195, 0.1)';
                        e.target.style.borderColor = 'rgba(0, 245, 195, 0.3)';
                        e.target.style.transform = 'translateY(0)';
                      }}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>

              {/* Compact Chat Messages Container */}
              <div style={{ 
                flex: 1,
                padding: '12px 16px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                scrollbarWidth: 'thin',
                scrollbarColor: 'rgba(0, 245, 195, 0.3) transparent'
              }}>
                {chatMessages.length === 0 ? (
                  <div style={{ 
                    color: '#71717a', 
                    textAlign: 'center',
                    padding: '40px 16px',
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column'
                  }}>
                    <div style={{ fontSize: '24px', marginBottom: '12px', opacity: '0.6' }}>💬</div>
                    <div style={{ fontSize: '12px', fontWeight: '500', marginBottom: '6px' }}>
                      Start a conversation
                    </div>
                    <div style={{ fontSize: '10px', opacity: '0.7' }}>
                      Ask about security analysis or try quick questions!
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {chatMessages.map((msg, index) => (
                      <div key={index} style={{
                        padding: '10px 12px',
                        borderRadius: '10px',
                        maxWidth: '90%',
                        lineHeight: '1.4',
                        fontSize: '12px',
                        ...(msg.type === 'user' ? {
                          background: 'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)',
                          color: '#000',
                          alignSelf: 'flex-end',
                          fontWeight: '500',
                          boxShadow: '0 2px 8px rgba(0, 245, 195, 0.3)'
                        } : {
                          background: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#e4e4e7',
                          alignSelf: 'flex-start'
                        })
                      }}>
                        {msg.type === 'assistant' && (
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '6px', 
                            marginBottom: '6px',
                            color: '#00f5c3',
                            fontSize: '10px',
                            fontWeight: '600'
                          }}>
                            🤖 AI Assistant
                          </div>
                        )}
                        <div style={{ 
                          whiteSpace: 'pre-line',
                          wordWrap: 'break-word'
                        }} dangerouslySetInnerHTML={{ __html: msg.message.replace(/\n/g, '<br />') }}>
                        </div>
                        <div style={{ 
                          fontSize: '9px', 
                          color: msg.type === 'user' ? 'rgba(0, 0, 0, 0.6)' : '#a1a1aa', 
                          marginTop: '6px',
                          opacity: 0.8,
                          textAlign: 'right'
                        }}>
                          {msg.timestamp}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {isAskingAI && (
                  <div style={{ 
                    color: '#a1a1aa', 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    padding: '10px 12px',
                    marginTop: '6px',
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '10px',
                    alignSelf: 'flex-start'
                  }}>
                    <div style={{ 
                      width: '12px', 
                      height: '12px', 
                      border: '2px solid rgba(0, 245, 195, 0.3)',
                      borderTop: '2px solid #00f5c3',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }}></div>
                    <span style={{ fontSize: '11px', fontWeight: '500' }}>AI analyzing...</span>
                  </div>
                )}
              </div>

              {/* Compact Chat Input */}
              <div style={{ 
                padding: '16px',
                borderTop: '1px solid rgba(0, 245, 195, 0.2)',
                background: 'linear-gradient(135deg, rgba(0, 245, 195, 0.05) 0%, rgba(0, 212, 255, 0.05) 100%)',
                borderRadius: '0 0 12px 12px'
              }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <input
                      type="text"
                      value={currentQuestion}
                      onChange={(e) => setCurrentQuestion(e.target.value)}
                      placeholder="Ask about security..."
                      onKeyPress={(e) => e.key === 'Enter' && askAI()}
                      disabled={!analysisResult || isAskingAI}
                      style={{
                        width: '100%',
                        background: 'rgba(0, 0, 0, 0.4)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        borderRadius: '8px',
                        padding: '10px 12px',
                        color: '#fff',
                        fontSize: '12px',
                        outline: 'none',
                        transition: 'all 0.2s ease',
                        boxSizing: 'border-box'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = 'rgba(0, 245, 195, 0.5)';
                        e.target.style.background = 'rgba(0, 0, 0, 0.6)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                        e.target.style.background = 'rgba(0, 0, 0, 0.4)';
                      }}
                    />
                  </div>
                  <button 
                    onClick={askAI} 
                    disabled={!analysisResult || isAskingAI || !currentQuestion.trim()}
                    style={{
                      background: currentQuestion.trim() && !isAskingAI ? 
                        'linear-gradient(135deg, #00f5c3 0%, #00d4ff 100%)' : 
                        'rgba(255, 255, 255, 0.1)',
                      border: 'none',
                      borderRadius: '8px',
                      padding: '10px 16px',
                      color: currentQuestion.trim() && !isAskingAI ? '#000' : '#71717a',
                      fontWeight: '600',
                      cursor: currentQuestion.trim() && !isAskingAI ? 'pointer' : 'not-allowed',
                      fontSize: '12px',
                      minWidth: '60px',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px'
                    }}
                    onMouseEnter={(e) => {
                      if (currentQuestion.trim() && !isAskingAI) {
                        e.target.style.transform = 'translateY(-1px)';
                        e.target.style.boxShadow = '0 4px 16px rgba(0, 245, 195, 0.4)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.transform = 'translateY(0)';
                      e.target.style.boxShadow = 'none';
                    }}
                  >
                    {isAskingAI ? (
                      <>
                        <div style={{
                          width: '12px',
                          height: '12px',
                          border: '2px solid rgba(0, 0, 0, 0.3)',
                          borderTop: '2px solid #000',
                          borderRadius: '50%',
                          animation: 'spin 1s linear infinite'
                        }}></div>
                      </>
                    ) : (
                      <>
                        <span>Ask</span>
                      </>
                    )}
                  </button>
                </div>
                <div style={{ 
                  fontSize: '10px', 
                  color: '#71717a', 
                  marginTop: '6px',
                  textAlign: 'center',
                  opacity: '0.7'
                }}>
                  💡 Be specific about vulnerabilities
                </div>
              </div>
              </div>
          </>
        )}
      </div>
    </PageWrapper>
  );
};

export default RepoAnalysisPage;
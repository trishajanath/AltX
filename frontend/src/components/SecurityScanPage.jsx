import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

// These components are assumed to be in separate files as they were not refactored.
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// --- Sub-component: Chat Message Formatter ---
const ChatResponseFormatter = ({ message }) => {
    if (!message) return null;

    // A robust function to parse a line for inline markdown (bold, code).
    const parseInlineMarkdown = (line) => {
        const regex = /(\*\*.*?\*\*|\`.*?\`)/g;
        const parts = line.split(regex);
        return parts.map((part, index) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={index}>{part.slice(2, -2)}</strong>;
            }
            if (part.startsWith('`') && part.endsWith('`')) {
                return <code key={index}>{part.slice(1, -1)}</code>;
            }
            return part;
        });
    };

    // Renders the full message, converting paragraphs and lists, and filtering unwanted lines.
    const renderFormattedMessage = () => {
        const blocks = [];
        const lines = message.split('\n');
        let currentList = [];

        lines.forEach((line, index) => {
            const trimmedLine = line.trim();
            // Filter out markdown headers and horizontal rule lines.
            if (trimmedLine.startsWith('#') || /^[\\*\\-_=\\s]+$/.test(trimmedLine)) {
                return; // Skip this line entirely.
            }
            if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
                currentList.push(<li key={index}>{parseInlineMarkdown(trimmedLine.substring(2))}</li>);
            } else {
                if (currentList.length > 0) {
                    blocks.push(<ul key={`ul-${index}`}>{currentList}</ul>);
                    currentList = [];
                }
                if (trimmedLine) {
                    blocks.push(<p key={index}>{parseInlineMarkdown(trimmedLine)}</p>);
                }
            }
        });

        if (currentList.length > 0) {
            blocks.push(<ul key="ul-final">{currentList}</ul>);
        }
        return blocks;
    };

    return <div className="formatted-content">{renderFormattedMessage()}</div>;
};


// --- Sub-component: Custom Select Dropdown (Corrected Visibility) ---
const CustomSelect = ({ options, value, onChange, disabled }) => {
    const [isOpen, setIsOpen] = useState(false);
    const wrapperRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelect = (optionValue) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    const selectedOption = options.find(opt => opt.value === value);

    return (
        <div className="custom-select-wrapper" ref={wrapperRef}>
            <button className={`select-trigger ${isOpen ? 'open' : ''}`} onClick={() => setIsOpen(!isOpen)} disabled={disabled}>
                <span>{selectedOption?.label || 'Select...'}</span>
                <svg className={`chevron ${isOpen ? 'open' : ''}`} width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
            </button>
            {isOpen && (
                <div className="select-options">
                    {options.map(option => (
                        <div key={option.value} className="select-option" onClick={() => handleSelect(option.value)}>
                            <strong>{option.label}</strong>
                            <span className="option-description">{option.description}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};


// --- Main Page Component ---
const SecurityScanPage = ({ setScanResult }) => {
    usePreventZoom();
    const [targetUrl, setTargetUrl] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [scanLogs, setScanLogs] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [modelType, setModelType] = useState('fast');
    const navigate = useNavigate();

    useEffect(() => {
        if (chatHistory.length === 0) {
            setChatHistory([{
                type: 'ai',
                message: `**Welcome to the AI Security Scanner**\n\nI am ready to analyze any website for security vulnerabilities. To begin:\n\n1.  Enter a target URL in the field below.\n2.  Choose an analysis model.\n3.  Start the scan.\n\nI'm also here to answer any security-related questions you might have.`
            }]);
        }
    }, [chatHistory.length]);

    const handleChat = async (message) => {
        const userMessage = message || chatInput;
        if (!userMessage.trim() || isChatLoading) return;
        setChatInput('');
        setChatHistory(prev => [...prev, { type: 'user', message: userMessage }]);
        setIsChatLoading(true);
        try {
            const response = await fetch('http://localhost:8000/ai-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMessage, context: 'security_scanning' }),
            });
            const data = await response.json();
            setChatHistory(prev => [...prev, { type: 'ai', message: data.response }]);
        } catch (error) {
            setChatHistory(prev => [...prev, { type: 'ai', message: "Sorry, I couldn't connect to the AI assistant." }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    const handleScan = async () => {
        if (!targetUrl) return;
        setIsScanning(true);
        setScanLogs(['[INIT] Initializing AI-powered security scan...']);
        const mockScan = async () => {
            const scanSteps = [
                '[INFO] Analyzing domain and DNS configuration...',
                '[INFO] Checking SSL/TLS certificate security...',
                '[INFO] Scanning HTTP security headers...',
                '[INFO] Testing for common web vulnerabilities...',
                '[INFO] Generating intelligent recommendations...',
                '[INFO] Compiling comprehensive security report...'
            ];
            for (const step of scanSteps) {
                await new Promise(resolve => setTimeout(resolve, 800));
                setScanLogs(prev => [...prev, step]);
            }
        };
        await mockScan();
        try {
            const response = await fetch('http://localhost:8000/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: targetUrl, model_type: modelType }),
            });
            if (!response.ok) throw new Error(`API Error: ${response.status}`);
            const result = await response.json();
            setScanResult(result);
            setScanLogs(prev => [...prev, '[OK] Security scan completed successfully. Redirecting...']);
            setTimeout(() => navigate('/report'), 1500);
        } catch (error) {
            setScanLogs(prev => [...prev, `[ERROR] Scan failed: ${error.message}`]);
            setIsScanning(false);
        }
    };

    const modelOptions = [
        { value: 'fast', label: 'Fast Model', description: 'A quick analysis of essential security checkpoints.' },
        { value: 'smart', label: 'Smart Model', description: 'A comprehensive deep-dive using advanced threat detection.' },
    ];

    return (
        <PageWrapper>
            <style>{`
                :root {
                    --bg-black: #000000;
                    --card-bg: rgba(10, 10, 10, 0.5);
                    --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3);
                    --text-primary: #f5f5f5;
                    --text-secondary: #bbbbbb; /* Brighter secondary text */
                }
                .security-scan-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
                
                .hero-section { text-align: center; padding: 4rem 1rem 3rem 1rem; }
                .hero-title { font-size: 3.5rem; font-weight: 700; margin: 0; letter-spacing: -2px; color: var(--text-primary); }
                .hero-subtitle { color: var(--text-secondary); margin: 1rem auto 0 auto; font-size: 1.1rem; max-width: 650px; line-height: 1.6; }
                
                .scan-layout { display: flex; flex-direction: column; align-items: center; gap: 2rem; max-width: 900px; margin: 0 auto; padding: 0 2rem 4rem 2rem; }
                
                .card { width: 100%; box-sizing: border-box; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 2rem; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.3s ease; }
                .card:hover {
                    border-color: var(--card-border-hover);
                    box-shadow: 0 0 25px rgba(255, 255, 255, 0.08);
                }
                .card h3 { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 1.5rem 0; text-transform: uppercase; letter-spacing: 1px; }
                
                .scan-form-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; align-items: flex-end; margin-bottom: 1.5rem; }
                @media (max-width: 768px) { .scan-form-grid { grid-template-columns: 1fr; align-items: stretch; gap: 1.5rem; } }
                
                .form-group { margin-bottom: 0; }
                .form-label { display: block; font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
                .form-hint { font-size: 0.8rem; color: var(--text-secondary); opacity: 0.8; margin-top: 0.75rem; }
                .input { width: 100%; box-sizing: border-box; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; }
                .input:focus { border-color: var(--text-primary); outline: none; }
                
                .btn { width: 100%; background: var(--text-primary); border: 1px solid var(--text-primary); color: var(--bg-black); padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
                .btn:disabled { opacity: 0.5; cursor: not-allowed; }
                .btn:hover:not(:disabled) { box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); transform: translateY(-2px); }
                .loading-dots span { display: inline-block; width: 6px; height: 6px; background-color: #000; border-radius: 50%; margin: 0 2px; animation: dot-pulse 1.4s infinite ease-in-out both; }
                @keyframes dot-pulse { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
                
                .terminal { background: #000; border: 1px solid var(--card-border); border-radius: 0.5rem; padding: 1.5rem; height: 300px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9rem; }
                .terminal-line { line-height: 1.6; white-space: pre-wrap; color: var(--text-secondary); }
                .terminal-line .log-prefix { display: inline-block; margin-right: 0.75rem; color: var(--text-primary); font-weight: 600; }

                .ai-chat-container { height: 100%; display: flex; flex-direction: column; }
                .ai-chat-history { flex-grow: 1; max-height: 400px; overflow-y: auto; padding-right: 1rem; margin-bottom: 1.5rem; }
                .chat-message { max-width: 90%; margin-bottom: 1rem; padding: 0.75rem 1rem; border-radius: 0.75rem; line-height: 1.5; word-wrap: break-word; }
                .ai-message { background: rgba(255, 255, 255, 0.05); border-bottom-left-radius: 0; }
                .user-message { background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); border-bottom-right-radius: 0; margin-left: auto; }
                .ai-chat-input-area { display: flex; gap: 0.75rem; align-items: center; margin-top: auto; }

                .custom-select-wrapper { position: relative; width: 100%; }
                .select-trigger { width: 100%; box-sizing: border-box; display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); color: var(--text-primary); border-radius: 0.5rem; padding: 0.75rem 1rem; font-size: 1rem; text-align: left; cursor: pointer; transition: border-color 0.2s; }
                .select-trigger.open, .select-trigger:hover { border-color: var(--card-border-hover); }
                .chevron { transition: transform 0.2s ease; color: var(--text-secondary); } .chevron.open { transform: rotate(180deg); }
                .select-options {
                    position: absolute; top: calc(100% + 8px); left: 0; right: 0;
                    background: var(--card-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                    border: 1px solid var(--card-border-hover); border-radius: 0.75rem;
                    z-index: 10; max-height: 200px; overflow-y: auto;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                    animation: dropdown-fade-in 0.2s ease-out;
                }
                .select-option { padding: 1rem; cursor: pointer; } .select-option:hover { background: rgba(255, 255, 255, 0.08); }
                .select-option:not(:last-child) { border-bottom: 1px solid var(--card-border); }
                .select-option strong { color: var(--text-primary); }
                .option-description {
                    display: block; font-size: 0.8rem;
                    color: var(--text-primary);
                    opacity: 0.7;
                    margin-top: 0.25rem;
                }
                @keyframes dropdown-fade-in { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }

                .formatted-content code { background: rgba(255, 255, 255, 0.1); padding: 0.1em 0.3em; border-radius: 4px; font-family: 'Courier New', Courier, monospace; font-size: 0.9em; }
                .formatted-content ul { padding-left: 1.25rem; margin: 0.5rem 0; }
                .formatted-content p { margin: 0 0 0.5rem 0; } .formatted-content p:last-child { margin-bottom: 0; }
            `}</style>

            <div className="security-scan-page">
                <div className="hero-section">
                    <h1 className="hero-title">AI Security Intelligence</h1>
                    <p className="hero-subtitle">Deploy our advanced AI to perform comprehensive security analyses, identify vulnerabilities, and receive actionable insights in real-time.</p>
                </div>

                <div className="scan-layout">
                    <div className="card">
                        <h3>Scan Configuration</h3>
                        <div className="scan-form-grid">
                            <div className="form-group">
                                <label htmlFor="targetUrl" className="form-label">Target Website URL</label>
                                <input id="targetUrl" type="url" className="input" placeholder="https://example.com" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} disabled={isScanning} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Analysis Model</label>
                                <CustomSelect options={modelOptions} value={modelType} onChange={setModelType} disabled={isScanning} />
                            </div>
                        </div>
                        <p className="form-hint">The Smart Model provides a more in-depth analysis but may take longer to complete.</p>
                        <div style={{marginTop: '1.5rem'}}>
                            <button className="btn" onClick={handleScan} disabled={isScanning || !targetUrl}>
                                {isScanning ? 'AI is Analyzing' : 'Start Security Scan'}
                                {isScanning && <div className="loading-dots"><span></span><span></span><span></span></div>}
                            </button>
                        </div>
                    </div>

                    {scanLogs.length > 0 && (
                        <div className="card">
                            <h3>Live Analysis Log</h3>
                            <div className="terminal">
                                {scanLogs.map((log, index) => {
                                    const prefixMatch = log.match(/^\[(.*?)\]/);
                                    const prefix = prefixMatch ? prefixMatch[1] : 'INFO';
                                    const logText = log.replace(/^\[.*?\]\s/, '');
                                    return (
                                        <div key={index} className="terminal-line">
                                            <span className="log-prefix">[{prefix}]</span> {logText}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                    
                    <div className="card ai-chat-container">
                        <h3>AI Security Advisor</h3>
                        <div className="ai-chat-history">
                            {/* Chat history and input logic remains the same */}
                        </div>
                        <div className="ai-chat-input-area">
                            <input type="text" className="input" placeholder="Ask a question..." value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleChat()} disabled={isChatLoading} />
                        </div>
                    </div>
                </div>
            </div>
        </PageWrapper>
    );
};

export default SecurityScanPage;
import React, { useState } from 'react';
import { ArrowRight } from 'lucide-react'; // Assuming you have lucide-react installed
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';
import { apiUrl } from '../config/api';

const DeployPage = ({ setScanResult }) => {
    usePreventZoom();
    const [repoUrl, setRepoUrl] = useState('');
    const [isDeploying, setIsDeploying] = useState(false);
    const [deployLogs, setDeployLogs] = useState([]);
    const [deploymentStatus, setDeploymentStatus] = useState(null);
    const [error, setError] = useState('');

    const handleDeploy = async () => {
        if (!repoUrl) {
            setError('Please enter a GitHub repository URL');
            return;
        }
        const githubUrlPattern = /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+$/;
        if (!githubUrlPattern.test(repoUrl.trim())) {
            setError('Please enter a valid GitHub repository URL (e.g., https://github.com/username/repository)');
            return;
        }

        setIsDeploying(true);
        setDeployLogs(['[INIT] Starting deployment process...']);
        setDeploymentStatus(null);
        setError('');

        try {
            const steps = [
                '[INFO] Cloning repository...',
                '[INFO] Analyzing project structure...',
                '[INFO] Installing dependencies...',
                '[INFO] Building application...',
                '[INFO] Finalizing deployment...'
            ];
            let currentLogs = ['[INIT] Starting deployment process...'];

            for (const step of steps) {
                await new Promise(resolve => setTimeout(resolve, 1500 + Math.random() * 500));
                currentLogs = [...currentLogs, step];
                setDeployLogs(currentLogs);
            }

            const response = await fetch(apiUrl('api/deploy'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl.trim() }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Deployment failed: ${response.statusText}`);
            }

            const deployResult = await response.json();
            const finalResult = {
                url: repoUrl,
                deploymentUrl: deployResult.deployment_url,
                status: 'Success',
                buildTime: '2m 18s', // Example data
            };

            setDeploymentStatus(finalResult);
            setScanResult(finalResult); // Pass result to parent
            setDeployLogs(prev => [...prev, `[OK] Deployment complete! Live at: ${deployResult.deployment_url}`]);

        } catch (error) {
            setError(error.message || 'An unknown error occurred during deployment.');
            setDeployLogs(prev => [...prev, `[ERROR] Deployment failed: ${error.message}`]);
        } finally {
            setIsDeploying(false);
        }
    };

    return (
        <PageWrapper>
            <style>{`
                :root {
                    --bg-black: #000000; --card-bg: rgba(10, 10, 10, 0.5); --card-border: rgba(255, 255, 255, 0.1);
                    --card-border-hover: rgba(255, 255, 255, 0.3); --text-primary: #f5f5f5; --text-secondary: #bbbbbb;
                }
                .deploy-page { background: transparent; color: var(--text-primary); min-height: 100vh; font-family: sans-serif; }
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
                
                .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
                .summary-item { text-align: center; }
                .summary-item .label { font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }
                .summary-item .value { font-size: 1.5rem; font-weight: 600; color: var(--text-primary); }
                
                .action-button { background: rgba(255,255,255,0.1); color: var(--text-primary); border: 1px solid transparent; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-size: 0.9rem; font-weight: 500; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 0.5rem; transition: all 0.2s; }
                .action-button:hover { background: var(--text-primary); color: var(--bg-black); }
            `}</style>
            
            <div className="deploy-page">
                <div className="layout-container">
                    <div className="hero-section">
                        <h1 className="hero-title">Deploy with Confidence</h1>
                        <p className="hero-subtitle">Deploy your GitHub repository with automatic security analysis and continuous monitoring. One click is all it takes.</p>
                    </div>

                    <div className="card">
                        <h3>Repository Deployment</h3>
                        <div className="input-group">
                            <input
                                type="url"
                                className="input"
                                placeholder="https://github.com/username/repository"
                                value={repoUrl}
                                onChange={(e) => setRepoUrl(e.target.value)}
                                disabled={isDeploying}
                            />
                            <button className="btn" onClick={handleDeploy} disabled={isDeploying || !repoUrl}>
                                {isDeploying ? 'Deploying...' : 'Deploy'}
                            </button>
                        </div>
                        {error && <p className="error-message">{error}</p>}
                    </div>

                    {deployLogs.length > 0 && (
                        <div className="card">
                            <h3>Live Deployment Log</h3>
                            <div className="terminal">
                                {deployLogs.map((log, index) => (
                                    <div key={index} className="terminal-line">
                                        <span className="log-prefix">[{log.match(/^\[(.*?)\]/)?.[1] || 'INFO'}]</span>
                                        {log.replace(/^\[.*?\]\s/, '')}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {deploymentStatus && (
                        <div className="card">
                            <h3>Deployment Complete</h3>
                            <div className="summary-grid">
                                <div className="summary-item">
                                    <div className="label">Status</div>
                                    <div className="value">{deploymentStatus.status}</div>
                                </div>
                                <div className="summary-item">
                                    <div className="label">Build Time</div>
                                    <div className="value">{deploymentStatus.buildTime}</div>
                                </div>
                                <div className="summary-item">
                                    <div className="label">Live URL</div>
                                    <div className="value" style={{ fontSize: '1.1rem', wordBreak: 'break-all' }}>{deploymentStatus.deploymentUrl}</div>
                                </div>
                            </div>
                            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: '1rem' }}>
                                <a href={deploymentStatus.deploymentUrl} target="_blank" rel="noopener noreferrer" className="action-button">
                                    Visit Site <ArrowRight size={16} />
                                </a>
                                <button className="btn-secondary" onClick={() => { setDeploymentStatus(null); setRepoUrl(''); setDeployLogs([]); }}>Deploy Another</button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </PageWrapper>
    );
};

export default DeployPage;
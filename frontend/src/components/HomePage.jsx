import React, { use } from 'react';
import { useNavigate } from 'react-router-dom';
import { Rocket, Shield, GitBranch, BrainCircuit, BarChart3, Zap, ArrowRight } from 'lucide-react';
import PageWrapper from './PageWrapper';
import usePreventZoom from './usePreventZoom';

// --- Feature Card Component ---
const FeatureCard = ({ icon, title, children, onClick }) => (
    <div className="feature-card" onClick={onClick}>
        <div className="feature-icon-wrapper">{icon}</div>
        <h3 className="feature-title">{title}</h3>
        <p className="feature-content">{children}</p>
        <div className="feature-learn-more">
            <span className="learn-more-group">
                Learn More <ArrowRight className="learn-more-arrow" />
            </span>
        </div>
    </div>
);

// --- Home Page Component ---
const HomePage = () => {
    usePreventZoom();
    const navigate = useNavigate();
    
    const features = [
        { icon: <Rocket size={24} />, title: 'One-Click Deploy', content: 'Deploy GitHub repositories instantly with automated builds, optimizations, and real-time security monitoring.', page: '/deploy' },
        { icon: <Shield size={24} />, title: 'Security Analysis', content: 'Comprehensive security scanning for any website. Get detailed vulnerability reports with actionable insights.', page: '/security' },
        { icon: <GitBranch size={24} />, title: 'Repository Analysis', content: 'Deep security analysis of GitHub repositories including secret detection and dependency scanning.', page: '/repo-analysis' },
        { icon: <BrainCircuit size={24} />, title: 'AI Security Advisor', content: 'Chat with our intelligent AI for personalized recommendations, threat analysis, and real-time guidance.', page: '/security' },
        { icon: <BarChart3 size={24} />, title: 'Real-time Monitoring', content: 'Continuous monitoring with instant alerts, performance metrics, and security status updates for all projects.', page: '/' },
        { icon: <Zap size={24} />, title: 'Edge Deployment', content: 'Global edge network deployment for maximum performance, automatic scaling, and zero-downtime updates.', page: '/' },
    ];

    return (
        <PageWrapper>
            <style>
                {`
                    .page-container {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 0 1rem;
                    }

                    /* --- Hero Section --- */
                    .hero-section {
                        min-height: 80vh;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        padding: 3rem 0;
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
                    .hero-title-highlight {
                        color: var(--primary-green);
                    }
                    .hero-subtitle {
                        margin-top: 1.5rem;
                        max-width: 42rem;
                        font-size: 1.125rem;
                        line-height: 1.75rem;
                        color: var(--text-dark);
                    }
                    .hero-actions {
                        margin-top: 2.5rem;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        gap: 1rem;
                        width: 100%;
                        max-width: 20rem;
                    }

                    /* --- General Section Styles --- */
                    .features-section, .stats-section {
                        padding: 6rem 0;
                    }
                    .section-header {
                        text-align: center;
                        margin-bottom: 4rem;
                    }
                    .section-title {
                        font-size: 2.25rem;
                        font-weight: 700;
                        color: var(--text-light);
                    }
                    .section-subtitle {
                        margin-top: 1rem;
                        max-width: 42rem;
                        margin-left: auto;
                        margin-right: auto;
                        font-size: 1.125rem;
                        color: var(--text-dark);
                    }

                    /* --- Features Section --- */
                    .features-grid {
                        display: grid;
                        grid-template-columns: repeat(1, 1fr);
                        gap: 2rem;
                    }
                    .feature-card {
                        background-color: var(--card-bg);
                        backdrop-filter: blur(4px);
                        border: 1px solid var(--card-border);
                        border-radius: 1rem;
                        padding: 2rem;
                        display: flex;
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 1rem;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    }
                    .feature-card:hover {
                        border-color: var(--card-border-hover);
                        background-color: var(--card-bg-hover);
                        transform: translateY(-0.5rem);
                    }
                    .feature-icon-wrapper {
                        background-color: rgba(0, 245, 195, 0.1);
                        color: var(--primary-green);
                        padding: 0.75rem;
                        border-radius: 9999px;
                        border: 1px solid rgba(0, 245, 195, 0.3);
                    }
                    .feature-title {
                        font-size: 1.25rem;
                        font-weight: 700;
                        color: var(--text-light);
                    }
                    .feature-content {
                        color: var(--text-dark);
                        line-height: 1.6;
                    }
                    .feature-learn-more {
                        margin-top: auto;
                        padding-top: 1rem;
                    }
                    .learn-more-group {
                        color: var(--primary-green);
                        font-weight: 600;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }
                    .learn-more-arrow {
                        width: 1rem;
                        height: 1rem;
                        transition: transform 0.3s ease;
                    }
                    .feature-card:hover .learn-more-arrow {
                        transform: translateX(0.25rem);
                    }

                    /* --- Stats Section --- */
                    .stats-card {
                        background-color: var(--card-bg);
                        backdrop-filter: blur(4px);
                        border: 1px solid var(--card-border);
                        border-radius: 1rem;
                        padding: 3rem 2rem;
                        text-align: center;
                    }
                    .stats-grid {
                        margin-top: 2.5rem;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        gap: 2rem;
                    }
                    .stat-item {
                        text-align: center;
                    }
                    .stat-value {
                        font-size: 2.25rem;
                        font-weight: 700;
                        color: var(--primary-green);
                    }
                    .stat-label {
                        margin-top: 0.25rem;
                        font-size: 0.875rem;
                        color: var(--text-dark);
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    }
                    .stat-divider {
                        display: none;
                    }
                    
                    /* --- Responsive Design --- */
                    @media (min-width: 640px) {
                        .hero-title {
                            font-size: 4.5rem;
                        }
                        .hero-subtitle {
                            font-size: 1.25rem;
                        }
                        .hero-actions {
                            flex-direction: row;
                            max-width: none;
                        }
                        .features-grid {
                            grid-template-columns: repeat(2, 1fr);
                        }
                        .stats-grid {
                            flex-direction: row;
                            gap: 4rem;
                        }
                        .stat-divider {
                            display: block;
                            width: 1px;
                            height: 3rem;
                            background-color: var(--card-border);
                        }
                        .section-title {
                           font-size: 3rem;
                        }
                        .stat-value {
                           font-size: 3rem;
                        }
                    }

                    @media (min-width: 1024px) {
                        .features-grid {
                            grid-template-columns: repeat(3, 1fr);
                        }
                        .hero-title {
                            font-size: 6rem;
                        }
                    }
                `}
            </style>
            <div className="page-container">
                <div className="content-wrapper">
                    {/* Hero Section */}
                    <section className="hero-section">
                        <h1 className="hero-title">
                            Deploy with AI Confidence
                        </h1>
                        <p className="hero-subtitle">
                            One-click GitHub deployments with real-time AI security analysis. Monitor vulnerabilities, get intelligent recommendations, and chat with our AI security advisor.
                        </p>
                        <div className="hero-actions">
                            <button onClick={() => navigate('/deploy')} className="btn btn-secondary">
                                 Deploy Project
                            </button>
                            <button onClick={() => navigate('/security')} className="btn btn-secondary">
                                 Security Scan
                            </button>
                        </div>
                    </section>

                    {/* Features Section */}
                    <section className="features-section">
                        <div className="section-header">
                            <h2 className="section-title">An All-in-One Platform</h2>
                            <p className="section-subtitle">
                                Everything you need to build, deploy, and secure your applications with confidence.
                            </p>
                        </div>
                        <div className="features-grid">
                            {features.map((feature, index) => (
                                <FeatureCard key={index} icon={feature.icon} title={feature.title} onClick={() => navigate(feature.page)}>
                                    {feature.content}
                                </FeatureCard>
                            ))}
                        </div>
                    </section>

                    {/* Stats Section */}

                </div>
            </div>
        </PageWrapper>
    );
};

export default HomePage;

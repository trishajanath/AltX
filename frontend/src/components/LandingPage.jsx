import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MarketingNavBar from './MarketingNavBar';
import VoiceChatInterface from './VoiceChatInterface';
import PageWrapper from './PageWrapper';
import { ArrowRight, X, Check } from 'lucide-react';

// --- YC-Style High-Conviction Landing Page ---
const VexelLandingPage = () => {
    const navigate = useNavigate();

    // Check authentication status on mount and redirect if logged in
    useEffect(() => {
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth');
        const userEmail = urlParams.get('user');
        
        if (authStatus === 'success' && userEmail) {
            localStorage.setItem('user', JSON.stringify({ email: userEmail }));
            localStorage.setItem('isAuthenticated', 'true');
            navigate('/voice-chat');
        } else {
            const storedAuth = localStorage.getItem('isAuthenticated');
            if (storedAuth === 'true') {
                navigate('/voice-chat');
            }
        }
    }, [navigate]);

    return (
        <PageWrapper>
            {/* Marketing Navigation Bar */}
            <MarketingNavBar />

            {/* Combined Hero Section with Demo */}
            <section style={styles.heroSection}>
                <div style={styles.heroContainer}>
                    <h1 style={styles.problemHeadline}>
                        Stop Wasting Months Talking to Developers.
                    </h1>
                    <p style={styles.solutionSubheadline}>
                        XVERTA is your 24/7 AI engineer. Speak your vision. Watch it build. Deploy in minutes.
                    </p>
                </div>
                
                {/* Interactive Demo - The "Magic" Moment */}
                <div style={styles.demoContainer}>
                    <VoiceChatInterface isDemo={true} />
                </div>
            </section>

            {/* Proof of Validation Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.proofCard}>
                        <h2 style={styles.proofHeadline}>Built After Talking to 20+ Founders</h2>
                        <p style={styles.proofText}>
                            We interviewed founders from startups and already established businessmen in India and the USA. 
                            Their biggest pain: <strong>the communication gap between founders and developers.</strong> 
                            <br /><br />
                            XVERTA eliminates that gap completely.
                        </p>
                    </div>
                </div>
            </section>

            {/* Before & After Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.beforeAfterGrid}>
                        {/* Before Column */}
                        <div style={styles.beforeCard}>
                            <div style={styles.beforeBadge}>
                                <X size={16} style={{ marginRight: '6px' }} />
                                Before XVERTA
                            </div>
                            <ul style={styles.beforeAfterList}>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    2–8 weeks for an MVP
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Thousands spent on freelancers
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Slow, painful iteration
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Lost in technical translation
                                </li>
                            </ul>
                        </div>

                        {/* After Column */}
                        <div style={styles.afterCard}>
                            <div style={styles.afterBadge}>
                                <Check size={16} style={{ marginRight: '6px' }} />
                                After XVERTA
                            </div>
                            <ul style={styles.beforeAfterList}>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    Functional app in minutes
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    Speak to generate changes
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    One-click deployment
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    AI understands your vision
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* Our Insight Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.insightCard}>
                        <h2 style={styles.insightHeadline}>
                            Non-technical founders don't need another no-code builder.
                        </h2>
                        <p style={styles.insightText}>
                            They need an AI engineer who truly understands them. XVERTA is that engineer.
                        </p>
                    </div>
                </div>
            </section>

            {/* Why Now Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.whyNowCard}>
                        <div style={styles.whyNowHeader}>
                            <h2 style={styles.whyNowHeadline}>Why Now?</h2>
                        </div>
                        <ul style={styles.whyNowList}>

                            <li style={styles.whyNowItem}>
                                <div style={styles.bulletDot}></div>
                                <p style={styles.whyNowText}>
                                    Developer costs are rising, forcing founders to find <strong>faster, cheaper ways to build</strong>
                                </p>
                            </li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Early Access CTA */}
            <section style={styles.ctaSection}>
                <div style={styles.ctaContainer}>
                    <h2 style={styles.ctaHeadline}>Ready to Build Your Vision?</h2>
                    <p style={styles.ctaSubtext}>
                        Start building for free. No credit card required.
                    </p>
                    
                    <button 
                        onClick={() => navigate('/signup')}
                        style={styles.startBuildingButton}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                        }}
                    >
                        Start Building Now
                        <ArrowRight size={20} style={{ marginLeft: '8px' }} />
                    </button>
                </div>
            </section>

            {/* Minimal Footer */}
            <footer style={styles.footer}>
                <div style={styles.footerContainer}>
                    <p style={styles.footerText}>
                        © 2025 XVERTA. Building the future of development.
                    </p>
                </div>
            </footer>
        </PageWrapper>
    );
};

// Styles object
const styles = {
    heroSection: {
        padding: '140px 0 40px',
        textAlign: 'center',
        position: 'relative',
        zIndex: 1
    },
    heroContainer: {
        maxWidth: '900px',
        margin: '0 auto 2rem',
        padding: '0 24px',
        position: 'relative',
        zIndex: 1
    },
    demoContainer: {
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0'
    },
    problemHeadline: {
        fontSize: '2.75rem',
        fontWeight: '700',
        color: 'var(--text-primary)',
        lineHeight: '1.1',
        margin: '0 0 0.75rem 0',
        letterSpacing: '-0.02em'
    },
    solutionSubheadline: {
        fontSize: '1.25rem',
        fontWeight: '400',
        color: 'var(--text-secondary)',
        lineHeight: '1.5',
        maxWidth: '700px',
        margin: '0 auto'
    },
    section: {
        padding: '80px 0',
        position: 'relative'
    },
    container: {
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '0 24px'
    },
    proofCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '2rem',
        textAlign: 'center',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    proofHeadline: {
        fontSize: '36px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        marginBottom: '16px',
        letterSpacing: '-1px'
    },
    proofText: {
        fontSize: '18px',
        color: 'var(--text-secondary)',
        lineHeight: '1.6',
        maxWidth: '700px',
        margin: '0 auto'
    },
    beforeAfterGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '32px',
        marginTop: '48px'
    },
    beforeCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '1.5rem',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    afterCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '1.5rem',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    beforeBadge: {
        display: 'inline-flex',
        alignItems: 'center',
        padding: '8px 16px',
        background: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '20px',
        color: '#ef4444',
        fontSize: '14px',
        fontWeight: '600',
        marginBottom: '24px'
    },
    afterBadge: {
        display: 'inline-flex',
        alignItems: 'center',
        padding: '8px 16px',
        background: 'rgba(34, 197, 94, 0.1)',
        border: '1px solid rgba(34, 197, 94, 0.3)',
        borderRadius: '20px',
        color: '#22c55e',
        fontSize: '14px',
        fontWeight: '600',
        marginBottom: '24px'
    },
    beforeAfterList: {
        listStyle: 'none',
        padding: 0,
        margin: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
    },
    beforeItem: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        fontSize: '16px',
        color: 'var(--text-secondary)'
    },
    afterItem: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        fontSize: '16px',
        color: 'var(--text-secondary)'
    },
    xIcon: {
        color: '#ef4444',
        flexShrink: 0,
        marginTop: '2px'
    },
    checkIcon: {
        color: '#22c55e',
        flexShrink: 0,
        marginTop: '2px'
    },
    insightCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '2rem',
        textAlign: 'center',
        maxWidth: '800px',
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    insightHeadline: {
        fontSize: '32px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        marginBottom: '16px',
        lineHeight: '1.3',
        letterSpacing: '-1px'
    },
    insightText: {
        fontSize: '20px',
        color: 'var(--text-secondary)',
        lineHeight: '1.6'
    },
    whyNowCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '2rem',
        maxWidth: '800px',
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    whyNowHeader: {
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        marginBottom: '32px',
        color: 'var(--accent)'
    },
    whyNowHeadline: {
        fontSize: '32px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        margin: 0,
        letterSpacing: '-1px'
    },
    whyNowList: {
        listStyle: 'none',
        padding: 0,
        margin: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
    },
    whyNowItem: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px'
    },
    bulletDot: {
        width: '8px',
        height: '8px',
        background: 'var(--accent)',
        borderRadius: '50%',
        flexShrink: 0,
        marginTop: '8px'
    },
    whyNowText: {
        fontSize: '18px',
        color: 'var(--text-secondary)',
        lineHeight: '1.6',
        margin: 0
    },
    ctaSection: {
        padding: '120px 0',
        position: 'relative'
    },
    ctaContainer: {
        maxWidth: '600px',
        margin: '0 auto',
        padding: '3rem 2.5rem',
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '24px',
        textAlign: 'center',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    ctaHeadline: {
        fontSize: '48px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        marginBottom: '16px',
        letterSpacing: '-1.5px'
    },
    ctaSubtext: {
        fontSize: '18px',
        color: 'var(--text-secondary)',
        marginBottom: '40px',
        lineHeight: '1.5'
    },
    startBuildingButton: {
        background: 'transparent',
        color: 'var(--text-primary)',
        border: '1px solid var(--border-color)',
        borderRadius: '25px',
        padding: '0.5rem 1rem',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease',
        whiteSpace: 'nowrap',
        minWidth: 'fit-content'
    },
    footer: {
        borderTop: '1px solid var(--border-color)',
        padding: '32px 0',
        marginTop: '80px'
    },
    footerContainer: {
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 24px',
        textAlign: 'center'
    },
    footerText: {
        fontSize: '13px',
        color: 'var(--text-secondary)',
        margin: 0
    }
};

export default VexelLandingPage;

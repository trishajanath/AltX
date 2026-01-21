import React from 'react';
import { useNavigate } from 'react-router-dom';
import MarketingNavBar from './MarketingNavBar';
import PageWrapper from './PageWrapper';
import { ArrowRight, Check, X } from 'lucide-react';

const FeaturesPage = () => {
    const navigate = useNavigate();

    return (
        <PageWrapper>
            {/* Marketing Navigation Bar */}
            <MarketingNavBar />

            {/* Hero Section */}
            <section style={styles.heroSection}>
                <div style={styles.heroContainer}>
                    <h1 style={styles.heroHeadline}>
                        Secure Code. Zero Compromise.
                    </h1>
                    <p style={styles.heroSubheadline}>
                        Generate production-ready applications with built-in compliance, encryption, and threat protection. Don't just build faster—build safer.
                    </p>
                </div>
            </section>

            {/* How It Works Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <h2 style={styles.sectionTitle}>How It Works</h2>
                    <div style={styles.stepsGrid}>
                        {/* Step 1 */}
                        <div style={styles.stepCard}>
                            <div style={styles.stepNumber}>1</div>
                            <h3 style={styles.stepTitle}>Speak Your Vision</h3>
                            <p style={styles.stepDescription}>
                                Tell XVERTA what you want to build in plain English. No technical jargon needed.
                            </p>
                        </div>

                        {/* Step 2 */}
                        <div style={styles.stepCard}>
                            <div style={styles.stepNumber}>2</div>
                            <h3 style={styles.stepTitle}>Watch It Build</h3>
                            <p style={styles.stepDescription}>
                                Our AI generates production-ready code, designs your UI, and sets up the architecture.
                            </p>
                        </div>

                        {/* Step 3 */}
                        <div style={styles.stepCard}>
                            <div style={styles.stepNumber}>3</div>
                            <h3 style={styles.stepTitle}>Deploy in Minutes</h3>
                            <p style={styles.stepDescription}>
                                One click to deploy. Your app is live and ready for users in minutes, not months.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Before & After Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <h2 style={styles.sectionTitle}>The Transformation</h2>
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
                                    Vulnerable to SQL Injection
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Data Privacy Nightmares
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Expensive Security Audits
                                </li>
                                <li style={styles.beforeItem}>
                                    <X size={18} style={styles.xIcon} />
                                    Spaghetti Code
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
                                    Auto-Sanitized Inputs
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    Built-in RBAC & Encryption
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    Real-time Threat Monitoring
                                </li>
                                <li style={styles.afterItem}>
                                    <Check size={18} style={styles.checkIcon} />
                                    Clean, Documented Code
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {/* AI Code Auditor Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.auditorCard}>
                        <h2 style={styles.auditorHeadline}>AI Code Auditor</h2>
                        <p style={styles.auditorSubheadline}>
                            Point XVERTA at any GitHub repository and get instant security analysis
                        </p>
                        <div style={styles.auditorFeatures}>
                            <div style={styles.auditorFeature}>
                                <Check size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                <span>Scans for security vulnerabilities in plain English</span>
                            </div>
                            <div style={styles.auditorFeature}>
                                <Check size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                <span>Explains risks without technical jargon</span>
                            </div>
                            <div style={styles.auditorFeature}>
                                <Check size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                <span>Suggests fixes you can understand and implement</span>
                            </div>
                            <div style={styles.auditorFeature}>
                                <Check size={20} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                                <span>Works with any codebase, any language</span>
                            </div>
                        </div>
                        <p style={styles.auditorNote}>
                            Perfect for founders who need to audit existing code or validate what their developers built.
                        </p>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section style={styles.ctaSection}>
                <div style={styles.ctaContainer}>
                    <h2 style={styles.ctaHeadline}>Ready to Build?</h2>
                    <p style={styles.ctaSubtext}>
                        Start building for free. No credit card required.
                    </p>
                    
                    <button 
                        onClick={() => navigate('/signup')}
                        style={styles.ctaButton}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-2px)';
                            e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
                        }}
                    >
                        Start Building Now
                        <ArrowRight size={20} style={{ marginLeft: '8px' }} />
                    </button>
                </div>
            </section>

            {/* Footer */}
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
        padding: '160px 0 80px',
        textAlign: 'center'
    },
    heroContainer: {
        maxWidth: '900px',
        margin: '0 auto',
        padding: '0 24px'
    },
    heroHeadline: {
        fontSize: '64px',
        fontWeight: '800',
        color: 'var(--text-primary)',
        lineHeight: '1.1',
        marginBottom: '24px',
        letterSpacing: '-2px'
    },
    heroSubheadline: {
        fontSize: '24px',
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
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '0 24px'
    },
    sectionTitle: {
        fontSize: '48px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        textAlign: 'center',
        marginBottom: '64px',
        letterSpacing: '-1.5px',
        fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace"
    },
    stepsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '32px'
    },
    stepCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '1.5rem',
        position: 'relative',
        textAlign: 'center',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    stepNumber: {
        position: 'absolute',
        top: '16px',
        right: '16px',
        width: '32px',
        height: '32px',
        background: 'rgba(102, 126, 234, 0.2)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '14px',
        fontWeight: '600',
        color: 'var(--text-primary)'
    },
    stepTitle: {
        fontSize: '24px',
        fontWeight: '600',
        color: 'var(--text-primary)',
        marginBottom: '12px'
    },
    stepDescription: {
        fontSize: '16px',
        color: 'var(--text-secondary)',
        lineHeight: '1.6'
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
    auditorCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '2rem',
        textAlign: 'center',
        maxWidth: '900px',
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    auditorHeadline: {
        fontSize: '40px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        marginBottom: '16px',
        letterSpacing: '-1px',
        fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace"
    },
    auditorSubheadline: {
        fontSize: '20px',
        color: 'var(--text-secondary)',
        marginBottom: '40px',
        lineHeight: '1.6'
    },
    auditorFeatures: {
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        marginBottom: '32px',
        textAlign: 'left',
        maxWidth: '600px',
        margin: '0 auto 32px'
    },
    auditorFeature: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        fontSize: '16px',
        color: 'var(--text-secondary)'
    },
    auditorNote: {
        fontSize: '16px',
        color: 'var(--text-secondary)',
        fontStyle: 'italic',
        marginTop: '24px'
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
        letterSpacing: '-1.5px',
        fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace"
    },
    ctaSubtext: {
        fontSize: '18px',
        color: 'var(--text-secondary)',
        marginBottom: '40px',
        lineHeight: '1.5'
    },
    ctaButton: {
        display: 'inline-flex',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: '#ffffff',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '4px',
        padding: '16px 32px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
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

export default FeaturesPage;

import React from 'react';
import { useNavigate } from 'react-router-dom';
import MarketingNavBar from './MarketingNavBar';
import PageWrapper from './PageWrapper';
import { ArrowRight } from 'lucide-react';

const PricingPage = () => {
    const navigate = useNavigate();

    return (
        <PageWrapper>
            {/* Marketing Navigation Bar */}
            <MarketingNavBar />

            {/* Hero Section */}
            <section style={styles.heroSection}>
                <div style={styles.heroContainer}>
                    <h1 style={styles.heroHeadline}>
                        Simple, Transparent Pricing
                    </h1>
                    <p style={styles.heroSubheadline}>
                        Pricing is coming soon.
                    </p>
                </div>
            </section>

            {/* Beta Announcement Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.betaCard}>
                        <h2 style={styles.betaHeadline}>
                            XVERTA is currently in a free, open Beta
                        </h2>
                        <p style={styles.betaText}>
                            Sign up today and get full access to all features. No credit card required.
                        </p>
                        <ul style={styles.featureList}>
                            <li style={styles.featureItem}>Unlimited AI-powered app generation</li>
                            <li style={styles.featureItem}>One-click deployment to production</li>
                            <li style={styles.featureItem}>AI security audits for any GitHub repo</li>
                            <li style={styles.featureItem}>Voice and text interaction with your AI engineer</li>
                            <li style={styles.featureItem}>Complete control over your codebase</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section style={styles.ctaSection}>
                <div style={styles.ctaContainer}>
                    <h2 style={styles.ctaHeadline}>Start Building For Free</h2>
                    <p style={styles.ctaSubtext}>
                        Join the Beta and be among the first to experience the future of development.
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
                        Start Building For Free
                        <ArrowRight size={20} style={{ marginLeft: '8px' }} />
                    </button>
                    
                    <p style={styles.ctaNote}>
                        No credit card required • Full feature access • Cancel anytime
                    </p>
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
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '0 24px'
    },
    betaCard: {
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
    betaHeadline: {
        fontSize: '40px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        marginBottom: '16px',
        lineHeight: '1.2',
        letterSpacing: '-1px'
    },
    betaText: {
        fontSize: '20px',
        color: 'var(--text-secondary)',
        lineHeight: '1.6',
        marginBottom: '40px'
    },
    featureList: {
        listStyle: 'none',
        padding: 0,
        margin: '0 auto',
        maxWidth: '500px',
        textAlign: 'left'
    },
    featureItem: {
        fontSize: '18px',
        color: 'var(--text-secondary)',
        padding: '12px 0',
        borderBottom: '1px solid var(--border-color)',
        lineHeight: '1.5'
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
    ctaButton: {
        display: 'inline-flex',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: '#ffffff',
        border: 'none',
        borderRadius: '25px',
        padding: '16px 32px',
        fontSize: '16px',
        fontWeight: '600',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
        marginBottom: '16px'
    },
    ctaNote: {
        fontSize: '14px',
        color: 'var(--text-secondary)',
        margin: '16px 0 0',
        opacity: 0.8
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

export default PricingPage;

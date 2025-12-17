import React from 'react';
import { useNavigate } from 'react-router-dom';
import MarketingNavBar from './MarketingNavBar';
import PageWrapper from './PageWrapper';
import { ArrowRight } from 'lucide-react';

const AboutPage = () => {
    const navigate = useNavigate();

    return (
        <PageWrapper>
            {/* Marketing Navigation Bar */}
            <MarketingNavBar />

            {/* Hero Section */}
            <section style={styles.heroSection}>
                <div style={styles.heroContainer}>
                    <h1 style={styles.heroHeadline}>
                        Our Mission: Empower Founders
                    </h1>
                </div>
            </section>

            {/* Insight Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.insightCard}>
                        <h2 style={styles.insightHeadline}>
                            Non-technical founders don't need another no-code builder. They need an AI engineer who truly understands them. XVERTA is that engineer.
                        </h2>
                    </div>
                </div>
            </section>

            {/* Story Section */}
            <section style={styles.section}>
                <div style={styles.container}>
                    <div style={styles.storyCard}>
                        <p style={styles.storyText}>
                            We're a team frustrated by the slow, expensive, and painful gap between a great idea and a live product. 
                        </p>
                        <p style={styles.storyText}>
                            We built XVERTA to eliminate the communication gap between founders and developers, turning months of iteration into minutes of conversation.
                        </p>
                        <p style={styles.storyText}>
                            After talking to 20+ founders from startups and established businesses in India and the USA, we discovered their biggest pain point wasn't technical complexity—it was the <strong>translation barrier</strong> between what they envisioned and what developers built.
                        </p>
                        <p style={styles.storyHighlight}>
                            XVERTA speaks your language, understands your vision, and builds exactly what you imagine.
                        </p>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section style={styles.ctaSection}>
                <div style={styles.ctaContainer}>
                    <h2 style={styles.ctaHeadline}>Ready to Build Your Vision?</h2>
                    <p style={styles.ctaSubtext}>
                        Join founders who are building faster, smarter, and without the headaches.
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
    section: {
        padding: '80px 0',
        position: 'relative'
    },
    container: {
        maxWidth: '1000px',
        margin: '0 auto',
        padding: '0 24px'
    },
    insightCard: {
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
    insightHeadline: {
        fontSize: '36px',
        fontWeight: '700',
        color: 'var(--text-primary)',
        lineHeight: '1.4',
        letterSpacing: '-1px'
    },
    storyCard: {
        background: 'var(--glass-bg, rgba(16, 16, 16, 0.6))',
        backdropFilter: 'blur(20px)',
        border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
        borderRadius: '16px',
        padding: '2rem',
        maxWidth: '900px',
        margin: '0 auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
    },
    storyText: {
        fontSize: '20px',
        color: 'var(--text-secondary)',
        lineHeight: '1.7',
        marginBottom: '24px'
    },
    storyHighlight: {
        fontSize: '24px',
        color: 'var(--accent)',
        fontWeight: '600',
        lineHeight: '1.6',
        marginTop: '32px',
        marginBottom: 0,
        textAlign: 'center'
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

export default AboutPage;

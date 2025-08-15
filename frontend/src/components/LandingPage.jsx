import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Code, Shield, Box } from 'lucide-react';

// --- Main Landing Page Component ---
const LandingPage = () => {
    const canvasRef = useRef(null);
    // The useNavigate hook is for client-side routing.
    // Since this is a single page, we will simulate navigation.


    // Effect for the animated "Matrix" background
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const fontSize = 16;
        let columns;
        let rainDrops = [];

        const katakana = 'アァカサタナハマヤャラワガザダバパイィキシチニヒミリヰギジヂビピウゥクスツヌフムユュルグズブヅプエェケセテネヘメレヱゲゼデベペオォコソトノホモヨョロヲゴゾドボポヴッン';
        const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const nums = '0123456789';
        const alphabet = katakana + latin + nums;

        // Handles resizing of the canvas to fit the window
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            columns = Math.floor(canvas.width / fontSize);
            rainDrops = Array(columns).fill(1);
        };

        // Main animation drawing function
        const draw = () => {
            ctx.fillStyle = 'rgba(10, 10, 10, 0.05)'; // Use a slightly off-black for a softer effect
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = '#00f5c3'; // Use the primary neon green color
            ctx.font = fontSize + 'px monospace';

            for (let i = 0; i < rainDrops.length; i++) {
                const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
                ctx.fillText(text, i * fontSize, rainDrops[i] * fontSize);

                if (rainDrops[i] * fontSize > canvas.height && Math.random() > 0.975) {
                    rainDrops[i] = 0;
                }
                rainDrops[i]++;
            }
        };

        resizeCanvas();
        const interval = setInterval(draw, 33); // Adjusted for smoother animation
        window.addEventListener('resize', resizeCanvas);

        // Cleanup function to remove listeners and interval
        return () => {
            clearInterval(interval);
            window.removeEventListener('resize', resizeCanvas);
        };
    }, []);

    // Smooth scroll functionality for navigation links
    const scrollToSection = (sectionId) => {
        const element = document.getElementById(sectionId);
        element?.scrollIntoView({ behavior: 'smooth' });
    };

    // --- Event Handlers for Buttons ---
    const navigate = useNavigate();
    
    const handleLogin = () => navigate('/login');
    const handleSignUp = () => navigate('/signup');
    const handleGetStarted = () => navigate('/signup');

    return (
        <div className="landing-container">
            {/* All styles are encapsulated within this component */}
            <style>{`
                /* --- FONT IMPORTS --- */
                @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@700&family=Inter:wght@400;500;600;700&display=swap');

                /* --- CSS VARIABLES (THEME) --- */
                :root {
                    --font-heading: 'Chakra Petch', sans-serif;
                    --font-body: 'Inter', sans-serif;
                    
                    --primary-green: #00f5c3;
                    --text-light: #e2e8f0;
                    --text-medium: #94a3b8;
                    --text-dark: #64748b;
                    --bg-dark: #0a0a0a;
                    --card-bg: rgba(16, 16, 16, 0.5);
                    --border-color: rgba(0, 245, 195, 0.15);
                    --border-color-hover: rgba(0, 245, 195, 0.4);
                }

                /* --- BASE & LAYOUT STYLES --- */
                .landing-container {
                    font-family: var(--font-body);
                    background-color: var(--bg-dark);
                    color: var(--text-light);
                    overflow-x: hidden;
                    position: relative;
                }

                .main-content {
                    padding-top: 6rem; /* Space for fixed header */
                    position: relative;
                    z-index: 2;
                }

                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                }

                /* --- BACKGROUND EFFECTS --- */
                .canvas-background {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    z-index: 0;
                    opacity: 0.2;
                    pointer-events: none;
                }
                .grid-background {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    z-index: -1;
                    background-image: 
                        linear-gradient(to right, rgba(0, 245, 195, 0.05) 1px, transparent 1px),
                        linear-gradient(to bottom, rgba(0, 245, 195, 0.05) 1px, transparent 1px);
                    background-size: 50px 50px;
                    animation: moveGrid 30s linear infinite;
                    pointer-events: none;
                }
                @keyframes moveGrid {
                    from { background-position: 0 0; }
                    to { background-position: 50px 50px; }
                }

                /* --- HEADER & NAVIGATION --- */
                .header {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    background: rgba(10, 10, 10, 0.7);
                    backdrop-filter: blur(10px);
                    z-index: 50;
                    border-bottom: 1px solid var(--border-color);
                }
                .header-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem 1.5rem;
                }
                .logo {
                    font-family: var(--font-heading);
                    font-size: 1.75rem;
                    font-weight: 700;
                    letter-spacing: 1px;
                }
                .nav {
                    display: none; /* Hidden on mobile */
                    gap: 2.5rem;
                }
                @media (min-width: 768px) { .nav { display: flex; } }
                .nav a {
                    color: var(--text-medium);
                    text-decoration: none;
                    transition: color 0.3s;
                    font-weight: 500;
                }
                .nav a:hover { color: var(--primary-green); }
                .header-buttons { display: flex; gap: 1rem; }

                /* --- BUTTON STYLES --- */
                .btn {
                    padding: 0.6rem 1.25rem;
                    border-radius: 0.375rem;
                    font-size: 0.9rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    border: 1px solid transparent;
                }
                .btn-ghost {
                    background: transparent;
                    color: var(--text-medium);
                }
                .btn-ghost:hover { background: rgba(255, 255, 255, 0.05); }
                .btn-primary {
                    background: var(--primary-green);
                    color: #000;
                    border-color: var(--primary-green);
                }
                .neon-glow {
                    transition: all 0.3s ease;
                    box-shadow: 0 0 5px var(--primary-green), 0 0 10px var(--primary-green);
                }
                .neon-glow:hover {
                    box-shadow: 0 0 10px var(--primary-green), 0 0 20px var(--primary-green);
                    transform: translateY(-2px);
                }

                /* --- TYPOGRAPHY & TEXT STYLES --- */
                h1, h2, h3 { font-family: var(--font-heading); letter-spacing: 1px; text-transform: uppercase; }
                p { color: var(--text-medium); line-height: 1.7; }
                .neon-text {
                    color: var(--primary-green);
                    text-shadow: 0 0 5px var(--primary-green), 0 0 15px rgba(0, 245, 195, 0.5);
                }

                /* --- HERO SECTION --- */
                .hero { padding: 6rem 0 8rem; text-align: center; }
                .hero .brand-name {
                    font-size: 5rem;
                    line-height: 1;
                    font-weight: 700;
                }
                .hero .tagline {
                    font-size: 2.5rem;
                    line-height: 1.1;
                    margin-top: 0.5rem;
                    color: var(--text-light);
                }
                @media (min-width: 768px) {
                    .hero .brand-name { font-size: 8rem; }
                    .hero .tagline { font-size: 4rem; }
                }
                .hero p {
                    margin-top: 2rem;
                    max-width: 36rem;
                    margin-left: auto;
                    margin-right: auto;
                    font-size: 1.125rem;
                }
                .hero-cta { margin-top: 3rem; }
                .btn-hero {
                    padding: 0.8rem 2.5rem;
                    font-size: 1.125rem;
                    font-weight: 700;
                    border-radius: 0.375rem;
                }

                /* --- SECTIONS & CARDS --- */
                .section { padding: 6rem 0; }
                .section-header { text-align: center; margin-bottom: 4rem; }
                .section-title { font-size: 3rem; font-weight: 700; }
                @media (min-width: 768px) { .section-title { font-size: 3.5rem; } }
                .section-subtitle { margin-top: 1rem; color: var(--text-medium); max-width: 32rem; margin-left: auto; margin-right: auto; }

                .features-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; }
                @media (min-width: 768px) { .features-grid { grid-template-columns: repeat(3, 1fr); } }
                
                .feature-card {
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    backdrop-filter: blur(10px);
                    transition: all 0.3s ease;
                    border-radius: 1rem;
                    padding: 2rem;
                }
                .feature-card:hover {
                    transform: translateY(-5px);
                    border-color: var(--border-color-hover);
                    box-shadow: 0 0 25px rgba(0, 245, 195, 0.1);
                }
                .feature-icon-container {
                    background: rgba(0, 245, 195, 0.1);
                    border-radius: 9999px;
                    width: 3.5rem;
                    height: 3.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 1.5rem;
                }
                .feature-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--text-light); }

                /* --- ABOUT SECTION --- */
                .about-content { display: flex; flex-direction: column; align-items: center; gap: 4rem; }
                @media (min-width: 768px) { .about-content { flex-direction: row; } }
                .about-text { flex: 1; }
                .about-image { flex: 1; }
                .image-container { padding: 0.5rem; border-radius: 1rem; border: 1px solid var(--border-color-hover); }
                .team-image { border-radius: 0.75rem; width: 100%; height: auto; display: block; }

                /* --- CONTACT & FOOTER --- */
                .contact-form { margin-top: 3rem; max-width: 32rem; margin-left: auto; margin-right: auto; display: flex; flex-direction: column; gap: 1rem; }
                @media (min-width: 640px) { .contact-form { flex-direction: row; } }
                .email-input {
                    flex-grow: 1;
                    padding: 0.75rem 1rem;
                    background: #111827;
                    border: 1px solid #374151;
                    border-radius: 0.375rem;
                    color: white;
                    outline: none;
                    transition: all 0.3s;
                }
                .email-input:focus { border-color: var(--primary-green); box-shadow: 0 0 0 2px rgba(0, 245, 195, 0.2); }
                .footer { border-top: 1px solid var(--border-color); }
                .footer-content { padding: 3rem 1.5rem; text-align: center; color: var(--text-dark); }
                .social-links { display: flex; justify-content: center; gap: 1.5rem; margin-top: 1rem; }
                .social-links a { color: var(--text-dark); text-decoration: none; transition: color 0.3s; }
                .social-links a:hover { color: var(--primary-green); }

                /* --- ANIMATIONS --- */
                @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
                .fade-in { animation: fadeIn 1s ease-out 0.2s forwards; opacity: 0; }
            `}</style>
            
            <div className="grid-background"></div>
            <canvas ref={canvasRef} className="canvas-background"></canvas>

            <header className="header">
                <div className="container header-content">
                    <h1 className="logo neon-text">Xverta</h1>
                    <nav className="nav">
                        <a href="#features" onClick={(e) => { e.preventDefault(); scrollToSection('features'); }}>Features</a>
                        <a href="#about" onClick={(e) => { e.preventDefault(); scrollToSection('about'); }}>About</a>
                        <a href="#contact" onClick={(e) => { e.preventDefault(); scrollToSection('contact'); }}>Contact</a>
                    </nav>
                    <div className="header-buttons">
                        <button className="btn btn-ghost" onClick={handleLogin}>Login</button>
                        <button className="btn btn-primary neon-glow" onClick={handleSignUp}>Sign Up</button>
                    </div>
                </div>
            </header>

            <main className="main-content">
                <section id="home" className="hero container">
                    <div className="fade-in">
                        <h1 className="brand-name neon-text">xverta</h1>
                        <h2 className="tagline">Build With Security.</h2>
                        <p>
                            The all-in-one platform for Software Engineers & Cybersecurity Analysts.
                            Integrate security seamlessly into your development lifecycle.
                        </p>
                        <div className="hero-cta">
                            <button className="btn btn-hero btn-primary neon-glow" onClick={handleGetStarted}>Get Started for Free</button>
                        </div>
                    </div>
                </section>

                <section id="features" className="section">
                    <div className="container">
                        <div className="section-header fade-in">
                            <h2 className="section-title">A New Era of <span className="neon-text">DevSecOps</span></h2>
                            <p className="section-subtitle">Everything you need to ship resilient applications.</p>
                        </div>
                        <div className="features-grid">
                            <div className="feature-card fade-in" style={{ animationDelay: '0.3s' }}>
                                <div className="feature-icon-container"><Code size={28} color="var(--primary-green)" /></div>
                                <h3 className="feature-title">Secure Code IDE</h3>
                                <p>Real-time vulnerability detection and smart-fixes directly in your development environment.</p>
                            </div>
                            <div className="feature-card fade-in" style={{ animationDelay: '0.5s' }}>
                                <div className="feature-icon-container"><Shield size={28} color="var(--primary-green)" /></div>
                                <h3 className="feature-title">Automated Threat Analysis</h3>
                                <p>Leverage AI to model threats, identify attack vectors, and prioritize security efforts before deployment.</p>
                            </div>
                            <div className="feature-card fade-in" style={{ animationDelay: '0.7s' }}>
                                <div className="feature-icon-container"><Box size={28} color="var(--primary-green)" /></div>
                                <h3 className="feature-title">CI/CD Security Pipeline</h3>
                                <p>Integrate security gates into your build and release pipelines to catch issues automatically.</p>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="about" className="section">
                    <div className="container about-content">
                        <div className="about-text fade-in">
                            <h2 className="section-title">Who We Are</h2>
                            <p>
                                CodeSecure was born from the collaboration between seasoned software architects and elite cybersecurity analysts. We saw the growing divide between development speed and security rigor and decided to bridge the gap.
                            </p>
                            <p>
                                Our mission is to empower developers to be the first line of defense and provide security teams with the tools they need to succeed in a fast-paced, agile world. We believe secure code is better code.
                            </p>
                        </div>
                        <div className="about-image fade-in" style={{ animationDelay: '0.3s' }}>
                            <div className="image-container">
                                <img src="https://placehold.co/600x400/0a0a0a/00f5c3?text=Our+Team" alt="CodeSecure Team" className="team-image"/>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="contact" className="section">
                    <div className="container section-header fade-in">
                        <h2 className="section-title">Ready to <span className="neon-text">Secure</span> Your Code?</h2>
                        <p className="section-subtitle">
                            Join the waitlist to get early access and start building more secure applications today.
                        </p>
                        <div className="contact-form">
                            <input type="email" placeholder="your-email@company.com" className="email-input"/>
                            <button className="btn btn-primary neon-glow">Join Waitlist</button>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="footer">
                <div className="footer-content container">
                    <p>&copy; 2024 CodeSecure. All rights reserved.</p>
                    <div className="social-links">
                        <a href="#">Twitter</a>
                        <a href="#">LinkedIn</a>
                        <a href="#">GitHub</a>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;

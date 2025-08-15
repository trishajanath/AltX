import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
    const navigate = useNavigate();
    const canvasRef = useRef(null);
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });

    // Matrix rain effect - same as landing page
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

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        // Here you would normally handle the login logic
        console.log('Login data:', formData);
        // Redirect to home page after successful login
        navigate('/home');
    };

    const handleBackToLanding = () => {
        navigate('/');
    };

    const handleSignupRedirect = () => {
        navigate('/signup');
    };

    return (
        <div className="login-container">
            <canvas ref={canvasRef} className="canvas-background"></canvas>
            <style>{`
                .login-container {
                    min-height: 100vh;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                    color: #E0E0E0;
                    font-family: 'Inter', sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 2rem;
                    position: relative;
                }

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

                .login-card {
                    background: rgba(16, 16, 16, 0.8);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(57, 255, 20, 0.2);
                    border-radius: 1rem;
                    padding: 3rem;
                    max-width: 400px;
                    width: 100%;
                    box-shadow: 0 0 25px rgba(57, 255, 20, 0.1);
                    position: relative;
                    z-index: 2;
                }

                .login-header {
                    text-align: center;
                    margin-bottom: 2rem;
                }

                .login-title {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #39FF14;
                    text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                    margin-bottom: 0.5rem;
                }

                .login-subtitle {
                    color: #9CA3AF;
                    font-size: 1rem;
                }

                .form-group {
                    margin-bottom: 1.5rem;
                }

                .form-label {
                    display: block;
                    margin-bottom: 0.5rem;
                    font-weight: 500;
                    color: #E0E0E0;
                }

                .form-input {
                    width: 100%;
                    padding: 0.75rem 1rem;
                    background: rgba(17, 24, 39, 0.8);
                    border: 1px solid #374151;
                    border-radius: 0.5rem;
                    color: white;
                    font-size: 1rem;
                    transition: all 0.3s;
                    box-sizing: border-box;
                }

                .form-input:focus {
                    outline: none;
                    border-color: #39FF14;
                    box-shadow: 0 0 0 2px rgba(57, 255, 20, 0.2);
                }

                .form-input::placeholder {
                    color: #6B7280;
                }

                .login-button {
                    width: 100%;
                    padding: 0.875rem;
                    background: #39FF14;
                    color: #000;
                    border: none;
                    border-radius: 0.5rem;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s;
                    box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
                    margin-bottom: 1.5rem;
                }

                .login-button:hover {
                    background: #2dd611;
                    box-shadow: 0 0 20px rgba(57, 255, 20, 0.5);
                    transform: translateY(-1px);
                }

                .forgot-password {
                    text-align: center;
                    margin-bottom: 1.5rem;
                }

                .forgot-link {
                    background: transparent;
                    color: #9CA3AF;
                    border: none;
                    cursor: pointer;
                    font-size: 0.9rem;
                    text-decoration: underline;
                    transition: color 0.3s;
                }

                .forgot-link:hover {
                    color: #39FF14;
                }

                .signup-link {
                    text-align: center;
                    margin-bottom: 1.5rem;
                    color: #9CA3AF;
                }

                .signup-link button {
                    background: transparent;
                    border: none;
                    color: #39FF14;
                    cursor: pointer;
                    text-decoration: underline;
                    font-size: inherit;
                }

                .signup-link button:hover {
                    color: #2dd611;
                }

                .back-link {
                    text-align: center;
                }

                .back-button {
                    background: transparent;
                    color: #9CA3AF;
                    border: none;
                    cursor: pointer;
                    font-size: 0.9rem;
                    text-decoration: underline;
                    transition: color 0.3s;
                }

                .back-button:hover {
                    color: #39FF14;
                }

                .social-login {
                    margin-bottom: 2rem;
                }

                .divider {
                    display: flex;
                    align-items: center;
                    margin: 1.5rem 0;
                }

                .divider-line {
                    flex: 1;
                    height: 1px;
                    background: #374151;
                }

                .divider-text {
                    padding: 0 1rem;
                    color: #6B7280;
                    font-size: 0.9rem;
                }

                .social-button {
                    width: 100%;
                    padding: 0.75rem;
                    background: rgba(17, 24, 39, 0.8);
                    border: 1px solid #374151;
                    border-radius: 0.5rem;
                    color: #E0E0E0;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: all 0.3s;
                    margin-bottom: 0.75rem;
                }

                .social-button:hover {
                    border-color: #39FF14;
                    background: rgba(57, 255, 20, 0.1);
                }
            `}</style>

            <div className="login-card">
                <div className="login-header">
                    <h1 className="login-title">Welcome Back</h1>
                    <p className="login-subtitle">Sign in to your Xverta account</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label" htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            className="form-input"
                            placeholder="john.doe@example.com"
                            value={formData.email}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            className="form-input"
                            placeholder="••••••••"
                            value={formData.password}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="forgot-password">
                        <button type="button" className="forgot-link">
                            Forgot your password?
                        </button>
                    </div>

                    <button type="submit" className="login-button">
                        Sign In
                    </button>
                </form>

                <div className="divider">
                    <div className="divider-line"></div>
                    <span className="divider-text">or</span>
                    <div className="divider-line"></div>
                </div>

                <div className="social-login">
                    <button className="social-button">
                        Continue with Google
                    </button>
                    <button className="social-button">
                        Continue with GitHub
                    </button>
                </div>

                <div className="signup-link">
                    Don't have an account?{' '}
                    <button onClick={handleSignupRedirect}>
                        Sign up
                    </button>
                </div>

                <div className="back-link">
                    <button className="back-button" onClick={handleBackToLanding}>
                        ← Back to Landing Page
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;

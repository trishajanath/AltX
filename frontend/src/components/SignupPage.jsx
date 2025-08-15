import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const SignupPage = () => {
    const navigate = useNavigate();
    const canvasRef = useRef(null);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: ''
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
        // Here you would normally handle the signup logic
        console.log('Signup data:', formData);
        // Redirect to home page after successful signup
        navigate('/home');
    };

    const handleBackToLanding = () => {
        navigate('/');
    };

    return (
        <div className="signup-container">
            <canvas ref={canvasRef} className="canvas-background"></canvas>
            <style>{`
                .signup-container {
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

                .signup-card {
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

                .signup-header {
                    text-align: center;
                    margin-bottom: 2rem;
                }

                .signup-title {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #074220ff;
                    text-shadow: 0 0 10px rgba(2, 49, 22, 0.5);
                    margin-bottom: 0.5rem;
                }

                .signup-subtitle {
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

                .name-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                }

                .signup-button {
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

                .signup-button:hover {
                    background: #2dd611;
                    box-shadow: 0 0 20px rgba(57, 255, 20, 0.5);
                    transform: translateY(-1px);
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

                .login-link {
                    text-align: center;
                    margin-top: 1.5rem;
                    color: #9CA3AF;
                }

                .login-link button {
                    background: transparent;
                    border: none;
                    color: #39FF14;
                    cursor: pointer;
                    text-decoration: underline;
                    font-size: inherit;
                }

                .login-link button:hover {
                    color: #2dd611;
                }
            `}</style>

            <div className="signup-card">
                <div className="signup-header">
                    <h1 className="signup-title">Join Xverta</h1>
                    <p className="signup-subtitle">Create your account to get started</p>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="name-row">
                        <div className="form-group">
                            <label className="form-label" htmlFor="firstName">First Name</label>
                            <input
                                type="text"
                                id="firstName"
                                name="firstName"
                                className="form-input"
                                placeholder="John"
                                value={formData.firstName}
                                onChange={handleChange}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label" htmlFor="lastName">Last Name</label>
                            <input
                                type="text"
                                id="lastName"
                                name="lastName"
                                className="form-input"
                                placeholder="Doe"
                                value={formData.lastName}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

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

                    <div className="form-group">
                        <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
                        <input
                            type="password"
                            id="confirmPassword"
                            name="confirmPassword"
                            className="form-input"
                            placeholder="••••••••"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <button type="submit" className="signup-button">
                        Create Account
                    </button>
                </form>

                <div className="login-link">
                    Already have an account?{' '}
                    <button onClick={() => navigate('/home')}>
                        Sign in
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

export default SignupPage;

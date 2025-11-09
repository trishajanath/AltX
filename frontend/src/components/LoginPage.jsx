import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from './PageWrapper';

const LoginPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [isLoggingIn, setIsLoggingIn] = useState(false);

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setIsLoggingIn(true);
        setTimeout(() => {
            setIsLoggingIn(false);
            // Here you would normally handle the login logic
            console.log('Login data:', formData);
            // Redirect to home page after successful login
            navigate('/home');
        }, 1800);
    };

    const handleBackToLanding = () => {
        navigate('/');
    };

    const handleSignupRedirect = () => {
        navigate('/signup');
    };

    return (
            <div className="login-container">
                <style>{`
                    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
                    
                    .login-container {
                        font-family: 'Inter', sans-serif;
                        background: #000000;
                        color: #ffffff;
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        position: relative;
                        overflow: hidden;
                    }

                    .header {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        z-index: 50;
                        padding: 1rem 0;
                        background: rgba(0, 0, 0, 0.8);
                        backdrop-filter: blur(10px);
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    }

                    .header-content {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        max-width: 1400px;
                        margin: 0 auto;
                        padding: 0 2rem;
                    }

                    .logo {
                        font-family: 'Inter', sans-serif !important;
                        font-size: 1.5rem !important;
                        font-weight: 700 !important;
                        letter-spacing: 1px !important;
                        cursor: pointer !important;
                        color: #ffffff !important;
                        transition: color 0.3s ease !important;
                        text-decoration: none !important;
                        background: transparent !important;
                        background-image: none !important;
                        background-clip: initial !important;
                        -webkit-background-clip: initial !important;
                        -webkit-text-fill-color: #ffffff !important;
                        -webkit-text-stroke: none !important;
                        text-shadow: none !important;
                        filter: none !important;
                    }

                    .header-buttons {
                        display: flex;
                        gap: 1rem;
                        align-items: center;
                    }

                    .btn {
                        padding: 0.7rem 1.5rem;
                        border-radius: 0.5rem;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        border: 2px solid transparent;
                        font-size: 0.9rem;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        text-decoration: none;
                    }

                    .btn-primary {
                        background: transparent;
                        color: #a3a3a3;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        font-weight: 500;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        display: flex;
                        margin-left: auto;
                        margin-right: auto;
                        
                    }

                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(255, 255, 255, 0.1);
                        background: rgba(255, 255, 255, 0.05) !important;
                        color: #ffffff !important;
                        border-color: rgba(255, 255, 255, 0.5) !important;
                    }

                    .main-content {
                        flex-grow: 1;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        position: relative;
                        z-index: 2;
                        padding: 5rem 2rem 2rem;
                        min-height: 100vh;
                        box-sizing: border-box;
                    }

                    .login-card {
                        background: rgba(16, 16, 16, 0.6);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 1rem;
                        padding: 2rem;
                        max-width: 420px;
                        width: 100%;
                        backdrop-filter: blur(20px);
                        -webkit-backdrop-filter: blur(20px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                        margin: auto;
                    }

                    .login-header {
                        text-align: center;
                        margin-bottom: 1.5rem;
                    }

                    .login-title {
                        font-family: 'Inter', sans-serif;
                        font-size: 2rem;
                        font-weight: 700;
                        color: #ffffff;
                        margin-bottom: 0.5rem;
                        letter-spacing: -1px;
                    }

                    .login-subtitle {
                        color: #a3a3a3;
                        font-size: 0.95rem;
                        font-weight: 400;
                        font-family: 'Inter', sans-serif;
                    }

                    .form-group {
                        margin-bottom: 1.2rem;
                        text-align: left;
                    }

                    .form-label {
                        display: block;
                        margin-bottom: 0.4rem;
                        font-weight: 500;
                        color: #ffffff;
                        font-size: 0.85rem;
                        font-family: 'Inter', sans-serif;
                    }

                    .form-input {
                        width: 100%;
                        padding: 0.85rem 1rem;
                        background: rgba(0, 0, 0, 0.4);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 0.75rem;
                        color: #ffffff;
                        font-size: 0.95rem;
                        transition: all 0.3s ease;
                        box-sizing: border-box;
                        font-family: 'Inter', sans-serif;
                    }

                    .form-input:focus {
                        outline: none;
                        border-color: rgba(255, 255, 255, 0.5);
                        background: rgba(255, 255, 255, 0.05);
                        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
                    }

                    .form-input::placeholder {
                        color: #a3a3a3;
                    }

                    .forgot-password {
                        text-align: right;
                        margin-bottom: 1.2rem;
                    }

                    .forgot-link {
                        background: transparent;
                        color: #a3a3a3;
                        border: none;
                        cursor: pointer;
                        font-size: 0.85rem;
                        text-decoration: underline;
                        transition: color 0.3s ease;
                        font-family: 'Inter', sans-serif;
                    }

                    .forgot-link:hover {
                        color: #ffffff;
                    }

                    .login-button {
                        width: 100%;
                        padding: 0.9rem 1.5rem;
                        background: transparent;
                        color: #a3a3a3;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 0.75rem;
                        font-size: 1rem;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 1.5rem;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        font-family: 'Inter', sans-serif;
                    }

                    .login-button:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(255, 255, 255, 0.1);
                        background: rgba(255, 255, 255, 0.05);
                        color: #ffffff;
                        border-color: rgba(255, 255, 255, 0.5);
                    }

                    .divider {
                        display: flex;
                        align-items: center;
                        margin: 1.5rem 0;
                    }

                    .divider-line {
                        flex: 1;
                        height: 1px;
                        background: rgba(255, 255, 255, 0.2);
                    }

                    .divider-text {
                        padding: 0 1rem;
                        color: #a3a3a3;
                        font-size: 0.85rem;
                        font-family: 'Inter', sans-serif;
                    }

                    .social-login {
                        margin-bottom: 1.5rem;
                    }

                    .social-button {
                        width: 100%;
                        padding: 0.85rem 1rem;
                        background: rgba(0, 0, 0, 0.4);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 0.75rem;
                        color: #ffffff;
                        font-size: 0.9rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 0.8rem;
                        font-family: 'Inter', sans-serif;
                        font-weight: 500;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.75rem;
                    }

                    .social-button:hover {
                        border-color: rgba(255, 255, 255, 0.5);
                        background: rgba(255, 255, 255, 0.05);
                        transform: translateY(-1px);
                        color: #ffffff;
                    }

                    .social-icon {
                        width: 20px;
                        height: 20px;
                        flex-shrink: 0;
                    }

                    .signup-link {
                        text-align: center;
                        margin-bottom: 1rem;
                        color: #a3a3a3;
                        font-size: 0.85rem;
                        font-family: 'Inter', sans-serif;
                    }

                    .signup-link button {
                        background: transparent;
                        border: none;
                        color: #ffffff;
                        cursor: pointer;
                        text-decoration: underline;
                        font-size: inherit;
                        font-family: 'Inter', sans-serif;
                        font-weight: 500;
                        transition: color 0.3s ease;
                    }

                    .signup-link button:hover {
                        color: #ffffff;
                        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    }

                    .back-link {
                        text-align: center;
                    }

                    .back-button {
                        background: transparent;
                        color: #a3a3a3;
                        border: none;
                        cursor: pointer;
                        font-size: 0.85rem;
                        transition: color 0.3s ease;
                        font-family: 'Inter', sans-serif;
                    }

                    .back-button:hover {
                        color: #ffffff;
                    }
                    
                    .scan-bar {
                        display: block;
                        height: 3px;
                        width: 100%;
                        background: linear-gradient(90deg, #a3a3a3 0%, #ffffff 100%);
                        margin-top: 6px;
                        border-radius: 2px;
                        opacity: 0;
                        transition: opacity 0.2s;
                    }
                    .btn.animating .scan-bar {
                        opacity: 1;
                        animation: scan-move 1.2s linear infinite;
                    }
                    @keyframes scan-move {
                        0% { transform: scaleX(0); opacity: 0.5; }
                        50% { transform: scaleX(1); opacity: 1; }
                        100% { transform: scaleX(0); opacity: 0.5; }
                    }
                    @media (max-width: 768px) {
                        .header-content { padding: 0 1rem; }
                        .main-content { 
                            padding: 5rem 1rem 2rem;
                            min-height: 100vh;
                        }
                        .login-card { 
                            padding: 2rem; 
                            margin: auto;
                            max-width: none;
                            border-radius: 1rem;
                            width: 100%;
                        }
                        .login-title {
                            font-size: 2rem;
                        }
                        .login-subtitle {
                            font-size: 1rem;
                        }
                        .form-input {
                            padding: 0.875rem 1rem;
                        }
                        .login-button {
                            padding: 1rem 2rem;
                        }
                        .social-button {
                            padding: 0.875rem 1rem;
                        }
                    }
                `}</style>
                
                <header className="header">
                    <div className="header-content">
                        <div className="logo" onClick={handleBackToLanding}>XVERTA</div>
                    </div>
                </header>

                <main className="main-content">
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
                                    autoComplete="username"
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
                                    autoComplete="current-password"
                                />
                            </div>

                            <div className="forgot-password">
                                <button type="button" className="forgot-link">
                                    Forgot your password?
                                </button>
                            </div>

                            <button type="submit" className={`btn btn-primary ${isLoggingIn ? 'animating' : ''}`} disabled={isLoggingIn}>
                                {isLoggingIn ? 'Authenticating...' : 'Login'}
                                <span className="scan-bar"></span>
                            </button>
                        </form>

                        <div className="divider">
                            <div className="divider-line"></div>
                            <span className="divider-text">or</span>
                            <div className="divider-line"></div>
                        </div>

                        <div className="social-login">
                            <button
                                className="social-button"
                                                    onClick={() => window.location.href = 'http://localhost:8000/auth/google/login'}
                            >
                                <svg className="social-icon" viewBox="0 0 24 24" fill="none">
                                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                                </svg>
                                Continue with Google
                            </button>

                            <button
                                className="social-button"
                                onClick={() => window.location.href = "http://127.0.0.1:8000/auth/github/login"}
                            >
                                <svg className="social-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                                </svg>
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
                                Back to Landing Page
                            </button>
                        </div>
                    </div>
                </main>
            </div>
    );
};

export default LoginPage;


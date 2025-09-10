import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import PageWrapper from './PageWrapper';

const SignupPage = () => {
    const navigate = useNavigate();
    // Store user info if redirected from Google OAuth
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get("auth") === "success") {
            const user = params.get("user");
            const name = params.get("name");
            const avatar = params.get("avatar");
            // You can store this in localStorage, context, or state as needed
            localStorage.setItem("user", JSON.stringify({ user, name, avatar }));
            // Redirect to dashboard or home page
            navigate("/home");
        }
    }, [navigate]);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: ''
    });
    
    const [validation, setValidation] = useState({
        email: { isValid: null, message: '' },
        password: { isValid: null, message: '', strength: 0 },
        confirmPassword: { isValid: null, message: '' },
        firstName: { isValid: null, message: '' },
        lastName: { isValid: null, message: '' }
    });
    
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    // Validation functions
    const validateEmail = (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) return { isValid: null, message: '' };
        if (emailRegex.test(email)) {
            return { isValid: true, message: 'Valid email address' };
        } else {
            return { isValid: false, message: 'Please enter a valid email address' };
        }
    };

    const validatePassword = (password) => {
        if (!password) return { isValid: null, message: '', strength: 0 };
        
        let strength = 0;
        let message = '';
        
        // Check length
        if (password.length >= 8) strength += 20;
        // Check uppercase
        if (/[A-Z]/.test(password)) strength += 20;
        // Check lowercase  
        if (/[a-z]/.test(password)) strength += 20;
        // Check numbers
        if (/\d/.test(password)) strength += 20;
        // Check special characters
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 20;
        
        if (strength < 40) {
            message = 'Password is too weak';
            return { isValid: false, message, strength };
        } else if (strength < 80) {
            message = 'Password strength: Medium';
            return { isValid: true, message, strength };
        } else {
            message = 'Password strength: Strong';
            return { isValid: true, message, strength };
        }
    };

    const validateConfirmPassword = (password, confirmPassword) => {
        if (!confirmPassword) return { isValid: null, message: '' };
        if (password === confirmPassword) {
            return { isValid: true, message: 'Passwords match' };
        } else {
            return { isValid: false, message: 'Passwords do not match' };
        }
    };

    const [loading, setLoading] = useState(false);

    const validateName = (name) => {
        if (!name) return { isValid: null, message: '' };
        if (name.trim().length >= 2) {
            return { isValid: true, message: '' };
        } else {
            return { isValid: false, message: 'Must be at least 2 characters' };
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        
        setFormData({
            ...formData,
            [name]: value
        });

        // Real-time validation
        let newValidation = { ...validation };
        
        switch (name) {
            case 'email':
                newValidation.email = validateEmail(value);
                break;
            case 'password':
                newValidation.password = validatePassword(value);
                newValidation.confirmPassword = validateConfirmPassword(value, formData.confirmPassword);
                break;
            case 'confirmPassword':
                newValidation.confirmPassword = validateConfirmPassword(formData.password, value);
                break;
            case 'firstName':
                newValidation.firstName = validateName(value);
                break;
            case 'lastName':
                newValidation.lastName = validateName(value);
                break;
            default:
                break;
        }
        
        setValidation(newValidation);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true);
        setTimeout(() => {
            setLoading(false);
            // Here you would normally handle the signup logic
            console.log('Signup data:', formData);
            // Redirect to home page after successful signup
            navigate('/home');
        }, 1800);
    };

    const handleBackToLanding = () => {
        navigate('/');
    };

    const handleLoginRedirect = () => {
        navigate('/login');
    };

    return (
        <PageWrapper>
            <div className="signup-container">
                <style>{`
                    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=Inter:wght@400;500&display=swap');
                    
                    .signup-container {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                        background: transparent;
                        color: #ffffff;
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        position: relative;
                    }

                    .header {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        z-index: 50;
                        background: rgba(10, 10, 10, 0.5);
                        backdrop-filter: blur(15px);
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        height: 70px;
                        min-height: 70px;
                    }

                    .header-content {
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 1rem 2rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        height: 100%;
                        box-sizing: border-box;
                    }

                    .logo {
                        font-family: 'Chakra Petch', sans-serif !important;
                        font-size: 1.8rem !important;
                        font-weight: 700 !important;
                        letter-spacing: 2px !important;
                        color: #ffffff !important;
                        text-shadow: none !important;
                        filter: none !important;
                        -webkit-text-fill-color: #ffffff !important;
                        -webkit-text-stroke: none !important;
                        background: none !important;
                        background-color: transparent !important;
                        cursor: pointer;
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

                    .btn-ghost {
                        background: transparent;
                        color: #a3a3a3;
                        border-color: rgba(255, 255, 255, 0.2);
                    }

                    .btn-ghost:hover {
                        color: #ffffff;
                        border-color: #ffffff;
                        background: rgba(255, 255, 255, 0.1);
                    }

                    .main-content {
                        flex-grow: 1;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        position: relative;
                        z-index: 2;
                        padding: 90px 2rem 2rem 2rem;
                        min-height: 100vh;
                        box-sizing: border-box;
                    }

                    .signup-card {
                        background: rgba(16, 16, 16, 0.8);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 1.5rem;
                        padding: 2.5rem;
                        max-width: 500px;
                        width: 100%;
                        backdrop-filter: blur(20px);
                        -webkit-backdrop-filter: blur(20px);
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        margin: 0 auto;
                    }

                    .signup-header {
                        text-align: center;
                        margin-bottom: 2rem;
                    }

                    .signup-title {
                        font-family: 'Chakra Petch', sans-serif;
                        font-size: 2.5rem;
                        font-weight: 700;
                        color: #ffffff !important;
                        margin-bottom: 0.5rem;
                        letter-spacing: -1px;
                    }

                    .signup-subtitle {
                        color: #a3a3a3;
                        font-size: 1.1rem;
                        font-weight: 400;
                    }
                    .form-group {
                        margin-bottom: 1.5rem;
                        text-align: left;
                    }

                    .form-label {
                        display: block;
                        margin-bottom: 0.75rem;
                        font-weight: 600;
                        color: #ffffff;
                        font-size: 0.95rem;
                    }

                    .form-input {
                        width: 100%;
                        padding: 1rem 1.25rem;
                        background: rgba(0, 0, 0, 0.4);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 0.75rem;
                        color: #ffffff;
                        font-size: 1rem;
                        transition: all 0.3s ease;
                        box-sizing: border-box;
                        font-family: inherit;
                    }

                    .form-input:focus {
                        outline: none;
                        border-color: #ffffff;
                        background: rgba(255, 255, 255, 0.05);
                        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
                    }

                    .form-input::placeholder {
                        color: #a3a3a3;
                    }

                    .forgot-password {
                        text-align: right;
                        margin-bottom: 1.5rem;
                    }

                    .forgot-link {
                        background: transparent;
                        color: #a3a3a3;
                        border: none;
                        cursor: pointer;
                        font-size: 0.9rem;
                        text-decoration: underline;
                        transition: color 0.3s ease;
                        font-family: inherit;
                    }

                    .forgot-link:hover {
                        color: #ffffff;
                    }

                    .input-wrapper {
                        position: relative;
                        display: flex;
                        align-items: center;
                    }


                    .form-input.valid {
                        border-color: #22c55e;
                        background: rgba(34, 197, 94, 0.1);
                    }

                    .form-input.invalid {
                        border-color: #ef4444;
                        background: rgba(239, 68, 68, 0.1);
                    }

                    .form-input:focus {
                        outline: none;
                        border-color: #ffffff;
                        background: rgba(255, 255, 255, 0.05);
                        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.1);
                    }

                    .form-input.valid:focus {
                        border-color: #22c55e;
                        box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
                    }

                    .form-input.invalid:focus {
                        border-color: #ef4444;
                        box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2);
                    }

                    .validation-icon {
                        position: absolute;
                        right: 0.75rem;
                        top: 50%;
                        transform: translateY(-50%);
                        width: 1.25rem;
                        height: 1.25rem;
                        pointer-events: none;
                    }

                    .validation-icon.valid {
                        color: #22c55e;
                    }

                    .validation-icon.invalid {
                        color: #ef4444;
                    }

                    .password-toggle {
                        position: absolute;
                        right: 0.75rem;
                        top: 50%;
                        transform: translateY(-50%);
                        background: none;
                        border: none;
                        cursor: pointer;
                        padding: 0.25rem;
                        color: #a3a3a3;
                        transition: color 0.3s ease;
                    }

                    .password-toggle:hover {
                        color: #ffffff;
                    }

                    .validation-message {
                        font-size: 0.8rem;
                        margin-top: 0.5rem;
                        min-height: 1.2rem;
                        transition: all 0.3s ease;
                    }

                    .validation-message.valid {
                        color: #22c55e;
                    }

                    .validation-message.invalid {
                        color: #ef4444;
                    }

                    .password-strength-meter {
                        margin-top: 0.5rem;
                        height: 4px;
                        background: rgba(0, 0, 0, 0.1);
                        border-radius: 2px;
                        overflow: hidden;
                    }

                    .strength-bar {
                        height: 100%;
                        width: 0%;
                        transition: all 0.3s ease;
                        border-radius: 2px;
                    }

                    .strength-bar.weak {
                        width: 40%;
                        background: #ef4444;
                    }

                    .strength-bar.medium {
                        width: 70%;
                        background: #f59e0b;
                    }

                    .strength-bar.strong {
                        width: 100%;
                        background: #22c55e;
                    }

                    .login-button {
                        width: 100%;
                        padding: 1.125rem 2rem;
                        background: #ffffff;
                        color: #000000;
                        border: 2px solid #ffffff;
                        border-radius: 0.75rem;
                        font-size: 1.1rem;
                        font-weight: 700;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 2rem;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        font-family: inherit;
                    }

                    .login-button:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
                        background: #ffffff;
                        color: #000000;
                    }

                    .login-button:disabled {
                        opacity: 0.7;
                        cursor: not-allowed;
                        transform: none;
                    }

                    .name-row {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 1.5rem;
                    }



                    .divider {
                        display: flex;
                        align-items: center;
                        margin: 2rem 0;
                    }

                    .divider-line {
                        flex: 1;
                        height: 1px;
                        background: rgba(255, 255, 255, 0.2);
                    }

                    .divider-text {
                        padding: 0 1rem;
                        color: #a3a3a3;
                        font-size: 0.9rem;
                    }

                    .social-login {
                        margin-bottom: 2rem;
                    }

                    .social-icon {
                        width: 20px;
                        height: 20px;
                        flex-shrink: 0;
                    }

                    .policy-links {
                        text-align: center;
                        margin: 1.5rem 0;
                        font-size: 0.85rem;
                        color: #a3a3a3;
                        line-height: 1.4;
                    }

                    .policy-link {
                        color: #ffffff;
                        text-decoration: underline;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }

                    .policy-link:hover {
                        color: #ffffff;
                        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
                    }

                    .login-link {
                        text-align: center;
                        margin-bottom: 1.5rem;
                        color: #a3a3a3;
                        font-size: 0.9rem;
                    }

                    .login-link button {
                        background: transparent;
                        border: none;
                        color: #ffffff;
                        cursor: pointer;
                        text-decoration: underline;
                        font-size: inherit;
                        font-family: inherit;
                        font-weight: 500;
                        transition: color 0.3s ease;
                    }

                    .login-link button:hover {
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
                        font-size: 0.9rem;
                        transition: color 0.3s ease;
                        font-family: inherit;
                    }

                    .back-button:hover {
                        color: #ffffff;
                    }
                    .social-button {
                        width: 100%;
                        padding: 1rem 1.25rem;
                        background: rgba(0, 0, 0, 0.4);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 0.75rem;
                        color: #ffffff;
                        font-size: 0.95rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 1rem;
                        font-family: inherit;
                        font-weight: 500;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 0.75rem;
                    }

                    .social-button.primary {
                        background: #ffffff;
                        color: #000000;
                        border: 2px solid #ffffff;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        font-size: 1.1rem;
                        padding: 1rem 2rem;
                    }

                    .social-button:hover {
                        border-color: #ffffff;
                        background: rgba(255, 255, 255, 0.1);
                        transform: translateY(-1px);
                    }

                    .social-button.primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
                        background: #ffffff;
                        color: #000000;
                    }

                    @media (max-width: 768px) {
                        .header { height: 70px; min-height: 70px; }
                        .header-content { padding: 1rem; }
                        .main-content { 
                            padding: 90px 1rem 2rem 1rem;
                            min-height: 100vh;
                        }
                        .signup-card { 
                            padding: 2rem; 
                            margin: 0;
                            max-width: none;
                            border-radius: 1rem;
                            width: 100%;
                        }
                        .name-row { 
                            grid-template-columns: 1fr; 
                            gap: 0; 
                        }
                        .signup-title {
                            font-size: 2rem;
                        }
                        .signup-subtitle {
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
                    <div className="signup-card">
                        <div className="signup-header">
                            <h1 className="signup-title">Join Xverta</h1>
                            <p className="signup-subtitle">Create your account to get started</p>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="name-row">
                                <div className="form-group">
                                    <label className="form-label" htmlFor="firstName">First Name</label>
                                    <div className="input-wrapper">
                                        <input
                                            type="text"
                                            id="firstName"
                                            name="firstName"
                                            className={`form-input ${validation.firstName.isValid === true ? 'valid' : validation.firstName.isValid === false ? 'invalid' : ''}`}
                                            placeholder="John"
                                            value={formData.firstName}
                                            onChange={handleChange}
                                            required
                                        />
                                        {validation.firstName.isValid === true && (
                                            <svg className="validation-icon valid" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                        {validation.firstName.isValid === false && (
                                            <svg className="validation-icon invalid" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                    </div>
                                    {validation.firstName.message && (
                                        <div className={`validation-message ${validation.firstName.isValid ? 'valid' : 'invalid'}`}>
                                            {validation.firstName.message}
                                        </div>
                                    )}
                                </div>
                                <div className="form-group">
                                    <label className="form-label" htmlFor="lastName">Last Name</label>
                                    <div className="input-wrapper">
                                        <input
                                            type="text"
                                            id="lastName"
                                            name="lastName"
                                            className={`form-input ${validation.lastName.isValid === true ? 'valid' : validation.lastName.isValid === false ? 'invalid' : ''}`}
                                            placeholder="Doe"
                                            value={formData.lastName}
                                            onChange={handleChange}
                                            required
                                        />
                                        {validation.lastName.isValid === true && (
                                            <svg className="validation-icon valid" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                        {validation.lastName.isValid === false && (
                                            <svg className="validation-icon invalid" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                    </div>
                                    {validation.lastName.message && (
                                        <div className={`validation-message ${validation.lastName.isValid ? 'valid' : 'invalid'}`}>
                                            {validation.lastName.message}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label" htmlFor="email">Email</label>
                                <div className="input-wrapper">
                                    <input
                                        type="email"
                                        id="email"
                                        name="email"
                                        className={`form-input ${validation.email.isValid === true ? 'valid' : validation.email.isValid === false ? 'invalid' : ''}`}
                                        placeholder="john.doe@example.com"
                                        value={formData.email}
                                        onChange={handleChange}
                                        required
                                    />
                                    {validation.email.isValid === true && (
                                        <svg className="validation-icon valid" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                                        </svg>
                                    )}
                                    {validation.email.isValid === false && (
                                        <svg className="validation-icon invalid" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/>
                                        </svg>
                                    )}
                                </div>
                                {validation.email.message && (
                                    <div className={`validation-message ${validation.email.isValid ? 'valid' : 'invalid'}`}>
                                        {validation.email.message}
                                    </div>
                                )}
                            </div>

                            <div className="form-group">
                                <label className="form-label" htmlFor="password">Password</label>
                                <div className="input-wrapper">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        id="password"
                                        name="password"
                                        className={`form-input ${validation.password.isValid === true ? 'valid' : validation.password.isValid === false ? 'invalid' : ''}`}
                                        placeholder="••••••••"
                                        value={formData.password}
                                        onChange={handleChange}
                                        required
                                        autocomplete="new-password"
                                    />
                                    <button
                                        type="button"
                                        className="password-toggle"
                                        onClick={() => setShowPassword(!showPassword)}
                                    >
                                        {showPassword ? (
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd"/>
                                                <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                                            </svg>
                                        ) : (
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                                                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                    </button>
                                </div>
                                {formData.password && (
                                    <div className="password-strength-meter">
                                        <div className={`strength-bar ${
                                            validation.password.strength < 40 ? 'weak' :
                                            validation.password.strength < 80 ? 'medium' : 'strong'
                                        }`}></div>
                                    </div>
                                )}
                                {validation.password.message && (
                                    <div className={`validation-message ${validation.password.isValid ? 'valid' : 'invalid'}`}>
                                        {validation.password.message}
                                    </div>
                                )}
                            </div>

                            <div className="form-group">
                                <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
                                <div className="input-wrapper">
                                    <input
                                        type={showConfirmPassword ? "text" : "password"}
                                        id="confirmPassword"
                                        name="confirmPassword"
                                        className={`form-input ${validation.confirmPassword.isValid === true ? 'valid' : validation.confirmPassword.isValid === false ? 'invalid' : ''}`}
                                        placeholder="••••••••"
                                        value={formData.confirmPassword}
                                        onChange={handleChange}
                                        required
                                        autocomplete="new-password"
                                    />
                                    <button
                                        type="button"
                                        className="password-toggle"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    >
                                        {showConfirmPassword ? (
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd"/>
                                                <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z"/>
                                            </svg>
                                        ) : (
                                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                                                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                                            </svg>
                                        )}
                                    </button>
                                </div>
                                {validation.confirmPassword.message && (
                                    <div className={`validation-message ${validation.confirmPassword.isValid ? 'valid' : 'invalid'}`}>
                                        {validation.confirmPassword.message}
                                    </div>
                                )}
                            </div>

                            <button type="submit" className="login-button" disabled={loading}>
                                {loading ? 'Creating Account...' : 'CREATE ACCOUNT'}
                            </button>
                        </form>

                        <div className="policy-links">
                            By signing up, you agree to our{' '}
                            <span className="policy-link" onClick={() => window.open('/terms', '_blank')}>
                                Terms of Service
                            </span>
                            {' '}and{' '}
                            <span className="policy-link" onClick={() => window.open('/privacy', '_blank')}>
                                Privacy Policy
                            </span>
                        </div>

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
                                Sign up with Google
                            </button>

                            <button
                                className="social-button"
                                onClick={() => window.location.href = "http://localhost:8000/auth/github/login"}
                            >
                                <svg className="social-icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                                </svg>
                                Sign up with GitHub
                            </button>
                        </div>

                        <div className="login-link">
                            Already have an account?{' '}
                            <button onClick={handleLoginRedirect}>
                                Sign in
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
        </PageWrapper>
    );
};

export default SignupPage;

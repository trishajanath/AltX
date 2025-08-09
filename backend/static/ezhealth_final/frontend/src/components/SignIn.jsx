import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignIn.css';

const SignIn = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    console.log('Submitting form with data:', formData);

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();
      console.log('Response data:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Store the access token
      localStorage.setItem('token', data.access_token);
      console.log('Token stored:', data.access_token);

      navigate('/home', { replace: true });
      

      
      console.log('Navigating to home page');
    } catch (error) {
      console.error('Error during sign in:', error);
      setError(error.message || 'An error occurred during sign in');
    }
  };

  const handleForgotPasswordClick = () => {
    navigate('/forgot-password');
  };

  return (
    <div className="signin-container">
      <h2>Welcome back</h2>
      <p>Sign in to continue your journey</p>
      {error && <p className="error-message">{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          name="email"
          placeholder="Enter your email"
          value={formData.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Enter your password"
          value={formData.password}
          onChange={handleChange}
          required
        />
        <div className="options">
          <label>
            <input type="checkbox" /> Remember me
          </label>
          <span onClick={handleForgotPasswordClick}>Forgot password?</span>
        </div>
        <button type="submit">Sign In</button>
      </form>
      <p>Don't have an account? <span onClick={() => navigate('/signup')}>Sign up</span></p>
    </div>
  );
};

export default SignIn;
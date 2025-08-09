import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css'; // Import the CSS file for styling

const LandingPage = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/sign-in');
  };

  return (
    <div className="landing-page-container" onClick={handleClick}>
      <h1 className="landing-title">EzHealth</h1>
      <p className="landing-catchphrase">Empowering Healthcare Professionals</p>
    </div>
  );
};

export default LandingPage;
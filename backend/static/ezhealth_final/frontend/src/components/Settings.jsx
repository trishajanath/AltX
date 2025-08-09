import React from 'react';
import { useNavigate } from 'react-router-dom';
import SignOut from './SignOut';
import BottomNavBar from './BottomNavBar'; // Import BottomNavBar component
import './Settings.css'; // Import the CSS file for styling

const Settings = () => {
  const navigate = useNavigate();

  return (
    <div className="settings-page-container">
      <h1 className="settings-title">Settings</h1>
      <p className="settings-description">Manage your account settings here.</p>
      
      <div className="settings-options">
        <h2 onClick={() => navigate('/update-profile')} className="clickable-option">Update Profile</h2>
        <p>Update your profile information.</p>
      </div>

      <div className="signout-container">
        <SignOut />
      </div>

      <BottomNavBar /> {/* Bottom navigation bar */}
    </div>
  );
};

export default Settings;
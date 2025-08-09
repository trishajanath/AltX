import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Signup from './components/Signup';
import SignIn from './components/SignIn';
import ForgotPassword from './components/ForgotPassword';
import ScanDetails from './components/ScanDetails';
import UploadSpecimen from './components/UploadSpecimen'; 
import Analysis from './components/Analysis'; 
import LandingPage from './components/LandingPage';
import Home from './components/Home'; 
import Reports from './components/Reports'; // Import Reports component
import Settings from './components/Settings'; // Import Settings component
import PrivateRoute from './components/PrivateRoute'; // Import PrivateRoute component
import UpdateProfile from './components/updateprofile';
import SignOut from './components/SignOut'; 

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} /> {/* Default to Landing Page */}
        <Route path="/signin" element={<SignIn />} /> {/* SignIn page */}
        <Route path="/home" element={<Home />} /> {/* Home page */}
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/update-profile" element={<UpdateProfile />} />
        <Route path="/scan-details" element={<ScanDetails />} /> {/* Add this route */}
        <Route path="/upload-specimen" element={<UploadSpecimen />} /> {/* Add this route */}
        <Route path="/analysis" element={<Analysis />} /> {/* Add this route */}
        <Route path="/reports" element={<Reports />} /> {/* Add this route */}
        <Route path="/settings" element={<Settings />} /> {/* Add this route */}
        <Route path="/signout" element={<SignOut />} />
        <Route path="*" element={<Navigate to="/signin" />} /> {/* Redirect to SignIn page */}
      </Routes>
    </Router>
  );
}

export default App;
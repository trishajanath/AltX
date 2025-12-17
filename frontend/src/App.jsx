import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import './App.css';
import HomePage from './components/HomePage';
import DeployPage from './components/DeployPage';
import SecurityScanPage from './components/SecurityScanPage';
import ReportPage from './components/ReportPage';
import RepoAnalysisPage from './components/RepoAnalysisPage';
import LandingPage from './components/LandingPage';
import SignupPage from './components/SignupPage';
import LoginPage from './components/LoginPage';
import ProtectedRoute from './components/ProtectedRoute';
import VoiceChatInterface from './components/VoiceChatInterface';
import MonacoProjectEditor from './components/MonacoProjectEditor';
import FeaturesPage from './components/FeaturesPage';
import AboutPage from './components/AboutPage';
import PricingPage from './components/PricingPage';
import OAuthCallback from './components/OAuthCallback';
import { AuthProvider } from './contexts/AuthContext';



function App() {
  const [scanResult, setScanResult] = useState(null);

  return (
    <AuthProvider>
      <Router>
        <div className="App">
    {/* Navigation removed: sidebar/menu is now handled in HomePage.jsx */}
          <div className="page-container">
            <Routes>
              <Route path="/" element={<div className="page"><LandingPage /></div>} />
              <Route path="/login" element={<div className="page"><LoginPage /></div>} />
              <Route path="/signup" element={<div className="page"><SignupPage /></div>} />
              <Route path="/features" element={<div className="page"><FeaturesPage /></div>} />
              <Route path="/pricing" element={<div className="page"><PricingPage /></div>} />
              <Route path="/about" element={<div className="page"><AboutPage /></div>} />
              
              {/* OAuth Callback Handler - processes auth params and redirects */}
              <Route path="/oauth/callback" element={<OAuthCallback />} />
              
              <Route path="/voice-chat" element={
                <ProtectedRoute>
                  <div className="page"><VoiceChatInterface onProjectGenerated={(projectName) => window.location.href = `/project/${projectName}`} /></div>
                </ProtectedRoute>
              } />
              <Route path="/home" element={
                <ProtectedRoute>
                  <div className="page"><HomePage/></div>
                </ProtectedRoute>
              } />
              <Route path="/project/*" element={
                <ProtectedRoute>
                  <div className="page"><MonacoProjectEditor /></div>
                </ProtectedRoute>
              } />
              <Route path="/deploy" element={
                <ProtectedRoute>
                  <div className="page"><DeployPage setScanResult={setScanResult} /></div>
                </ProtectedRoute>
              } />
              <Route path="/security" element={
                <ProtectedRoute>
                  <div className="page"><SecurityScanPage setScanResult={setScanResult} /></div>
                </ProtectedRoute>
              } />
              <Route path="/repo-analysis" element={
                <ProtectedRoute>
                  <div className="page"><RepoAnalysisPage /></div>
                </ProtectedRoute>
              } />
              <Route path="/report" element={
                <ProtectedRoute>
                  <div className="page"><ReportPage scanResult={scanResult} /></div>
                </ProtectedRoute>
              } />
              
              {/* Catch-all route - redirect to landing page */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

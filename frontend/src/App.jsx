import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
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



function App() {
  const [scanResult, setScanResult] = useState(null);

  return (
    <Router>
      <div className="App">
  {/* Navigation removed: sidebar/menu is now handled in HomePage.jsx */}
        <div className="page-container">
          <Routes>
            <Route path="/" element={<div className="page"><LandingPage /></div>} />
            <Route path="/login" element={<div className="page"><LoginPage /></div>} />
            <Route path="/signup" element={<div className="page"><SignupPage /></div>} />
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
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

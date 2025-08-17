import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import HomePage from './components/HomePage';
import DeployPage from './components/DeployPage';
import SecurityScanPage from './components/SecurityScanPage';
import ReportPage from './components/ReportPage';
import RepoAnalysisPage from './components/RepoAnalysisPage';
import ProjectBuilder from './components/ProjectBuilder';
import LandingPage from './components/LandingPage';
import SignupPage from './components/SignupPage';
import LoginPage from './components/LoginPage';



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
            <Route path="/home" element={<div className="page"><HomePage /></div>} />
            <Route path="/build" element={<div className="page"><ProjectBuilder /></div>} />
            <Route path="/deploy" element={<div className="page"><DeployPage setScanResult={setScanResult} /></div>} />
            <Route path="/security" element={<div className="page"><SecurityScanPage setScanResult={setScanResult} /></div>} />
            <Route path="/repo-analysis" element={<div className="page"><RepoAnalysisPage /></div>} />
            <Route path="/report" element={<div className="page"><ReportPage scanResult={scanResult} /></div>} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

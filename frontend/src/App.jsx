import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import HomePage from './components/HomePage';
import DeployPage from './components/DeployPage';
import SecurityScanPage from './components/SecurityScanPage';
import ReportPage from './components/ReportPage';
import RepoAnalysisPage from './components/RepoAnalysisPage';
import ProjectBuilder from './components/ProjectBuilder';

function Navigation() {
  const location = useLocation();
  const activeTab = location.pathname === '/' ? 'home' : location.pathname.slice(1);

  return (
    <nav className="nav">
      <Link to="/" className="logo">
        AltX
      </Link>
      <ul className="nav-links">
        <li>
          <Link 
            to="/"
            className={`nav-link ${activeTab === 'home' ? 'active' : ''}`}
          >
            Home
          </Link>
        </li>
        <li>
          <Link 
            to="/build"
            className={`nav-link ${activeTab === 'build' ? 'active' : ''}`}
          >
            Build Apps
          </Link>
        </li>
        <li>
          <Link 
            to="/deploy"
            className={`nav-link ${activeTab === 'deploy' ? 'active' : ''}`}
          >
            Deploy
          </Link>
        </li>
        <li>
          <Link 
            to="/security"
            className={`nav-link ${activeTab === 'security' ? 'active' : ''}`}
          >
            Security Scan
          </Link>
        </li>
        <li>
          <Link 
            to="/repo-analysis"
            className={`nav-link ${activeTab === 'repo-analysis' ? 'active' : ''}`}
          >
            Repository Analysis
          </Link>
        </li>
        <li>
          <Link 
            to="/report"
            className={`nav-link ${activeTab === 'report' ? 'active' : ''}`}
          >
            Reports
          </Link>
        </li>
      </ul>
    </nav>
  );
}

function App() {
  const [scanResult, setScanResult] = useState(null);

  return (
    <Router>
      <div className="App">
        <Navigation />
        <div className="page-container">
          <Routes>
            <Route path="/" element={<div className="page"><HomePage /></div>} />
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

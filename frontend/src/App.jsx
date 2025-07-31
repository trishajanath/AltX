import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import HomePage from './components/HomePage';
import DeployPage from './components/DeployPage';
import SecurityScanPage from './components/SecurityScanPage';
import ReportPage from './components/ReportPage';

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
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/deploy" element={<DeployPage setScanResult={setScanResult} />} />
          <Route path="/security" element={<SecurityScanPage setScanResult={setScanResult} />} />
          <Route path="/report" element={<ReportPage scanResult={scanResult} />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

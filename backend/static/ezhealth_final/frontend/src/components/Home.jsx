import React from "react";
import BottomNavBar from "./BottomNavBar";
import "./Home.css";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home-page-container">
      <h1 className="home-title">Welcome to EzHealth</h1>
      <p className="home-description">
        Empowering Healthcare Professionals with the tools and information they need to provide the best care possible.
      </p>

      {/* Categories Section */}
      <div className="grid-section">
        <div className="feature-card" onClick={() => navigate('/reports')}>
          <h2 className="card-title">Medical Scans</h2>
          <p className="card-content">Upload and analyze medical scans with AI-powered insights.</p>
        </div>
        <div className="feature-card" onClick={() => navigate('/upload-specimen')}>
          <h2 className="card-title">Specimen Upload</h2>
          <p className="card-content">Submit patient specimens for lab analysis and results.</p>
        </div>
        <div className="feature-card" onClick={() => navigate('/analysis')}>
          <h2 className="card-title">Detailed Analysis</h2>
          <p className="card-content">Get in-depth reports on medical data and trends.</p>
        </div>
        <div className="feature-card" onClick={() => navigate('/reports')}>
          <h2 className="card-title">Patient Reports</h2>
          <p className="card-content">Generate and manage patient reports efficiently.</p>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNavBar />
    </div>
  );
};

export default Home;

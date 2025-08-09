import React from "react";
import { NavLink } from "react-router-dom";
import "./BottomNavBar.css";

const BottomNavBar = () => {
  return (
    <div className="bottom-nav-bar">
      <NavLink to="/home" className="nav-link" activeClassName="active">
        <span className="nav-icon">🏠</span> Home
      </NavLink>
      <NavLink to="/reports" className="nav-link" activeClassName="active">
        <span className="nav-icon">📄</span> Reports
      </NavLink>
      <NavLink to="/upload-specimen" className="upload-btn">
        +
      </NavLink>
      <NavLink to="/analysis" className="nav-link" activeClassName="active">
        <span className="nav-icon">📊</span> Analysis
      </NavLink>
      <NavLink to="/settings" className="nav-link" activeClassName="active">
        <span className="nav-icon">⚙️</span> Settings
      </NavLink>
    </div>
  );
};

export default BottomNavBar;

import React from "react";
import { useNavigate } from "react-router-dom";
import "./SignOut.css"; // Import the CSS file for styling

const SignOut = () => {
    const navigate = useNavigate();

    const handleSignOut = () => {
        localStorage.removeItem("token"); // Remove token from localStorage
        navigate("/signin"); // Redirect to sign-in page
    };

    return (
        <button onClick={handleSignOut} className="signout-button">
            Sign Out
        </button>
    );
};

export default SignOut;

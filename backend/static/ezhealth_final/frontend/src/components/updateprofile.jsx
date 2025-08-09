import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./updateprofile.css";
import BottomNavBar from "./BottomNavBar";

const UpdateProfile = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        currentPassword: "",
        newPassword: ""
    });
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setSuccess("");
    
        const token = localStorage.getItem("token");
        console.log("Token before request:", token);
    
        if (!token) {
            navigate("/signin");
            return;
        }
    
        try {
            const response = await fetch("http://127.0.0.1:8000/auth/update-profile", {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData),
            });
    
            if (response.status === 401) {
                console.warn("Invalid token detected, clearing local storage.");
                localStorage.removeItem("token");  // Force logout
                navigate("/signin");
                return;
            }
    
            const data = await response.json();
    
            if (!response.ok) {
                throw new Error(data.detail || "Update failed");
            }
    
            setSuccess("Profile updated successfully!");
            setFormData({ currentPassword: "", newPassword: "" });
    
            setTimeout(() => {
                navigate("/profile");
            }, 1500);
        } catch (error) {
            console.error("Update error:", error);
            setError(error.message || "An error occurred during updating");
        }
    };
    

    return (
        <div className="update-profile-container">
            <h2>Update Profile</h2>
            {error && <p className="error-message">{error}</p>}
            {success && <p className="success-message">{success}</p>}
            <form className="update-profile-form" onSubmit={handleSubmit}>
                <label htmlFor="currentPassword">Current Password:</label>
                <input 
                    type="password" 
                    id="currentPassword" 
                    name="currentPassword" 
                    value={formData.currentPassword} 
                    onChange={handleChange} 
                    required 
                />

                <label htmlFor="newPassword">New Password:</label>
                <input 
                    type="password" 
                    id="newPassword" 
                    name="newPassword" 
                    value={formData.newPassword} 
                    onChange={handleChange} 
                />

                <button type="submit">Update</button>
            </form>
            <BottomNavBar />
        </div>
    );
};

export default UpdateProfile;

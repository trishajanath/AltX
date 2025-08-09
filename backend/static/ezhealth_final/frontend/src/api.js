import axios from "axios";

const API_URL = "http://127.0.0.1:8000"; // FastAPI backend URL

// Signup
export const signup = async (userData) => {
  const response = await axios.post(`${API_URL}/auth/signup`, userData);
  return response.data;
};

// Login
export const login = async (userData) => {
  const response = await axios.post(`${API_URL}/auth/login`, userData);
  localStorage.setItem("token", response.data.access_token); // Save token for auth
  return response.data;
};

// Upload Image
export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await axios.post(`${API_URL}/images/upload-image`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  return response.data;
};

// Analyze Image
export const analyzeImage = async (imagePath) => {
  const response = await axios.get(`${API_URL}/analysis/${imagePath}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });
  return response.data;
};

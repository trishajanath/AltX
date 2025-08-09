import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNavBar from './BottomNavBar';
import './UploadSpecimen.css';

const UploadSpecimen = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [patientName, setPatientName] = useState('');
  const [sn, setSn] = useState('');
  const [gender, setGender] = useState('');
  const [uploadStatus, setUploadStatus] = useState('');

  // Additional patient details for prediction
  const [year, setYear] = useState('');
  const [age, setAge] = useState('');
  const [tumorSize, setTumorSize] = useState('');
  const [invNodes, setInvNodes] = useState('');
  const [breastCancerCell, setBreastCancerCell] = useState('');
  const [menopause, setMenopause] = useState('');
  const [metastasis, setMetastasis] = useState('');
  const [breastQuadrant, setBreastQuadrant] = useState('');
  const [history, setHistory] = useState('');

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.type !== "image/jpeg" && file.type !== "image/png") {
      alert("Only JPG and PNG image files are allowed!");
      return;
    }
    setSelectedFile(file);
  };

  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    if (!selectedFile || !patientName || !sn || !gender ) {
      alert("Please fill in all patient details and select a file before submitting.");
      return;
    }
    if(age<0 || year<0 || tumorSize<0 || invNodes<0 || breastCancerCell<0 || menopause<0 || metastasis<0 || breastQuadrant<0 || history<0){
      alert("Negative values are not allowed");
      return;
    }
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("patientName", patientName);
      formData.append("sn", sn);
      formData.append("gender", gender);
      // Append additional patient details for prediction
      formData.append("year", year);
      formData.append("age", age);
      formData.append("tumorSize", tumorSize);
      formData.append("invNodes", invNodes);
      formData.append("breastCancerCell", breastCancerCell);
      formData.append("menopause", menopause);
      formData.append("metastasis", metastasis);
      formData.append("breastQuadrant", breastQuadrant);
      formData.append("history", history);
  
      const response = await fetch("http://127.0.0.1:8000/images/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }
  
      const data = await response.json();
      setUploadStatus("Upload successful!");
  
      // Navigate to the analysis page with the response data
      navigate("/analysis", {
        state: {
          imageData: data,
        },
      });
    } catch (error) {
      setUploadStatus("Upload failed. Please try again.");
      console.error("Upload error:", error);
    }
  };

  return (
    <div className="upload-specimen-container">
      <h1>Upload Specimen</h1>
      <div className="upload-section">
        <div className="drag-drop-area">
          <p>Drag and drop your image here</p>
          <p>or</p>
          <input
            type="file"
            accept="image/jpeg, image/png"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileSelect}
          />
          <button onClick={handleBrowseClick}>Browse Files</button>
          {selectedFile && (
            <div className="selected-files">
              <p>Selected file: {selectedFile.name}</p>
            </div>
          )}
        </div>
        <div className="patient-details">
          <input
            type="text"
            placeholder="Enter patient name"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="SN"
            value={sn}
            onChange={(e) => setSn(e.target.value)}
            required
          />
          <div className="gender-selection">
            <label>
              <input
                type="radio"
                name="gender"
                value="male"
                onChange={(e) => setGender(e.target.value)}
              /> Male
            </label>
            <label>
              <input
                type="radio"
                name="gender"
                value="female"
                onChange={(e) => setGender(e.target.value)}
              /> Female
            </label>
            <label>
              <input
                type="radio"
                name="gender"
                value="other"
                onChange={(e) => setGender(e.target.value)}
              /> Other
            </label>
          </div>

          {/* Additional patient details for prediction */}
          <input
            type="number"
            placeholder="Year"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Age"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Tumor Size"
            value={tumorSize}
            onChange={(e) => setTumorSize(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Inv Nodes"
            value={invNodes}
            onChange={(e) => setInvNodes(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Breast Cancer Cell"
            value={breastCancerCell}
            onChange={(e) => setBreastCancerCell(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Menopause"
            value={menopause}
            onChange={(e) => setMenopause(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Metastasis"
            value={metastasis}
            onChange={(e) => setMetastasis(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Breast Quadrant"
            value={breastQuadrant}
            onChange={(e) => setBreastQuadrant(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="History"
            value={history}
            onChange={(e) => setHistory(e.target.value)}
            required
          />
        </div>
      </div>
      <div className="action-buttons">
        <button onClick={handleSubmit} disabled={!selectedFile}>
          Submit
        </button>
      </div>
      {uploadStatus && <p>{uploadStatus}</p>}
      <BottomNavBar />
    </div>
  );
};

export default UploadSpecimen;
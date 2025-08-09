import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const ScanDetails = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { scan } = location.state || {}; // Get scan data passed via navigation

  if (!scan) {
    return <div>No scan data found.</div>;
  }

  const handleDelete = () => {
    const confirmDelete = window.confirm("Are you sure you want to delete this scan?");
    if (confirmDelete) {
      // Fetch the existing scans from localStorage
      const savedScans = JSON.parse(localStorage.getItem('scans')) || [];

      // Remove the selected scan
      const updatedScans = savedScans.filter((s) => s.id !== scan.id);

      // Update localStorage
      localStorage.setItem('scans', JSON.stringify(updatedScans));

      // Navigate back to the scans list
      navigate('/medical-scans', { state: { deletedScanId: scan.id } });
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Scan Details</h1>
      <div style={{ backgroundColor: '#f9f9f9', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h2>{scan.name}</h2>
        <p><strong>Type of Cancer:</strong> {scan.type}</p>
        <p><strong>Patient Name:</strong> {scan.patientName}</p>
        <p><strong>Severity:</strong> {scan.severity}</p>
        <p><strong>Date:</strong> {scan.date}</p>
        <p><strong>Doctor:</strong> {scan.doctor}</p>
      </div>

      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <button onClick={() => navigate(-1)} style={{ padding: '10px 20px', borderRadius: '5px', backgroundColor: '#007bff', color: 'white' }}>
          Go Back
        </button>
        <button onClick={handleDelete} style={{ padding: '10px 20px', borderRadius: '5px', backgroundColor: '#dc3545', color: 'white' }}>
          Delete Scan
        </button>
      </div>
    </div>
  );
};

export default ScanDetails;

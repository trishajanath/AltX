import React from 'react';
import { useLocation } from 'react-router-dom';
import { FiZoomIn, FiZoomOut, FiMove, FiShare2, FiDownload } from 'react-icons/fi';
import './Analysis.css';
import BottomNavBar from './BottomNavBar';
import { use } from 'react';

const Analysis = () => {
  const location = useLocation();
  const { imageData } = location.state || {};
  const { patientInfo } = location.state || {};

  return (
    <div className="analysis-container">
      {/* Header */}
      <h1 className="analysis-head">AI Analysis Results</h1>

      {/* Main Content */}
      <div className="main-section">
        {!imageData ? (
          <div className="error-message">No analysis data available. Please upload an image first.</div>
        ) : (
          <>
            {/* Image Panel */}
            <div className="image-panel glassmorphism-effect">
              <h2 className="image-title">Original Image</h2>
              <div className="image-container">
                {imageData.original_image && (
                  <img src={imageData.original_image} alt="Original Image" className="scan-image" />
                )}
              </div>
              
              <div className="image-controls">
                <button className="control-btn">
                  <FiZoomIn className="icon" />
                  Zoom In
                </button>
                <button className="control-btn">
                  <FiZoomOut className="icon" />
                  Zoom Out
                </button>
                <button className="control-btn">
                  <FiMove className="icon" />
                  Pan
                </button>
              </div>
            </div>

            {/* Results Panel */}
            <div className="results-panel glassmorphism-effect">
              <h2 className="results-title">
                  Diagnostic Insights
              </h2>
              
              <div className="metrics-grid">
                <div className="metric-card confidence">
                  <h3 className="text1">AI Confidence</h3>
                  <div className="metric-value">{imageData.confidence}</div>
                  <div className="confidence-bar">
                    <div 
                      className="confidence-fill" 
                      style={{ width: `${imageData.confidence}%` }}
                    ></div>
                  </div>
                </div>

                <div className="metric-card anomalies">
                  <h3 className="text1">Predicted Subtype</h3>
                  <div className="subtype-value">{imageData.predicted_subtype || 'Unknown'}</div>
                  <h4>{['adenosis', 'fibroadenoma', 'phyllodes_tumor', 'tubular_adenoma'].includes(imageData.predicted_subtype) ? 'This is not cancer' : 'This is cancer'}</h4>
                </div>
                <div className='metric-card predictedstage'>
                  <h3 className="text1">Predicted Stage</h3>
                  <div className="subtype-value">Predicted Stage: {imageData.predicted_stage}</div>
                </div>
                <div className='metric-card treatment'>
                  <h3 className="text1">Recommended treatment</h3>
                  <div className="subtype-value">Recommended treatment: {imageData.recommended_treatment}</div>
                </div>
                

                <div className="metric-card heatmap">
                  <h3 className='text1'>Tissue Analysis</h3>
                  {imageData.heatmap && (
                    <img src={imageData.heatmap} alt="Heatmap Visualization" className="heatmap-image" />
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      

      <BottomNavBar />
    </div>
  );
};

export default Analysis;
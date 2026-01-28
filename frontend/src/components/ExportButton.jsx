/**
 * ExportButton Component
 * ======================
 * Button component for exporting projects as runnable packages.
 * 
 * Shows progress during export and displays setup instructions on completion.
 */

import React, { useState } from 'react';
import { useProjectExport, ExportStage } from '../hooks/useProjectExport';

export function ExportButton({ 
  projectName, 
  projectFiles, 
  includeDocker = true,
  buttonStyle = {},
  showInstructions = true,
}) {
  const {
    exportProject,
    reset,
    getInstructions,
    stage,
    progress,
    isExporting,
    error,
    isComplete,
  } = useProjectExport();

  const [showModal, setShowModal] = useState(false);

  const handleExport = async () => {
    const result = await exportProject({
      projectName,
      projectFiles,
      includeDocker,
    });

    if (result.success && showInstructions) {
      setShowModal(true);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    reset();
  };

  // Get stage icon
  const getStageIcon = () => {
    switch (stage) {
      case ExportStage.PREPARING:
      case ExportStage.EXPORTING:
        return '📦';
      case ExportStage.DOWNLOADING:
        return '⬇️';
      case ExportStage.COMPLETE:
        return '✅';
      case ExportStage.ERROR:
        return '❌';
      default:
        return '📤';
    }
  };

  // Button text
  const getButtonText = () => {
    if (isExporting) {
      return progress.message || 'Exporting...';
    }
    if (isComplete) {
      return 'Export Complete!';
    }
    if (error) {
      return 'Export Failed';
    }
    return 'Export Project';
  };

  return (
    <>
      <button
        onClick={handleExport}
        disabled={isExporting}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 16px',
          background: isExporting 
            ? '#374151' 
            : error 
              ? '#dc2626' 
              : isComplete 
                ? '#16a34a' 
                : '#2563eb',
          color: '#ffffff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '14px',
          fontWeight: '500',
          cursor: isExporting ? 'wait' : 'pointer',
          transition: 'all 0.2s',
          opacity: isExporting ? 0.8 : 1,
          ...buttonStyle,
        }}
      >
        <span style={{ fontSize: '16px' }}>{getStageIcon()}</span>
        <span>{getButtonText()}</span>
        {isExporting && (
          <span 
            style={{ 
              display: 'inline-block',
              width: '12px',
              height: '12px',
              border: '2px solid transparent',
              borderTopColor: '#ffffff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }} 
          />
        )}
      </button>

      {/* Instructions Modal */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
          }}
          onClick={handleCloseModal}
        >
          <div
            style={{
              background: '#1a1a1a',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '600px',
              maxHeight: '80vh',
              overflow: 'auto',
              border: '1px solid #333',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '16px',
            }}>
              <h2 style={{ margin: 0, color: '#ffffff', fontSize: '18px' }}>
                ✅ Export Complete!
              </h2>
              <button
                onClick={handleCloseModal}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#888',
                  fontSize: '24px',
                  cursor: 'pointer',
                  padding: '0',
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>

            <div style={{ 
              background: '#0d1117', 
              borderRadius: '8px', 
              padding: '16px',
              marginBottom: '16px',
            }}>
              <p style={{ color: '#22c55e', margin: '0 0 8px 0', fontSize: '14px' }}>
                Your project has been downloaded as a ZIP file.
              </p>
              <p style={{ color: '#888', margin: 0, fontSize: '13px' }}>
                Extract it and follow the instructions below to run locally.
              </p>
            </div>

            <div style={{
              background: '#0d1117',
              borderRadius: '8px',
              padding: '16px',
              fontFamily: 'monospace',
              fontSize: '13px',
              color: '#e6e6e6',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.6,
            }}>
              {getInstructions()}
            </div>

            <div style={{ marginTop: '16px', textAlign: 'right' }}>
              <button
                onClick={handleCloseModal}
                style={{
                  padding: '8px 24px',
                  background: '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                }}
              >
                Got it!
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSS for spinner animation */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}

export default ExportButton;

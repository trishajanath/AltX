/**
 * Project Export Service
 * ======================
 * Frontend service for exporting projects as runnable packages.
 * 
 * Features:
 * - Export project as ZIP with Docker files
 * - Download exported package
 * - Progress tracking
 */

import { apiUrl } from './api';

/**
 * Export a project as a runnable package
 * 
 * @param {Object} options
 * @param {string} options.projectName - Name of the project
 * @param {Object<string, string>} options.projectFiles - Project files (path -> content)
 * @param {boolean} options.includeDocker - Include Docker configuration (default: true)
 * @returns {Promise<{success: boolean, downloadUrl: string, ...}>}
 */
export async function exportProject(options) {
  const {
    projectName,
    projectFiles,
    includeDocker = true,
  } = options;

  try {
    const response = await fetch(apiUrl('/api/export/package'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_name: projectName,
        project_files: projectFiles,
        include_docker: includeDocker,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `Export failed: ${response.status}`);
    }

    const result = await response.json();
    
    return {
      success: true,
      projectName: result.project_name,
      projectSlug: result.project_slug,
      fileCount: result.file_count,
      files: result.files,
      downloadUrl: apiUrl(result.download_url),
    };
  } catch (error) {
    console.error('Export failed:', error);
    return {
      success: false,
      error: error.message,
    };
  }
}

/**
 * Download an exported project
 * 
 * @param {string} downloadUrl - URL from exportProject result
 * @param {string} filename - Optional filename for download
 */
export async function downloadExport(downloadUrl, filename = null) {
  try {
    const response = await fetch(downloadUrl);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || downloadUrl.split('/').pop() || 'project-export.zip';
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    return { success: true };
  } catch (error) {
    console.error('Download failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Export and download project in one step
 * 
 * @param {Object} options - Same as exportProject
 * @param {function} onProgress - Optional progress callback
 * @returns {Promise<{success: boolean}>}
 */
export async function exportAndDownload(options, onProgress = null) {
  onProgress?.({ stage: 'exporting', message: 'Creating export package...' });
  
  const exportResult = await exportProject(options);
  
  if (!exportResult.success) {
    onProgress?.({ stage: 'error', message: exportResult.error });
    return exportResult;
  }
  
  onProgress?.({ 
    stage: 'downloading', 
    message: `Downloading ${exportResult.fileCount} files...` 
  });
  
  const downloadResult = await downloadExport(
    exportResult.downloadUrl,
    `${exportResult.projectSlug}.zip`
  );
  
  if (downloadResult.success) {
    onProgress?.({ stage: 'complete', message: 'Download complete!' });
  } else {
    onProgress?.({ stage: 'error', message: downloadResult.error });
  }
  
  return {
    ...exportResult,
    downloaded: downloadResult.success,
  };
}

/**
 * Generate local setup instructions
 * 
 * @param {string} projectSlug - Project slug/name
 * @returns {string} Markdown instructions
 */
export function getSetupInstructions(projectSlug) {
  return `
# Running ${projectSlug} Locally

## Prerequisites
- Docker and Docker Compose
- OR Node.js 18+ and Python 3.11+

## Quick Start (Docker)

1. Extract the downloaded ZIP file
2. Navigate to the project folder:
   \`\`\`bash
   cd ${projectSlug}
   \`\`\`

3. Copy the environment file:
   \`\`\`bash
   cp .env.example .env
   \`\`\`

4. **IMPORTANT**: Edit \`.env\` and set a secure \`JWT_SECRET\`:
   \`\`\`bash
   # Generate a secure secret
   openssl rand -hex 32
   \`\`\`

5. Start the application:
   \`\`\`bash
   docker-compose up --build
   \`\`\`

6. Access the app:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Running Without Docker

### Backend
\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET=your-secret-key
uvicorn main:app --reload --port 8000
\`\`\`

### Frontend
\`\`\`bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
npm run dev
\`\`\`
`;
}

export default {
  exportProject,
  downloadExport,
  exportAndDownload,
  getSetupInstructions,
};

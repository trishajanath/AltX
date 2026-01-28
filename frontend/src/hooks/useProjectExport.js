/**
 * useProjectExport Hook
 * =====================
 * React hook for exporting projects as runnable packages.
 * 
 * Usage:
 * ```jsx
 * function ExportButton({ projectName, projectFiles }) {
 *   const { 
 *     exportProject, 
 *     isExporting, 
 *     progress, 
 *     error 
 *   } = useProjectExport();
 * 
 *   return (
 *     <button 
 *       onClick={() => exportProject({ projectName, projectFiles })}
 *       disabled={isExporting}
 *     >
 *       {isExporting ? progress.message : 'Export Project'}
 *     </button>
 *   );
 * }
 * ```
 */

import { useState, useCallback } from 'react';
import {
  exportProject as doExport,
  downloadExport,
  getSetupInstructions,
} from '../config/projectExport';

/**
 * Export progress stages
 */
export const ExportStage = {
  IDLE: 'idle',
  PREPARING: 'preparing',
  EXPORTING: 'exporting',
  DOWNLOADING: 'downloading',
  COMPLETE: 'complete',
  ERROR: 'error',
};

/**
 * React hook for project export functionality
 */
export function useProjectExport() {
  const [stage, setStage] = useState(ExportStage.IDLE);
  const [progress, setProgress] = useState({ stage: 'idle', message: '' });
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState(null);
  const [lastExport, setLastExport] = useState(null);

  /**
   * Export project and automatically download
   */
  const exportProject = useCallback(async (options) => {
    const { projectName, projectFiles, includeDocker = true } = options;

    setIsExporting(true);
    setError(null);
    setStage(ExportStage.PREPARING);
    setProgress({ stage: 'preparing', message: 'Preparing export...' });

    try {
      // Create export package
      setStage(ExportStage.EXPORTING);
      setProgress({ stage: 'exporting', message: 'Creating export package...' });

      const exportResult = await doExport({
        projectName,
        projectFiles,
        includeDocker,
      });

      if (!exportResult.success) {
        throw new Error(exportResult.error || 'Export failed');
      }

      // Download the package
      setStage(ExportStage.DOWNLOADING);
      setProgress({ 
        stage: 'downloading', 
        message: `Downloading ${exportResult.fileCount} files...` 
      });

      const downloadResult = await downloadExport(
        exportResult.downloadUrl,
        `${exportResult.projectSlug}.zip`
      );

      if (!downloadResult.success) {
        throw new Error(downloadResult.error || 'Download failed');
      }

      // Success
      setStage(ExportStage.COMPLETE);
      setProgress({ stage: 'complete', message: 'Export complete!' });
      setLastExport(exportResult);

      return {
        success: true,
        ...exportResult,
        instructions: getSetupInstructions(exportResult.projectSlug),
      };

    } catch (err) {
      setStage(ExportStage.ERROR);
      setProgress({ stage: 'error', message: err.message });
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsExporting(false);
    }
  }, []);

  /**
   * Reset state for new export
   */
  const reset = useCallback(() => {
    setStage(ExportStage.IDLE);
    setProgress({ stage: 'idle', message: '' });
    setIsExporting(false);
    setError(null);
    setLastExport(null);
  }, []);

  /**
   * Get setup instructions for last export
   */
  const getInstructions = useCallback(() => {
    if (!lastExport) return null;
    return getSetupInstructions(lastExport.projectSlug);
  }, [lastExport]);

  return {
    // Actions
    exportProject,
    reset,
    getInstructions,

    // State
    stage,
    progress,
    isExporting,
    error,
    lastExport,

    // Computed
    isComplete: stage === ExportStage.COMPLETE,
    isError: stage === ExportStage.ERROR,
    isIdle: stage === ExportStage.IDLE,
  };
}

export default useProjectExport;

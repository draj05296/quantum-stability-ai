import { useQuantumData } from "./useQuantumData";
import { useAnalysisData } from "./useAnalysisData";

/** Which dataset the dashboard is currently rendering. */
export const DATA_SOURCE = {
  LOCAL: "local",
  ANALYSIS: "analysis",
};

/**
 * Chooses which dataset the dashboard renders, returning one uniform bundle
 * either way: { summary, allRecords, trendData, isLoading }.
 *
 * The bundled CSV data is loaded unconditionally and is therefore always
 * available. An analysis is used only when the caller passes one in *and* it
 * parsed into a usable bundle - so an absent, failed, or malformed analysis
 * simply isn't selected, and the dashboard falls back to local data without
 * any error handling of its own. The backend is never required for the
 * dashboard to render.
 *
 * @param activeAnalysis A POST /analyze response the user has explicitly
 *   chosen to display, or null to stay on the bundled sample data.
 */
export function useQuantumDataSource(activeAnalysis) {
  // Both hooks run on every render (hooks cannot be called conditionally),
  // which is also what keeps the local fallback warm and ready.
  const local = useQuantumData();
  const analyzed = useAnalysisData(activeAnalysis);

  if (analyzed) {
    return {
      summary: analyzed.summary,
      allRecords: analyzed.allRecords,
      trendData: analyzed.trendData,
      // Analyzed data arrives complete - there is nothing left to wait for.
      isLoading: false,
      activeSource: DATA_SOURCE.ANALYSIS,
      analysisMetadata: analyzed.metadata,
    };
  }

  return {
    summary: local.summary,
    allRecords: local.allRecords,
    trendData: local.trendData,
    isLoading: local.isLoading,
    activeSource: DATA_SOURCE.LOCAL,
    analysisMetadata: null,
  };
}

import { useMemo } from "react";
import { computeDailyTrend } from "../utils/dashboardCalculations";
import {
  extractAnalysisMetadata,
  formatAnalysisSummaryValues,
  isValidAnalysis,
  mapAnalysisToRecords,
} from "../utils/analysisAdapter";

/**
 * Derives the dashboard's data bundle from a POST /analyze response.
 *
 * Produces exactly the same `{ summary, allRecords, trendData }` contract as
 * useQuantumData(), so either source can drive the dashboard without any
 * component knowing which one it got.
 *
 * No QSFI arithmetic is repeated here: the per-qubit values and stability
 * statuses come from the backend, the summary is formatted straight from
 * `analysis.summary`, and the daily trend reuses the existing
 * computeDailyTrend(). Metadata is returned alongside - never merged into
 * the records themselves.
 *
 * Returns null when there is no analysis, or when the payload is incomplete,
 * which is what lets the caller fall back to the bundled CSV data.
 */
export function useAnalysisData(analysis) {
  return useMemo(() => {
    if (!isValidAnalysis(analysis)) return null;

    const allRecords = mapAnalysisToRecords(analysis);

    return {
      summary: formatAnalysisSummaryValues(analysis),
      allRecords,
      trendData: computeDailyTrend(allRecords),
      metadata: extractAnalysisMetadata(analysis),
    };
  }, [analysis]);
}

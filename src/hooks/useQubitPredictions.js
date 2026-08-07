import { useMemo } from "react";
import {
  computePredictionChartData,
  computePredictionSummary,
  computeQubitPredictions,
} from "../utils/dashboardCalculations";

/**
 * Runs the linear-regression forecast for every qubit and derives the
 * prediction summary cards and the Actual-vs-Predicted chart series from it.
 */
export function useQubitPredictions(allRecords, trendData) {
  const qubitPredictions = useMemo(
    () => computeQubitPredictions(allRecords),
    [allRecords]
  );

  const predictionSummary = useMemo(
    () => computePredictionSummary(qubitPredictions),
    [qubitPredictions]
  );

  const predictionChartData = useMemo(
    () => computePredictionChartData(qubitPredictions, trendData),
    [qubitPredictions, trendData]
  );

  return { qubitPredictions, predictionSummary, predictionChartData };
}

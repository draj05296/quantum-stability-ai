// Translates a POST /analyze response into the shapes the dashboard already
// speaks, so backend results can be rendered with the existing components
// instead of a parallel set of them.
//
// The one thing that must not be forgotten: the API returns T1/T2/QSFI in
// seconds (exactly as stored in the CSV), while every dashboard component
// renders microseconds. `toMicroseconds` is reused here so the conversion
// stays defined in a single place.

import { toMicroseconds } from "./dashboardCalculations";

/** Day label applied to a single uploaded file, which carries no day of its own. */
export const UPLOADED_DAY_LABEL = "Uploaded";

/**
 * Maps `analysis.qubits` onto the dashboard's canonical record shape:
 * { day, qubit, t1, t2, qsfi, status }.
 *
 * The status is taken straight from the backend (which applies the same
 * "QSFI >= average is Stable" rule as attachStatus) rather than recomputed.
 */
export function mapAnalysisToRecords(analysis, dayLabel = UPLOADED_DAY_LABEL) {
  if (!analysis?.qubits) return [];

  return analysis.qubits.map((entry) => ({
    day: dayLabel,
    qubit: entry.qubit,
    t1: toMicroseconds(entry.t1),
    t2: toMicroseconds(entry.t2),
    qsfi: toMicroseconds(entry.qsfi),
    status: entry.status,
  }));
}

/**
 * Formats `analysis.summary` into the same label -> value map that
 * formatSummaryCardValues() produces, so the result can be handed to the
 * existing <SummaryCards labels={SUMMARY_LABELS} /> component unchanged.
 */
export function formatAnalysisSummaryValues(analysis) {
  const summary = analysis?.summary;
  if (!summary) return null;

  return {
    "Average QSFI": toMicroseconds(summary.average_qsfi).toFixed(2),
    "Best Qubit": `Q${summary.best_qubit.qubit}`,
    "Average T1": `${toMicroseconds(summary.average_t1).toFixed(2)} μs`,
    "Average T2": `${toMicroseconds(summary.average_t2).toFixed(2)} μs`,
    "Total Qubits": `${summary.total_qubits}`,
  };
}

/**
 * Summarises `analysis.data_quality` as label/value pairs for display -
 * how many rows arrived, how many were dropped as duplicates or incomplete,
 * and how many were actually analyzed.
 */
export function formatDataQualityRows(analysis) {
  const quality = analysis?.data_quality;
  if (!quality) return [];

  return [
    { label: "Rows received", value: quality.rows_received },
    { label: "Duplicates removed", value: quality.duplicate_rows_removed },
    { label: "Incomplete rows dropped", value: quality.rows_with_missing_values_dropped },
    { label: "Rows analyzed", value: quality.rows_analyzed },
  ];
}

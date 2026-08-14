// Translates a POST /analyze response into the shapes the dashboard already
// speaks, so backend results can be rendered with the existing components
// instead of a parallel set of them.
//
// The one thing that must not be forgotten: the API returns T1/T2/QSFI in
// seconds (exactly as stored in the CSV), while every dashboard component
// renders microseconds. `toMicroseconds` is reused here so the conversion
// stays defined in a single place.

import { toMicroseconds } from "./dashboardCalculations";

/**
 * One /analyze call covers a single CSV, which carries no day of its own, so
 * its records are labelled as day 1.
 *
 * The label deliberately uses the dashboard's "Day N" format rather than a
 * free-text word: getDayNumber() parses it with Number(label.replace("Day ",
 * "")), and anything unparseable would sort day options and match prediction
 * chart points incorrectly. Passing a different `dayNumber` is what will let
 * several saved analyses be stitched into one multi-day series later.
 */
export const UPLOADED_DAY_NUMBER = 1;

/**
 * True when `analysis` is a /analyze response complete enough to drive the
 * dashboard. Guards the fields that are read without optional chaining
 * downstream, so a partial or errored payload can never be made active.
 */
export function isValidAnalysis(analysis) {
  const summary = analysis?.summary;

  return Boolean(
    Array.isArray(analysis?.qubits) &&
      analysis.qubits.length > 0 &&
      summary &&
      Number.isFinite(summary.average_t1) &&
      Number.isFinite(summary.average_t2) &&
      Number.isFinite(summary.average_qsfi) &&
      Number.isFinite(summary.total_qubits) &&
      Number.isFinite(summary.best_qubit?.qubit)
  );
}

/**
 * Maps `analysis.qubits` onto the dashboard's canonical record shape:
 * { day, qubit, t1, t2, qsfi, status }.
 *
 * The status is taken straight from the backend (which applies the same
 * "QSFI >= average is Stable" rule as attachStatus) rather than recomputed -
 * the backend stays the source of truth for uploaded-file analysis.
 */
export function mapAnalysisToRecords(analysis, dayNumber = UPLOADED_DAY_NUMBER) {
  if (!analysis?.qubits) return [];

  const dayLabel = `Day ${dayNumber}`;

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

/**
 * Provenance and data-quality facts about an analysis, kept deliberately
 * separate from the per-qubit records: these describe the dataset as a whole
 * and must not be mixed into individual rows, which the dashboard's
 * calculations iterate over.
 *
 * `averageQsfi` is converted to microseconds for display consistency; every
 * other field is passed through as the backend reported it.
 */
export function extractAnalysisMetadata(analysis) {
  if (!analysis) return null;

  const quality = analysis.data_quality ?? {};

  return {
    filename: analysis.filename ?? null,
    processedFilename: analysis.processed_filename ?? null,
    analyzedAt: analysis.analyzed_at ?? null,
    rowsReceived: quality.rows_received ?? null,
    rowsAnalyzed: quality.rows_analyzed ?? null,
    rowsWithMissingValuesDropped: quality.rows_with_missing_values_dropped ?? null,
    duplicateRowsRemoved: quality.duplicate_rows_removed ?? null,
    averageQsfi: analysis.summary ? toMicroseconds(analysis.summary.average_qsfi) : null,
  };
}

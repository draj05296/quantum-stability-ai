// Calls for the AI engine's historical trend endpoint.

import { getJson } from "./apiClient";
import { API_ENDPOINTS } from "./config";

/**
 * Fetches GET /trend?days=N: per-qubit QSFI/T1/T2 trend across the backend's
 * last N saved analyses.
 *
 *   { days_analyzed, qubits_analyzed, oldest, latest,
 *     trends: [{ qubit, qsfi_day1, qsfi_latest, qsfi_change_percent,
 *                qsfi_slope, t1_slope, t2_slope }] }
 *
 * `oldest`/`latest` are { filename, analyzed_at } references to the saved
 * analyses the window spans, not calendar days.
 *
 * Throws ApiError (status 400 when fewer than two analyses are saved).
 */
export function fetchTrend(days = 5, { signal } = {}) {
  const query = new URLSearchParams({ days: String(days) });

  return getJson(`${API_ENDPOINTS.trend}?${query}`, { signal });
}

// Calls for the AI engine's risk endpoint.

import { getJson } from "./apiClient";
import { API_ENDPOINTS } from "./config";

/**
 * Fetches GET /risk?days=N: a prototype early-instability score per qubit,
 * computed by the backend from its last N saved analyses.
 *
 *   { days_analyzed, qubits_analyzed, oldest, latest,
 *     risk_results: [{ qubit, risk_score, risk_level, qsfi_change_percent,
 *                      qsfi_slope, t1_slope, t2_slope }] }
 *
 * risk_results arrives sorted highest score first. The score is a
 * project-defined heuristic, not a validated failure probability.
 *
 * Throws ApiError (status 400 when fewer than two analyses are saved).
 */
export function fetchRisk(days = 5, { signal } = {}) {
  const query = new URLSearchParams({ days: String(days) });

  return getJson(`${API_ENDPOINTS.risk}?${query}`, { signal });
}

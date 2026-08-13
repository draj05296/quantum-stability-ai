// Calls for the AI engine's analysis endpoints.

import { postFormData } from "./apiClient";
import { API_ENDPOINTS } from "./config";

// The backend's UploadFile parameter is named `file`; the multipart field
// name has to match it exactly or FastAPI answers 422.
const FILE_FIELD_NAME = "file";

/**
 * Uploads one CSV to POST /analyze and returns the parsed analysis:
 *
 *   { success, filename, processed_filename, analyzed_at,
 *     summary: { total_qubits, average_t1, average_t2, average_qsfi,
 *                best_qubit: { qubit, qsfi }, worst_qubit: { qubit, qsfi } },
 *     data_quality: { rows_received, duplicate_rows_removed, missing_values,
 *                     rows_with_missing_values_dropped, rows_analyzed },
 *     qubits: [{ qubit, t1, t2, qsfi, status }] }
 *
 * T1/T2/QSFI come back in seconds (as stored in the CSV) - use
 * utils/analysisAdapter to convert them into the microsecond-based shape the
 * dashboard renders.
 *
 * Throws ApiError if the file is rejected (400), the request is malformed
 * (422), the server errors (500), or the backend can't be reached.
 */
export function analyzeCsvFile(file, { signal } = {}) {
  const formData = new FormData();
  formData.append(FILE_FIELD_NAME, file);

  return postFormData(API_ENDPOINTS.analyze, formData, { signal });
}

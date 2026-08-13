// Minimal fetch wrapper for the QSFI AI engine.
//
// This is the only place that knows how the backend reports failures, so
// callers can just catch ApiError and show `error.message` instead of
// unpicking FastAPI's response bodies themselves. Uses the platform fetch -
// no HTTP dependency is added to the project.

import { API_BASE_URL } from "./config";

/** An error from the API layer, carrying the HTTP status when there was one. */
export class ApiError extends Error {
  constructor(message, { status = null, cause = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.cause = cause;
  }
}

/**
 * Pulls a human-readable message out of a FastAPI error body.
 *
 * FastAPI uses `detail` for both raised HTTPExceptions (a string) and request
 * validation failures (a list of {loc, msg} objects), so both shapes are
 * handled here.
 */
function extractErrorMessage(payload, fallback) {
  const detail = payload?.detail;

  if (typeof detail === "string" && detail.trim() !== "") return detail;

  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((item) => (typeof item === "string" ? item : item?.msg))
      .filter(Boolean);

    if (messages.length > 0) return messages.join("; ");
  }

  return fallback;
}

async function readJsonBody(response) {
  try {
    return await response.json();
  } catch {
    // A non-JSON body (proxy error page, empty 500, ...) isn't fatal here -
    // the caller falls back to a status-based message.
    return null;
  }
}

/**
 * POSTs multipart/form-data to `path` and returns the parsed JSON response.
 *
 * The Content-Type header is deliberately not set: the browser has to add it
 * itself so the multipart boundary is included.
 *
 * Throws ApiError on a non-2xx response or an unreachable server. AbortError
 * is re-thrown untouched so callers can tell a cancellation apart from a
 * genuine failure.
 */
export async function postFormData(path, formData, { signal } = {}) {
  const url = `${API_BASE_URL}${path}`;
  let response;

  try {
    response = await fetch(url, { method: "POST", body: formData, signal });
  } catch (error) {
    if (error?.name === "AbortError") throw error;

    throw new ApiError(
      `Could not reach the QSFI AI engine at ${API_BASE_URL}. Make sure the backend is running.`,
      { cause: error }
    );
  }

  const payload = await readJsonBody(response);

  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(payload, `Request failed with status ${response.status}.`),
      { status: response.status }
    );
  }

  return payload;
}

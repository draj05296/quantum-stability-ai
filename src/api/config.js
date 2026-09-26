// Configuration for the QSFI AI engine (the FastAPI backend under ai-engine/).
//
// The base URL can be overridden per environment with VITE_API_BASE_URL in a
// .env file; it falls back to the local dev address the backend runs on, so
// no extra setup is needed to work locally.

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

// Trailing slashes are stripped so `${API_BASE_URL}${path}` never produces a
// double slash.
export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, "");

export const API_ENDPOINTS = {
  analyze: "/analyze",
  risk: "/risk",
};

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRisk } from "../api/riskApi";

/** Request lifecycle states, mirroring useAnalyzeUpload. */
export const RISK_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

const NOT_ENOUGH_ANALYSES_MESSAGE =
  "At least two uploaded analyses are required for risk analysis.";

/**
 * Owns the state of a GET /risk request. Nothing is fetched until the UI
 * calls `loadRisk`, so the dashboard never depends on the backend to render.
 *
 * Only one request is active at a time: a new one aborts the previous, and
 * unmounting aborts whatever is still running.
 */
export function useRiskAnalysis() {
  const [status, setStatus] = useState(RISK_STATUS.IDLE);
  const [risk, setRisk] = useState(null);
  const [error, setError] = useState(null);

  const abortControllerRef = useRef(null);

  const abortActiveRequest = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  useEffect(() => abortActiveRequest, [abortActiveRequest]);

  const loadRisk = useCallback(
    async (days = 5) => {
      abortActiveRequest();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus(RISK_STATUS.LOADING);
      setError(null);

      try {
        const result = await fetchRisk(days, { signal: controller.signal });

        setRisk(result);
        setStatus(RISK_STATUS.SUCCESS);
      } catch (requestError) {
        if (requestError?.name === "AbortError") return;

        // 400 means fewer than two saved analyses: an expected empty state.
        setError(
          requestError.status === 400
            ? NOT_ENOUGH_ANALYSES_MESSAGE
            : requestError.message || "Risk analysis failed. Please try again."
        );
        setRisk(null);
        setStatus(RISK_STATUS.ERROR);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [abortActiveRequest]
  );

  return {
    status,
    isLoading: status === RISK_STATUS.LOADING,
    risk,
    error,
    loadRisk,
  };
}

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchTrend } from "../api/trendApi";

/** Request lifecycle states, mirroring useRiskAnalysis. */
export const TREND_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

const NOT_ENOUGH_ANALYSES_MESSAGE =
  "At least two uploaded analyses are required for historical trend analysis.";

/**
 * Owns the state of a GET /trend request. Nothing is fetched until the UI
 * calls `loadTrend`, so the dashboard never depends on the backend to render.
 *
 * Only one request is active at a time: a new one aborts the previous, and
 * unmounting aborts whatever is still running.
 */
export function useTrendAnalysis() {
  const [status, setStatus] = useState(TREND_STATUS.IDLE);
  const [trend, setTrend] = useState(null);
  const [error, setError] = useState(null);

  const abortControllerRef = useRef(null);

  const abortActiveRequest = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  useEffect(() => abortActiveRequest, [abortActiveRequest]);

  const loadTrend = useCallback(
    async (days = 5) => {
      abortActiveRequest();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus(TREND_STATUS.LOADING);
      setError(null);

      try {
        const result = await fetchTrend(days, { signal: controller.signal });

        setTrend(result);
        setStatus(TREND_STATUS.SUCCESS);
      } catch (requestError) {
        if (requestError?.name === "AbortError") return;

        // 400 means fewer than two saved analyses: an expected empty state.
        setError(
          requestError.status === 400
            ? NOT_ENOUGH_ANALYSES_MESSAGE
            : requestError.message || "Historical trend analysis failed. Please try again."
        );
        setTrend(null);
        setStatus(TREND_STATUS.ERROR);
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
    isLoading: status === TREND_STATUS.LOADING,
    trend,
    error,
    loadTrend,
  };
}

import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeCsvFile } from "../api/analyzeApi";

/** Request lifecycle states, so components branch on a status instead of juggling booleans. */
export const ANALYZE_STATUS = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
};

/**
 * Owns the state of a POST /analyze upload: which file was sent, whether a
 * request is in flight, the parsed analysis, and any error message.
 *
 * Only one request is ever active - starting a new one aborts the previous
 * request, and unmounting aborts whatever is still running, so a late
 * response can never write state into an unmounted component.
 */
export function useAnalyzeUpload() {
  const [status, setStatus] = useState(ANALYZE_STATUS.IDLE);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [analyzedFileName, setAnalyzedFileName] = useState(null);

  const abortControllerRef = useRef(null);

  const abortActiveRequest = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  useEffect(() => abortActiveRequest, [abortActiveRequest]);

  const analyzeFile = useCallback(
    async (file) => {
      if (!file) return;

      abortActiveRequest();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus(ANALYZE_STATUS.LOADING);
      setError(null);

      try {
        const result = await analyzeCsvFile(file, { signal: controller.signal });

        setAnalysis(result);
        setAnalyzedFileName(file.name);
        setStatus(ANALYZE_STATUS.SUCCESS);
      } catch (requestError) {
        // A superseded/unmounted request isn't a failure the user should see.
        if (requestError?.name === "AbortError") return;

        setError(requestError.message || "Analysis failed. Please try again.");
        setAnalysis(null);
        setStatus(ANALYZE_STATUS.ERROR);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [abortActiveRequest]
  );

  /** Clears the last result/error and cancels anything still in flight. */
  const reset = useCallback(() => {
    abortActiveRequest();
    setStatus(ANALYZE_STATUS.IDLE);
    setAnalysis(null);
    setError(null);
    setAnalyzedFileName(null);
  }, [abortActiveRequest]);

  return {
    status,
    isLoading: status === ANALYZE_STATUS.LOADING,
    analysis,
    error,
    analyzedFileName,
    analyzeFile,
    reset,
  };
}

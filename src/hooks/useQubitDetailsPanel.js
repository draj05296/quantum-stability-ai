import { useCallback, useEffect, useMemo, useState } from "react";
import { computeSelectedQubitDetails } from "../utils/dashboardCalculations";

// Slide-in/out transition duration for the panel, in ms. Must stay in sync
// with the CSS transition on .qubit-panel (see App.css).
const PANEL_CLOSE_ANIMATION_MS = 320;

/**
 * Owns the Qubit Details side panel's open/close state and the derived data
 * for whichever qubit is currently selected. Closing is a two-step process
 * (start the CSS transition, then unmount after it finishes) so the slide-out
 * animation has time to play before the panel's data is cleared.
 */
export function useQubitDetailsPanel(allRecords) {
  const [selectedQubit, setSelectedQubit] = useState(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  useEffect(() => {
    if (selectedQubit === null) return undefined;

    const raf = requestAnimationFrame(() => setIsPanelOpen(true));
    return () => cancelAnimationFrame(raf);
  }, [selectedQubit]);

  const openQubitPanel = useCallback((qubit) => {
    setSelectedQubit(qubit);
  }, []);

  const closeQubitPanel = useCallback(() => {
    setIsPanelOpen(false);
    window.setTimeout(() => setSelectedQubit(null), PANEL_CLOSE_ANIMATION_MS);
  }, []);

  const selectedQubitDetails = useMemo(
    () => computeSelectedQubitDetails(allRecords, selectedQubit),
    [allRecords, selectedQubit]
  );

  return { selectedQubitDetails, isPanelOpen, openQubitPanel, closeQubitPanel };
}

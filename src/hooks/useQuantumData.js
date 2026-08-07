import { useEffect, useState } from "react";
import { getAllQuantumData } from "../data/quantumData";
import {
  attachStatus,
  buildRecordsFromRawData,
  computeDailyTrend,
  computeSummaryStats,
  formatSummaryCardValues,
} from "../utils/dashboardCalculations";

/**
 * Loads all five days of CSV data once on mount and derives the flattened
 * per-qubit-per-day records, the top summary card values, and the daily
 * average trend used across the dashboard.
 */
export function useQuantumData() {
  const [summary, setSummary] = useState(null);
  const [allRecords, setAllRecords] = useState([]);
  const [trendData, setTrendData] = useState([]);

  useEffect(() => {
    let isMounted = true;

    getAllQuantumData().then((data) => {
      const records = buildRecordsFromRawData(data);

      if (!isMounted || records.length === 0) return;

      const stats = computeSummaryStats(records);
      const dailyTrend = computeDailyTrend(records);
      const recordsWithStatus = attachStatus(records, stats.avgQsfi);

      setSummary(formatSummaryCardValues(stats));
      setAllRecords(recordsWithStatus);
      setTrendData(dailyTrend);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  const isLoading = allRecords.length === 0;

  return { summary, allRecords, trendData, isLoading };
}

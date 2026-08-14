// Pure, framework-free calculations for the QSFI dashboard. Nothing in this
// file touches React state - each function takes plain data in and returns
// plain data out, which keeps the numbers easy to unit-test and reuse across
// hooks/components without duplicating formulas.

import { QSFI_BIN_COUNT, SEC_TO_US, TREND_THRESHOLD_PERCENT } from "./constants";

export function toMicroseconds(seconds) {
  return seconds * SEC_TO_US;
}

// Minimum readings a qubit needs before a regression forecast is meaningful.
// A single reading yields a zero-variance fit (R² = 1), which would report
// 100% confidence from one data point - so those qubits are skipped entirely
// rather than given a fabricated prediction.
const MIN_READINGS_FOR_PREDICTION = 2;

// Every "day" value in this dataset is the literal string "Day N" - this is
// the single place that turns it back into a number, so sorting/lookups by
// day stay consistent everywhere they're needed. An unparseable label falls
// back to 0 so a stray value can never poison a sort comparator or an
// equality lookup with NaN.
export function getDayNumber(dayLabel) {
  const dayNumber = Number(String(dayLabel).replace("Day ", ""));
  return Number.isFinite(dayNumber) ? dayNumber : 0;
}

/**
 * Flattens the { day1: [...], day2: [...], ... } shape returned by
 * getAllQuantumData() into one array of { day, qubit, t1, t2, qsfi } rows,
 * converting T1/T2 from seconds to microseconds and computing QSFI.
 * Rows with a missing Qubit/T1/T2 are skipped.
 */
export function buildRecordsFromRawData(data) {
  const records = [];

  Object.values(data).forEach((dayRows, dayIndex) => {
    dayRows.forEach((row) => {
      if (row.Qubit == null || row.T1 == null || row.T2 == null) return;

      const t1 = toMicroseconds(row.T1);
      const t2 = toMicroseconds(row.T2);

      records.push({
        day: `Day ${dayIndex + 1}`,
        qubit: row.Qubit,
        t1,
        t2,
        qsfi: (t1 + t2) / 2,
      });
    });
  });

  return records;
}

/** Site-wide averages, best qubit, and total qubit count used by the summary cards. */
export function computeSummaryStats(records) {
  const avgT1 = records.reduce((sum, r) => sum + r.t1, 0) / records.length;
  const avgT2 = records.reduce((sum, r) => sum + r.t2, 0) / records.length;
  const avgQsfi = (avgT1 + avgT2) / 2;
  const totalQubits = new Set(records.map((r) => r.qubit)).size;

  const bestRecord = records.reduce(
    (best, r) => (r.qsfi > best.qsfi ? r : best),
    records[0]
  );

  return { avgT1, avgT2, avgQsfi, totalQubits, bestRecord };
}

/** Formats computeSummaryStats() output into the label->value map the summary cards render. */
export function formatSummaryCardValues({ avgQsfi, bestRecord, avgT1, avgT2, totalQubits }) {
  return {
    "Average QSFI": avgQsfi.toFixed(2),
    "Best Qubit": `Q${bestRecord.qubit}`,
    "Average T1": `${avgT1.toFixed(2)} μs`,
    "Average T2": `${avgT2.toFixed(2)} μs`,
    "Total Qubits": `${totalQubits}`,
  };
}

/** Attaches a Stable/Degrading status to each record based on the site-wide average QSFI. */
export function attachStatus(records, avgQsfi) {
  return records.map((r) => ({
    ...r,
    status: r.qsfi >= avgQsfi ? "Stable" : "Degrading",
  }));
}

/** Average T1/T2/QSFI per day across all qubits, sorted chronologically. */
export function computeDailyTrend(records) {
  const dailyTotals = new Map();

  records.forEach((r) => {
    const entry = dailyTotals.get(r.day) ?? {
      t1Total: 0,
      t2Total: 0,
      qsfiTotal: 0,
      count: 0,
    };
    entry.t1Total += r.t1;
    entry.t2Total += r.t2;
    entry.qsfiTotal += r.qsfi;
    entry.count += 1;
    dailyTotals.set(r.day, entry);
  });

  return Array.from(dailyTotals.entries())
    .map(([day, { t1Total, t2Total, qsfiTotal, count }]) => ({
      day,
      t1: t1Total / count,
      t2: t2Total / count,
      qsfi: qsfiTotal / count,
    }))
    .sort((a, b) => getDayNumber(a.day) - getDayNumber(b.day));
}

/** Stable vs. Degrading counts (with % share) for the stability pie chart. */
export function computeStabilityDistribution(allRecords, colors) {
  const total = allRecords.length;
  const stableCount = allRecords.filter((r) => r.status === "Stable").length;
  const degradingCount = total - stableCount;

  return [
    { name: "Stable", value: stableCount, total, color: colors.stable },
    { name: "Degrading", value: degradingCount, total, color: colors.degrading },
  ];
}

/** Buckets every reading's QSFI value into QSFI_BIN_COUNT equal-width ranges. */
export function computeQsfiDistribution(allRecords, binCount = QSFI_BIN_COUNT) {
  if (allRecords.length === 0) return [];

  const qsfiValues = allRecords.map((r) => r.qsfi);
  const min = Math.min(...qsfiValues);
  const max = Math.max(...qsfiValues);
  const binSize = (max - min) / binCount || 1;

  const bins = Array.from({ length: binCount }, (_, index) => {
    const rangeStart = min + index * binSize;
    const rangeEnd = index === binCount - 1 ? max : rangeStart + binSize;
    return {
      range: `${rangeStart.toFixed(0)}–${rangeEnd.toFixed(0)}`,
      count: 0,
    };
  });

  qsfiValues.forEach((value) => {
    let index = Math.floor((value - min) / binSize);
    if (index >= binCount) index = binCount - 1;
    if (index < 0) index = 0;
    bins[index].count += 1;
  });

  return bins;
}

/** Per-qubit average T1/T2 (across all days) for the T1 vs T2 scatter plot. */
export function computeQubitScatterData(allRecords) {
  const qubitTotals = new Map();

  allRecords.forEach((r) => {
    const entry = qubitTotals.get(r.qubit) ?? {
      qubit: r.qubit,
      t1Total: 0,
      t2Total: 0,
      count: 0,
    };
    entry.t1Total += r.t1;
    entry.t2Total += r.t2;
    entry.count += 1;
    qubitTotals.set(r.qubit, entry);
  });

  return Array.from(qubitTotals.values()).map(
    ({ qubit, t1Total, t2Total, count }) => ({
      qubit,
      t1: t1Total / count,
      t2: t2Total / count,
    })
  );
}

/** Ordinary least-squares fit of y over x, plus R² (clamped to 0-100%) as a confidence score. */
export function linearRegression(points) {
  const n = points.length;
  const sumX = points.reduce((sum, p) => sum + p.x, 0);
  const sumY = points.reduce((sum, p) => sum + p.y, 0);
  const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
  const sumXX = points.reduce((sum, p) => sum + p.x * p.x, 0);

  const denominator = n * sumXX - sumX * sumX;
  const slope = denominator === 0 ? 0 : (n * sumXY - sumX * sumY) / denominator;
  const intercept = (sumY - slope * sumX) / n;

  const meanY = sumY / n;
  const ssTot = points.reduce((sum, p) => sum + (p.y - meanY) ** 2, 0);
  const ssRes = points.reduce((sum, p) => {
    const fitted = intercept + slope * p.x;
    return sum + (p.y - fitted) ** 2;
  }, 0);

  const rSquared = ssTot === 0 ? 1 : 1 - ssRes / ssTot;
  const confidence = Math.max(0, Math.min(1, rSquared)) * 100;

  return { slope, intercept, confidence };
}

/**
 * Fits a linear regression to each qubit's 5-day QSFI history and forecasts
 * day 6, classifying the qubit as Improving/Stable/Degrading based on the
 * expected % change.
 *
 * Qubits with fewer than MIN_READINGS_FOR_PREDICTION readings are excluded:
 * a single-point fit is mathematically degenerate (slope 0, R² 1), so
 * including them would publish a meaningless forecast at 100% confidence.
 */
export function computeQubitPredictions(
  allRecords,
  trendThresholdPercent = TREND_THRESHOLD_PERCENT
) {
  const qubitGroups = new Map();

  allRecords.forEach((r) => {
    const dayNumber = getDayNumber(r.day);
    const entry = qubitGroups.get(r.qubit) ?? [];
    entry.push({ x: dayNumber, y: r.qsfi });
    qubitGroups.set(r.qubit, entry);
  });

  return Array.from(qubitGroups.entries())
    .filter(([, points]) => points.length >= MIN_READINGS_FOR_PREDICTION)
    .map(([qubit, points]) => {
      const sortedPoints = [...points].sort((a, b) => a.x - b.x);
      const { slope, intercept, confidence } = linearRegression(sortedPoints);

      const lastPoint = sortedPoints[sortedPoints.length - 1];
      const currentQsfi = lastPoint.y;
      const nextDay = lastPoint.x + 1;
      const predictedQsfi = intercept + slope * nextDay;

      const percentChange =
        currentQsfi !== 0
          ? ((predictedQsfi - currentQsfi) / currentQsfi) * 100
          : 0;

      let trend = "Stable";
      if (percentChange > trendThresholdPercent) trend = "Improving";
      else if (percentChange < -trendThresholdPercent) trend = "Degrading";

      return {
        qubit,
        slope,
        intercept,
        currentQsfi,
        predictedQsfi,
        percentChange,
        trend,
        confidence,
      };
    })
    .sort((a, b) => a.qubit - b.qubit);
}

/** Average predicted QSFI plus a count of qubits in each trend bucket. */
export function computePredictionSummary(qubitPredictions) {
  if (qubitPredictions.length === 0) return null;

  const avgPredictedQsfi =
    qubitPredictions.reduce((sum, p) => sum + p.predictedQsfi, 0) /
    qubitPredictions.length;

  const improvingCount = qubitPredictions.filter((p) => p.trend === "Improving").length;
  const stableCount = qubitPredictions.filter((p) => p.trend === "Stable").length;
  const degradingCount = qubitPredictions.filter((p) => p.trend === "Degrading").length;

  return {
    "Average Predicted QSFI": `${avgPredictedQsfi.toFixed(2)} μs`,
    "Improving Qubits": `${improvingCount}`,
    "Stable Qubits": `${stableCount}`,
    "Degrading Qubits": `${degradingCount}`,
  };
}

/**
 * Builds the Actual-vs-Predicted chart series: real daily averages for days
 * 1-5, plus each qubit's fitted regression line averaged per day and
 * extended one day into the future (Day 6 forecast).
 */
export function computePredictionChartData(qubitPredictions, trendData) {
  if (qubitPredictions.length === 0 || trendData.length === 0) return [];

  const dayNumbers = [1, 2, 3, 4, 5, 6];

  return dayNumbers.map((dayNumber) => {
    const actualEntry = trendData.find((t) => getDayNumber(t.day) === dayNumber);

    const avgFitted =
      qubitPredictions.reduce((sum, p) => {
        const fittedValue =
          dayNumber === 6 ? p.predictedQsfi : p.intercept + p.slope * dayNumber;
        return sum + fittedValue;
      }, 0) / qubitPredictions.length;

    return {
      day: dayNumber === 6 ? "Day 6 (Forecast)" : `Day ${dayNumber}`,
      actual: actualEntry ? actualEntry.qsfi : null,
      predicted: avgFitted,
    };
  });
}

/**
 * Builds the data shown in the Qubit Details side panel: the selected
 * qubit's 5 daily readings plus highest/lowest/average QSFI and an overall
 * stability status (majority vote of its daily statuses).
 */
export function computeSelectedQubitDetails(allRecords, selectedQubit) {
  if (selectedQubit === null) return null;

  const records = allRecords
    .filter((r) => r.qubit === selectedQubit)
    .sort((a, b) => getDayNumber(a.day) - getDayNumber(b.day));

  if (records.length === 0) return null;

  const qsfiValues = records.map((r) => r.qsfi);
  const highestQsfi = Math.max(...qsfiValues);
  const lowestQsfi = Math.min(...qsfiValues);
  const averageQsfi = qsfiValues.reduce((sum, value) => sum + value, 0) / qsfiValues.length;

  const stableCount = records.filter((r) => r.status === "Stable").length;
  const stabilityStatus = stableCount >= records.length - stableCount ? "Stable" : "Degrading";

  return {
    qubit: selectedQubit,
    records,
    highestQsfi,
    lowestQsfi,
    averageQsfi,
    stabilityStatus,
  };
}

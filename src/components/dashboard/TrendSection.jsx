import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTrendAnalysis } from "../../hooks/useTrendAnalysis";
import { toMicroseconds } from "../../utils/dashboardCalculations";

const TREND_DAYS = 5;
const MAX_TABLE_ROWS = 25;
const TOP_DECLINES_COUNT = 5;

// Display-only bucketing of qsfi_change_percent into a direction label. This
// is a formatting convenience, not a stability classification - the backend
// does not classify these qubits, so no status such as "unstable" is applied.
const NEUTRAL_CHANGE_PERCENT_THRESHOLD = 0.5;

function directionOf(changePercent) {
  if (changePercent <= -NEUTRAL_CHANGE_PERCENT_THRESHOLD) return "Declining";
  if (changePercent >= NEUTRAL_CHANGE_PERCENT_THRESHOLD) return "Improving";
  return "No significant change";
}

function directionClassName(changePercent) {
  if (changePercent <= -NEUTRAL_CHANGE_PERCENT_THRESHOLD) return "trend-decline";
  if (changePercent >= NEUTRAL_CHANGE_PERCENT_THRESHOLD) return "trend-improve";
  return "trend-neutral";
}

function formatReference(reference) {
  if (!reference?.filename) return "—";
  if (!reference.analyzed_at) return reference.filename;

  return `${reference.filename} (${new Date(reference.analyzed_at).toLocaleString()})`;
}

function formatSlope(secondsPerStep) {
  const perStepUs = toMicroseconds(secondsPerStep);
  const sign = perStepUs > 0 ? "+" : "";
  return `${sign}${perStepUs.toFixed(4)} μs/analysis`;
}

function formatQsfiUs(seconds) {
  return `${toMicroseconds(seconds).toFixed(2)} μs`;
}

function formatPointLabel(point, index) {
  if (!point.analyzed_at) return `Analysis ${index + 1}`;
  return new Date(point.analyzed_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

/** Tooltip for the selected-qubit historical QSFI chart: filename, timestamp, QSFI, T1, T2. */
function QubitHistoryTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;

  const point = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{point.filename ?? "Unknown analysis"}</span>
      {point.analyzed_at && (
        <span className="chart-tooltip-value">
          {new Date(point.analyzed_at).toLocaleString()}
        </span>
      )}
      <span className="chart-tooltip-metric">QSFI: {formatQsfiUs(point.qsfi)}</span>
      <span className="chart-tooltip-metric">T1: {formatQsfiUs(point.t1)}</span>
      <span className="chart-tooltip-metric">T2: {formatQsfiUs(point.t2)}</span>
    </div>
  );
}

/** Tooltip for the average-QSFI-across-analyses chart. */
function AverageQsfiTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;

  const point = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{point.filename ?? point.label}</span>
      {point.analyzed_at && (
        <span className="chart-tooltip-value">
          {new Date(point.analyzed_at).toLocaleString()}
        </span>
      )}
      <span className="chart-tooltip-metric">
        Average QSFI: {formatQsfiUs(point.averageQsfi)} ({point.qubitCount} qubits)
      </span>
    </div>
  );
}

/**
 * Historical Trend Analysis: per-qubit QSFI/T1/T2 trend across the backend's
 * saved analysis history, loaded on demand.
 *
 * Each qubit trend now carries a `history` array - its actual measured
 * QSFI/T1/T2 from every saved analysis in the selected window, straight from
 * the saved PostgreSQL records (see ai-engine/services/trend_service.py).
 * Nothing here interpolates or invents a point: a qubit only appears in
 * `trends` (and so only has a chart/history to show) when it has a real
 * reading in every one of those analyses.
 */
function TrendSection() {
  const { isLoading, trend, error, loadTrend } = useTrendAnalysis();
  // Only what the user explicitly picked from the dropdown. null means "no
  // explicit choice yet" - the default below applies instead - rather than
  // syncing a default value into state via an effect.
  const [explicitSelectedQubit, setExplicitSelectedQubit] = useState(null);

  const sortedTrends = useMemo(() => {
    if (!trend) return [];
    // Ascending by qsfi_change_percent: the largest declines (most negative) first.
    return [...trend.trends].sort(
      (a, b) => a.qsfi_change_percent - b.qsfi_change_percent
    );
  }, [trend]);

  // Defaults to the largest actual QSFI decline (the same ordering used for
  // "Largest QSFI declines" below) whenever there's no explicit choice, or
  // the explicitly chosen qubit isn't in the current result (e.g. after
  // refreshing to a window that no longer includes it).
  const selectedQubit = useMemo(() => {
    if (
      explicitSelectedQubit !== null &&
      sortedTrends.some((t) => t.qubit === explicitSelectedQubit)
    ) {
      return explicitSelectedQubit;
    }
    return sortedTrends[0]?.qubit ?? null;
  }, [explicitSelectedQubit, sortedTrends]);

  const selectedTrend = useMemo(
    () => trend?.trends.find((t) => t.qubit === selectedQubit) ?? null,
    [trend, selectedQubit]
  );

  const chartData = useMemo(() => {
    if (!selectedTrend) return [];
    return selectedTrend.history.map((point, index) => ({
      ...point,
      label: formatPointLabel(point, index),
      qsfiUs: toMicroseconds(point.qsfi),
    }));
  }, [selectedTrend]);

  // Average QSFI per analysis, computed only from qubits with a complete
  // measured history (i.e. every qubit already in `trends`) - a real
  // aggregate of actual returned values, not a fabricated series. Every
  // trend's `history` is the same length and chronological order (see
  // trend_service.get_trend_analysis), so index i across all trends
  // corresponds to the same saved analysis.
  const averageQsfiSeries = useMemo(() => {
    if (!trend || trend.trends.length === 0) return [];

    const pointCount = trend.trends[0].history.length;

    return Array.from({ length: pointCount }, (_, index) => {
      const reference = trend.trends[0].history[index];
      const qsfiValues = trend.trends.map((t) => t.history[index].qsfi);
      const averageQsfi =
        qsfiValues.reduce((sum, value) => sum + value, 0) / qsfiValues.length;

      return {
        label: formatPointLabel(reference, index),
        filename: reference.filename,
        analyzed_at: reference.analyzed_at,
        averageQsfi,
        averageQsfiUs: toMicroseconds(averageQsfi),
        qubitCount: qsfiValues.length,
      };
    });
  }, [trend]);

  const topDeclines = useMemo(
    () =>
      sortedTrends
        .filter((t) => t.qsfi_change_percent < 0)
        .slice(0, TOP_DECLINES_COUNT),
    [sortedTrends]
  );

  const tableRows = sortedTrends.slice(0, MAX_TABLE_ROWS);

  return (
    <div className="analytics-section">
      <div className="analytics-heading">
        <h3>Historical Trend Analysis</h3>
        <p>Track QSFI, T1 and T2 changes across the uploaded analysis history.</p>
      </div>

      <div className="analysis-upload-actions">
        <button
          type="button"
          className="analysis-upload-button"
          onClick={() => loadTrend(TREND_DAYS)}
          disabled={isLoading}
        >
          {isLoading
            ? "Loading…"
            : trend
              ? "Refresh Trend"
              : "Load Historical Trend"}
        </button>
      </div>

      {isLoading && (
        <p className="analysis-upload-status" role="status">
          Loading historical trend data…
        </p>
      )}

      {error && (
        <p className="analysis-upload-error" role="alert">
          {error}
        </p>
      )}

      {!trend && !isLoading && !error && (
        <p className="analysis-upload-status">
          Load historical analysis data to view QSFI, T1 and T2 trends across
          previous uploads.
        </p>
      )}

      {trend && (
        <div className="analysis-upload-result">
          <p className="analysis-upload-status">
            Based on the last {trend.days_analyzed} uploaded analyses ·{" "}
            {trend.qubits_analyzed} qubits analyzed
          </p>

          <ul className="analysis-quality-list">
            <li>
              <span className="analysis-quality-label">Analyses analyzed</span>
              <span className="analysis-quality-value">{trend.days_analyzed}</span>
            </li>
            <li>
              <span className="analysis-quality-label">Qubits analyzed</span>
              <span className="analysis-quality-value">{trend.qubits_analyzed}</span>
            </li>
            <li>
              <span className="analysis-quality-label">Oldest analysis</span>
              <span className="analysis-quality-value">{formatReference(trend.oldest)}</span>
            </li>
            <li>
              <span className="analysis-quality-label">Latest analysis</span>
              <span className="analysis-quality-value">{formatReference(trend.latest)}</span>
            </li>
          </ul>

          {trend.trends.length === 0 ? (
            <p className="analysis-upload-status">
              No qubit had a measurement in every one of the last{" "}
              {trend.days_analyzed} analyses, so there is no historical series
              to chart.
            </p>
          ) : (
            <>
              <div className="trend-qubit-selector filter-group">
                <label htmlFor="trend-qubit-select">Selected qubit</label>
                <select
                  id="trend-qubit-select"
                  value={selectedQubit ?? ""}
                  onChange={(event) => setExplicitSelectedQubit(Number(event.target.value))}
                >
                  {trend.trends
                    .slice()
                    .sort((a, b) => a.qubit - b.qubit)
                    .map((t) => (
                      <option key={t.qubit} value={t.qubit}>
                        Q{t.qubit}
                      </option>
                    ))}
                </select>
              </div>

              {selectedTrend && (
                <div className="dashboard-graph-panel">
                  <div className="graph-panel-header">
                    <h3>Q{selectedTrend.qubit} — Historical QSFI</h3>
                    <span className="graph-badge">
                      {selectedTrend.history.length} measurements
                    </span>
                  </div>

                  {chartData.length < 2 ? (
                    <p className="analysis-upload-status">
                      Only {chartData.length} measurement is available for Q
                      {selectedTrend.qubit} in this window - not enough to plot a
                      trend line.
                    </p>
                  ) : (
                    <div className="graph-canvas">
                      <ResponsiveContainer width="100%" height={240}>
                        <LineChart
                          data={chartData}
                          margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                        >
                          <defs>
                            <linearGradient id="qubitHistoryGradient" x1="0" y1="0" x2="1" y2="0">
                              <stop offset="0%" stopColor="#00b4ff" />
                              <stop offset="100%" stopColor="#8b5cf6" />
                            </linearGradient>
                          </defs>

                          <CartesianGrid stroke="rgba(255,255,255,.08)" vertical={false} />

                          <XAxis
                            dataKey="label"
                            stroke="rgba(255,255,255,.15)"
                            tick={{ fill: "#9ca3af", fontSize: 12 }}
                            tickLine={false}
                          />

                          <YAxis
                            dataKey="qsfiUs"
                            stroke="rgba(255,255,255,.15)"
                            tick={{ fill: "#9ca3af", fontSize: 12 }}
                            tickLine={false}
                            width={50}
                            tickFormatter={(value) => value.toFixed(0)}
                          />

                          <Tooltip
                            content={<QubitHistoryTooltip />}
                            cursor={{ stroke: "rgba(255,255,255,.2)" }}
                          />

                          <Line
                            type="monotone"
                            dataKey="qsfiUs"
                            stroke="url(#qubitHistoryGradient)"
                            strokeWidth={3}
                            dot={{ r: 5, fill: "#00b4ff", stroke: "#0f172a", strokeWidth: 2 }}
                            activeDot={{ r: 7, fill: "#00b4ff", stroke: "#0f172a", strokeWidth: 2 }}
                            connectNulls={false}
                            animationDuration={900}
                            animationEasing="ease-out"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  <ul className="analysis-quality-list">
                    <li>
                      <span className="analysis-quality-label">Oldest QSFI</span>
                      <span className="analysis-quality-value">
                        {formatQsfiUs(selectedTrend.qsfi_day1)}
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">Latest QSFI</span>
                      <span className="analysis-quality-value">
                        {formatQsfiUs(selectedTrend.qsfi_latest)}
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">QSFI change</span>
                      <span
                        className={
                          directionClassName(selectedTrend.qsfi_change_percent) ===
                          "trend-decline"
                            ? "analysis-quality-value trend-decline"
                            : "analysis-quality-value"
                        }
                      >
                        {selectedTrend.qsfi_change_percent > 0 ? "+" : ""}
                        {selectedTrend.qsfi_change_percent.toFixed(2)}%
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">QSFI slope (estimate)</span>
                      <span className="analysis-quality-value">
                        {formatSlope(selectedTrend.qsfi_slope)}
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">T1 slope (estimate)</span>
                      <span className="analysis-quality-value">
                        {formatSlope(selectedTrend.t1_slope)}
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">T2 slope (estimate)</span>
                      <span className="analysis-quality-value">
                        {formatSlope(selectedTrend.t2_slope)}
                      </span>
                    </li>
                    <li>
                      <span className="analysis-quality-label">Measurements available</span>
                      <span className="analysis-quality-value">
                        {selectedTrend.history.length}
                      </span>
                    </li>
                  </ul>
                </div>
              )}

              {averageQsfiSeries.length >= 2 && (
                <div className="dashboard-graph-panel">
                  <div className="graph-panel-header">
                    <h3>Average QSFI Across Saved Analyses</h3>
                    <span className="graph-badge">
                      {trend.trends.length} qubits with complete history
                    </span>
                  </div>
                  <p className="trend-average-note">
                    Averaged only across the {trend.trends.length} qubits with a
                    measurement in every one of the {trend.days_analyzed} selected
                    analyses - not necessarily the full qubit count.
                  </p>

                  <div className="graph-canvas">
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart
                        data={averageQsfiSeries}
                        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                      >
                        <CartesianGrid stroke="rgba(255,255,255,.08)" vertical={false} />

                        <XAxis
                          dataKey="label"
                          stroke="rgba(255,255,255,.15)"
                          tick={{ fill: "#9ca3af", fontSize: 12 }}
                          tickLine={false}
                        />

                        <YAxis
                          dataKey="averageQsfiUs"
                          stroke="rgba(255,255,255,.15)"
                          tick={{ fill: "#9ca3af", fontSize: 12 }}
                          tickLine={false}
                          width={50}
                          tickFormatter={(value) => value.toFixed(0)}
                        />

                        <Tooltip
                          content={<AverageQsfiTooltip />}
                          cursor={{ stroke: "rgba(255,255,255,.2)" }}
                        />

                        <Line
                          type="monotone"
                          dataKey="averageQsfiUs"
                          stroke="#8b5cf6"
                          strokeWidth={3}
                          dot={{ r: 4, fill: "#8b5cf6", stroke: "#0f172a", strokeWidth: 2 }}
                          activeDot={{ r: 6 }}
                          animationDuration={900}
                          animationEasing="ease-out"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </>
          )}

          {topDeclines.length > 0 && (
            <div className="trend-top-declines">
              <h4>Largest QSFI declines</h4>
              <ul>
                {topDeclines.map((t) => (
                  <li key={t.qubit}>
                    Q{t.qubit}{" "}
                    <span className="trend-decline">
                      ({t.qsfi_change_percent.toFixed(2)}%)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="dashboard-table-section">
            <h3>QSFI, T1 and T2 Trend by Qubit</h3>
            <div className="dashboard-table-wrapper">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Qubit</th>
                    <th>QSFI Change</th>
                    <th>QSFI Slope</th>
                    <th>T1 Slope</th>
                    <th>T2 Slope</th>
                    <th>Direction</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRows.map((t) => (
                    <tr key={t.qubit}>
                      <td>Q{t.qubit}</td>
                      <td className={directionClassName(t.qsfi_change_percent)}>
                        {t.qsfi_change_percent > 0 ? "+" : ""}
                        {t.qsfi_change_percent.toFixed(2)}%
                      </td>
                      <td>{formatSlope(t.qsfi_slope)}</td>
                      <td>{formatSlope(t.t1_slope)}</td>
                      <td>{formatSlope(t.t2_slope)}</td>
                      <td>{directionOf(t.qsfi_change_percent)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {sortedTrends.length > MAX_TABLE_ROWS && (
              <p className="analysis-upload-status">
                Showing the {MAX_TABLE_ROWS} largest declines of{" "}
                {sortedTrends.length} qubits.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default TrendSection;

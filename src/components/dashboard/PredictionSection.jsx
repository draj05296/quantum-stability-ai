import { memo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS, PREDICTION_SUMMARY_LABELS } from "../../utils/constants";
import SummaryCards from "./SummaryCards";
import StatusBadge from "./StatusBadge";
import { PredictionTooltip } from "./ChartTooltips";

/**
 * QSFI Prediction Engine: summary cards (average predicted QSFI + trend
 * counts), an Actual-vs-Predicted QSFI line chart, and a per-qubit
 * prediction table (current/predicted QSFI, difference, trend, confidence).
 * All figures come from linear regression over each qubit's 5-day history.
 */
function PredictionSection({ predictionSummary, predictionChartData, qubitPredictions }) {
  return (
    <div className="analytics-section">
      <div className="analytics-heading">
        <h3>QSFI Prediction Engine</h3>
        <p>
          Linear regression over each qubit's 5-day QSFI history, forecasting
          tomorrow's stability and confidence.
        </p>
      </div>

      <SummaryCards labels={PREDICTION_SUMMARY_LABELS} values={predictionSummary} />

      <div className="dashboard-graph-panel">
        <div className="graph-panel-header">
          <h3>Actual vs Predicted QSFI</h3>
          <span className="graph-badge">Linear Regression</span>
        </div>

        <div className="graph-canvas">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={predictionChartData}
              margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
            >
              <CartesianGrid stroke="rgba(255,255,255,.08)" vertical={false} />

              <XAxis
                dataKey="day"
                stroke="rgba(255,255,255,.15)"
                tick={{ fill: "#9ca3af", fontSize: 12 }}
                tickLine={false}
              />

              <YAxis
                stroke="rgba(255,255,255,.15)"
                tick={{ fill: "#9ca3af", fontSize: 12 }}
                tickLine={false}
                width={50}
                tickFormatter={(value) => value.toFixed(0)}
              />

              <Tooltip
                content={<PredictionTooltip />}
                cursor={{ stroke: "rgba(255,255,255,.2)" }}
              />

              <Legend wrapperStyle={{ color: "#e2e8f0", fontSize: 13 }} />

              <Line
                type="monotone"
                dataKey="actual"
                name="Actual QSFI"
                stroke={CHART_COLORS.primary}
                strokeWidth={3}
                dot={{ r: 4, fill: CHART_COLORS.primary, stroke: "#0f172a", strokeWidth: 2 }}
                activeDot={{ r: 6 }}
                connectNulls={false}
                animationDuration={900}
                animationEasing="ease-out"
              />

              <Line
                type="monotone"
                dataKey="predicted"
                name="Predicted QSFI"
                stroke={CHART_COLORS.secondary}
                strokeWidth={3}
                strokeDasharray="6 4"
                dot={{ r: 4, fill: CHART_COLORS.secondary, stroke: "#0f172a", strokeWidth: 2 }}
                activeDot={{ r: 6 }}
                animationDuration={900}
                animationEasing="ease-out"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="dashboard-table-section">
        <h3>Qubit Predictions</h3>

        <div className="dashboard-table-wrapper">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Qubit</th>
                <th>Current QSFI (μs)</th>
                <th>Predicted QSFI (μs)</th>
                <th>Difference (μs)</th>
                <th>Trend</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {qubitPredictions.length === 0 ? (
                <tr className="table-empty-row">
                  <td colSpan={6}>No prediction data available.</td>
                </tr>
              ) : (
                qubitPredictions.map((p) => {
                  const difference = p.predictedQsfi - p.currentQsfi;
                  return (
                    <tr key={p.qubit}>
                      <td>Q{p.qubit}</td>
                      <td>{p.currentQsfi.toFixed(2)}</td>
                      <td>{p.predictedQsfi.toFixed(2)}</td>
                      <td
                        className={
                          difference >= 0
                            ? "prediction-diff-positive"
                            : "prediction-diff-negative"
                        }
                      >
                        {difference >= 0 ? "+" : ""}
                        {difference.toFixed(2)}
                      </td>
                      <td>
                        <StatusBadge status={p.trend} />
                      </td>
                      <td>{p.confidence.toFixed(0)}%</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default memo(PredictionSection);

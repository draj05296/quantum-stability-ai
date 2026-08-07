import { memo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { TrendTooltip } from "./ChartTooltips";

/** The headline "Fidelity Trends" panel: average QSFI per day. */
function FidelityTrendChart({ trendData }) {
  return (
    <div className="dashboard-graph-panel">
      <div className="graph-panel-header">
        <h3>Fidelity Trends</h3>
        <span className="graph-badge">Live Analytics</span>
      </div>

      <div className="graph-canvas">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00b4ff" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>

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
              content={<TrendTooltip />}
              cursor={{ stroke: "rgba(255,255,255,.2)" }}
            />

            <Line
              type="monotone"
              dataKey="qsfi"
              stroke="url(#trendGradient)"
              strokeWidth={3}
              dot={{ r: 5, fill: "#00b4ff", stroke: "#0f172a", strokeWidth: 2 }}
              activeDot={{ r: 7, fill: "#00b4ff", stroke: "#0f172a", strokeWidth: 2 }}
              animationDuration={900}
              animationEasing="ease-out"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default memo(FidelityTrendChart);

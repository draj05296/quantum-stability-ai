import { memo } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CHART_COLORS } from "../../utils/constants";
import { MetricTooltip } from "./ChartTooltips";

/**
 * Small sparkline-style line chart used three times inside the Qubit
 * Details panel (QSFI/T1/T2 trend over the qubit's 5 daily readings).
 * Pass `gradientId` for the QSFI trend to draw it with the same
 * primary->secondary gradient as the main Fidelity Trends chart; pass a
 * plain `stroke` color for the T1/T2 lines.
 */
function QubitTrendChart({ title, data, dataKey, stroke, gradientId }) {
  const dotColor = gradientId ? CHART_COLORS.primary : stroke;
  const lineStroke = gradientId ? `url(#${gradientId})` : stroke;

  return (
    <div className="qubit-trend-chart">
      <span className="qubit-trend-title">{title}</span>
      <ResponsiveContainer width="100%" height={110}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          {gradientId && (
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor={CHART_COLORS.primary} />
                <stop offset="100%" stopColor={CHART_COLORS.secondary} />
              </linearGradient>
            </defs>
          )}
          <XAxis dataKey="day" hide />
          <YAxis hide domain={["auto", "auto"]} />
          <Tooltip
            content={<MetricTooltip unit="μs" />}
            cursor={{ stroke: "rgba(255,255,255,.2)" }}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={lineStroke}
            strokeWidth={2.5}
            dot={{ r: 3, fill: dotColor, stroke: "#0f172a", strokeWidth: 1.5 }}
            activeDot={{ r: 5 }}
            animationDuration={700}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default memo(QubitTrendChart);

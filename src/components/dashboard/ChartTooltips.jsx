// Custom Recharts tooltip renderers and the pie-slice percentage label,
// shared across the Fidelity Trends, Research Insights, Prediction, and
// Qubit Details charts. All are pure presentational components driven
// entirely by the `active`/`payload`/`label` props Recharts injects.

/** Single-value tooltip for the main Fidelity Trends line chart (day -> QSFI). */
export function TrendTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{label}</span>
      <span className="chart-tooltip-value">
        {payload[0].value.toFixed(2)} μs
      </span>
    </div>
  );
}

/** Generic single-value tooltip with a configurable unit, used by the bar/area charts. */
export function MetricTooltip({ active, payload, label, unit }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{label}</span>
      <span className="chart-tooltip-value">
        {payload[0].value.toFixed(2)} {unit}
      </span>
    </div>
  );
}

/** Stability pie chart tooltip: reading count plus % share. */
export function PieTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;

  const { name, value, total } = payload[0].payload;
  const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{name}</span>
      <span className="chart-tooltip-value">
        {value} readings ({percentage}%)
      </span>
    </div>
  );
}

/** QSFI distribution histogram tooltip. */
export function HistogramTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{label} μs</span>
      <span className="chart-tooltip-value">
        {payload[0].value} qubit readings
      </span>
    </div>
  );
}

/** T1 vs T2 scatter plot tooltip. */
export function ScatterTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;

  const point = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">Q{point.qubit}</span>
      <span className="chart-tooltip-value">T1: {point.t1.toFixed(2)} μs</span>
      <span className="chart-tooltip-value">T2: {point.t2.toFixed(2)} μs</span>
    </div>
  );
}

/** Actual-vs-Predicted chart tooltip: one line per series, colored to match. */
export function PredictionTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-day">{label}</span>
      {payload.map((entry) => (
        <span
          className="chart-tooltip-metric"
          key={entry.dataKey}
          style={{ color: entry.color }}
        >
          {entry.name}:{" "}
          {entry.value != null ? `${entry.value.toFixed(2)} μs` : "—"}
        </span>
      ))}
    </div>
  );
}

/** Custom percentage label rendered on each Stability Distribution pie slice. */
export function renderPieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5 + 22;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="#e2e8f0"
      fontSize={13}
      fontWeight={700}
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

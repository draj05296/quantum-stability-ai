import { memo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "../../utils/constants";
import ChartCard from "./ChartCard";
import {
  HistogramTooltip,
  MetricTooltip,
  PieTooltip,
  renderPieLabel,
  ScatterTooltip,
} from "./ChartTooltips";

/**
 * The six-chart "Analytics Overview" grid: Average T1/T2 per day (bar),
 * Average QSFI per day (area), Stability Distribution (pie), QSFI
 * Distribution (histogram), and T1 vs T2 (scatter). All data is pre-computed
 * by the caller from the shared quantum data records.
 */
function AnalyticsCharts({
  trendData,
  qsfiDistribution,
  stabilityDistribution,
  qubitScatterData,
  isLoading,
}) {
  return (
    <div className="analytics-grid">
      <ChartCard
        title="Average T1 per Day"
        description="Mean T1 relaxation time across all qubits, tracked by day."
        isLoading={isLoading}
      >
        <BarChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="t1BarGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.95} />
              <stop offset="100%" stopColor={CHART_COLORS.secondary} stopOpacity={0.55} />
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
            content={<MetricTooltip unit="μs" />}
            cursor={{ fill: "rgba(255,255,255,.05)" }}
          />
          <Bar
            dataKey="t1"
            fill="url(#t1BarGradient)"
            radius={[8, 8, 0, 0]}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </BarChart>
      </ChartCard>

      <ChartCard
        title="Average T2 per Day"
        description="Mean T2 dephasing time across all qubits, tracked by day."
        isLoading={isLoading}
      >
        <BarChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="t2BarGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.secondary} stopOpacity={0.95} />
              <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.55} />
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
            content={<MetricTooltip unit="μs" />}
            cursor={{ fill: "rgba(255,255,255,.05)" }}
          />
          <Bar
            dataKey="t2"
            fill="url(#t2BarGradient)"
            radius={[8, 8, 0, 0]}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </BarChart>
      </ChartCard>

      <ChartCard
        title="Average QSFI per Day"
        description="Blended stability index (T1 + T2) / 2, tracked by day."
        isLoading={isLoading}
      >
        <AreaChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="qsfiAreaFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.5} />
              <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="qsfiAreaLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor={CHART_COLORS.primary} />
              <stop offset="100%" stopColor={CHART_COLORS.secondary} />
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
            content={<MetricTooltip unit="μs" />}
            cursor={{ stroke: "rgba(255,255,255,.2)" }}
          />
          <Area
            type="monotone"
            dataKey="qsfi"
            stroke="url(#qsfiAreaLine)"
            strokeWidth={3}
            fill="url(#qsfiAreaFill)"
            animationDuration={900}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ChartCard>

      <ChartCard
        title="Stability Distribution"
        description="Share of qubit readings classified Stable vs. Degrading."
        isLoading={isLoading}
        height={320}
      >
        <PieChart>
          <Tooltip content={<PieTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            wrapperStyle={{ color: "#e2e8f0", fontSize: 13 }}
            formatter={(value, entry) => {
              const payload = entry?.payload ?? {};
              const percentage =
                payload.total > 0
                  ? ((payload.value / payload.total) * 100).toFixed(1)
                  : "0.0";
              return `${value}: ${payload.value ?? 0} (${percentage}%)`;
            }}
          />
          <Pie
            data={stabilityDistribution}
            dataKey="value"
            nameKey="name"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={4}
            label={renderPieLabel}
            labelLine={false}
            animationDuration={900}
            animationEasing="ease-out"
          >
            {stabilityDistribution.map((entry) => (
              <Cell key={entry.name} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
            ))}
          </Pie>
        </PieChart>
      </ChartCard>

      <ChartCard
        title="QSFI Distribution"
        description="Count of qubit readings across QSFI value ranges."
        isLoading={isLoading}
      >
        <BarChart data={qsfiDistribution} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
          <defs>
            <linearGradient id="qsfiHistGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.secondary} stopOpacity={0.95} />
              <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.55} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(255,255,255,.08)" vertical={false} />
          <XAxis
            dataKey="range"
            stroke="rgba(255,255,255,.15)"
            tick={{ fill: "#9ca3af", fontSize: 11 }}
            tickLine={false}
            angle={-20}
            textAnchor="end"
            height={50}
          />
          <YAxis
            stroke="rgba(255,255,255,.15)"
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            tickLine={false}
            width={40}
            allowDecimals={false}
          />
          <Tooltip
            content={<HistogramTooltip />}
            cursor={{ fill: "rgba(255,255,255,.05)" }}
          />
          <Bar
            dataKey="count"
            fill="url(#qsfiHistGradient)"
            radius={[6, 6, 0, 0]}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </BarChart>
      </ChartCard>

      <ChartCard
        title="T1 vs T2"
        description="Each point is one qubit, averaged across all days."
        isLoading={isLoading}
      >
        <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,.08)" />
          <XAxis
            type="number"
            dataKey="t1"
            name="T1"
            unit=" μs"
            stroke="rgba(255,255,255,.15)"
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            tickLine={false}
            tickFormatter={(value) => value.toFixed(0)}
          />
          <YAxis
            type="number"
            dataKey="t2"
            name="T2"
            unit=" μs"
            stroke="rgba(255,255,255,.15)"
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            tickLine={false}
            width={50}
            tickFormatter={(value) => value.toFixed(0)}
          />
          <Tooltip
            content={<ScatterTooltip />}
            cursor={{ stroke: "rgba(255,255,255,.2)" }}
          />
          <Scatter
            data={qubitScatterData}
            fill={CHART_COLORS.primary}
            fillOpacity={0.85}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </ScatterChart>
      </ChartCard>
    </div>
  );
}

export default memo(AnalyticsCharts);

import { memo } from "react";
import { ResponsiveContainer } from "recharts";

/**
 * Chrome shared by every chart in the Research Insights / Prediction
 * sections: a title, a short description, and either the chart itself
 * (wrapped in a ResponsiveContainer) or a loading placeholder while the CSV
 * data is still being fetched.
 */
function ChartCard({ title, description, isLoading, height = 280, children }) {
  return (
    <div className="analytics-card">
      <div className="analytics-card-header">
        <h4>{title}</h4>
        <p>{description}</p>
      </div>
      <div className="analytics-card-body">
        {isLoading ? (
          <div className="analytics-placeholder" style={{ height }}>
            <span className="analytics-placeholder-spinner" />
            <span>Loading chart data…</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            {children}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

export default memo(ChartCard);

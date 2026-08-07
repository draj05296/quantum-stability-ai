import { memo } from "react";
import FidelityTrendChart from "./FidelityTrendChart";
import AnalyticsCharts from "./AnalyticsCharts";

/**
 * "Research Insights": the headline Fidelity Trends chart plus the Analytics
 * Overview grid of six charts. The Prediction Engine section is rendered
 * directly below this one.
 */
function ResearchInsights({
  trendData,
  qsfiDistribution,
  stabilityDistribution,
  qubitScatterData,
  isLoading,
}) {
  return (
    <>
      <FidelityTrendChart trendData={trendData} />

      <div className="analytics-section">
        <div className="analytics-heading">
          <h3>Analytics Overview</h3>
          <p>
            Deeper insights into qubit coherence, stability, and distribution
            across the full IBM Quantum dataset.
          </p>
        </div>

        <AnalyticsCharts
          trendData={trendData}
          qsfiDistribution={qsfiDistribution}
          stabilityDistribution={stabilityDistribution}
          qubitScatterData={qubitScatterData}
          isLoading={isLoading}
        />
      </div>
    </>
  );
}

export default memo(ResearchInsights);

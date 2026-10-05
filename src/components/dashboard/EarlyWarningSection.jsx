import { useMemo } from "react";
import { toMicroseconds } from "../../utils/dashboardCalculations";
import StatusBadge from "./StatusBadge";

const MAX_HIGH_ALERTS = 25;
const MAX_MODERATE_LIST = 25;

function formatPercent(value) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

// Reuses the same seconds -> microseconds convention as the rest of the
// dashboard (see utils/dashboardCalculations.toMicroseconds), so a slope
// here reads the same way it does in the Historical Trend table.
function formatSlope(secondsPerStep) {
  const perStepUs = toMicroseconds(secondsPerStep);
  return `${perStepUs > 0 ? "+" : ""}${perStepUs.toFixed(4)} μs/analysis`;
}

/**
 * Early-Warning Alerts: a presentation layer over the risk data the Risk
 * Analysis section already loaded (via the shared useRiskAnalysis state
 * lifted into Dashboard). This component never calls /risk itself - it only
 * reads whatever RiskSection has already fetched, so loading risk data once
 * drives both sections.
 *
 * This surfaces the backend's existing High/Moderate/Low risk_level as
 * plain-language monitoring alerts. It does not compute risk itself, invent
 * new thresholds, or claim to predict hardware failure.
 */
function EarlyWarningSection({ isLoading, risk, error }) {
  const grouped = useMemo(() => {
    const groups = { High: [], Moderate: [], Low: [] };
    risk?.risk_results.forEach((r) => {
      if (r.risk_level in groups) groups[r.risk_level].push(r);
    });
    return groups;
  }, [risk]);

  // The backend already returns risk_results sorted by risk_score
  // descending, but sorting defensively here doesn't depend on that holding.
  const highestRisk = useMemo(() => {
    if (!risk || risk.risk_results.length === 0) return null;
    return [...risk.risk_results].sort((a, b) => b.risk_score - a.risk_score)[0];
  }, [risk]);

  return (
    <div className="analytics-section">
      <div className="analytics-heading">
        <h3>Early-Warning Alerts</h3>
        <p>
          Plain-language monitoring alerts derived from the Risk Analysis
          results above.
        </p>
        <p className="risk-disclaimer">
          Prototype research indicator — not a validated prediction of quantum
          hardware failure.
        </p>
      </div>

      {!risk && !isLoading && !error && (
        <p className="analysis-upload-status">
          Load Risk Analysis to view early-warning alerts.
        </p>
      )}

      {isLoading && (
        <p className="analysis-upload-status" role="status">
          Loading early-warning indicators…
        </p>
      )}

      {error && (
        <p className="analysis-upload-error" role="alert">
          {error}
        </p>
      )}

      {risk && !isLoading && (
        <div className="analysis-upload-result">
          <div className="dashboard-summary">
            <div className="summary-card">
              <span className="summary-label">High</span>
              <span className="summary-value">{grouped.High.length}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Moderate</span>
              <span className="summary-value">{grouped.Moderate.length}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Low</span>
              <span className="summary-value">{grouped.Low.length}</span>
            </div>
          </div>

          {!highestRisk ? (
            <p className="analysis-upload-status">
              No risk results were returned, so there is nothing to alert on.
            </p>
          ) : (
            <div className="early-warning-priority">
              <h4>Highest prototype risk indicator</h4>
              <ul className="analysis-quality-list">
                <li>
                  <span className="analysis-quality-label">Qubit</span>
                  <span className="analysis-quality-value">Q{highestRisk.qubit}</span>
                </li>
                <li>
                  <span className="analysis-quality-label">Risk score</span>
                  <span className="analysis-quality-value">
                    {highestRisk.risk_score.toFixed(2)}
                  </span>
                </li>
                <li>
                  <span className="analysis-quality-label">QSFI change</span>
                  <span className="analysis-quality-value">
                    {formatPercent(highestRisk.qsfi_change_percent)}
                  </span>
                </li>
              </ul>
            </div>
          )}

          {grouped.High.length > 0 && (
            <div className="early-warning-group">
              <h4>High-priority monitoring alerts</h4>
              <div className="early-warning-alert-list">
                {grouped.High.slice(0, MAX_HIGH_ALERTS).map((r) => (
                  <div className="early-warning-alert early-warning-alert-high" key={r.qubit}>
                    <div className="early-warning-alert-header">
                      <span>
                        Q{r.qubit} — High prototype risk indicator
                      </span>
                      <StatusBadge status={r.risk_level} />
                    </div>
                    <p className="early-warning-alert-note">
                      Significant QSFI decline detected. Requires further
                      monitoring.
                    </p>
                    <ul className="analysis-quality-list">
                      <li>
                        <span className="analysis-quality-label">Risk score</span>
                        <span className="analysis-quality-value">
                          {r.risk_score.toFixed(2)}
                        </span>
                      </li>
                      <li>
                        <span className="analysis-quality-label">QSFI change</span>
                        <span className="analysis-quality-value">
                          {formatPercent(r.qsfi_change_percent)}
                        </span>
                      </li>
                      <li>
                        <span className="analysis-quality-label">QSFI slope</span>
                        <span className="analysis-quality-value">
                          {formatSlope(r.qsfi_slope)}
                        </span>
                      </li>
                      <li>
                        <span className="analysis-quality-label">T1 slope</span>
                        <span className="analysis-quality-value">
                          {formatSlope(r.t1_slope)}
                        </span>
                      </li>
                      <li>
                        <span className="analysis-quality-label">T2 slope</span>
                        <span className="analysis-quality-value">
                          {formatSlope(r.t2_slope)}
                        </span>
                      </li>
                    </ul>
                  </div>
                ))}
              </div>
              {grouped.High.length > MAX_HIGH_ALERTS && (
                <p className="analysis-upload-status">
                  Showing {MAX_HIGH_ALERTS} of {grouped.High.length} High
                  prototype risk alerts.
                </p>
              )}
            </div>
          )}

          {grouped.Moderate.length > 0 && (
            <div className="early-warning-group">
              <h4>Moderate-priority monitoring</h4>
              <ul className="early-warning-moderate-list">
                {grouped.Moderate.slice(0, MAX_MODERATE_LIST).map((r) => (
                  <li key={r.qubit} className="early-warning-alert-moderate">
                    <span>
                      Q{r.qubit} — Qubit requires monitoring
                    </span>
                    <span className="early-warning-moderate-detail">
                      Risk score {r.risk_score.toFixed(2)} · QSFI change{" "}
                      {formatPercent(r.qsfi_change_percent)}
                    </span>
                  </li>
                ))}
              </ul>
              {grouped.Moderate.length > MAX_MODERATE_LIST && (
                <p className="analysis-upload-status">
                  Showing {MAX_MODERATE_LIST} of {grouped.Moderate.length}{" "}
                  Moderate monitoring alerts.
                </p>
              )}
            </div>
          )}

          <p className="analysis-upload-status">
            {grouped.Low.length} qubit{grouped.Low.length === 1 ? "" : "s"}{" "}
            currently {grouped.Low.length === 1 ? "has" : "have"} a Low
            prototype risk indicator.
          </p>
        </div>
      )}
    </div>
  );
}

export default EarlyWarningSection;

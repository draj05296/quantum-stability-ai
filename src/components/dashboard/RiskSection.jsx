import { useMemo } from "react";
import StatusBadge from "./StatusBadge";

const RISK_DAYS = 5;
const RISK_LEVELS = ["High", "Moderate", "Low"];
const MAX_TABLE_ROWS = 25;

/**
 * Early Instability Risk: the backend's prototype risk score per qubit,
 * loaded on demand. Independent of the client-side prediction section and of
 * whichever dataset the dashboard is currently showing - the backend scores
 * its own saved upload history.
 *
 * Controlled: the request state lives in Dashboard (via useRiskAnalysis) so
 * EarlyWarningSection can read the same loaded result instead of triggering
 * a second /risk request.
 */
function RiskSection({ isLoading, risk, error, onLoadRisk }) {
  const levelCounts = useMemo(() => {
    const counts = { High: 0, Moderate: 0, Low: 0 };
    risk?.risk_results.forEach((r) => {
      if (r.risk_level in counts) counts[r.risk_level] += 1;
    });
    return counts;
  }, [risk]);

  const topRows = useMemo(
    () => (risk ? risk.risk_results.slice(0, MAX_TABLE_ROWS) : []),
    [risk]
  );

  return (
    <div className="analytics-section">
      <div className="analytics-heading">
        <h3>Early Instability Risk</h3>
        <p>
          Scores each qubit from QSFI, T1 and T2 trends across the last{" "}
          {RISK_DAYS} uploaded analyses saved by the AI engine.
        </p>
        <p className="risk-disclaimer">
          Prototype heuristic — not a validated probability of quantum hardware
          failure.
        </p>
      </div>

      <div className="analysis-upload-actions">
        <button
          type="button"
          className="analysis-upload-button"
          onClick={() => onLoadRisk(RISK_DAYS)}
          disabled={isLoading}
        >
          {isLoading ? "Loading…" : "Load Risk Analysis"}
        </button>
      </div>

      {isLoading && (
        <p className="analysis-upload-status" role="status">
          Calculating risk…
        </p>
      )}

      {error && (
        <p className="analysis-upload-error" role="alert">
          {error}
        </p>
      )}

      {!risk && !isLoading && !error && (
        <p className="analysis-upload-status">
          Press “Load Risk Analysis” to score qubits from the saved analyses.
        </p>
      )}

      {risk && (
        <div className="analysis-upload-result">
          <p className="analysis-upload-status">
            Based on the last {risk.days_analyzed} uploaded analyses ·{" "}
            {risk.qubits_analyzed} qubits analyzed
          </p>

          <div className="dashboard-summary">
            {RISK_LEVELS.map((level) => (
              <div className="summary-card" key={level}>
                <span className="summary-label">{level} risk</span>
                <span className="summary-value">{levelCounts[level]}</span>
              </div>
            ))}
          </div>

          <div className="dashboard-table-section">
            <h3>Highest-Risk Qubits</h3>
            <div className="dashboard-table-wrapper">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Qubit</th>
                    <th>Risk Score</th>
                    <th>Risk Level</th>
                    <th>QSFI Change</th>
                  </tr>
                </thead>
                <tbody>
                  {topRows.map((r) => (
                    <tr key={r.qubit}>
                      <td>Q{r.qubit}</td>
                      <td>{r.risk_score.toFixed(2)}</td>
                      <td>
                        <StatusBadge status={r.risk_level} />
                      </td>
                      <td>
                        {r.qsfi_change_percent > 0 ? "+" : ""}
                        {r.qsfi_change_percent.toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {risk.risk_results.length > MAX_TABLE_ROWS && (
              <p className="analysis-upload-status">
                Showing the {MAX_TABLE_ROWS} highest of{" "}
                {risk.risk_results.length} qubits.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default RiskSection;

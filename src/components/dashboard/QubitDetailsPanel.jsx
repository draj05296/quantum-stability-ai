import { useEffect } from "react";
import { CHART_COLORS } from "../../utils/constants";
import StatusBadge from "./StatusBadge";
import QubitTrendChart from "./QubitTrendChart";

/**
 * Right-side sliding panel showing one qubit's full history: highest/lowest/
 * average QSFI, an overall stability status, small QSFI/T1/T2 trend charts,
 * and a compact table of its 5 daily readings. Closable via the × button,
 * clicking the backdrop, or pressing Escape.
 */
function QubitDetailsPanel({ details, isOpen, onClose }) {
  useEffect(() => {
    if (!details) return undefined;

    function handleKeyDown(event) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [details, onClose]);

  if (!details) return null;

  const { qubit, records, highestQsfi, lowestQsfi, averageQsfi, stabilityStatus } = details;

  return (
    <>
      <div
        className={`qubit-panel-overlay${isOpen ? " open" : ""}`}
        onClick={onClose}
      />
      <aside className={`qubit-panel${isOpen ? " open" : ""}`}>
        <div className="qubit-panel-header">
          <div>
            <span className="qubit-panel-eyebrow">Qubit Details</span>
            <h3>Q{qubit}</h3>
          </div>
          <button
            type="button"
            className="qubit-panel-close"
            onClick={onClose}
            aria-label="Close qubit details panel"
          >
            ×
          </button>
        </div>

        <div className="qubit-panel-body">
          <div className="qubit-panel-stats">
            <div className="qubit-stat">
              <span className="qubit-stat-label">Highest QSFI</span>
              <span className="qubit-stat-value">{highestQsfi.toFixed(2)} μs</span>
            </div>
            <div className="qubit-stat">
              <span className="qubit-stat-label">Lowest QSFI</span>
              <span className="qubit-stat-value">{lowestQsfi.toFixed(2)} μs</span>
            </div>
            <div className="qubit-stat">
              <span className="qubit-stat-label">Average QSFI</span>
              <span className="qubit-stat-value">{averageQsfi.toFixed(2)} μs</span>
            </div>
            <div className="qubit-stat">
              <span className="qubit-stat-label">Stability Status</span>
              <StatusBadge status={stabilityStatus} />
            </div>
          </div>

          <QubitTrendChart
            title="QSFI Trend"
            data={records}
            dataKey="qsfi"
            gradientId="qubitPanelQsfiGradient"
          />
          <QubitTrendChart
            title="T1 Trend"
            data={records}
            dataKey="t1"
            stroke={CHART_COLORS.primary}
          />
          <QubitTrendChart
            title="T2 Trend"
            data={records}
            dataKey="t2"
            stroke={CHART_COLORS.secondary}
          />

          <div className="qubit-panel-table-section">
            <h4>Daily Readings</h4>
            <div className="qubit-panel-table-wrapper">
              <table className="qubit-panel-table">
                <thead>
                  <tr>
                    <th>Day</th>
                    <th>T1 (μs)</th>
                    <th>T2 (μs)</th>
                    <th>QSFI (μs)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.day}>
                      <td>{r.day}</td>
                      <td>{r.t1.toFixed(2)}</td>
                      <td>{r.t2.toFixed(2)}</td>
                      <td>{r.qsfi.toFixed(2)}</td>
                      <td>
                        <StatusBadge status={r.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default QubitDetailsPanel;

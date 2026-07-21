const SUMMARY_CARDS = [
  { label: "QSFI", value: "233.90" },
  { label: "Best Qubit", value: "Q3" },
  { label: "Average T1", value: "146.10 μs" },
  { label: "Average T2", value: "104.41 μs" },
];

const ANALYSIS_ROWS = [
  {
    timestamp: "2026-07-21 09:42",
    backend: "IBM Fez",
    qubit: "Q3",
    fidelity: "99.2%",
    status: "Stable",
  },
  {
    timestamp: "2026-07-21 08:15",
    backend: "IBM Fez",
    qubit: "Q7",
    fidelity: "97.8%",
    status: "Stable",
  },
  {
    timestamp: "2026-07-20 22:03",
    backend: "IBM Fez",
    qubit: "Q1",
    fidelity: "94.5%",
    status: "Degrading",
  },
  {
    timestamp: "2026-07-20 19:47",
    backend: "IBM Fez",
    qubit: "Q5",
    fidelity: "98.9%",
    status: "Stable",
  },
];

function Dashboard() {
  return (
    <section className="dashboard" id="dashboard">
      <div className="dashboard-heading">
        <h2>Dashboard</h2>
        <p>A live-style snapshot of qubit fidelity across IBM Quantum backends.</p>
      </div>

      <div className="dashboard-summary">
        {SUMMARY_CARDS.map((card) => (
          <div className="summary-card" key={card.label}>
            <span className="summary-label">{card.label}</span>
            <span className="summary-value">{card.value}</span>
          </div>
        ))}
      </div>

      <div className="dashboard-graph-panel">
        <div className="graph-panel-header">
          <h3>Fidelity Trends</h3>
          <span className="graph-badge">Live Analytics · Coming Soon</span>
        </div>

        <div className="graph-canvas">
          <svg
            className="graph-svg"
            viewBox="0 0 600 200"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="trendGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#00b4ff" />
                <stop offset="100%" stopColor="#8b5cf6" />
              </linearGradient>
            </defs>

            <polyline
              className="trend-line"
              fill="none"
              stroke="url(#trendGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              points="0,150 80,132 160,142 240,92 320,110 400,62 480,80 560,42 600,55"
            />

            <circle className="trend-point" cx="600" cy="55" r="6" />
          </svg>
        </div>
      </div>

      <div className="dashboard-table-section">
        <h3>Recent Quantum Analysis</h3>
        <div className="dashboard-table-wrapper">
          <table className="dashboard-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Backend</th>
                <th>Qubit</th>
                <th>Fidelity</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {ANALYSIS_ROWS.map((row) => (
                <tr key={row.timestamp + row.qubit}>
                  <td>{row.timestamp}</td>
                  <td>{row.backend}</td>
                  <td>{row.qubit}</td>
                  <td>{row.fidelity}</td>
                  <td>
                    <span
                      className={`status-badge status-${row.status.toLowerCase()}`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

export default Dashboard;

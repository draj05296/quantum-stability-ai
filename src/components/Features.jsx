const FEATURES = [
  {
    title: "Real-Time Fidelity Scoring",
    description:
      "Continuously measures and scores qubit fidelity using live data from IBM Quantum backends to catch instability early.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12h4l2 8 4-16 2 8h6" />
      </svg>
    ),
  },
  {
    title: "AI Qubit Recommendation",
    description:
      "Machine learning models recommend the most stable, lowest-noise qubits for your next circuit execution.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="6" y="6" width="12" height="12" rx="2" />
        <path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3" />
      </svg>
    ),
  },
  {
    title: "IBM Quantum Integration",
    description:
      "Connects directly to IBM Quantum systems, pulling calibration and error-rate data in real time.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
        <ellipse cx="12" cy="12" rx="9" ry="3.8" />
        <ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(60 12 12)" />
        <ellipse cx="12" cy="12" rx="9" ry="3.8" transform="rotate(120 12 12)" />
      </svg>
    ),
  },
  {
    title: "Predictive Stability Analytics",
    description:
      "Forecasts decoherence and error trends before they degrade results, so you can plan runs with confidence.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l6-6 4 4 8-8" />
        <path d="M15 7h6v6" />
      </svg>
    ),
  },
];

function Features() {
  return (
    <section className="features" id="features">
      <div className="features-heading">
        <h2>Features</h2>
        <p>Everything QSFI brings to quantum research, in one platform.</p>
      </div>

      <div className="features-grid">
        {FEATURES.map((feature, index) => (
          <div
            className="feature-card"
            key={feature.title}
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="feature-icon">{feature.icon}</div>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default Features;

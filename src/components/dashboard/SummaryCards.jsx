import { memo } from "react";

/** A single stat tile: a label and its (possibly still-loading) value. */
export const SummaryCard = memo(function SummaryCard({ label, value }) {
  return (
    <div className="summary-card">
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  );
});

/**
 * Renders a row of SummaryCard tiles for a fixed list of labels, pulling
 * each value out of `values` (or showing a loading placeholder when
 * `values` is still null). Reused for both the top dashboard summary and
 * the prediction summary cards.
 */
function SummaryCards({ labels, values }) {
  return (
    <div className="dashboard-summary">
      {labels.map((label) => (
        <SummaryCard key={label} label={label} value={values ? values[label] : "…"} />
      ))}
    </div>
  );
}

export default memo(SummaryCards);

import { memo } from "react";

/**
 * Small pill badge used for Stable/Degrading/Improving status everywhere in
 * the dashboard (tables, the qubit panel, prediction rows). Centralizing it
 * here removes the `status-badge status-${status.toLowerCase()}` string
 * that was previously duplicated in four different places.
 */
function StatusBadge({ status }) {
  return (
    <span className={`status-badge status-${status.toLowerCase()}`}>
      {status}
    </span>
  );
}

export default memo(StatusBadge);

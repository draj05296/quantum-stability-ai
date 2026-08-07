import { memo } from "react";
import StatusBadge from "./StatusBadge";

/**
 * The paginated Qubit Readings table. Clicking any row opens that qubit's
 * details panel via `onRowClick`.
 */
function QubitTable({ rows, onRowClick }) {
  return (
    <div className="dashboard-table-wrapper">
      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Qubit</th>
            <th>Day</th>
            <th>T1 (μs)</th>
            <th>T2 (μs)</th>
            <th>QSFI (μs)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr className="table-empty-row">
              <td colSpan={6}>No qubit readings match these filters.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={`${row.day}-${row.qubit}`} onClick={() => onRowClick(row.qubit)}>
                <td>Q{row.qubit}</td>
                <td>{row.day}</td>
                <td>{row.t1.toFixed(2)}</td>
                <td>{row.t2.toFixed(2)}</td>
                <td>{row.qsfi.toFixed(2)}</td>
                <td>
                  <StatusBadge status={row.status} />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export default memo(QubitTable);

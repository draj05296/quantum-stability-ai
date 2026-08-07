import { memo } from "react";
import { ROWS_PER_PAGE_OPTIONS } from "../../utils/constants";

/**
 * Rows-per-page selector plus Previous/page-number/Next controls for the
 * Qubit Readings table.
 */
function Pagination({
  rowsPerPage,
  onRowsPerPageChange,
  pageNumbers,
  safePage,
  totalPages,
  onPageChange,
}) {
  return (
    <div className="table-pagination">
      <div className="rows-per-page">
        <label htmlFor="rows-per-page">Rows per page</label>
        <select
          id="rows-per-page"
          value={rowsPerPage}
          onChange={(e) => onRowsPerPageChange(Number(e.target.value))}
        >
          {ROWS_PER_PAGE_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>

      <div className="pagination-controls">
        <button
          type="button"
          className="pagination-btn"
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
          disabled={safePage === 1}
        >
          Previous
        </button>

        {pageNumbers.map((page, index) =>
          page === "…" ? (
            <span className="pagination-ellipsis" key={`ellipsis-${index}`}>
              …
            </span>
          ) : (
            <button
              type="button"
              key={page}
              className={`pagination-btn pagination-page${page === safePage ? " active" : ""}`}
              onClick={() => onPageChange(page)}
              aria-current={page === safePage ? "page" : undefined}
            >
              {page}
            </button>
          )
        )}

        <button
          type="button"
          className="pagination-btn"
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
          disabled={safePage === totalPages}
        >
          Next
        </button>
      </div>

      <span className="pagination-summary">
        Page {safePage} of {totalPages}
      </span>
    </div>
  );
}

export default memo(Pagination);

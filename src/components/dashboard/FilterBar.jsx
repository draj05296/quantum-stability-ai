import { memo } from "react";
import { SORT_FIELDS, STATUS_OPTIONS } from "../../utils/constants";

/**
 * Day/status/search filters, sort field/direction controls, and the
 * "Showing X of Y readings" counter above the Qubit Readings table.
 */
function FilterBar({
  dayFilter,
  onDayFilterChange,
  statusFilter,
  onStatusFilterChange,
  qubitSearch,
  onQubitSearchChange,
  sortField,
  onSortFieldChange,
  sortDirection,
  onSortDirectionChange,
  dayOptions,
  filteredCount,
  totalCount,
}) {
  return (
    <div className="dashboard-filters">
      <div className="filter-group">
        <label htmlFor="day-filter">Day</label>
        <select
          id="day-filter"
          value={dayFilter}
          onChange={(e) => onDayFilterChange(e.target.value)}
        >
          {dayOptions.map((day) => (
            <option key={day} value={day}>
              {day}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="status-filter">Status</label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
        >
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group filter-search">
        <label htmlFor="qubit-search">Qubit ID</label>
        <input
          id="qubit-search"
          type="text"
          placeholder="Search qubit ID…"
          value={qubitSearch}
          onChange={(e) => onQubitSearchChange(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label htmlFor="sort-field">Sort By</label>
        <select
          id="sort-field"
          value={sortField}
          onChange={(e) => onSortFieldChange(e.target.value)}
        >
          {SORT_FIELDS.map((field) => (
            <option key={field.value} value={field.value}>
              {field.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="sort-direction">Order</label>
        <select
          id="sort-direction"
          value={sortDirection}
          onChange={(e) => onSortDirectionChange(e.target.value)}
        >
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </select>
      </div>

      <span className="filter-results-count">
        Showing {filteredCount} of {totalCount} readings
      </span>
    </div>
  );
}

export default memo(FilterBar);

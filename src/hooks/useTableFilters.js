import { useMemo, useState } from "react";
import { ALL_DAYS_LABEL } from "../utils/constants";
import { getDayNumber } from "../utils/dashboardCalculations";

/**
 * Owns the Qubit Readings filter/sort state (day, status, qubit search,
 * sort field/direction) and derives the day dropdown options and the
 * filtered+sorted row set from allRecords.
 */
export function useTableFilters(allRecords) {
  const [dayFilter, setDayFilter] = useState(ALL_DAYS_LABEL);
  const [statusFilter, setStatusFilter] = useState("All");
  const [qubitSearch, setQubitSearch] = useState("");
  const [sortField, setSortField] = useState("qsfi");
  const [sortDirection, setSortDirection] = useState("desc");

  const dayOptions = useMemo(() => {
    const uniqueDays = Array.from(new Set(allRecords.map((r) => r.day))).sort(
      (a, b) => getDayNumber(a) - getDayNumber(b)
    );

    return [ALL_DAYS_LABEL, ...uniqueDays];
  }, [allRecords]);

  const filteredRows = useMemo(() => {
    const query = qubitSearch.trim();

    const filtered = allRecords.filter((r) => {
      if (dayFilter !== ALL_DAYS_LABEL && r.day !== dayFilter) return false;
      if (statusFilter !== "All" && r.status !== statusFilter) return false;
      if (query && !String(r.qubit).includes(query)) return false;
      return true;
    });

    const direction = sortDirection === "asc" ? 1 : -1;

    return filtered.sort((a, b) => (a[sortField] - b[sortField]) * direction);
  }, [allRecords, dayFilter, statusFilter, qubitSearch, sortField, sortDirection]);

  return {
    dayFilter,
    setDayFilter,
    statusFilter,
    setStatusFilter,
    qubitSearch,
    setQubitSearch,
    sortField,
    setSortField,
    sortDirection,
    setSortDirection,
    dayOptions,
    filteredRows,
  };
}

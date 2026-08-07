import { useEffect, useMemo, useState } from "react";
import { ROWS_PER_PAGE_OPTIONS } from "../utils/constants";
import { getPageNumbers } from "../utils/pagination";

/**
 * Owns rows-per-page/current-page state and slices `filteredRows` into the
 * current page. The page resets to 1 whenever any value in `resetKeys`
 * changes (e.g. the active filters/sort) or rows-per-page changes, so a
 * stale page number never points past the end of a newly filtered set.
 */
export function usePagination(filteredRows, resetKeys = []) {
  const [rowsPerPage, setRowsPerPage] = useState(ROWS_PER_PAGE_OPTIONS[0]);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    setCurrentPage(1);
    // resetKeys is spread intentionally: any filter/sort value changing
    // (as well as rowsPerPage) should snap the page back to 1.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...resetKeys, rowsPerPage]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / rowsPerPage));
  const safePage = Math.min(currentPage, totalPages);

  const paginatedRows = useMemo(() => {
    const start = (safePage - 1) * rowsPerPage;
    return filteredRows.slice(start, start + rowsPerPage);
  }, [filteredRows, safePage, rowsPerPage]);

  const pageNumbers = useMemo(
    () => getPageNumbers(safePage, totalPages),
    [safePage, totalPages]
  );

  return {
    rowsPerPage,
    setRowsPerPage,
    currentPage,
    setCurrentPage,
    totalPages,
    safePage,
    paginatedRows,
    pageNumbers,
  };
}

import { useMemo } from "react";
import { useQuantumData } from "../hooks/useQuantumData";
import { useTableFilters } from "../hooks/useTableFilters";
import { usePagination } from "../hooks/usePagination";
import { useQubitPredictions } from "../hooks/useQubitPredictions";
import { useQubitDetailsPanel } from "../hooks/useQubitDetailsPanel";
import {
  computeQsfiDistribution,
  computeQubitScatterData,
  computeStabilityDistribution,
} from "../utils/dashboardCalculations";
import { CHART_COLORS, SUMMARY_LABELS } from "../utils/constants";
import SummaryCards from "./dashboard/SummaryCards";
import ResearchInsights from "./dashboard/ResearchInsights";
import PredictionSection from "./dashboard/PredictionSection";
import FilterBar from "./dashboard/FilterBar";
import QubitTable from "./dashboard/QubitTable";
import Pagination from "./dashboard/Pagination";
import QubitDetailsPanel from "./dashboard/QubitDetailsPanel";

/**
 * Top-level Dashboard page. This component only wires data (via custom
 * hooks) to layout - all calculations live in src/utils, and every visual
 * piece is its own component under src/components/dashboard.
 */
function Dashboard() {
  const { summary, allRecords, trendData, isLoading } = useQuantumData();

  const {
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
  } = useTableFilters(allRecords);

  const {
    rowsPerPage,
    setRowsPerPage,
    setCurrentPage,
    totalPages,
    safePage,
    paginatedRows,
    pageNumbers,
  } = usePagination(filteredRows, [
    dayFilter,
    statusFilter,
    qubitSearch,
    sortField,
    sortDirection,
  ]);

  const stabilityDistribution = useMemo(
    () => computeStabilityDistribution(allRecords, CHART_COLORS),
    [allRecords]
  );

  const qsfiDistribution = useMemo(
    () => computeQsfiDistribution(allRecords),
    [allRecords]
  );

  const qubitScatterData = useMemo(
    () => computeQubitScatterData(allRecords),
    [allRecords]
  );

  const { qubitPredictions, predictionSummary, predictionChartData } =
    useQubitPredictions(allRecords, trendData);

  const { selectedQubitDetails, isPanelOpen, openQubitPanel, closeQubitPanel } =
    useQubitDetailsPanel(allRecords);

  return (
    <section className="dashboard" id="dashboard">
      <div className="dashboard-heading">
        <h2>Dashboard</h2>
        <p>A live-style snapshot of qubit fidelity across IBM Quantum backends.</p>
      </div>

      <SummaryCards labels={SUMMARY_LABELS} values={summary} />

      <ResearchInsights
        trendData={trendData}
        qsfiDistribution={qsfiDistribution}
        stabilityDistribution={stabilityDistribution}
        qubitScatterData={qubitScatterData}
        isLoading={isLoading}
      />

      <PredictionSection
        predictionSummary={predictionSummary}
        predictionChartData={predictionChartData}
        qubitPredictions={qubitPredictions}
      />

      <div className="dashboard-table-section">
        <h3>Qubit Readings</h3>

        <FilterBar
          dayFilter={dayFilter}
          onDayFilterChange={setDayFilter}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          qubitSearch={qubitSearch}
          onQubitSearchChange={setQubitSearch}
          sortField={sortField}
          onSortFieldChange={setSortField}
          sortDirection={sortDirection}
          onSortDirectionChange={setSortDirection}
          dayOptions={dayOptions}
          filteredCount={filteredRows.length}
          totalCount={allRecords.length}
        />

        <QubitTable rows={paginatedRows} onRowClick={openQubitPanel} />

        <Pagination
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={setRowsPerPage}
          pageNumbers={pageNumbers}
          safePage={safePage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      <QubitDetailsPanel
        details={selectedQubitDetails}
        isOpen={isPanelOpen}
        onClose={closeQubitPanel}
      />
    </section>
  );
}

export default Dashboard;

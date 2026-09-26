import { useCallback, useMemo, useState } from "react";
import { DATA_SOURCE, useQuantumDataSource } from "../hooks/useQuantumDataSource";
import { useAnalyzeUpload } from "../hooks/useAnalyzeUpload";
import { isValidAnalysis } from "../utils/analysisAdapter";
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
import AnalysisUploadPanel from "./dashboard/AnalysisUploadPanel";
import RiskSection from "./dashboard/RiskSection";

/**
 * Top-level Dashboard page. This component only wires data (via custom
 * hooks) to layout - all calculations live in src/utils, and every visual
 * piece is its own component under src/components/dashboard.
 */
function Dashboard() {
  // The upload request state lives here (rather than inside the panel) so a
  // successful analysis can also become the dashboard's data source.
  const {
    isLoading: isAnalyzing,
    analysis,
    error: analysisError,
    analyzedFileName,
    analyzeFile,
    reset: resetUpload,
  } = useAnalyzeUpload();

  // Holds the analysis the user explicitly promoted, never the latest upload:
  // analyzing a new file leaves the dashboard alone until it is chosen too.
  // Its display name is captured at the same moment, because `analyzedFileName`
  // tracks the most recent upload and would otherwise label the banner with a
  // file the dashboard isn't actually showing.
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [activeAnalysisName, setActiveAnalysisName] = useState(null);

  const { summary, allRecords, trendData, isLoading, activeSource, analysisMetadata } =
    useQuantumDataSource(activeAnalysis);

  const isAnalysisActive = activeSource === DATA_SOURCE.ANALYSIS;

  const useAnalysisAsDataSource = useCallback(() => {
    setActiveAnalysis(analysis);
    setActiveAnalysisName(analyzedFileName);
  }, [analysis, analyzedFileName]);

  const resetToSampleData = useCallback(() => {
    setActiveAnalysis(null);
    setActiveAnalysisName(null);
  }, []);

  // Clearing the panel also drops the dataset it loaded, so the dashboard
  // never keeps rendering an analysis the user just dismissed.
  const clearAnalysis = useCallback(() => {
    setActiveAnalysis(null);
    setActiveAnalysisName(null);
    resetUpload();
  }, [resetUpload]);

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
    // Swapping datasets changes the row count, so start again from page 1.
    activeAnalysis,
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
        {isAnalysisActive && (
          <p className="dashboard-active-source">
            Showing analyzed upload:{" "}
            <strong>{activeAnalysisName ?? analysisMetadata?.filename}</strong> (
            {analysisMetadata?.rowsAnalyzed} qubits)
          </p>
        )}
      </div>

      <SummaryCards labels={SUMMARY_LABELS} values={summary} />

      <ResearchInsights
        trendData={trendData}
        qsfiDistribution={qsfiDistribution}
        stabilityDistribution={stabilityDistribution}
        qubitScatterData={qubitScatterData}
        isLoading={isLoading}
      />

      {/* A single uploaded snapshot gives one reading per qubit, which cannot
          support a regression forecast - so the section is hidden rather than
          shown with a degenerate single-point fit. */}
      {isAnalysisActive ? (
        <div className="analytics-section">
          <div className="analytics-heading">
            <h3>QSFI Prediction Engine</h3>
            <p>Forecasting requires ≥2 daily readings.</p>
          </div>
        </div>
      ) : (
        <PredictionSection
          predictionSummary={predictionSummary}
          predictionChartData={predictionChartData}
          qubitPredictions={qubitPredictions}
        />
      )}

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

      <RiskSection />

      <AnalysisUploadPanel
        isAnalyzing={isAnalyzing}
        analysis={analysis}
        error={analysisError}
        analyzedFileName={analyzedFileName}
        onAnalyzeFile={analyzeFile}
        onClear={clearAnalysis}
        isActiveDataSource={isAnalysisActive && activeAnalysis === analysis}
        canActivate={isValidAnalysis(analysis)}
        onUseAsDashboardData={useAnalysisAsDataSource}
        onResetToSampleData={resetToSampleData}
      />

      <QubitDetailsPanel
        details={selectedQubitDetails}
        isOpen={isPanelOpen}
        onClose={closeQubitPanel}
      />
    </section>
  );
}

export default Dashboard;

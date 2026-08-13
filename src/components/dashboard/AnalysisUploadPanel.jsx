import { useCallback, useRef, useState } from "react";
import { useAnalyzeUpload } from "../../hooks/useAnalyzeUpload";
import {
  formatAnalysisSummaryValues,
  formatDataQualityRows,
} from "../../utils/analysisAdapter";
import { SUMMARY_LABELS } from "../../utils/constants";
import SummaryCards from "./SummaryCards";

/**
 * Uploads a CSV to the AI engine's POST /analyze endpoint and renders the
 * result.
 *
 * The dashboard above still runs entirely on the bundled CSVs - this panel is
 * the backend-powered path alongside it, and reuses <SummaryCards /> so an
 * API-computed summary looks identical to the local one.
 */
function AnalysisUploadPanel() {
  const { isLoading, analysis, error, analyzedFileName, analyzeFile, reset } =
    useAnalyzeUpload();

  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = useCallback((event) => {
    setSelectedFile(event.target.files?.[0] ?? null);
  }, []);

  const handleSubmit = useCallback(
    (event) => {
      event.preventDefault();
      analyzeFile(selectedFile);
    },
    [analyzeFile, selectedFile]
  );

  const handleClear = useCallback(() => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    reset();
  }, [reset]);

  const summaryValues = formatAnalysisSummaryValues(analysis);
  const dataQualityRows = formatDataQualityRows(analysis);

  return (
    <div className="analysis-upload-section">
      <div className="analysis-upload-heading">
        <h3>Analyze a CSV with the AI Engine</h3>
        <p>
          Upload a calibration CSV (columns: Qubit, T1, T2) to the QSFI AI engine.
          The backend cleans the data and computes the summary below. The charts
          and table above continue to use the bundled sample data.
        </p>
      </div>

      <form className="analysis-upload-form" onSubmit={handleSubmit}>
        <div className="filter-group filter-search">
          <label htmlFor="analysis-csv-input">CSV File</label>
          <input
            id="analysis-csv-input"
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileChange}
            disabled={isLoading}
          />
        </div>

        <div className="analysis-upload-actions">
          <button
            type="submit"
            className="analysis-upload-button"
            disabled={!selectedFile || isLoading}
          >
            {isLoading ? "Analyzing…" : "Analyze"}
          </button>

          <button
            type="button"
            className="analysis-upload-button analysis-upload-button-secondary"
            onClick={handleClear}
            disabled={isLoading || (!selectedFile && !analysis && !error)}
          >
            Clear
          </button>
        </div>
      </form>

      {isLoading && (
        <p className="analysis-upload-status" role="status">
          Uploading and analyzing…
        </p>
      )}

      {error && (
        <p className="analysis-upload-error" role="alert">
          {error}
        </p>
      )}

      {analysis && !isLoading && (
        <div className="analysis-upload-result">
          <p className="analysis-upload-status">
            Analyzed <strong>{analyzedFileName}</strong> — saved as{" "}
            <code>{analysis.processed_filename}</code>
          </p>

          <SummaryCards labels={SUMMARY_LABELS} values={summaryValues} />

          <ul className="analysis-quality-list">
            {dataQualityRows.map(({ label, value }) => (
              <li key={label}>
                <span className="analysis-quality-label">{label}</span>
                <span className="analysis-quality-value">{value}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default AnalysisUploadPanel;

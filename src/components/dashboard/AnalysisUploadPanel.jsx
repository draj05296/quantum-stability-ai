import { useCallback, useRef, useState } from "react";
import {
  formatAnalysisSummaryValues,
  formatDataQualityRows,
} from "../../utils/analysisAdapter";
import { SUMMARY_LABELS } from "../../utils/constants";
import SummaryCards from "./SummaryCards";

/**
 * Uploads a CSV to the AI engine's POST /analyze endpoint, renders the
 * result, and offers to promote that result to the dashboard's active
 * dataset.
 *
 * This component is controlled: the upload request state lives in Dashboard
 * (via useAnalyzeUpload) so the analysis can also feed the dashboard's data
 * pipeline. Everything here is presentation plus local file-input state.
 */
function AnalysisUploadPanel({
  isAnalyzing,
  analysis,
  error,
  analyzedFileName,
  onAnalyzeFile,
  onClear,
  isActiveDataSource,
  canActivate,
  onUseAsDashboardData,
  onResetToSampleData,
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = useCallback((event) => {
    setSelectedFile(event.target.files?.[0] ?? null);
  }, []);

  const handleSubmit = useCallback(
    (event) => {
      event.preventDefault();
      onAnalyzeFile(selectedFile);
    },
    [onAnalyzeFile, selectedFile]
  );

  const handleClear = useCallback(() => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    onClear();
  }, [onClear]);

  const summaryValues = formatAnalysisSummaryValues(analysis);
  const dataQualityRows = formatDataQualityRows(analysis);

  return (
    <div className="analysis-upload-section">
      <div className="analysis-upload-heading">
        <h3>Analyze a CSV with the AI Engine</h3>
        <p>
          Upload a calibration CSV (columns: Qubit, T1, T2) to the QSFI AI engine.
          The backend cleans the data and computes the summary below, which you
          can then load into the dashboard above.
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
            disabled={isAnalyzing}
          />
        </div>

        <div className="analysis-upload-actions">
          <button
            type="submit"
            className="analysis-upload-button"
            disabled={!selectedFile || isAnalyzing}
          >
            {isAnalyzing ? "Analyzing…" : "Analyze"}
          </button>

          <button
            type="button"
            className="analysis-upload-button analysis-upload-button-secondary"
            onClick={handleClear}
            disabled={isAnalyzing || (!selectedFile && !analysis && !error)}
          >
            Clear
          </button>
        </div>
      </form>

      {isAnalyzing && (
        <p className="analysis-upload-status" role="status">
          Uploading and analyzing…
        </p>
      )}

      {error && (
        <p className="analysis-upload-error" role="alert">
          {error}
        </p>
      )}

      {analysis && !isAnalyzing && (
        <div className="analysis-upload-result">
          <p className="analysis-upload-status">
            Analyzed <strong>{analyzedFileName}</strong> — saved as{" "}
            <code>{analysis.processed_filename}</code>
          </p>

          <div className="analysis-source-actions">
            {isActiveDataSource ? (
              <>
                <span className="analysis-source-active">
                  This dataset is driving the dashboard.
                </span>
                <button
                  type="button"
                  className="analysis-upload-button analysis-upload-button-secondary"
                  onClick={onResetToSampleData}
                >
                  Reset to sample data
                </button>
              </>
            ) : (
              <button
                type="button"
                className="analysis-upload-button"
                onClick={onUseAsDashboardData}
                disabled={!canActivate}
              >
                Use as dashboard data
              </button>
            )}
          </div>

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

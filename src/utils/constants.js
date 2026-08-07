// Shared constants for the QSFI dashboard: unit conversion, chart palette,
// and the option lists that drive the summary cards, filters, and tables.

export const SEC_TO_US = 1e6;

export const ALL_DAYS_LABEL = "All Days";

export const CHART_COLORS = {
  primary: "#00b4ff",
  secondary: "#8b5cf6",
  stable: "#34d399",
  degrading: "#fbbf24",
};

// Number of buckets used to build the QSFI distribution histogram.
export const QSFI_BIN_COUNT = 8;

export const SUMMARY_LABELS = [
  "Average QSFI",
  "Best Qubit",
  "Average T1",
  "Average T2",
  "Total Qubits",
];

export const STATUS_OPTIONS = ["All", "Stable", "Degrading"];

export const SORT_FIELDS = [
  { value: "qsfi", label: "QSFI" },
  { value: "t1", label: "T1" },
  { value: "t2", label: "T2" },
];

export const ROWS_PER_PAGE_OPTIONS = [25, 50, 100];

// Minimum % change (from linear regression) before a qubit is classified
// Improving/Degrading instead of Stable.
export const TREND_THRESHOLD_PERCENT = 1;

export const PREDICTION_SUMMARY_LABELS = [
  "Average Predicted QSFI",
  "Improving Qubits",
  "Stable Qubits",
  "Degrading Qubits",
];

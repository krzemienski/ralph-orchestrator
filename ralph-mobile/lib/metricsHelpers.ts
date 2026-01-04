/**
 * @fileoverview Metrics helpers for 60-second rolling window chart display
 * Provides data structures and functions for tracking and displaying system metrics
 */

/**
 * Single data point with timestamp and metric values
 */
export interface MetricsDataPoint {
  timestamp: number;
  cpu: number;
  memory: number;
  iterations: number;
}

/**
 * Metrics window configuration and data storage
 */
export interface MetricsWindow {
  dataPoints: MetricsDataPoint[];
  windowSizeMs: number;
  maxDataPoints: number;
}

/**
 * Chart data formatted for rendering
 */
export interface ChartData {
  labels: string[];
  values: number[];
}

/**
 * Metric type for extracting specific values
 */
export type MetricType = 'cpu' | 'memory' | 'iterations';

/**
 * Options for creating a metrics window
 */
export interface MetricsWindowOptions {
  windowSizeMs?: number;
  maxDataPoints?: number;
}

const DEFAULT_WINDOW_SIZE_MS = 60000; // 60 seconds
const DEFAULT_MAX_DATA_POINTS = 60; // 1 point per second

/**
 * Creates an empty metrics window with specified or default settings
 */
export function createMetricsWindow(options: MetricsWindowOptions = {}): MetricsWindow {
  return {
    dataPoints: [],
    windowSizeMs: options.windowSizeMs ?? DEFAULT_WINDOW_SIZE_MS,
    maxDataPoints: options.maxDataPoints ?? DEFAULT_MAX_DATA_POINTS,
  };
}

/**
 * Adds a data point to the window and prunes old points
 */
export function addMetricsDataPoint(
  window: MetricsWindow,
  dataPoint: MetricsDataPoint
): MetricsWindow {
  const updatedDataPoints = [...window.dataPoints, dataPoint];
  const cutoffTime = dataPoint.timestamp - window.windowSizeMs;

  // Remove points older than window size
  const prunedDataPoints = updatedDataPoints.filter(
    (point) => point.timestamp >= cutoffTime
  );

  return {
    ...window,
    dataPoints: prunedDataPoints,
  };
}

/**
 * Prunes data points older than the window size
 */
export function pruneOldDataPoints(
  window: MetricsWindow,
  currentTime: number
): MetricsWindow {
  const cutoffTime = currentTime - window.windowSizeMs;
  const prunedDataPoints = window.dataPoints.filter(
    (point) => point.timestamp >= cutoffTime
  );

  return {
    ...window,
    dataPoints: prunedDataPoints,
  };
}

/**
 * Gets chart data for a specific metric type
 */
export function getChartData(
  window: MetricsWindow,
  metric: MetricType,
  referenceTime?: number
): ChartData {
  const now = referenceTime ?? Date.now();

  const labels = window.dataPoints.map((point) => {
    const secondsAgo = Math.round((point.timestamp - now) / 1000);
    return `${secondsAgo}s`;
  });

  const values = window.dataPoints.map((point) => point[metric]);

  return { labels, values };
}

/**
 * Formats a metric value for display
 */
export function formatMetricValue(value: number, metric: MetricType): string {
  switch (metric) {
    case 'cpu':
      return `${value.toFixed(1)}%`;
    case 'memory':
      return `${Math.round(value)} MB`;
    case 'iterations':
      return `${Math.floor(value)}`;
    default:
      return String(value);
  }
}

/**
 * Calculates the average value for a metric across all data points
 */
export function calculateAverageMetric(
  window: MetricsWindow,
  metric: MetricType
): number {
  if (window.dataPoints.length === 0) {
    return 0;
  }

  const sum = window.dataPoints.reduce((acc, point) => acc + point[metric], 0);
  return sum / window.dataPoints.length;
}

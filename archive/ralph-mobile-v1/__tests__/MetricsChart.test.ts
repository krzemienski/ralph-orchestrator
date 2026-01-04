/**
 * @fileoverview TDD tests for MetricsChart helpers
 * Tests for 60-second rolling window metrics display
 */

import {
  MetricsDataPoint,
  MetricsWindow,
  createMetricsWindow,
  addMetricsDataPoint,
  pruneOldDataPoints,
  getChartData,
  formatMetricValue,
  calculateAverageMetric,
} from '../lib/metricsHelpers';

describe('MetricsChart Helpers', () => {
  const WINDOW_SIZE_MS = 60000; // 60 seconds

  describe('createMetricsWindow', () => {
    it('creates an empty metrics window with correct properties', () => {
      const window = createMetricsWindow();

      expect(window.dataPoints).toEqual([]);
      expect(window.windowSizeMs).toBe(WINDOW_SIZE_MS);
      expect(window.maxDataPoints).toBe(60); // 1 point per second
    });

    it('allows custom window size', () => {
      const window = createMetricsWindow({ windowSizeMs: 30000 });

      expect(window.windowSizeMs).toBe(30000);
    });

    it('allows custom max data points', () => {
      const window = createMetricsWindow({ maxDataPoints: 120 });

      expect(window.maxDataPoints).toBe(120);
    });
  });

  describe('addMetricsDataPoint', () => {
    it('adds a data point to the window', () => {
      const window = createMetricsWindow();
      const timestamp = Date.now();
      const dataPoint: MetricsDataPoint = {
        timestamp,
        cpu: 45.5,
        memory: 1024,
        iterations: 10,
      };

      const updated = addMetricsDataPoint(window, dataPoint);

      expect(updated.dataPoints).toHaveLength(1);
      expect(updated.dataPoints[0]).toEqual(dataPoint);
    });

    it('maintains chronological order', () => {
      let window = createMetricsWindow();
      const now = Date.now();

      window = addMetricsDataPoint(window, { timestamp: now, cpu: 10, memory: 100, iterations: 1 });
      window = addMetricsDataPoint(window, { timestamp: now + 1000, cpu: 20, memory: 200, iterations: 2 });
      window = addMetricsDataPoint(window, { timestamp: now + 2000, cpu: 30, memory: 300, iterations: 3 });

      expect(window.dataPoints[0].timestamp).toBe(now);
      expect(window.dataPoints[2].timestamp).toBe(now + 2000);
    });

    it('removes old data points beyond window size', () => {
      let window = createMetricsWindow({ windowSizeMs: 5000 }); // 5 second window
      const now = Date.now();

      // Add points spanning more than window size
      window = addMetricsDataPoint(window, { timestamp: now - 6000, cpu: 10, memory: 100, iterations: 1 });
      window = addMetricsDataPoint(window, { timestamp: now - 3000, cpu: 20, memory: 200, iterations: 2 });
      window = addMetricsDataPoint(window, { timestamp: now, cpu: 30, memory: 300, iterations: 3 });

      // Only points within last 5 seconds should remain
      expect(window.dataPoints).toHaveLength(2);
      expect(window.dataPoints[0].timestamp).toBe(now - 3000);
    });
  });

  describe('pruneOldDataPoints', () => {
    it('removes data points older than window size', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 70000, cpu: 10, memory: 100, iterations: 1 }, // 70s ago - old
          { timestamp: now - 50000, cpu: 20, memory: 200, iterations: 2 }, // 50s ago - keep
          { timestamp: now - 10000, cpu: 30, memory: 300, iterations: 3 }, // 10s ago - keep
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const pruned = pruneOldDataPoints(window, now);

      expect(pruned.dataPoints).toHaveLength(2);
      expect(pruned.dataPoints[0].cpu).toBe(20);
      expect(pruned.dataPoints[1].cpu).toBe(30);
    });

    it('keeps all points if none are old', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 30000, cpu: 10, memory: 100, iterations: 1 },
          { timestamp: now - 20000, cpu: 20, memory: 200, iterations: 2 },
          { timestamp: now - 10000, cpu: 30, memory: 300, iterations: 3 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const pruned = pruneOldDataPoints(window, now);

      expect(pruned.dataPoints).toHaveLength(3);
    });

    it('returns empty array if all points are old', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 120000, cpu: 10, memory: 100, iterations: 1 },
          { timestamp: now - 90000, cpu: 20, memory: 200, iterations: 2 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const pruned = pruneOldDataPoints(window, now);

      expect(pruned.dataPoints).toHaveLength(0);
    });
  });

  describe('getChartData', () => {
    it('formats data points for chart rendering', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 30000, cpu: 25.5, memory: 512, iterations: 5 },
          { timestamp: now - 20000, cpu: 45.2, memory: 768, iterations: 10 },
          { timestamp: now - 10000, cpu: 65.8, memory: 1024, iterations: 15 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const chartData = getChartData(window, 'cpu');

      expect(chartData.labels).toHaveLength(3);
      expect(chartData.values).toEqual([25.5, 45.2, 65.8]);
    });

    it('returns memory values when metric is memory', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 20000, cpu: 25.5, memory: 512, iterations: 5 },
          { timestamp: now - 10000, cpu: 45.2, memory: 768, iterations: 10 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const chartData = getChartData(window, 'memory');

      expect(chartData.values).toEqual([512, 768]);
    });

    it('returns iterations when metric is iterations', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 20000, cpu: 25.5, memory: 512, iterations: 5 },
          { timestamp: now - 10000, cpu: 45.2, memory: 768, iterations: 10 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const chartData = getChartData(window, 'iterations');

      expect(chartData.values).toEqual([5, 10]);
    });

    it('returns empty arrays for empty window', () => {
      const window: MetricsWindow = {
        dataPoints: [],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const chartData = getChartData(window, 'cpu');

      expect(chartData.labels).toEqual([]);
      expect(chartData.values).toEqual([]);
    });

    it('formats timestamp labels as relative time', () => {
      const now = Date.now();
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: now - 30000, cpu: 25.5, memory: 512, iterations: 5 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const chartData = getChartData(window, 'cpu', now);

      // Label should be relative (e.g., "-30s")
      expect(chartData.labels[0]).toBe('-30s');
    });
  });

  describe('formatMetricValue', () => {
    it('formats CPU as percentage', () => {
      expect(formatMetricValue(45.678, 'cpu')).toBe('45.7%');
      expect(formatMetricValue(100, 'cpu')).toBe('100.0%');
      expect(formatMetricValue(0, 'cpu')).toBe('0.0%');
    });

    it('formats memory in MB', () => {
      expect(formatMetricValue(1024, 'memory')).toBe('1024 MB');
      expect(formatMetricValue(512.5, 'memory')).toBe('513 MB');
    });

    it('formats iterations as integer', () => {
      expect(formatMetricValue(15, 'iterations')).toBe('15');
      expect(formatMetricValue(0, 'iterations')).toBe('0');
    });
  });

  describe('calculateAverageMetric', () => {
    it('calculates average CPU correctly', () => {
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: Date.now() - 20000, cpu: 20, memory: 100, iterations: 1 },
          { timestamp: Date.now() - 10000, cpu: 40, memory: 200, iterations: 2 },
          { timestamp: Date.now(), cpu: 60, memory: 300, iterations: 3 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const avg = calculateAverageMetric(window, 'cpu');

      expect(avg).toBe(40); // (20 + 40 + 60) / 3
    });

    it('calculates average memory correctly', () => {
      const window: MetricsWindow = {
        dataPoints: [
          { timestamp: Date.now() - 20000, cpu: 20, memory: 100, iterations: 1 },
          { timestamp: Date.now() - 10000, cpu: 40, memory: 200, iterations: 2 },
          { timestamp: Date.now(), cpu: 60, memory: 300, iterations: 3 },
        ],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const avg = calculateAverageMetric(window, 'memory');

      expect(avg).toBe(200); // (100 + 200 + 300) / 3
    });

    it('returns 0 for empty window', () => {
      const window: MetricsWindow = {
        dataPoints: [],
        windowSizeMs: WINDOW_SIZE_MS,
        maxDataPoints: 60,
      };

      const avg = calculateAverageMetric(window, 'cpu');

      expect(avg).toBe(0);
    });
  });
});

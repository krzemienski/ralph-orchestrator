/**
 * TaskList Component
 *
 * List of tasks within an orchestration:
 * - Task name and status
 * - Duration and timing info
 * - Expandable error details
 * - Color-coded status indicators
 */

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Pressable, FlatList } from 'react-native';
import * as Haptics from 'expo-haptics';
import type { Task, TaskStatus } from '../../lib/types';

// Theme colors
const colors = {
  surface: '#1a1a1a',
  surfaceLight: '#262626',
  border: '#333333',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

interface TaskListProps {
  /** List of tasks */
  tasks: Task[];
  /** Enable haptic feedback */
  hapticEnabled?: boolean;
}

/**
 * Get status color for task
 */
function getStatusColor(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return colors.success;
    case 'running':
      return colors.info;
    case 'failed':
      return colors.error;
    case 'pending':
    default:
      return colors.gray500;
  }
}

/**
 * Get status icon for task
 */
function getStatusIcon(status: TaskStatus): string {
  switch (status) {
    case 'completed':
      return '✓';
    case 'running':
      return '▶';
    case 'failed':
      return '✗';
    case 'pending':
    default:
      return '○';
  }
}

/**
 * Format duration for display
 */
function formatTaskDuration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt) return '—';

  const start = new Date(startedAt);
  const end = completedAt ? new Date(completedAt) : new Date();
  const durationMs = end.getTime() - start.getTime();
  const seconds = Math.round(durationMs / 1000);

  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp: string | null): string {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Individual task item
 */
interface TaskItemProps {
  task: Task;
  isExpanded: boolean;
  onToggle: () => void;
  hapticEnabled: boolean;
}

function TaskItem({ task, isExpanded, onToggle, hapticEnabled }: TaskItemProps): React.ReactElement {
  const statusColor = getStatusColor(task.status);
  const statusIcon = getStatusIcon(task.status);
  const hasError = task.status === 'failed' && task.error_message;

  const handlePress = useCallback(() => {
    if (hasError || task.status === 'running') {
      if (hapticEnabled) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      }
      onToggle();
    }
  }, [hasError, task.status, hapticEnabled, onToggle]);

  return (
    <Pressable
      onPress={handlePress}
      style={({ pressed }) => [
        styles.taskItem,
        (hasError || task.status === 'running') && styles.taskItemExpandable,
        pressed && (hasError || task.status === 'running') && styles.taskItemPressed,
      ]}
      accessibilityLabel={`Task ${task.name}, status: ${task.status}`}
      accessibilityHint={hasError ? 'Tap to see error details' : undefined}
    >
      <View style={styles.taskHeader}>
        {/* Status indicator */}
        <View style={[styles.statusIndicator, { backgroundColor: statusColor }]}>
          <Text style={styles.statusIcon}>{statusIcon}</Text>
        </View>

        {/* Task info */}
        <View style={styles.taskInfo}>
          <Text style={styles.taskName} numberOfLines={1}>
            {task.name}
          </Text>
          <View style={styles.taskMeta}>
            <Text style={[styles.taskStatus, { color: statusColor }]}>
              {task.status.charAt(0).toUpperCase() + task.status.slice(1)}
            </Text>
            {task.started_at && (
              <Text style={styles.taskTime}>
                {task.status === 'running' ? 'Started ' : ''}
                {formatTime(task.started_at)}
              </Text>
            )}
          </View>
        </View>

        {/* Duration */}
        <View style={styles.durationContainer}>
          <Text style={styles.duration}>
            {formatTaskDuration(task.started_at, task.completed_at)}
          </Text>
          {(hasError || task.status === 'running') && (
            <Text style={styles.expandIcon}>
              {isExpanded ? '▼' : '▶'}
            </Text>
          )}
        </View>
      </View>

      {/* Expanded details */}
      {isExpanded && (
        <View style={styles.expandedContent}>
          {task.status === 'failed' && task.error_message && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorLabel}>Error:</Text>
              <Text style={styles.errorMessage}>{task.error_message}</Text>
            </View>
          )}
          {task.status === 'running' && (
            <View style={styles.runningDetails}>
              <Text style={styles.runningText}>
                Processing since {formatTime(task.started_at)}
              </Text>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

/**
 * TaskList - List of orchestration tasks
 *
 * Displays all tasks with:
 * - Status icons and colors
 * - Duration tracking
 * - Expandable error messages
 * - Running task details
 */
export function TaskList({ tasks, hapticEnabled = true }: TaskListProps): React.ReactElement {
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);

  const toggleExpanded = useCallback((taskId: string) => {
    setExpandedTaskId((current) => (current === taskId ? null : taskId));
  }, []);

  // Sort tasks: running first, then by order
  const sortedTasks = React.useMemo(() => {
    return [...tasks].sort((a, b) => {
      // Running tasks first
      if (a.status === 'running' && b.status !== 'running') return -1;
      if (b.status === 'running' && a.status !== 'running') return 1;
      // Then by iteration order
      return a.iteration_number - b.iteration_number;
    });
  }, [tasks]);

  const renderItem = useCallback(
    ({ item }: { item: Task }) => (
      <TaskItem
        task={item}
        isExpanded={expandedTaskId === item.id}
        onToggle={() => toggleExpanded(item.id)}
        hapticEnabled={hapticEnabled}
      />
    ),
    [expandedTaskId, toggleExpanded, hapticEnabled]
  );

  const keyExtractor = useCallback((item: Task) => item.id, []);

  // Summary stats
  const stats = React.useMemo(() => {
    const completed = tasks.filter((t) => t.status === 'completed').length;
    const failed = tasks.filter((t) => t.status === 'failed').length;
    const running = tasks.filter((t) => t.status === 'running').length;
    const pending = tasks.filter((t) => t.status === 'pending').length;
    return { completed, failed, running, pending };
  }, [tasks]);

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Tasks</Text>
        <View style={styles.statsContainer}>
          {stats.completed > 0 && (
            <Text style={[styles.statBadge, { backgroundColor: colors.success }]}>
              {stats.completed} ✓
            </Text>
          )}
          {stats.running > 0 && (
            <Text style={[styles.statBadge, { backgroundColor: colors.info }]}>
              {stats.running} ▶
            </Text>
          )}
          {stats.failed > 0 && (
            <Text style={[styles.statBadge, { backgroundColor: colors.error }]}>
              {stats.failed} ✗
            </Text>
          )}
        </View>
      </View>

      {tasks.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No tasks yet</Text>
          <Text style={styles.emptySubtext}>
            Tasks will appear here when the orchestration starts
          </Text>
        </View>
      ) : (
        <FlatList
          data={sortedTasks}
          renderItem={renderItem}
          keyExtractor={keyExtractor}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  statsContainer: {
    flexDirection: 'row',
    gap: 6,
  },
  statBadge: {
    color: colors.white,
    fontSize: 11,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
    overflow: 'hidden',
  },
  taskItem: {
    paddingVertical: 12,
  },
  taskItemExpandable: {
    borderRadius: 8,
  },
  taskItemPressed: {
    backgroundColor: colors.surfaceLight,
  },
  taskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIndicator: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  statusIcon: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '600',
  },
  taskInfo: {
    flex: 1,
  },
  taskName: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  taskMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  taskStatus: {
    fontSize: 12,
    fontWeight: '500',
  },
  taskTime: {
    color: colors.gray500,
    fontSize: 12,
  },
  durationContainer: {
    alignItems: 'flex-end',
  },
  duration: {
    color: colors.gray400,
    fontSize: 13,
    fontWeight: '500',
  },
  expandIcon: {
    color: colors.gray500,
    fontSize: 10,
    marginTop: 4,
  },
  expandedContent: {
    marginTop: 12,
    marginLeft: 40,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  errorContainer: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: colors.error,
  },
  errorLabel: {
    color: colors.error,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  errorMessage: {
    color: colors.gray400,
    fontSize: 13,
    lineHeight: 18,
  },
  runningDetails: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: colors.info,
  },
  runningText: {
    color: colors.info,
    fontSize: 13,
  },
  separator: {
    height: 1,
    backgroundColor: colors.border,
  },
  emptyState: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  emptyText: {
    color: colors.gray400,
    fontSize: 14,
    marginBottom: 4,
  },
  emptySubtext: {
    color: colors.gray500,
    fontSize: 12,
    textAlign: 'center',
  },
});

export default TaskList;

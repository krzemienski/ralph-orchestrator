/**
 * TaskList - Task breakdown display for orchestrator detail
 *
 * Displays:
 * - Task name and status badge
 * - Duration (if started)
 * - Expandable output/error content
 * - Scrollable list for many tasks
 */

import React, { useState, useCallback, useMemo } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import type { Task, TaskStatus } from '../../lib/types';

interface TaskListProps {
  /** List of tasks to display */
  tasks: Task[];
  /** Maximum height before scrolling (default: 400) */
  maxHeight?: number;
}

/** Get status configuration for display */
function getStatusConfig(status: TaskStatus): { color: string; bgColor: string; icon: string } {
  switch (status) {
    case 'pending':
      return { color: 'text-gray-400', bgColor: 'bg-gray-500/20', icon: '○' };
    case 'running':
      return { color: 'text-blue-400', bgColor: 'bg-blue-500/20', icon: '◐' };
    case 'completed':
      return { color: 'text-green-400', bgColor: 'bg-green-500/20', icon: '●' };
    case 'failed':
      return { color: 'text-red-400', bgColor: 'bg-red-500/20', icon: '✕' };
  }
}

/** Calculate task duration */
function calculateDuration(startedAt?: string, completedAt?: string): string | null {
  if (!startedAt) return null;

  const start = new Date(startedAt);
  const end = completedAt ? new Date(completedAt) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) {
    return `${diffSeconds}s`;
  }
  const mins = Math.floor(diffSeconds / 60);
  const secs = diffSeconds % 60;
  return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
}

/** Individual task row component */
function TaskRow({ task }: { task: Task }): React.JSX.Element {
  const [isExpanded, setIsExpanded] = useState(false);
  const statusConfig = getStatusConfig(task.status);
  const duration = calculateDuration(task.started_at, task.completed_at);
  const hasExpandableContent = Boolean(task.output || task.error);

  /** Toggle expansion */
  const handlePress = useCallback(() => {
    if (hasExpandableContent) {
      setIsExpanded((prev) => !prev);
    }
  }, [hasExpandableContent]);

  return (
    <Pressable
      className={`py-3 px-2 ${hasExpandableContent ? 'active:opacity-70' : ''}`}
      onPress={handlePress}
      disabled={!hasExpandableContent}
    >
      {/* Main row content */}
      <View className="flex-row items-center">
        {/* Status icon */}
        <Text className={`text-base mr-2 ${statusConfig.color}`}>{statusConfig.icon}</Text>

        {/* Task name */}
        <View className="flex-1">
          <Text className="text-sm text-textPrimary" numberOfLines={1}>
            {task.name}
          </Text>
        </View>

        {/* Duration */}
        {duration && (
          <Text className="text-xs text-textSecondary mr-2">{duration}</Text>
        )}

        {/* Status badge */}
        <View className={`rounded-md px-2 py-0.5 ${statusConfig.bgColor}`}>
          <Text className={`text-xs font-medium capitalize ${statusConfig.color}`}>
            {task.status}
          </Text>
        </View>

        {/* Expand indicator */}
        {hasExpandableContent && (
          <Text className="text-xs text-textSecondary ml-2">
            {isExpanded ? '▼' : '▶'}
          </Text>
        )}
      </View>

      {/* Expanded content */}
      {isExpanded && (
        <View className="mt-2 ml-6">
          {/* Output */}
          {task.output && (
            <View className="bg-surfaceLight rounded-lg p-3 mb-2">
              <Text className="text-xs text-textSecondary font-medium mb-1">Output</Text>
              <Text className="text-xs text-textPrimary font-mono" numberOfLines={10}>
                {task.output}
              </Text>
            </View>
          )}

          {/* Error */}
          {task.error && (
            <View className="bg-red-500/10 rounded-lg p-3">
              <Text className="text-xs text-red-400 font-medium mb-1">Error</Text>
              <Text className="text-xs text-red-300 font-mono" numberOfLines={10}>
                {task.error}
              </Text>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

/**
 * TaskList component
 */
export function TaskList({ tasks, maxHeight = 400 }: TaskListProps): React.JSX.Element {
  // Sort tasks: running first, then by status order
  const sortedTasks = useMemo(() => {
    const statusOrder: Record<TaskStatus, number> = {
      running: 0,
      pending: 1,
      completed: 2,
      failed: 3,
    };
    return [...tasks].sort((a, b) => statusOrder[a.status] - statusOrder[b.status]);
  }, [tasks]);

  // Calculate summary stats
  const stats = useMemo(() => {
    return {
      total: tasks.length,
      completed: tasks.filter((t) => t.status === 'completed').length,
      failed: tasks.filter((t) => t.status === 'failed').length,
      running: tasks.filter((t) => t.status === 'running').length,
    };
  }, [tasks]);

  // Empty state
  if (tasks.length === 0) {
    return (
      <View className="bg-surface rounded-2xl p-6">
        <Text className="text-sm font-medium text-textSecondary mb-4">Tasks</Text>
        <View className="items-center py-6">
          <Text className="text-3xl mb-2">📋</Text>
          <Text className="text-sm text-textSecondary text-center">No tasks yet</Text>
          <Text className="text-xs text-textSecondary text-center mt-1">
            Tasks will appear as the orchestration runs
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View className="bg-surface rounded-2xl p-4">
      {/* Header with stats */}
      <View className="flex-row items-center justify-between mb-2">
        <Text className="text-sm font-medium text-textSecondary">Tasks</Text>
        <View className="flex-row items-center">
          {stats.failed > 0 && (
            <View className="flex-row items-center mr-2">
              <Text className="text-xs text-red-400">{stats.failed} failed</Text>
            </View>
          )}
          <Text className="text-xs text-textSecondary">
            {stats.completed}/{stats.total} done
          </Text>
        </View>
      </View>

      {/* Running indicator */}
      {stats.running > 0 && (
        <View className="flex-row items-center bg-blue-500/10 rounded-lg px-3 py-2 mb-3">
          <Text className="text-sm text-blue-400 mr-2">◐</Text>
          <Text className="text-xs text-blue-400">
            {stats.running} task{stats.running > 1 ? 's' : ''} running
          </Text>
        </View>
      )}

      {/* Task list */}
      <ScrollView
        style={{ maxHeight }}
        showsVerticalScrollIndicator={false}
        nestedScrollEnabled
      >
        <View className="divide-y divide-gray-800">
          {sortedTasks.map((task) => (
            <TaskRow key={task.id} task={task} />
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

export default TaskList;

/**
 * ActionHistory - Recent actions log
 *
 * Displays the last 10 actions taken on orchestrators with:
 * - Action type (start, stop, pause, resume)
 * - Timestamp
 * - Target orchestrator name
 * - Success/failure status
 */

import React, { useMemo } from 'react';
import { View, Text, FlatList } from 'react-native';

/** Action types that can be performed on orchestrators */
export type ActionType = 'start' | 'stop' | 'pause' | 'resume';

/** Status of the action */
export type ActionStatus = 'success' | 'pending' | 'failed';

/** Individual action record */
export interface ActionRecord {
  id: string;
  type: ActionType;
  orchestratorId: string;
  orchestratorName: string;
  timestamp: Date;
  status: ActionStatus;
  error?: string;
}

interface ActionHistoryProps {
  /** List of recent actions */
  actions: ActionRecord[];
  /** Maximum number of actions to display */
  maxItems?: number;
}

/** Action type display configuration */
interface ActionConfig {
  icon: string;
  label: string;
  color: string;
}

/** Get display configuration for action type */
function getActionConfig(type: ActionType): ActionConfig {
  switch (type) {
    case 'start':
      return { icon: '▶', label: 'Started', color: 'text-green-400' };
    case 'stop':
      return { icon: '■', label: 'Stopped', color: 'text-red-400' };
    case 'pause':
      return { icon: '⏸', label: 'Paused', color: 'text-orange-400' };
    case 'resume':
      return { icon: '▶', label: 'Resumed', color: 'text-blue-400' };
  }
}

/** Get status indicator */
function getStatusIndicator(status: ActionStatus): { icon: string; color: string } {
  switch (status) {
    case 'success':
      return { icon: '✓', color: 'text-green-400' };
    case 'pending':
      return { icon: '⏳', color: 'text-yellow-400' };
    case 'failed':
      return { icon: '✕', color: 'text-red-400' };
  }
}

/** Format timestamp to relative time */
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);

  if (diffSeconds < 60) {
    return 'just now';
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  return date.toLocaleDateString();
}

/** Individual action row */
function ActionRow({ action }: { action: ActionRecord }): React.JSX.Element {
  const actionConfig = getActionConfig(action.type);
  const statusIndicator = getStatusIndicator(action.status);

  return (
    <View className="flex-row items-center py-3 border-b border-gray-800">
      {/* Action icon and type */}
      <View className="w-20">
        <Text className={`text-sm font-medium ${actionConfig.color}`}>
          {actionConfig.icon} {actionConfig.label}
        </Text>
      </View>

      {/* Orchestrator name and timestamp */}
      <View className="flex-1 px-2">
        <Text className="text-sm text-textPrimary" numberOfLines={1}>
          {action.orchestratorName}
        </Text>
        <Text className="text-xs text-textSecondary">
          {formatRelativeTime(action.timestamp)}
        </Text>
      </View>

      {/* Status indicator */}
      <View className="w-8 items-end">
        <Text className={statusIndicator.color}>{statusIndicator.icon}</Text>
      </View>
    </View>
  );
}

/**
 * ActionHistory component
 */
export function ActionHistory({
  actions,
  maxItems = 10,
}: ActionHistoryProps): React.JSX.Element {
  // Limit and sort actions (most recent first)
  const displayActions = useMemo(() => {
    return [...actions]
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, maxItems);
  }, [actions, maxItems]);

  // Empty state
  if (displayActions.length === 0) {
    return (
      <View className="bg-surface rounded-2xl p-6">
        <Text className="text-sm font-medium text-textSecondary mb-4">
          Recent Actions
        </Text>
        <View className="items-center py-6">
          <Text className="text-3xl mb-2">📋</Text>
          <Text className="text-sm text-textSecondary text-center">
            No actions yet
          </Text>
          <Text className="text-xs text-textSecondary text-center mt-1">
            Actions will appear here as you control orchestrations
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View className="bg-surface rounded-2xl p-4">
      <Text className="text-sm font-medium text-textSecondary mb-2 px-2">
        Recent Actions
      </Text>
      <FlatList
        data={displayActions}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <ActionRow action={item} />}
        scrollEnabled={false}
        ItemSeparatorComponent={null}
      />
    </View>
  );
}

export default ActionHistory;

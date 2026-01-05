/**
 * StatusBadge - Color-coded status indicator for orchestrator status
 *
 * Displays status with appropriate color and optional pulse animation for running state.
 */

import React from 'react';
import { View, Text } from 'react-native';
import type { OrchestratorStatus } from '../../lib/types';

interface StatusBadgeProps {
  /** Current status to display */
  status: OrchestratorStatus;
  /** Size variant */
  size?: 'small' | 'medium' | 'large';
}

/**
 * Get display text for status
 */
function getStatusText(status: OrchestratorStatus): string {
  const statusMap: Record<OrchestratorStatus, string> = {
    pending: 'Pending',
    running: 'Running',
    paused: 'Paused',
    completed: 'Completed',
    failed: 'Failed',
  };
  return statusMap[status];
}

/**
 * Get color classes for status
 */
function getStatusColors(status: OrchestratorStatus): {
  bg: string;
  text: string;
  dot: string;
} {
  const colorMap: Record<OrchestratorStatus, { bg: string; text: string; dot: string }> = {
    pending: {
      bg: 'bg-gray-500/20',
      text: 'text-gray-400',
      dot: 'bg-gray-400',
    },
    running: {
      bg: 'bg-blue-500/20',
      text: 'text-blue-400',
      dot: 'bg-blue-400',
    },
    paused: {
      bg: 'bg-yellow-500/20',
      text: 'text-yellow-400',
      dot: 'bg-yellow-400',
    },
    completed: {
      bg: 'bg-green-500/20',
      text: 'text-green-400',
      dot: 'bg-green-400',
    },
    failed: {
      bg: 'bg-red-500/20',
      text: 'text-red-400',
      dot: 'bg-red-400',
    },
  };
  return colorMap[status];
}

/**
 * Get size classes
 */
function getSizeClasses(size: 'small' | 'medium' | 'large'): {
  container: string;
  text: string;
  dot: string;
} {
  const sizeMap = {
    small: {
      container: 'px-2 py-0.5',
      text: 'text-xs',
      dot: 'w-1.5 h-1.5',
    },
    medium: {
      container: 'px-2.5 py-1',
      text: 'text-sm',
      dot: 'w-2 h-2',
    },
    large: {
      container: 'px-3 py-1.5',
      text: 'text-base',
      dot: 'w-2.5 h-2.5',
    },
  };
  return sizeMap[size];
}

/**
 * StatusBadge component
 */
export function StatusBadge({ status, size = 'medium' }: StatusBadgeProps): React.JSX.Element {
  const colors = getStatusColors(status);
  const sizes = getSizeClasses(size);

  return (
    <View
      className={`flex-row items-center rounded-full ${colors.bg} ${sizes.container}`}
    >
      <View className={`rounded-full ${colors.dot} ${sizes.dot} mr-1.5`} />
      <Text className={`font-medium ${colors.text} ${sizes.text}`}>
        {getStatusText(status)}
      </Text>
    </View>
  );
}

export default StatusBadge;

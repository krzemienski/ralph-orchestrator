/**
 * StatusBadge Component
 *
 * Color-coded status indicator for orchestrator lifecycle status.
 * Features pulse animation for running state.
 */

import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import type { OrchestratorStatus } from '../../lib/types';
import { STATUS_COLORS } from '../../lib/types';

interface StatusBadgeProps {
  /** Current status to display */
  status: OrchestratorStatus;
  /** Optional size variant */
  size?: 'small' | 'medium' | 'large';
  /** Optional custom label override */
  label?: string;
}

/**
 * Status label mapping for display
 */
const STATUS_LABELS: Record<OrchestratorStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  paused: 'Paused',
  completed: 'Completed',
  failed: 'Failed',
};

/**
 * Size configurations for badge variants
 */
const SIZE_CONFIG = {
  small: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    fontSize: 10,
    borderRadius: 8,
    indicatorSize: 6,
  },
  medium: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    fontSize: 12,
    borderRadius: 12,
    indicatorSize: 8,
  },
  large: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    fontSize: 14,
    borderRadius: 16,
    indicatorSize: 10,
  },
};

/**
 * StatusBadge - Visual indicator for orchestrator status
 *
 * Features:
 * - Color-coded background based on status
 * - Pulse animation for running state (visual indicator)
 * - Three size variants: small, medium, large
 * - Customizable label override
 */
export function StatusBadge({
  status,
  size = 'medium',
  label,
}: StatusBadgeProps): React.ReactElement {
  const color = STATUS_COLORS[status];
  const displayLabel = label ?? STATUS_LABELS[status];
  const config = SIZE_CONFIG[size];

  // Use animated value for running pulse effect
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    if (status === 'running') {
      // Create pulse animation loop for running status
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 0.6,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();

      return () => {
        pulse.stop();
        pulseAnim.setValue(1);
      };
    } else {
      // Reset animation for non-running states
      pulseAnim.setValue(1);
    }
  }, [status, pulseAnim]);

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: color + '20', // 20% opacity background
          paddingHorizontal: config.paddingHorizontal,
          paddingVertical: config.paddingVertical,
          borderRadius: config.borderRadius,
        },
      ]}
    >
      {/* Status indicator dot with optional pulse */}
      <Animated.View
        style={[
          styles.indicator,
          {
            backgroundColor: color,
            width: config.indicatorSize,
            height: config.indicatorSize,
            borderRadius: config.indicatorSize / 2,
            opacity: status === 'running' ? pulseAnim : 1,
          },
        ]}
      />
      <Text
        style={[
          styles.label,
          {
            color: color,
            fontSize: config.fontSize,
          },
        ]}
      >
        {displayLabel}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  indicator: {
    marginRight: 6,
  },
  label: {
    fontWeight: '600',
  },
});

export default StatusBadge;

/**
 * EmptyState Component
 *
 * Displays when no orchestrators exist in the system.
 * Shows a friendly message and a button to start a new orchestration.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface EmptyStateProps {
  /** Title message to display */
  title?: string;
  /** Subtitle/description message */
  subtitle?: string;
  /** Text for the action button */
  actionText?: string;
  /** Callback when action button is pressed */
  onAction?: () => void;
}

/**
 * Theme colors for dark mode
 */
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceHover: '#252525',
  border: '#333333',
  white: '#ffffff',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  info: '#3b82f6',
  infoDim: '#3b82f620',
};

/**
 * EmptyState - Shows when no orchestrators are available
 *
 * Features:
 * - Large icon for visual clarity
 * - Customizable title and subtitle
 * - Optional action button (e.g., "Start New")
 * - Accessible with proper labels
 */
export function EmptyState({
  title = 'No Orchestrators',
  subtitle = 'Start a new orchestration to monitor your workflows',
  actionText = 'Start New',
  onAction,
}: EmptyStateProps): React.ReactElement {
  return (
    <View
      style={styles.container}
      accessibilityRole="none"
      accessibilityLabel={`${title}. ${subtitle}`}
    >
      {/* Icon */}
      <View style={styles.iconContainer}>
        <Ionicons
          name="layers-outline"
          size={64}
          color={colors.gray500}
        />
      </View>

      {/* Title */}
      <Text style={styles.title}>{title}</Text>

      {/* Subtitle */}
      <Text style={styles.subtitle}>{subtitle}</Text>

      {/* Action Button */}
      {onAction && (
        <Pressable
          onPress={onAction}
          style={({ pressed }) => [
            styles.button,
            pressed && styles.buttonPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel={actionText}
          accessibilityHint="Double tap to start a new orchestration"
        >
          <Ionicons
            name="add-circle-outline"
            size={20}
            color={colors.white}
            style={styles.buttonIcon}
          />
          <Text style={styles.buttonText}>{actionText}</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    paddingVertical: 48,
    minHeight: 300,
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.infoDim,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    color: colors.white,
    fontSize: 20,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    color: colors.gray400,
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.info,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonIcon: {
    marginRight: 8,
  },
  buttonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default EmptyState;

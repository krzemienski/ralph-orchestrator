/**
 * OrchestratorSelector Component
 *
 * Dropdown/picker for selecting which orchestrator's logs to view.
 * Shows orchestrator name, status, and iteration count.
 */

import React, { memo, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Modal,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { Orchestrator, OrchestratorStatus } from '../../lib/types';

interface OrchestratorSelectorProps {
  /** List of available orchestrators */
  orchestrators: Orchestrator[];
  /** Currently selected orchestrator ID */
  selectedId: string | null;
  /** Callback when orchestrator is selected */
  onSelect: (id: string) => void;
  /** Whether the selector is disabled */
  disabled?: boolean;
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
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  info: '#3b82f6',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
};

/**
 * Get status color
 */
function getStatusColor(status: OrchestratorStatus): string {
  switch (status) {
    case 'running':
      return colors.success;
    case 'completed':
      return colors.info;
    case 'failed':
      return colors.error;
    case 'pending':
      return colors.warning;
    default:
      return colors.gray500;
  }
}

/**
 * Format status for display
 */
function formatStatus(status: OrchestratorStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * OrchestratorSelector - Dropdown for selecting orchestrator
 *
 * Features:
 * - Shows current selection with status indicator
 * - Modal picker for selecting different orchestrator
 * - Displays orchestrator name, status, and iteration info
 * - Sorted with running orchestrators first
 */
function OrchestratorSelectorComponent({
  orchestrators,
  selectedId,
  onSelect,
  disabled = false,
}: OrchestratorSelectorProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(false);

  const selectedOrchestrator = orchestrators.find((o) => o.id === selectedId);

  /**
   * Sort orchestrators: running first, then by updated_at
   */
  const sortedOrchestrators = [...orchestrators].sort((a, b) => {
    // Running first
    if (a.status === 'running' && b.status !== 'running') return -1;
    if (b.status === 'running' && a.status !== 'running') return 1;
    // Then by updated_at (most recent first)
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  const handleOpen = useCallback(() => {
    if (!disabled) {
      setIsOpen(true);
    }
  }, [disabled]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  const handleSelect = useCallback(
    (id: string) => {
      onSelect(id);
      setIsOpen(false);
    },
    [onSelect]
  );

  const renderItem = useCallback(
    ({ item }: { item: Orchestrator }) => {
      const isSelected = item.id === selectedId;
      const statusColor = getStatusColor(item.status);

      return (
        <Pressable
          onPress={() => handleSelect(item.id)}
          style={({ pressed }) => [
            styles.option,
            isSelected && styles.optionSelected,
            pressed && styles.optionPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel={`Select ${item.name}`}
          accessibilityState={{ selected: isSelected }}
        >
          <View style={styles.optionContent}>
            {/* Status Dot */}
            <View style={[styles.statusDot, { backgroundColor: statusColor }]} />

            {/* Name and Info */}
            <View style={styles.optionInfo}>
              <Text style={styles.optionName} numberOfLines={1}>
                {item.name}
              </Text>
              <Text style={styles.optionMeta}>
                {formatStatus(item.status)} • Iteration {item.metrics.iterations_completed}/
                {item.metrics.iterations_total}
              </Text>
            </View>

            {/* Selected Check */}
            {isSelected && (
              <Ionicons name="checkmark" size={20} color={colors.info} />
            )}
          </View>
        </Pressable>
      );
    },
    [selectedId, handleSelect]
  );

  const keyExtractor = useCallback((item: Orchestrator) => item.id, []);

  return (
    <View style={styles.container}>
      {/* Selector Button */}
      <Pressable
        onPress={handleOpen}
        disabled={disabled}
        style={({ pressed }) => [
          styles.selector,
          pressed && !disabled && styles.selectorPressed,
          disabled && styles.selectorDisabled,
        ]}
        accessibilityRole="button"
        accessibilityLabel="Select orchestrator"
        accessibilityHint="Opens orchestrator selection menu"
        accessibilityState={{ disabled, expanded: isOpen }}
      >
        {selectedOrchestrator ? (
          <View style={styles.selectedContent}>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: getStatusColor(selectedOrchestrator.status) },
              ]}
            />
            <Text style={styles.selectedName} numberOfLines={1}>
              {selectedOrchestrator.name}
            </Text>
          </View>
        ) : (
          <Text style={styles.placeholder}>Select Orchestrator</Text>
        )}
        <Ionicons
          name={isOpen ? 'chevron-up' : 'chevron-down'}
          size={20}
          color={disabled ? colors.gray500 : colors.gray400}
        />
      </Pressable>

      {/* Dropdown Modal */}
      <Modal
        visible={isOpen}
        transparent
        animationType="fade"
        onRequestClose={handleClose}
      >
        <Pressable style={styles.modalOverlay} onPress={handleClose}>
          <View style={styles.modalContent}>
            {/* Header */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Orchestrator</Text>
              <Pressable
                onPress={handleClose}
                style={styles.closeButton}
                accessibilityRole="button"
                accessibilityLabel="Close"
              >
                <Ionicons name="close" size={24} color={colors.gray400} />
              </Pressable>
            </View>

            {/* Options List */}
            {sortedOrchestrators.length > 0 ? (
              <FlatList
                data={sortedOrchestrators}
                renderItem={renderItem}
                keyExtractor={keyExtractor}
                style={styles.optionsList}
                showsVerticalScrollIndicator={false}
              />
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyText}>No orchestrators available</Text>
              </View>
            )}
          </View>
        </Pressable>
      </Modal>
    </View>
  );
}

export const OrchestratorSelector = memo(OrchestratorSelectorComponent);

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  selector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  selectorPressed: {
    backgroundColor: colors.surfaceHover,
  },
  selectorDisabled: {
    opacity: 0.5,
  },
  selectedContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 10,
  },
  selectedName: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  placeholder: {
    color: colors.gray500,
    fontSize: 16,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    width: '100%',
    maxWidth: 400,
    maxHeight: '70%',
    overflow: 'hidden',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalTitle: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '600',
  },
  closeButton: {
    padding: 4,
  },
  optionsList: {
    maxHeight: 400,
  },
  option: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  optionSelected: {
    backgroundColor: `${colors.info}15`,
  },
  optionPressed: {
    backgroundColor: colors.surfaceHover,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionInfo: {
    flex: 1,
    marginRight: 12,
  },
  optionName: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '500',
    marginBottom: 2,
  },
  optionMeta: {
    color: colors.gray500,
    fontSize: 13,
  },
  emptyState: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    color: colors.gray500,
    fontSize: 14,
  },
});

export default OrchestratorSelector;

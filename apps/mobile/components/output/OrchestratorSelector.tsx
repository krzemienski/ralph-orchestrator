/**
 * OrchestratorSelector - Dropdown to select orchestrator for log viewing
 *
 * Shows currently selected orchestrator and lists all running orchestrators.
 */

import React, { useState, useCallback } from 'react';
import { View, Text, Pressable, Modal, FlatList } from 'react-native';
import type { ListRenderItem } from 'react-native';
import type { Orchestrator } from '../../lib/types';
import { StatusBadge } from '../ui/StatusBadge';

interface OrchestratorSelectorProps {
  /** List of available orchestrators */
  orchestrators: Orchestrator[];
  /** Currently selected orchestrator ID */
  selectedId: string | null;
  /** Callback when orchestrator is selected */
  onSelect: (id: string) => void;
  /** Whether data is loading */
  isLoading?: boolean;
}

/**
 * OrchestratorSelector component
 */
export function OrchestratorSelector({
  orchestrators,
  selectedId,
  onSelect,
  isLoading = false,
}: OrchestratorSelectorProps): React.JSX.Element {
  const [modalVisible, setModalVisible] = useState(false);

  const selectedOrchestrator = orchestrators.find((o) => o.id === selectedId);

  const handleOpen = useCallback(() => {
    setModalVisible(true);
  }, []);

  const handleClose = useCallback(() => {
    setModalVisible(false);
  }, []);

  const handleSelect = useCallback(
    (id: string) => {
      onSelect(id);
      setModalVisible(false);
    },
    [onSelect]
  );

  const renderItem: ListRenderItem<Orchestrator> = useCallback(
    ({ item }) => {
      const isSelected = item.id === selectedId;
      return (
        <Pressable
          onPress={() => handleSelect(item.id)}
          className={`p-4 border-b border-border flex-row items-center justify-between active:bg-surface ${
            isSelected ? 'bg-blue-500/10' : ''
          }`}
        >
          <View className="flex-1 mr-3">
            <Text
              className={`text-base font-medium ${
                isSelected ? 'text-blue-400' : 'text-textPrimary'
              }`}
              numberOfLines={1}
            >
              {item.name}
            </Text>
            <Text className="text-xs text-textSecondary mt-0.5">
              {item.metrics.iterations_completed}/{item.metrics.iterations_total} iterations
            </Text>
          </View>
          <StatusBadge status={item.status} size="small" />
        </Pressable>
      );
    },
    [selectedId, handleSelect]
  );

  const keyExtractor = useCallback((item: Orchestrator) => item.id, []);

  return (
    <>
      {/* Selector Button */}
      <Pressable
        onPress={handleOpen}
        className="bg-surface border-b border-border p-3 flex-row items-center justify-between active:opacity-80"
      >
        <View className="flex-row items-center flex-1">
          <View className="w-8 h-8 rounded-full bg-blue-500/20 items-center justify-center mr-3">
            <Text className="text-blue-400">🔧</Text>
          </View>
          {selectedOrchestrator ? (
            <View className="flex-1">
              <Text className="text-base font-medium text-textPrimary" numberOfLines={1}>
                {selectedOrchestrator.name}
              </Text>
              <Text className="text-xs text-textSecondary">
                {selectedOrchestrator.status}
              </Text>
            </View>
          ) : (
            <Text className="text-base text-textSecondary">
              {isLoading ? 'Loading...' : 'Select Orchestrator'}
            </Text>
          )}
        </View>
        <Text className="text-textSecondary">▼</Text>
      </Pressable>

      {/* Selection Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={handleClose}
      >
        <View className="flex-1 bg-background">
          {/* Modal Header */}
          <View className="flex-row items-center justify-between p-4 border-b border-border">
            <Text className="text-lg font-semibold text-textPrimary">
              Select Orchestrator
            </Text>
            <Pressable
              onPress={handleClose}
              className="p-2 rounded-full active:bg-surface"
            >
              <Text className="text-blue-400 text-base font-medium">Done</Text>
            </Pressable>
          </View>

          {/* Orchestrator List */}
          {orchestrators.length === 0 ? (
            <View className="flex-1 items-center justify-center p-8">
              <Text className="text-2xl mb-2">📭</Text>
              <Text className="text-base text-textSecondary text-center">
                No orchestrators available
              </Text>
              <Text className="text-sm text-textSecondary text-center mt-1">
                Start an orchestration to view logs
              </Text>
            </View>
          ) : (
            <FlatList
              data={orchestrators}
              renderItem={renderItem}
              keyExtractor={keyExtractor}
              showsVerticalScrollIndicator={false}
            />
          )}
        </View>
      </Modal>
    </>
  );
}

export default OrchestratorSelector;

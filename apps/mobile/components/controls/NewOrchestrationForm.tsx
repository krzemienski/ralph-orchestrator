/**
 * NewOrchestrationForm - Form for starting a new orchestration
 *
 * Provides inputs for:
 * - Prompt file path (required)
 * - Config file path (optional)
 * - Max iterations (optional, default: unlimited)
 * - Max runtime in seconds (optional, default: unlimited)
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import type { StartOrchestratorRequest } from '../../lib/types';

interface NewOrchestrationFormProps {
  /** Called when form is submitted with valid data */
  onSubmit: (request: StartOrchestratorRequest) => void;
  /** Whether form submission is in progress */
  isSubmitting: boolean;
  /** Called to cancel/close the form */
  onCancel: () => void;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
}

/**
 * NewOrchestrationForm component
 */
export function NewOrchestrationForm({
  onSubmit,
  isSubmitting,
  onCancel,
  hapticEnabled = true,
}: NewOrchestrationFormProps): React.JSX.Element {
  // Form state
  const [promptFile, setPromptFile] = useState('');
  const [configFile, setConfigFile] = useState('');
  const [maxIterations, setMaxIterations] = useState('');
  const [maxRuntime, setMaxRuntime] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  /** Trigger haptic feedback */
  const triggerHaptic = useCallback(() => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  }, [hapticEnabled]);

  /** Validate form inputs */
  const validate = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};

    // Prompt file is required
    if (!promptFile.trim()) {
      newErrors.promptFile = 'Prompt file is required';
    } else if (!promptFile.endsWith('.md')) {
      newErrors.promptFile = 'Prompt file must be a .md file';
    }

    // Max iterations must be positive if provided
    if (maxIterations.trim()) {
      const parsed = parseInt(maxIterations, 10);
      if (isNaN(parsed) || parsed < 1) {
        newErrors.maxIterations = 'Must be a positive number';
      }
    }

    // Max runtime must be positive if provided
    if (maxRuntime.trim()) {
      const parsed = parseInt(maxRuntime, 10);
      if (isNaN(parsed) || parsed < 1) {
        newErrors.maxRuntime = 'Must be a positive number';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [promptFile, maxIterations, maxRuntime]);

  /** Handle form submission */
  const handleSubmit = useCallback(() => {
    triggerHaptic();

    if (!validate()) {
      return;
    }

    const request: StartOrchestratorRequest = {
      prompt_file: promptFile.trim(),
    };

    if (configFile.trim()) {
      request.config_file = configFile.trim();
    }

    if (maxIterations.trim()) {
      request.max_iterations = parseInt(maxIterations, 10);
    }

    if (maxRuntime.trim()) {
      request.max_runtime_seconds = parseInt(maxRuntime, 10);
    }

    onSubmit(request);
  }, [promptFile, configFile, maxIterations, maxRuntime, validate, onSubmit, triggerHaptic]);

  /** Handle cancel */
  const handleCancel = useCallback(() => {
    triggerHaptic();
    onCancel();
  }, [onCancel, triggerHaptic]);

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1"
    >
      <ScrollView
        className="flex-1"
        contentContainerClassName="p-4 gap-4"
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View className="mb-2">
          <Text className="text-xl font-bold text-textPrimary">
            New Orchestration
          </Text>
          <Text className="text-sm text-textSecondary mt-1">
            Configure and start a new Ralph orchestration run
          </Text>
        </View>

        {/* Prompt File Input */}
        <View>
          <Text className="text-sm font-medium text-textPrimary mb-1">
            Prompt File <Text className="text-red-500">*</Text>
          </Text>
          <TextInput
            className={`bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary ${
              errors.promptFile ? 'border-2 border-red-500' : ''
            }`}
            placeholder="prompts/my-task/PROMPT.md"
            placeholderTextColor="#6b7280"
            value={promptFile}
            onChangeText={setPromptFile}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {errors.promptFile && (
            <Text className="text-xs text-red-500 mt-1">{errors.promptFile}</Text>
          )}
        </View>

        {/* Config File Input */}
        <View>
          <Text className="text-sm font-medium text-textPrimary mb-1">
            Config File <Text className="text-textSecondary">(optional)</Text>
          </Text>
          <TextInput
            className="bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary"
            placeholder="configs/my-config.json"
            placeholderTextColor="#6b7280"
            value={configFile}
            onChangeText={setConfigFile}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        {/* Max Iterations Input */}
        <View>
          <Text className="text-sm font-medium text-textPrimary mb-1">
            Max Iterations <Text className="text-textSecondary">(optional)</Text>
          </Text>
          <TextInput
            className={`bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary ${
              errors.maxIterations ? 'border-2 border-red-500' : ''
            }`}
            placeholder="50"
            placeholderTextColor="#6b7280"
            value={maxIterations}
            onChangeText={setMaxIterations}
            keyboardType="number-pad"
          />
          {errors.maxIterations && (
            <Text className="text-xs text-red-500 mt-1">{errors.maxIterations}</Text>
          )}
          <Text className="text-xs text-textSecondary mt-1">
            Leave empty for unlimited iterations
          </Text>
        </View>

        {/* Max Runtime Input */}
        <View>
          <Text className="text-sm font-medium text-textPrimary mb-1">
            Max Runtime (seconds) <Text className="text-textSecondary">(optional)</Text>
          </Text>
          <TextInput
            className={`bg-surfaceLight rounded-lg px-4 py-3 text-textPrimary ${
              errors.maxRuntime ? 'border-2 border-red-500' : ''
            }`}
            placeholder="3600"
            placeholderTextColor="#6b7280"
            value={maxRuntime}
            onChangeText={setMaxRuntime}
            keyboardType="number-pad"
          />
          {errors.maxRuntime && (
            <Text className="text-xs text-red-500 mt-1">{errors.maxRuntime}</Text>
          )}
          <Text className="text-xs text-textSecondary mt-1">
            Leave empty for unlimited runtime
          </Text>
        </View>

        {/* Action Buttons */}
        <View className="flex-row gap-3 mt-4">
          <Pressable
            className="flex-1 bg-surfaceLight rounded-lg py-4 active:opacity-80"
            onPress={handleCancel}
            disabled={isSubmitting}
          >
            <Text className="text-textSecondary font-semibold text-center">Cancel</Text>
          </Pressable>

          <Pressable
            className={`flex-1 bg-primary rounded-lg py-4 ${
              isSubmitting ? 'opacity-50' : 'active:opacity-80'
            }`}
            onPress={handleSubmit}
            disabled={isSubmitting}
          >
            <Text className="text-white font-semibold text-center">
              {isSubmitting ? 'Starting...' : 'Start Orchestration'}
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

export default NewOrchestrationForm;

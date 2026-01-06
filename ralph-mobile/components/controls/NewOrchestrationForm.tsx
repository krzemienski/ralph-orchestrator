/**
 * NewOrchestrationForm Component
 *
 * Form to start a new orchestration with:
 * - Prompt file path input
 * - Max iterations input
 * - Max runtime input (seconds)
 * - Start button with validation
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import type { StartOrchestratorRequest } from '../../lib/types';

// Theme colors
const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceLight: '#262626',
  border: '#333333',
  success: '#22c55e',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray700: '#374151',
};

interface NewOrchestrationFormProps {
  /** Callback when form is submitted */
  onSubmit: (request: StartOrchestratorRequest) => void;
  /** Whether the form is submitting */
  isSubmitting?: boolean;
  /** Whether haptic feedback is enabled */
  hapticEnabled?: boolean;
  /** Error message to display */
  errorMessage?: string;
}

/**
 * NewOrchestrationForm - Start new orchestration
 *
 * Form fields:
 * - Prompt file path (required)
 * - Config file path (optional)
 * - Max iterations (default: 50)
 * - Max runtime in seconds (default: 3600)
 */
export function NewOrchestrationForm({
  onSubmit,
  isSubmitting = false,
  hapticEnabled = true,
  errorMessage,
}: NewOrchestrationFormProps): React.ReactElement {
  // Form state
  const [promptFile, setPromptFile] = useState('');
  const [configFile, setConfigFile] = useState('');
  const [maxIterations, setMaxIterations] = useState('50');
  const [maxRuntime, setMaxRuntime] = useState('3600');
  const [validationError, setValidationError] = useState<string | null>(null);

  /**
   * Validate form inputs
   */
  const validateForm = useCallback((): boolean => {
    setValidationError(null);

    if (!promptFile.trim()) {
      setValidationError('Prompt file path is required');
      return false;
    }

    // Check for valid file extension
    if (!promptFile.endsWith('.md') && !promptFile.includes('/')) {
      setValidationError('Prompt file should be a .md file or path');
      return false;
    }

    const iterations = parseInt(maxIterations, 10);
    if (isNaN(iterations) || iterations < 1 || iterations > 1000) {
      setValidationError('Max iterations must be between 1 and 1000');
      return false;
    }

    const runtime = parseInt(maxRuntime, 10);
    if (isNaN(runtime) || runtime < 60 || runtime > 86400) {
      setValidationError('Max runtime must be between 60 and 86400 seconds');
      return false;
    }

    return true;
  }, [promptFile, maxIterations, maxRuntime]);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) {
      if (hapticEnabled) {
        try {
          await Haptics.notificationAsync(
            Haptics.NotificationFeedbackType.Error
          );
        } catch {
          // Haptics not available
        }
      }
      return;
    }

    if (hapticEnabled) {
      try {
        await Haptics.notificationAsync(
          Haptics.NotificationFeedbackType.Success
        );
      } catch {
        // Haptics not available
      }
    }

    const request: StartOrchestratorRequest = {
      prompt_file: promptFile.trim(),
      max_iterations: parseInt(maxIterations, 10),
      max_runtime_seconds: parseInt(maxRuntime, 10),
    };

    if (configFile.trim()) {
      request.config_file = configFile.trim();
    }

    onSubmit(request);
  }, [
    promptFile,
    configFile,
    maxIterations,
    maxRuntime,
    validateForm,
    onSubmit,
    hapticEnabled,
  ]);

  /**
   * Handle number input with validation
   */
  const handleNumberInput = useCallback(
    (setter: (value: string) => void) => (text: string) => {
      // Only allow digits
      const cleaned = text.replace(/[^0-9]/g, '');
      setter(cleaned);
    },
    []
  );

  const displayError = validationError || errorMessage;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.keyboardView}
    >
      <View style={styles.container}>
        <Text style={styles.title}>New Orchestration</Text>

        {/* Prompt File Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Prompt File *</Text>
          <TextInput
            style={styles.input}
            value={promptFile}
            onChangeText={setPromptFile}
            placeholder="prompts/my-prompt.md"
            placeholderTextColor={colors.gray500}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!isSubmitting}
            accessibilityLabel="Prompt file path"
          />
          <Text style={styles.hint}>Path to the prompt markdown file</Text>
        </View>

        {/* Config File Input (optional) */}
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Config File (optional)</Text>
          <TextInput
            style={styles.input}
            value={configFile}
            onChangeText={setConfigFile}
            placeholder="config/orchestrator.yaml"
            placeholderTextColor={colors.gray500}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!isSubmitting}
            accessibilityLabel="Config file path"
          />
        </View>

        {/* Numeric inputs row */}
        <View style={styles.row}>
          {/* Max Iterations */}
          <View style={[styles.inputGroup, styles.halfWidth]}>
            <Text style={styles.label}>Max Iterations</Text>
            <TextInput
              style={styles.input}
              value={maxIterations}
              onChangeText={handleNumberInput(setMaxIterations)}
              placeholder="50"
              placeholderTextColor={colors.gray500}
              keyboardType="number-pad"
              editable={!isSubmitting}
              accessibilityLabel="Maximum iterations"
            />
          </View>

          {/* Max Runtime */}
          <View style={[styles.inputGroup, styles.halfWidth]}>
            <Text style={styles.label}>Max Runtime (s)</Text>
            <TextInput
              style={styles.input}
              value={maxRuntime}
              onChangeText={handleNumberInput(setMaxRuntime)}
              placeholder="3600"
              placeholderTextColor={colors.gray500}
              keyboardType="number-pad"
              editable={!isSubmitting}
              accessibilityLabel="Maximum runtime in seconds"
            />
          </View>
        </View>

        {/* Error message */}
        {displayError && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{displayError}</Text>
          </View>
        )}

        {/* Submit button */}
        <Pressable
          style={({ pressed }) => [
            styles.submitButton,
            pressed && styles.buttonPressed,
            isSubmitting && styles.buttonDisabled,
          ]}
          onPress={handleSubmit}
          disabled={isSubmitting}
          accessibilityLabel="Start orchestration"
          accessibilityRole="button"
        >
          {isSubmitting ? (
            <ActivityIndicator size="small" color={colors.white} />
          ) : (
            <Text style={styles.submitButtonText}>Start Orchestration</Text>
          )}
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardView: {
    width: '100%',
  },
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 16,
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    color: colors.gray300,
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 6,
  },
  input: {
    backgroundColor: colors.surfaceLight,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    color: colors.white,
    fontSize: 15,
    borderWidth: 1,
    borderColor: colors.border,
  },
  hint: {
    color: colors.gray500,
    fontSize: 11,
    marginTop: 4,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  halfWidth: {
    flex: 1,
  },
  errorContainer: {
    backgroundColor: colors.error + '15',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.error + '30',
  },
  errorText: {
    color: colors.error,
    fontSize: 13,
    textAlign: 'center',
  },
  submitButton: {
    backgroundColor: colors.success,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  submitButtonText: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default NewOrchestrationForm;

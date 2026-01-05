/**
 * ErrorBoundary - Catches and displays errors gracefully
 *
 * Features:
 * - Catches React errors in child components
 * - Displays user-friendly error message
 * - Provides retry functionality
 * - Reports errors for debugging
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, Pressable } from 'react-native';
import * as Haptics from 'expo-haptics';

interface ErrorBoundaryProps {
  /** Child components to wrap */
  children: ReactNode;
  /** Optional fallback component */
  fallback?: ReactNode;
  /** Callback when error occurs */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary component - Class component required for error boundaries
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error for debugging
    console.error('ErrorBoundary caught error:', error);
    console.error('Error info:', errorInfo);

    // Notify parent if callback provided
    this.props.onError?.(error, errorInfo);
  }

  /** Handle retry button press */
  handleRetry = async (): Promise<void> => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <View
          className="flex-1 bg-background items-center justify-center p-6"
          accessibilityRole="alert"
          accessibilityLabel="An error occurred"
        >
          <View className="bg-red-500/20 rounded-full w-20 h-20 items-center justify-center mb-6">
            <Text className="text-4xl">⚠️</Text>
          </View>

          <Text
            className="text-xl font-semibold text-textPrimary text-center mb-2"
            accessibilityRole="header"
          >
            Something went wrong
          </Text>

          <Text className="text-sm text-textSecondary text-center mb-6">
            An unexpected error occurred. Please try again.
          </Text>

          {__DEV__ && this.state.error && (
            <View className="bg-surfaceLight rounded-lg p-3 mb-6 w-full max-w-xs">
              <Text className="text-xs text-red-400 font-mono">
                {this.state.error.message}
              </Text>
            </View>
          )}

          <Pressable
            className="bg-primary rounded-lg px-6 py-3 active:opacity-80"
            onPress={this.handleRetry}
            accessibilityRole="button"
            accessibilityLabel="Try again"
            accessibilityHint="Attempts to reload the component"
          >
            <Text className="text-white font-medium">Try Again</Text>
          </Pressable>
        </View>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

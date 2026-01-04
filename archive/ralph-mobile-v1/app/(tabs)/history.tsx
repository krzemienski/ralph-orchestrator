/**
 * @fileoverview History tab - shows past orchestration runs
 * Displays completed, failed, and cancelled orchestrations
 */

import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../../lib/theme';

/**
 * History screen component
 * Shows past orchestration runs and their results
 */
export default function HistoryScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>History</Text>
      <Text style={styles.subtitle}>Past orchestrations will appear here</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: colors.textMuted,
  },
});

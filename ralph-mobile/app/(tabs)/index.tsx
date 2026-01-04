/**
 * @fileoverview Dashboard tab - shows active orchestrators
 * Main entry point for the app, displays running orchestrations
 */

import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../../lib/theme';

/**
 * Dashboard screen component
 * Shows active orchestrators and quick actions
 */
export default function DashboardScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Dashboard</Text>
      <Text style={styles.subtitle}>Active orchestrators will appear here</Text>
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

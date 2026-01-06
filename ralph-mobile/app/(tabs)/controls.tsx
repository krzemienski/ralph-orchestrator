import { View, Text, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  success: '#22c55e',
  warning: '#eab308',
  error: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  black: '#000000',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

export default function ControlsScreen() {
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.content}>
        <View style={styles.headerSection}>
          <Text style={styles.title}>Controls</Text>
          <Text style={styles.subtitle}>
            Start, stop, pause, and resume orchestrations
          </Text>
        </View>

        {/* Control buttons */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Quick Actions</Text>

          <View style={styles.buttonRow}>
            <Pressable style={[styles.button, { backgroundColor: colors.success }]}>
              <Text style={styles.buttonText}>Start</Text>
            </Pressable>
            <Pressable style={[styles.button, { backgroundColor: colors.warning }]}>
              <Text style={[styles.buttonText, { color: colors.black }]}>Pause</Text>
            </Pressable>
          </View>

          <View style={styles.buttonRow}>
            <Pressable style={[styles.button, { backgroundColor: colors.info }]}>
              <Text style={styles.buttonText}>Resume</Text>
            </Pressable>
            <Pressable style={[styles.button, { backgroundColor: colors.error }]}>
              <Text style={styles.buttonText}>Stop</Text>
            </Pressable>
          </View>
        </View>

        {/* Current status */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Current Status</Text>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>No active orchestration</Text>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  headerSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.white,
    marginBottom: 8,
  },
  subtitle: {
    color: colors.gray400,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTitle: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 16,
    marginBottom: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  button: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 14,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.gray500,
    marginRight: 8,
  },
  statusText: {
    color: colors.gray400,
    fontSize: 14,
  },
});

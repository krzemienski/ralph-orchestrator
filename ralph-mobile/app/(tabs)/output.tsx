import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  border: '#333333',
  info: '#3b82f6',
  success: '#22c55e',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

export default function OutputScreen() {
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.contentContainer}>
        <View style={styles.headerSection}>
          <Text style={styles.title}>Output</Text>
          <Text style={styles.subtitle}>
            Real-time log streaming will appear here
          </Text>
        </View>

        {/* Sample log entries */}
        <View style={styles.logEntry}>
          <View style={styles.logContent}>
            <View style={[styles.logBadge, { backgroundColor: colors.info }]}>
              <Text style={styles.logBadgeText}>INFO</Text>
            </View>
            <View style={styles.logText}>
              <Text style={styles.logMessage}>
                Starting orchestration loop...
              </Text>
              <Text style={styles.logTimestamp}>12:34:56.789</Text>
            </View>
          </View>
        </View>

        <View style={styles.logEntry}>
          <View style={styles.logContent}>
            <View style={[styles.logBadge, { backgroundColor: colors.success }]}>
              <Text style={styles.logBadgeText}>DEBUG</Text>
            </View>
            <View style={styles.logText}>
              <Text style={styles.logMessage}>
                Processing iteration 1 of 10
              </Text>
              <Text style={styles.logTimestamp}>12:34:57.123</Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  headerSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 80,
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
  logEntry: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  logContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  logBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8,
  },
  logBadgeText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '500',
  },
  logText: {
    flex: 1,
  },
  logMessage: {
    color: colors.gray300,
    fontSize: 14,
  },
  logTimestamp: {
    color: colors.gray500,
    fontSize: 12,
    marginTop: 4,
  },
});

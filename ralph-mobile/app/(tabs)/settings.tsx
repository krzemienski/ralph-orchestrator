import { View, Text, TextInput, Switch, Pressable, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useState } from 'react';

const colors = {
  background: '#0a0a0a',
  surface: '#1a1a1a',
  surfaceSecondary: '#262626',
  border: '#333333',
  info: '#3b82f6',
  white: '#ffffff',
  gray300: '#d1d5db',
  gray400: '#9ca3af',
  gray500: '#6b7280',
};

export default function SettingsScreen() {
  const [serverUrl, setServerUrl] = useState('http://localhost:8420');
  const [hapticEnabled, setHapticEnabled] = useState(true);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.content}>
        {/* Server Connection */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Server Connection</Text>

          <Text style={styles.label}>API URL</Text>
          <TextInput
            value={serverUrl}
            onChangeText={setServerUrl}
            style={styles.input}
            placeholderTextColor={colors.gray500}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Pressable style={styles.primaryButton}>
            <Text style={styles.buttonText}>Test Connection</Text>
          </Pressable>
        </View>

        {/* Preferences */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Preferences</Text>

          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Haptic Feedback</Text>
            <Switch
              value={hapticEnabled}
              onValueChange={setHapticEnabled}
              trackColor={{ false: colors.border, true: colors.info }}
              thumbColor={colors.white}
            />
          </View>
        </View>

        {/* About */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>About</Text>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>App Version</Text>
            <Text style={styles.infoValue}>1.0.0</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Build</Text>
            <Text style={styles.infoValue}>Phase 0</Text>
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
  label: {
    color: colors.gray400,
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: colors.surfaceSecondary,
    color: colors.white,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
    fontSize: 14,
  },
  primaryButton: {
    backgroundColor: colors.info,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: colors.white,
    fontWeight: '600',
    fontSize: 14,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  settingLabel: {
    color: colors.gray300,
    fontSize: 14,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  infoLabel: {
    color: colors.gray400,
    fontSize: 14,
  },
  infoValue: {
    color: colors.white,
    fontSize: 14,
  },
});

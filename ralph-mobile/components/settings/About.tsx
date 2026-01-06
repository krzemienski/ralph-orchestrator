/**
 * About Component
 *
 * App information display with:
 * - App version
 * - Build info
 * - Links to documentation/support
 * - Credits/acknowledgments
 */

import React from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Linking,
} from 'react-native';
import Constants from 'expo-constants';

// Theme colors
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

interface AboutProps {
  /** Optional custom version override */
  version?: string;
}

/**
 * Info row with label and value
 */
function InfoRow({
  label,
  value,
}: {
  label: string;
  value: string;
}): React.ReactElement {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

/**
 * Link row with label and URL
 */
function LinkRow({
  label,
  url,
  description,
}: {
  label: string;
  url: string;
  description?: string;
}): React.ReactElement {
  const handlePress = async () => {
    const supported = await Linking.canOpenURL(url);
    if (supported) {
      await Linking.openURL(url);
    }
  };

  return (
    <Pressable
      style={({ pressed }) => [
        styles.linkRow,
        pressed && styles.linkRowPressed,
      ]}
      onPress={handlePress}
      accessibilityLabel={`Open ${label}`}
      accessibilityHint={`Opens ${url} in browser`}
      accessibilityRole="link"
    >
      <View style={styles.linkContent}>
        <Text style={styles.linkLabel}>{label}</Text>
        {description && (
          <Text style={styles.linkDescription}>{description}</Text>
        )}
      </View>
      <Text style={styles.linkArrow}>→</Text>
    </Pressable>
  );
}

/**
 * About - App information component
 *
 * Displays version info, build details, and links to
 * documentation and support resources.
 */
export function About({ version }: AboutProps): React.ReactElement {
  // Get version from Expo Constants or props
  const appVersion = version ?? Constants.expoConfig?.version ?? '1.0.0';
  const sdkVersion = Constants.expoConfig?.sdkVersion ?? 'Unknown';
  const buildDate = new Date().toISOString().split('T')[0]; // Simplified for now

  return (
    <View style={styles.container}>
      <Text style={styles.title}>About</Text>

      {/* App Identity */}
      <View style={styles.appHeader}>
        <View style={styles.appIcon}>
          <Text style={styles.appIconText}>R</Text>
        </View>
        <View style={styles.appInfo}>
          <Text style={styles.appName}>Ralph Mobile</Text>
          <Text style={styles.appTagline}>
            Orchestrator Control Center
          </Text>
        </View>
      </View>

      {/* Version Info */}
      <View style={styles.infoSection}>
        <InfoRow label="Version" value={appVersion} />
        <InfoRow label="Expo SDK" value={sdkVersion} />
        <InfoRow label="Build Date" value={buildDate} />
      </View>

      {/* Links Section */}
      <View style={styles.linksSection}>
        <Text style={styles.sectionTitle}>Resources</Text>
        <LinkRow
          label="Documentation"
          url="https://github.com/nick/ralph-orchestrator"
          description="View API docs and guides"
        />
        <LinkRow
          label="Report Issue"
          url="https://github.com/nick/ralph-orchestrator/issues"
          description="Report bugs or request features"
        />
        <LinkRow
          label="View Source"
          url="https://github.com/nick/ralph-orchestrator/tree/main/ralph-mobile"
          description="Browse the source code"
        />
      </View>

      {/* Credits */}
      <View style={styles.creditsSection}>
        <Text style={styles.sectionTitle}>Credits</Text>
        <Text style={styles.creditsText}>
          Built with React Native, Expo, and TanStack Query.
        </Text>
        <Text style={styles.creditsText}>
          Designed for the Ralph Orchestrator ecosystem.
        </Text>
      </View>

      {/* Copyright */}
      <Text style={styles.copyright}>
        © {new Date().getFullYear()} Ralph Orchestrator Project
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
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
  appHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  appIcon: {
    width: 56,
    height: 56,
    borderRadius: 12,
    backgroundColor: colors.info,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  appIconText: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '700',
  },
  appInfo: {
    flex: 1,
  },
  appName: {
    color: colors.white,
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 2,
  },
  appTagline: {
    color: colors.gray400,
    fontSize: 14,
  },
  infoSection: {
    marginBottom: 20,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  infoLabel: {
    color: colors.gray400,
    fontSize: 14,
  },
  infoValue: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '500',
  },
  linksSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    color: colors.gray500,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  linkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 12,
    backgroundColor: colors.surfaceSecondary,
    borderRadius: 8,
    marginBottom: 8,
  },
  linkRowPressed: {
    opacity: 0.7,
  },
  linkContent: {
    flex: 1,
  },
  linkLabel: {
    color: colors.white,
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  linkDescription: {
    color: colors.gray500,
    fontSize: 12,
  },
  linkArrow: {
    color: colors.info,
    fontSize: 16,
    marginLeft: 12,
  },
  creditsSection: {
    marginBottom: 16,
  },
  creditsText: {
    color: colors.gray500,
    fontSize: 13,
    lineHeight: 20,
  },
  copyright: {
    color: colors.gray500,
    fontSize: 12,
    textAlign: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});

export default About;

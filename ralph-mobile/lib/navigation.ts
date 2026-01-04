/**
 * @fileoverview Tab navigation configuration for Ralph Mobile
 * Defines the tab structure for Dashboard, History, and Settings
 */

/**
 * Configuration for a navigation tab
 */
export interface TabConfig {
  /** Route name (used by expo-router) */
  name: string;
  /** Display title for the tab */
  title: string;
  /** Icon name (Ionicons) */
  icon: string;
}

/**
 * Tab configuration array defining the navigation structure
 */
export const tabs: TabConfig[] = [
  {
    name: 'index',
    title: 'Dashboard',
    icon: 'home',
  },
  {
    name: 'history',
    title: 'History',
    icon: 'time',
  },
  {
    name: 'settings',
    title: 'Settings',
    icon: 'settings',
  },
];

/**
 * Get icon name for a tab by route name
 * @param tabName - The route name of the tab
 * @returns Icon name (Ionicons)
 */
export function getTabIcon(tabName: string): string {
  const tab = tabs.find((t) => t.name === tabName);
  return tab?.icon ?? 'help';
}

/**
 * Get display title for a tab by route name
 * @param tabName - The route name of the tab
 * @returns Display title
 */
export function getTabTitle(tabName: string): string {
  const tab = tabs.find((t) => t.name === tabName);
  if (tab) {
    return tab.title;
  }
  // Capitalize first letter for unknown tabs
  return tabName.charAt(0).toUpperCase() + tabName.slice(1);
}

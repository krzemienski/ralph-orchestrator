/**
 * @fileoverview TDD tests for tab navigation structure (Plan 04-03)
 * Tests Dashboard, History, and Settings tab navigation
 */

import { tabs, TabConfig, getTabIcon, getTabTitle } from '../lib/navigation';

describe('Tab Navigation Configuration', () => {
  describe('tabs array', () => {
    it('should have exactly 3 tabs', () => {
      expect(tabs).toHaveLength(3);
    });

    it('should have Dashboard as first tab', () => {
      expect(tabs[0].name).toBe('index');
      expect(tabs[0].title).toBe('Dashboard');
    });

    it('should have History as second tab', () => {
      expect(tabs[1].name).toBe('history');
      expect(tabs[1].title).toBe('History');
    });

    it('should have Settings as third tab', () => {
      expect(tabs[2].name).toBe('settings');
      expect(tabs[2].title).toBe('Settings');
    });

    it('should have icons for all tabs', () => {
      tabs.forEach((tab: TabConfig) => {
        expect(tab.icon).toBeDefined();
        expect(typeof tab.icon).toBe('string');
        expect(tab.icon.length).toBeGreaterThan(0);
      });
    });
  });

  describe('getTabIcon', () => {
    it('should return correct icon for Dashboard tab', () => {
      expect(getTabIcon('index')).toBe('home');
    });

    it('should return correct icon for History tab', () => {
      expect(getTabIcon('history')).toBe('time');
    });

    it('should return correct icon for Settings tab', () => {
      expect(getTabIcon('settings')).toBe('settings');
    });

    it('should return default icon for unknown tab', () => {
      expect(getTabIcon('unknown')).toBe('help');
    });
  });

  describe('getTabTitle', () => {
    it('should return correct title for Dashboard tab', () => {
      expect(getTabTitle('index')).toBe('Dashboard');
    });

    it('should return correct title for History tab', () => {
      expect(getTabTitle('history')).toBe('History');
    });

    it('should return correct title for Settings tab', () => {
      expect(getTabTitle('settings')).toBe('Settings');
    });

    it('should return capitalized name for unknown tab', () => {
      expect(getTabTitle('unknown')).toBe('Unknown');
    });
  });

  describe('TabConfig type', () => {
    it('should have required properties for each tab', () => {
      tabs.forEach((tab: TabConfig) => {
        expect(tab).toHaveProperty('name');
        expect(tab).toHaveProperty('title');
        expect(tab).toHaveProperty('icon');
        expect(typeof tab.name).toBe('string');
        expect(typeof tab.title).toBe('string');
        expect(typeof tab.icon).toBe('string');
      });
    });
  });
});

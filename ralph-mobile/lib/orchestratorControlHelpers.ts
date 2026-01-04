/**
 * @fileoverview Helper functions for orchestrator control actions
 * Plan 06-02: Stop/Pause/Resume Controls
 *
 * Provides validation and UI helpers for control actions
 */

import { OrchestratorStatus } from './types';

/**
 * Valid control actions for orchestrators
 */
export type ControlAction = 'stop' | 'pause' | 'resume';

/**
 * Validate that a string is a valid control action
 */
export function validateControlAction(action: string): action is ControlAction {
  return ['stop', 'pause', 'resume'].includes(action);
}

/**
 * Get user-friendly confirmation message for an action
 */
export function getConfirmationMessage(action: ControlAction, instanceId: string): string {
  switch (action) {
    case 'stop':
      return `Are you sure you want to stop orchestrator ${instanceId}? This action cannot be undone.`;
    case 'pause':
      return `Pause orchestrator ${instanceId}? You can resume it later.`;
    case 'resume':
      return `Resume orchestrator ${instanceId}?`;
    default:
      return `Perform action on orchestrator ${instanceId}?`;
  }
}

/**
 * Allowed state transitions for control actions
 */
const ALLOWED_TRANSITIONS: Record<ControlAction, OrchestratorStatus[]> = {
  stop: ['running', 'paused'],
  pause: ['running'],
  resume: ['paused'],
};

/**
 * Check if an action is allowed for the current orchestrator status
 */
export function isActionAllowed(action: ControlAction, currentStatus: OrchestratorStatus): boolean {
  const allowedStatuses = ALLOWED_TRANSITIONS[action];
  return allowedStatuses?.includes(currentStatus) ?? false;
}

/**
 * Get the expected status after performing an action
 */
export function getNextStatus(action: ControlAction): string | null {
  switch (action) {
    case 'stop':
      return 'stopped';
    case 'pause':
      return 'paused';
    case 'resume':
      return 'running';
    default:
      return null;
  }
}

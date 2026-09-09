/**
 * Centralized mapping between risk levels, their visual class, color token,
 * label copy, and recommended security action. Every component should read
 * from here instead of re-implementing this mapping locally.
 */

const RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const POLICY = {
  LOW: {
    className: 'low',
    color: 'var(--success)',
    label: 'Low Risk',
    action: 'MONITOR',
    actionLabel: 'Continue Monitoring',
    voiceHeadline: 'Voice appears authentic',
    voiceBody: 'No significant threat indicators detected.',
  },
  MEDIUM: {
    className: 'medium',
    color: 'var(--warning)',
    label: 'Medium Risk',
    action: 'WARNING',
    actionLabel: 'Acknowledge Warning',
    voiceHeadline: 'Suspicious voice activity',
    voiceBody: 'Unusual voice characteristics detected.',
  },
  HIGH: {
    className: 'high',
    color: 'var(--high)',
    label: 'High Risk',
    action: 'VERIFY',
    actionLabel: 'Start Verification',
    voiceHeadline: 'High risk voice detected',
    voiceBody: 'Synthetic voice indicators require verification.',
  },
  CRITICAL: {
    className: 'critical',
    color: 'var(--critical)',
    label: 'Critical Risk',
    action: 'BLOCK',
    actionLabel: 'Session Blocked',
    voiceHeadline: 'Critical synthetic voice threat',
    voiceBody: 'Immediate defensive action is recommended.',
  },
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getRiskClass(riskLevel) {
  return POLICY[riskLevel]?.className ?? 'low'
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getRiskColor(riskLevel) {
  return POLICY[riskLevel]?.color ?? POLICY.LOW.color
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getRiskLabel(riskLevel) {
  return POLICY[riskLevel]?.label ?? 'Unknown'
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getRecommendedAction(riskLevel) {
  return POLICY[riskLevel]?.action ?? 'MONITOR'
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getActionLabel(riskLevel) {
  return POLICY[riskLevel]?.actionLabel ?? 'Continue Monitoring'
}

/**
 * @param {import('../types/detection.js').RiskLevel} riskLevel
 */
export function getVoiceCopy(riskLevel) {
  const entry = POLICY[riskLevel] ?? POLICY.LOW
  return { headline: entry.voiceHeadline, body: entry.voiceBody }
}

export function getRiskLevels() {
  return RISK_LEVELS
}

export default POLICY

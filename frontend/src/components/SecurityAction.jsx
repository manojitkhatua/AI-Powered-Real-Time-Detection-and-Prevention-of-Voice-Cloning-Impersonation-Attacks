import { Eye, TriangleAlert, UserCheck, Ban } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

const ACTION_CONTENT = {
  LOW: { icon: Eye, label: 'Monitor', button: 'Continue Monitoring' },
  MEDIUM: { icon: TriangleAlert, label: 'Warning', button: 'Acknowledge Warning' },
  HIGH: { icon: UserCheck, label: 'Verify identity', button: 'Start Verification' },
  CRITICAL: { icon: Ban, label: 'Block session', button: 'Session Blocked' },
}

function SecurityAction({ detection, onStartVerification }) {
  if (!detection) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Recommended security action</h2>
        </div>
        <p className="empty-state">Waiting for detection stream…</p>
      </section>
    )
  }

  const { risk_level } = detection
  const riskClass = getRiskClass(risk_level)
  const entry = ACTION_CONTENT[risk_level] ?? ACTION_CONTENT.LOW
  const Icon = entry.icon
  const isHigh = risk_level === 'HIGH'
  const isCritical = risk_level === 'CRITICAL'

  return (
    <section className="panel" aria-labelledby="security-action-title">
      <div className="panel-header">
        <h2 className="panel-title" id="security-action-title">Recommended security action</h2>
      </div>

      <div className={`action-callout action-callout-${riskClass}`}>
        <Icon size={20} strokeWidth={2} />
        <span className="action-callout-label">{entry.label}</span>
      </div>

      <button
        type="button"
        className={`action-button ${isCritical ? 'action-button-disabled' : ''} ${isHigh ? 'action-button-primary' : ''}`}
        disabled={isCritical}
        onClick={isHigh ? onStartVerification : undefined}
      >
        {entry.button}
      </button>
    </section>
  )
}

export default SecurityAction

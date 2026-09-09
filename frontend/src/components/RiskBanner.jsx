import { ShieldCheck, ShieldAlert, ShieldQuestion, ShieldX } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

const CONTENT = {
  LOW: {
    icon: ShieldCheck,
    title: 'Voice appears authentic',
    body: 'No significant threat indicators detected.',
    action: 'MONITOR',
  },
  MEDIUM: {
    icon: ShieldQuestion,
    title: 'Suspicious voice activity',
    body: 'Unusual voice characteristics detected.',
    action: 'WARNING',
  },
  HIGH: {
    icon: ShieldAlert,
    title: 'High risk voice detected',
    body: 'Synthetic voice indicators require verification.',
    action: 'VERIFY',
  },
  CRITICAL: {
    icon: ShieldX,
    title: 'Critical synthetic voice threat',
    body: 'Immediate defensive action is recommended.',
    action: 'BLOCK',
  },
}

function RiskBanner({ riskLevel = 'LOW' }) {
  const entry = CONTENT[riskLevel] ?? CONTENT.LOW
  const Icon = entry.icon
  const riskClass = getRiskClass(riskLevel)

  return (
    <div className={`risk-banner risk-banner-${riskClass}`} role="alert">
      <div className="risk-banner-icon">
        <Icon size={22} strokeWidth={2} />
      </div>
      <div className="risk-banner-copy">
        <span className="risk-banner-title">{entry.title}</span>
        <span className="risk-banner-body">{entry.body}</span>
      </div>
      <div className="risk-banner-action">
        <span className="risk-banner-action-label">Action</span>
        <span className="risk-banner-action-value">{entry.action}</span>
      </div>
    </div>
  )
}

export default RiskBanner

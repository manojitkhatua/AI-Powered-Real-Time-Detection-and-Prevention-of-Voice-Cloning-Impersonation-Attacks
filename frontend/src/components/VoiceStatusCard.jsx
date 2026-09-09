import { AudioLines } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

const STATUS_COPY = {
  REAL: 'Authentic voice',
  SUSPICIOUS: 'Suspicious voice',
  FAKE: 'Synthetic voice',
}

function VoiceStatusCard({ detection }) {
  if (!detection) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Voice authenticity</h2>
        </div>
        <p className="empty-state">Waiting for detection stream…</p>
      </section>
    )
  }

  const { voice_status, spoof_probability, risk_level, anomaly_detected } = detection
  const riskClass = getRiskClass(risk_level)
  const spoofPercent = Math.round(spoof_probability * 100)

  return (
    <section className="panel" aria-labelledby="voice-status-title">
      <div className="panel-header">
        <h2 className="panel-title" id="voice-status-title">
          <AudioLines size={15} strokeWidth={2.2} />
          Voice authenticity
        </h2>
        <span className={`badge badge-${riskClass.toLowerCase()}`}>
          <span className="badge-dot" aria-hidden="true" />
          {STATUS_COPY[voice_status] ?? voice_status}
        </span>
      </div>

      <div className="metric-block">
        <div className="metric-block-header">
          <span className="metric-label">AI / spoof probability</span>
          <span className={`metric-value metric-value-${riskClass}`}>{spoofPercent}%</span>
        </div>
        <div className="progress-track" role="progressbar" aria-valuenow={spoofPercent} aria-valuemin={0} aria-valuemax={100} aria-label="Spoof probability">
          <div
            className={`progress-fill progress-fill-${riskClass}`}
            style={{ width: `${spoofPercent}%` }}
          />
        </div>
      </div>

      <div className="mini-stat-row">
        <div className="mini-stat">
          <span className="mini-stat-label">Anomaly status</span>
          <span className={`mini-stat-value ${anomaly_detected ? 'text-warn' : 'text-ok'}`}>
            {anomaly_detected ? 'Detected' : 'None'}
          </span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Detection basis</span>
          <span className="mini-stat-value">MFCC + MLP</span>
        </div>
      </div>
    </section>
  )
}

export default VoiceStatusCard

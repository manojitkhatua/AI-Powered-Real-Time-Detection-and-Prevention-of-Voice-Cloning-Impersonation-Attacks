import { Gauge } from 'lucide-react'
import { getRiskClass, getRiskColor, getRiskLabel } from '../services/riskPolicy.js'

const RADIUS = 54
const CIRCUMFERENCE = Math.PI * RADIUS // semicircle

function RiskScoreCard({ detection }) {
  if (!detection) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Risk score</h2>
        </div>
        <p className="empty-state">Waiting for detection stream…</p>
      </section>
    )
  }

  const { risk_score, risk_level, processing_latency, audio_window } = detection
  const riskClass = getRiskClass(risk_level)
  const color = getRiskColor(risk_level)
  const offset = CIRCUMFERENCE - (risk_score / 100) * CIRCUMFERENCE

  return (
    <section className="panel" aria-labelledby="risk-score-title">
      <div className="panel-header">
        <h2 className="panel-title" id="risk-score-title">
          <Gauge size={15} strokeWidth={2.2} />
          Risk score
        </h2>
        <span className={`badge badge-${riskClass}`}>
          <span className="badge-dot" aria-hidden="true" />
          {getRiskLabel(risk_level)}
        </span>
      </div>

      <div className="gauge-wrap">
        <svg viewBox="0 0 140 80" className="gauge-svg" role="img" aria-label={`Risk score ${risk_score} out of 100, ${risk_level}`}>
          <path
            d="M 10 74 A 54 54 0 0 1 130 74"
            fill="none"
            stroke="var(--border-strong)"
            strokeWidth="10"
            strokeLinecap="round"
          />
          <path
            d="M 10 74 A 54 54 0 0 1 130 74"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            className="gauge-progress"
          />
        </svg>
        <div className="gauge-readout">
          <span className="gauge-score">{risk_score}</span>
          <span className="gauge-max">/ 100</span>
        </div>
      </div>

      <div className="mini-stat-row">
        <div className="mini-stat">
          <span className="mini-stat-label">Processing latency</span>
          <span className="mini-stat-value">{processing_latency} ms</span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Audio window</span>
          <span className="mini-stat-value">{audio_window}s</span>
        </div>
      </div>
    </section>
  )
}

export default RiskScoreCard

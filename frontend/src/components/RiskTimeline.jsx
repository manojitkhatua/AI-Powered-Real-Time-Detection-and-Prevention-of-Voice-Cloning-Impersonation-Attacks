import { TrendingUp } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

function RiskTimeline({ detectionHistory = [] }) {
  if (detectionHistory.length === 0) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Risk timeline</h2>
        </div>
        <p className="empty-state">No detection history yet.</p>
      </section>
    )
  }

  return (
    <section className="panel" aria-labelledby="risk-timeline-title">
      <div className="panel-header">
        <h2 className="panel-title" id="risk-timeline-title">
          <TrendingUp size={15} strokeWidth={2.2} />
          Risk timeline
        </h2>
        <span className="panel-subtitle">{detectionHistory.length} windows analyzed</span>
      </div>

      <div className="timeline">
        <div className="timeline-track" aria-hidden="true" />
        {detectionHistory.map((event, i) => {
          const riskClass = getRiskClass(event.risk_level)
          const isLatest = i === detectionHistory.length - 1
          const windowLabel = event.window_index != null ? `W${Number(event.window_index) + 1}` : 'Final'
          return (
            <div className="timeline-point" key={`${event.audio_window ?? windowLabel}-${i}`}>
              <span
                className={`timeline-dot timeline-dot-${riskClass} ${isLatest ? 'timeline-dot-latest' : ''}`}
                aria-hidden="true"
              />
              <span className="timeline-window">{windowLabel}</span>
              <span className={`timeline-score timeline-score-${riskClass}`}>{event.risk_score}</span>
              <span className="timeline-level">{event.risk_level}</span>
            </div>
          )
        })}
      </div>
    </section>
  )
}

export default RiskTimeline

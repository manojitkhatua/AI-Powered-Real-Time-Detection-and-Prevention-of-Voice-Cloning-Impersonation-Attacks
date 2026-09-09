import { Activity } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

function TemporalDetectionAnalysis({ detectionHistory = [] }) {
  if (detectionHistory.length === 0) {
    return (
      <section className="panel" aria-labelledby="temporal-analysis-title">
        <div className="panel-header">
          <h2 className="panel-title" id="temporal-analysis-title">
            <Activity size={15} strokeWidth={2.2} />
            Temporal detection analysis
          </h2>
        </div>
        <p className="empty-state">Waiting for detection stream…</p>
      </section>
    )
  }

  // Live mode can produce hundreds of windows. Showing the latest 60 keeps the
  // visualization readable while every event remains available in Detection Events.
  const visibleHistory = detectionHistory.slice(-60)
  const latest = detectionHistory[detectionHistory.length - 1]
  const peak = detectionHistory.reduce((max, event) => Math.max(max, Number(event.spoof_probability) || 0), 0)
  const currentPercent = Math.round((Number(latest.spoof_probability) || 0) * 100)

  return (
    <section className="panel" aria-labelledby="temporal-analysis-title">
      <div className="panel-header">
        <div>
          <h2 className="panel-title" id="temporal-analysis-title">
            <Activity size={15} strokeWidth={2.2} />
            Temporal detection analysis
          </h2>
          <span className="panel-subtitle">Model output across analyzed windows</span>
        </div>
        <span className={`badge badge-${getRiskClass(latest.risk_level)}`}>
          <span className="badge-dot" aria-hidden="true" />
          {latest.risk_level}
        </span>
      </div>

      <div className="temporal-chart" role="img" aria-label={`Spoof probability over ${detectionHistory.length} analyzed windows`}>
        <div className="temporal-chart-grid" aria-hidden="true">
          <span>100%</span>
          <span>50%</span>
          <span>0%</span>
        </div>
        <div className="temporal-bars">
          {visibleHistory.map((event, index) => {
            const probability = Math.max(0, Math.min(1, Number(event.spoof_probability) || 0))
            const riskClass = getRiskClass(event.risk_level)
            return (
              <span
                key={`${event.audio_window}-${index}`}
                className={`temporal-bar temporal-bar-${riskClass}`}
                style={{ height: `${Math.max(3, probability * 100)}%` }}
                title={`Window ${event.audio_window}: ${Math.round(probability * 100)}% spoof probability`}
              />
            )
          })}
        </div>
      </div>

      <div className="temporal-axis">
        <span>Earlier</span>
        <span>Latest window</span>
      </div>

      <div className="mini-stat-row mini-stat-row-three">
        <div className="mini-stat">
          <span className="mini-stat-label">Current probability</span>
          <span className="mini-stat-value">{currentPercent}%</span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Peak probability</span>
          <span className="mini-stat-value">{Math.round(peak * 100)}%</span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Windows analyzed</span>
          <span className="mini-stat-value">{detectionHistory.length}</span>
        </div>
      </div>

      <p className="panel-footnote">
        Each bar is a model output from an analyzed window; live sessions update this view continuously.
      </p>
    </section>
  )
}

export default TemporalDetectionAnalysis

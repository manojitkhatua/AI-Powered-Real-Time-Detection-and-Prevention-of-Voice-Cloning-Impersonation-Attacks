import { useEffect, useRef } from 'react'
import { ClipboardCheck, X } from 'lucide-react'
import { getRiskClass, getRiskLabel, getActionLabel } from '../services/riskPolicy.js'

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, '0')
  return `${minutes}m ${seconds}s`
}

function SessionSummaryModal({ summary, onClose }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (!summary) return
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    dialogRef.current?.focus()
    return () => document.removeEventListener('keydown', handleKey)
  }, [summary, onClose])

  if (!summary) return null

  const riskClass = getRiskClass(summary.finalRiskLevel)

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="session-summary-title"
        ref={dialogRef}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="session-summary-title">Live session summary</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        <div className={`action-callout action-callout-${riskClass}`}>
          <ClipboardCheck size={20} strokeWidth={2} />
          <span className="action-callout-label">Final verdict: {getRiskLabel(summary.finalRiskLevel)}</span>
        </div>

        <div className="blocked-metrics summary-metrics">
          <div className="blocked-metric">
            <span className="blocked-metric-value">{summary.finalRiskScore}/100</span>
            <span className="blocked-metric-label">Risk score</span>
          </div>
          <div className="blocked-metric">
            <span className="blocked-metric-value">{Math.round(summary.finalSpoofProbability * 100)}%</span>
            <span className="blocked-metric-label">Spoof probability</span>
          </div>
          <div className="blocked-metric">
            <span className="blocked-metric-value">{formatDuration(summary.durationSeconds)}</span>
            <span className="blocked-metric-label">Session duration</span>
          </div>
        </div>

        <div className="summary-detail-row">
          <span className="mini-stat-label">Windows analyzed</span>
          <span className="mini-stat-value">{summary.eventCount}</span>
        </div>
        <div className="summary-detail-row">
          <span className="mini-stat-label">Recommended action</span>
          <span className="mini-stat-value">{getActionLabel(summary.finalRiskLevel)}</span>
        </div>

        {summary.notableEvents.length > 0 && (
          <div className="blocked-details summary-notable">
            <span className="blocked-details-heading">Notable events during this session</span>
            <ol className="blocked-steps">
              {summary.notableEvents.map((event, i) => (
                <li key={`${event.audio_window}-${i}`}>
                  {event.audio_window}s window — {event.risk_level} ({event.risk_score}/100): {event.message}
                </li>
              ))}
            </ol>
          </div>
        )}

        <div className="modal-actions">
          <button type="button" className="btn-primary" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  )
}

export default SessionSummaryModal

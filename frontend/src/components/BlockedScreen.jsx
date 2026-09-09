import { useState } from 'react'
import { ShieldOff, X } from 'lucide-react'

const RESPONSE_STEPS = [
  'Terminate the session',
  'Preserve call metadata',
  'Notify the purported caller',
  'Re-establish contact using a verified number',
]

function BlockedScreen({ detection, onClose }) {
  const [showDetails, setShowDetails] = useState(false)

  if (!detection) return null

  const { risk_score, spoof_probability, processing_latency, session_id } = detection

  return (
    <div className="modal-overlay blocked-overlay" role="presentation">
      <div className="modal blocked-modal" role="dialog" aria-modal="true" aria-labelledby="blocked-title">
        <div className="blocked-icon">
          <ShieldOff size={28} strokeWidth={2} />
        </div>

        <h2 id="blocked-title" className="blocked-title">Call blocked</h2>
        <p className="blocked-subtitle">Critical synthetic voice threat detected.</p>

        <div className="blocked-metrics">
          <div className="blocked-metric">
            <span className="blocked-metric-value">{risk_score}/100</span>
            <span className="blocked-metric-label">Risk score</span>
          </div>
          <div className="blocked-metric">
            <span className="blocked-metric-value">{Math.round(spoof_probability * 100)}%</span>
            <span className="blocked-metric-label">Spoof probability</span>
          </div>
          <div className="blocked-metric">
            <span className="blocked-metric-value">{processing_latency}ms</span>
            <span className="blocked-metric-label">Processing</span>
          </div>
        </div>

        {showDetails && (
          <div className="blocked-details">
            <span className="blocked-details-heading">Recommended response</span>
            <ol className="blocked-steps">
              {RESPONSE_STEPS.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <span className="blocked-details-heading">Session</span>
            <p className="blocked-session-id">{session_id}</p>
          </div>
        )}

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            <X size={15} strokeWidth={2} />
            Close
          </button>
          <button type="button" className="btn-danger" onClick={() => setShowDetails((v) => !v)}>
            {showDetails ? 'Hide Incident Details' : 'View Incident Details'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default BlockedScreen

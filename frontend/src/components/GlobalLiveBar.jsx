import { Radio, Square } from 'lucide-react'
import { useLiveDetection } from '../context/LiveDetectionContext.jsx'
import { getRiskClass, getRiskLabel } from '../services/riskPolicy.js'

function formatDuration(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, '0')
  return `${minutes}:${seconds}`
}

function GlobalLiveBar() {
  const { isLive, status, currentDetection, elapsedSeconds, stopLive } = useLiveDetection()

  if (!isLive) return null

  const riskLevel = currentDetection?.risk_level ?? 'LOW'
  const riskClass = getRiskClass(riskLevel)

  return (
    <div className={`global-live-bar global-live-bar-${riskClass}`} role="status">
      <div className="global-live-bar-inner">
        <div className="global-live-bar-left">
          <span className="global-live-dot" aria-hidden="true" />
          <Radio size={14} strokeWidth={2.4} />
          <span className="global-live-bar-title">
            {status === 'connecting' ? 'Connecting live detection…' : 'Live detection active'}
          </span>
        </div>

        <div className="global-live-bar-mid">
          <span className="global-live-bar-stat">
            <span className="global-live-bar-stat-label">Current risk</span>
            <span className={`global-live-bar-stat-value global-live-bar-stat-${riskClass}`}>
              {getRiskLabel(riskLevel)}
            </span>
          </span>
          <span className="global-live-bar-stat">
            <span className="global-live-bar-stat-label">Session duration</span>
            <span className="global-live-bar-stat-value">{formatDuration(elapsedSeconds)}</span>
          </span>
        </div>

        <button type="button" className="global-live-bar-stop" onClick={stopLive}>
          <Square size={13} strokeWidth={2.4} />
          Stop Detection
        </button>
      </div>
    </div>
  )
}

export default GlobalLiveBar

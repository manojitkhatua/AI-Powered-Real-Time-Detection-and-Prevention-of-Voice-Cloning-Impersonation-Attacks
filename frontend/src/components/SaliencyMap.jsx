import { ScanEye } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

// Deterministic pseudo-random generator so the heatmap is stable across
// re-renders for a given detection, without needing real model output.
function seededValue(row, col, seed) {
  const n = Math.sin(row * 12.9898 + col * 78.233 + seed * 37.719) * 43758.5453
  return n - Math.floor(n)
}

const ROWS = 10
const COLS = 24

function SaliencyMap({ detection }) {
  const riskLevel = detection?.risk_level ?? 'LOW'
  const saliencyLevel = detection?.saliency_level ?? 'LOW'
  const riskClass = getRiskClass(riskLevel)
  const seed = detection ? detection.audio_window * 10 : 1

  const intensityBySaliency = { LOW: 0.25, MEDIUM: 0.45, HIGH: 0.68, CRITICAL: 0.9 }
  const baseIntensity = intensityBySaliency[saliencyLevel] ?? 0.25

  const cells = []
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const noise = seededValue(r, c, seed)
      // Concentrate hot cells toward the later time columns to suggest
      // an emerging anomaly region, scaled by the current saliency level.
      const timeBias = c / COLS
      const value = Math.min(1, noise * 0.6 + timeBias * baseIntensity * 0.9)
      cells.push({ r, c, value })
    }
  }

  return (
    <section className="panel" aria-labelledby="saliency-title">
      <div className="panel-header">
        <div>
          <h2 className="panel-title" id="saliency-title">
            <ScanEye size={15} strokeWidth={2.2} />
            Spectro-temporal saliency
          </h2>
          <span className="panel-subtitle">AI analysis visualization</span>
        </div>
        <span className={`badge badge-${riskClass}`}>
          <span className="badge-dot" aria-hidden="true" />
          {saliencyLevel}
        </span>
      </div>

      <div className="saliency-map" role="img" aria-label={`Saliency heatmap, current level ${saliencyLevel}`}>
        <div className="saliency-axis-y">
          <span>8k</span>
          <span>4k</span>
          <span>1k</span>
          <span>Hz</span>
        </div>
        <div className="saliency-grid">
          {cells.map(({ r, c, value }) => (
            <span
              key={`${r}-${c}`}
              className="saliency-cell"
              style={{ backgroundColor: `rgba(240, 80, 61, ${(value * 0.75).toFixed(2)})` }}
            />
          ))}
        </div>
      </div>
      <div className="saliency-axis-x">
        <span>0.0s</span>
        <span>0.4s</span>
        <span>0.8s</span>
        <span>1.2s</span>
        <span>1.6s</span>
      </div>

      <p className="panel-footnote">
        Frontend representation of anomaly regions reported by the detection model — not a live spectrogram.
      </p>
    </section>
  )
}

export default SaliencyMap

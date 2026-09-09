import { AudioWaveform } from 'lucide-react'

// Fixed waveform bar heights keep the compact visual stable between renders.
// This is an audio-activity illustration, not a model explanation map.
const BAR_HEIGHTS = [22, 40, 30, 55, 70, 48, 62, 35, 50, 68, 44, 58, 30, 46, 60, 38, 52, 66, 42, 28, 36, 54, 32, 20]

function UltraShortAnalysis({ detection }) {
  if (!detection) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2 className="panel-title">Ultra-short audio analysis</h2>
        </div>
        <p className="empty-state">Waiting for detection stream…</p>
      </section>
    )
  }

  const { audio_window = 2, processing_latency } = detection
  const latencyLabel = Number(processing_latency) > 0 ? `${processing_latency} ms` : 'Live stream'

  return (
    <section className="panel" aria-labelledby="ultra-short-title">
      <div className="panel-header">
        <div>
          <h2 className="panel-title" id="ultra-short-title">
            <AudioWaveform size={15} strokeWidth={2.2} />
            Ultra-short audio analysis
          </h2>
        </div>
        <span className="live-tag">
          <span className="live-tag-dot" aria-hidden="true" />
          Real-time
        </span>
      </div>

      <div className="waveform" role="img" aria-label={`Audio window ${audio_window} seconds`}>
        {BAR_HEIGHTS.map((height, i) => (
          <span key={i} className="waveform-bar" style={{ height: `${height}%` }} />
        ))}
      </div>

      <div className="mini-stat-row mini-stat-row-three">
        <div className="mini-stat">
          <span className="mini-stat-label">Analysis window</span>
          <span className="mini-stat-value">{audio_window}s</span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Window overlap</span>
          <span className="mini-stat-value">1.0s</span>
        </div>
        <div className="mini-stat">
          <span className="mini-stat-label">Processing</span>
          <span className="mini-stat-value">{latencyLabel}</span>
        </div>
      </div>

      <p className="panel-footnote">
        Audio is evaluated in overlapping short windows so suspicious evidence can accumulate over time.
      </p>
    </section>
  )
}

export default UltraShortAnalysis

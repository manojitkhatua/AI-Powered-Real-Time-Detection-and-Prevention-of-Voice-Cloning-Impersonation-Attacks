import { Mic, Loader2, AlertTriangle } from 'lucide-react'
import { useLiveDetection } from '../context/LiveDetectionContext.jsx'

function LiveEntryPanel() {
  const { status, error, startLive, clearError } = useLiveDetection()
  const busy = status === 'requesting-permission' || status === 'connecting'

  return (
    <section className="panel entry-panel" aria-labelledby="live-panel-title">
      <div className="panel-header">
        <h2 className="panel-title" id="live-panel-title">
          <Mic size={15} strokeWidth={2.2} />
          Live voice detection
        </h2>
      </div>

      <p className="entry-panel-desc">
        Start continuous microphone-based detection. Detection keeps running even if you
        navigate to another page — a live status bar stays visible until you stop it.
      </p>

      {error && (
        <div className="inline-error">
          <AlertTriangle size={14} strokeWidth={2.2} />
          <span>{error.message}</span>
        </div>
      )}

      <button
        type="button"
        className="action-button action-button-primary"
        onClick={error ? clearError : startLive}
        disabled={busy}
      >
        {busy ? (
          <>
            <Loader2 size={15} strokeWidth={2.4} className="spin" />
            {status === 'requesting-permission' ? 'Requesting microphone…' : 'Connecting…'}
          </>
        ) : error ? (
          'Try Again'
        ) : (
          <>
            <Mic size={15} strokeWidth={2.2} />
            Start Live Detection
          </>
        )}
      </button>
    </section>
  )
}

export default LiveEntryPanel

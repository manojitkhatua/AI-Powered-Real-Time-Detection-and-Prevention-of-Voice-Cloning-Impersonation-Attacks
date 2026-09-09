import { useEffect, useState } from 'react'
import RiskBanner from '../components/RiskBanner.jsx'
import CallerPanel from '../components/CallerPanel.jsx'
import VoiceStatusCard from '../components/VoiceStatusCard.jsx'
import RiskScoreCard from '../components/RiskScoreCard.jsx'
import SecurityAction from '../components/SecurityAction.jsx'
import RiskTimeline from '../components/RiskTimeline.jsx'
import TemporalDetectionAnalysis from '../components/TemporalDetectionAnalysis.jsx'
import UltraShortAnalysis from '../components/UltraShortAnalysis.jsx'
import DetectionEvents from '../components/DetectionEvents.jsx'
import VerificationModal from '../components/VerificationModal.jsx'
import BlockedScreen from '../components/BlockedScreen.jsx'
import UploadPanel from '../components/UploadPanel.jsx'
import LiveEntryPanel from '../components/LiveEntryPanel.jsx'
import SessionSummaryModal from '../components/SessionSummaryModal.jsx'
import { useLiveDetection } from '../context/LiveDetectionContext.jsx'

function Dashboard() {
  const {
    isLive,
    status,
    sessionId: liveSessionId,
    currentDetection: liveDetection,
    detectionHistory: liveHistory,
    finalSummary,
    dismissSummary,
  } = useLiveDetection()

  const [uploadResult, setUploadResult] = useState(null)
  const [showVerification, setShowVerification] = useState(false)
  const [showBlockedScreen, setShowBlockedScreen] = useState(false)
  const [dismissedBlockFor, setDismissedBlockFor] = useState(null)

  // Whichever source is currently authoritative: an active/just-stopped
  // live session takes priority over a previous upload result.
  const source = isLive || status === 'stopped' ? 'live' : uploadResult ? 'upload' : null
  const activeDetection = source === 'live' ? liveDetection : uploadResult
  const activeHistory = source === 'live' ? liveHistory : uploadResult ? [uploadResult] : []

  useEffect(() => {
    if (activeDetection?.action === 'BLOCK' && dismissedBlockFor !== `${source}-${activeDetection.audio_window}`) {
      setShowBlockedScreen(true)
    }
  }, [activeDetection, dismissedBlockFor, source])

  const handleCloseBlocked = () => {
    setShowBlockedScreen(false)
    setDismissedBlockFor(activeDetection ? `${source}-${activeDetection.audio_window}` : null)
  }

  const handleUploadResult = (result) => {
    // Normalize the REST response to the same shape used by the live stream.
    // The REST endpoint returns aggregate values rather than per-window events.
    setUploadResult({
      ...result,
      file_name: result.file_name ?? result.filename,
      audio_window: Number(result.audio_window ?? 2),
      processing_latency: Number(result.processing_latency ?? 0),
      anomaly_detected: Number(result.spoof_probability ?? 0) >= 0.5,
    })
  }

  return (
    <>
      <main className="dashboard">
        <div className="dashboard-intro">
          <h1>EchoVerify</h1>
          <p>AI voice security &amp; verification platform</p>
          <div className="dashboard-intro-meta">
            <span>Real-time AI analysis</span>
            <span className="dashboard-intro-dot" aria-hidden="true">•</span>
            <span>Session: {source === 'live' ? (liveSessionId ?? '—') : (activeDetection?.session_id ?? 'No session yet')}</span>
          </div>
        </div>

        {!isLive && (
          <div className="grid grid-2col entry-grid">
            <UploadPanel onResult={handleUploadResult} disabled={isLive} />
            <LiveEntryPanel />
          </div>
        )}

        {!activeDetection && !isLive && (
          <p className="empty-state entry-empty-hint">
            Upload an audio file or start live detection above to see results here.
          </p>
        )}

        {activeDetection && (
          <>
            <RiskBanner riskLevel={activeDetection.risk_level} />

            <div className="grid grid-2col">
              <CallerPanel
                sessionId={activeDetection.session_id}
                mode={source}
                fileName={activeDetection.file_name}
                riskLevel={activeDetection.risk_level}
              />
              <VoiceStatusCard detection={activeDetection} />
            </div>

            <div className="grid grid-2col">
              <RiskScoreCard detection={activeDetection} />
              <SecurityAction detection={activeDetection} onStartVerification={() => setShowVerification(true)} />
            </div>

            <div className="section-heading">
              <h2>AI detection analysis</h2>
            </div>

            <div className="grid grid-2col">
              <TemporalDetectionAnalysis detectionHistory={activeHistory} />
              <UltraShortAnalysis detection={activeDetection} />
            </div>

            <RiskTimeline detectionHistory={activeHistory} />

            <DetectionEvents detectionHistory={activeHistory} />
          </>
        )}
      </main>

      <VerificationModal
        open={showVerification}
        onClose={() => setShowVerification(false)}
        onConfirm={() => setShowVerification(false)}
      />

      {showBlockedScreen && activeDetection?.action === 'BLOCK' && (
        <BlockedScreen detection={activeDetection} onClose={handleCloseBlocked} />
      )}

      <SessionSummaryModal summary={finalSummary} onClose={dismissSummary} />
    </>
  )
}

export default Dashboard

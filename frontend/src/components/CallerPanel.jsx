import { UserRound, CircleAlert, FileAudio } from 'lucide-react'

function CallerPanel({ sessionId = 'CALL-001', mode = 'live', fileName, riskLevel = 'LOW' }) {
  const isUpload = mode === 'upload'
  const verificationLabel = riskLevel === 'CRITICAL'
    ? 'Session blocked'
    : riskLevel === 'HIGH'
      ? 'Verification required'
      : riskLevel === 'MEDIUM'
        ? 'Verification recommended'
        : 'Monitoring active'

  return (
    <section className="panel" aria-labelledby="caller-panel-title">
      <div className="panel-header">
        <h2 className="panel-title" id="caller-panel-title">
          {isUpload ? 'Audio source' : 'Caller identity'}
        </h2>
      </div>

      <div className="caller-body">
        <div className="caller-avatar" aria-hidden="true">
          {isUpload ? <FileAudio size={26} strokeWidth={1.8} /> : <UserRound size={26} strokeWidth={1.8} />}
        </div>
        <div className="caller-info">
          <span className="caller-name">{isUpload ? (fileName ?? 'Uploaded file') : 'Unknown Caller'}</span>
          <span className="caller-session">Session: {sessionId}</span>
        </div>
      </div>

      <div className="caller-status">
        <CircleAlert size={15} strokeWidth={2.2} />
        <div>
          <span className="caller-status-label">{verificationLabel}</span>
          <p className="caller-status-desc">
            {isUpload
              ? 'Review the analysis result below before trusting this recording.'
              : 'Additional identity verification is recommended.'}
          </p>
        </div>
      </div>
    </section>
  )
}

export default CallerPanel

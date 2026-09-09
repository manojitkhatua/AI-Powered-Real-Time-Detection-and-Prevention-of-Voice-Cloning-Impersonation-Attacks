import { History as HistoryIcon, Trash2, Mic, UploadCloud } from 'lucide-react'
import useHistory from '../hooks/useHistory.js'
import { groupHistoryByDay, clearHistory } from '../services/history.js'
import { getRiskClass, getRiskLabel } from '../services/riskPolicy.js'

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function HistoryGroup({ label, entries }) {
  if (entries.length === 0) return null
  return (
    <div className="history-group">
      <h3 className="history-group-title">{label}</h3>
      <div className="history-list">
        {entries.map((entry) => {
          const riskClass = getRiskClass(entry.riskLevel)
          return (
            <div className="history-row" key={entry.id}>
              <span className="history-row-time">{formatTime(entry.timestamp)}</span>
              <span className="history-row-type">
                {entry.type === 'live' ? <Mic size={13} strokeWidth={2.2} /> : <UploadCloud size={13} strokeWidth={2.2} />}
                {entry.type === 'live' ? 'Live Detection' : 'Uploaded Audio'}
              </span>
              <span className="history-row-detail">{entry.detail ?? entry.sessionId}</span>
              <span className={`badge badge-${riskClass}`}>
                <span className="badge-dot" aria-hidden="true" />
                {getRiskLabel(entry.riskLevel)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function History() {
  const entries = useHistory()
  const groups = groupHistoryByDay(entries)

  return (
    <main className="dashboard">
      <div className="dashboard-intro">
        <h1>Detection session history</h1>
        <p>A local record of your upload and live detection sessions.</p>
      </div>

      <section className="panel" aria-labelledby="history-panel-title">
        <div className="panel-header">
          <h2 className="panel-title" id="history-panel-title">
            <HistoryIcon size={15} strokeWidth={2.2} />
            Sessions
          </h2>
          {entries.length > 0 && (
            <button type="button" className="icon-button" onClick={clearHistory} aria-label="Clear history">
              <Trash2 size={15} strokeWidth={2} />
            </button>
          )}
        </div>

        {entries.length === 0 ? (
          <p className="empty-state">No sessions recorded yet. Analyze an audio file or run a live detection to see it here.</p>
        ) : (
          <>
            <HistoryGroup label="Today" entries={groups.Today} />
            <HistoryGroup label="Yesterday" entries={groups.Yesterday} />
            <HistoryGroup label="Earlier" entries={groups.Earlier} />
          </>
        )}
      </section>
    </main>
  )
}

export default History

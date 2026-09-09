import { ListTree } from 'lucide-react'
import { getRiskClass } from '../services/riskPolicy.js'

function DetectionEvents({ detectionHistory = [] }) {
  return (
    <section className="panel" aria-labelledby="detection-events-title">
      <div className="panel-header">
        <h2 className="panel-title" id="detection-events-title">
          <ListTree size={15} strokeWidth={2.2} />
          Detection events
        </h2>
        <span className="panel-subtitle">{detectionHistory.length} events</span>
      </div>

      {detectionHistory.length === 0 ? (
        <p className="empty-state">No detection events recorded yet.</p>
      ) : (
        <div className="table-scroll">
          <table className="events-table">
            <thead>
              <tr>
                <th scope="col">Window</th>
                <th scope="col">Voice status</th>
                <th scope="col">Spoof probability</th>
                <th scope="col">Risk score</th>
                <th scope="col">Risk level</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {detectionHistory.map((event, i) => {
                const isLatest = i === detectionHistory.length - 1
                const riskClass = getRiskClass(event.risk_level)
                const windowLabel = event.window_index != null ? `W${Number(event.window_index) + 1}` : 'Final'
                return (
                  <tr key={`${event.audio_window ?? windowLabel}-${i}`} className={isLatest ? 'events-row-latest' : ''}>
                    <td data-label="Window">{windowLabel}</td>
                    <td data-label="Voice status">{event.voice_status}</td>
                    <td data-label="Spoof probability">{Math.round(event.spoof_probability * 100)}%</td>
                    <td data-label="Risk score">{event.risk_score}</td>
                    <td data-label="Risk level">
                      <span className={`badge badge-${riskClass}`}>
                        <span className="badge-dot" aria-hidden="true" />
                        {event.risk_level}
                      </span>
                    </td>
                    <td data-label="Action">{event.action}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default DetectionEvents

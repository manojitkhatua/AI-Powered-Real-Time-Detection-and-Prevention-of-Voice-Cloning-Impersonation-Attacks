import { useState } from 'react'
import { Settings as SettingsIcon, Server, FlaskConical } from 'lucide-react'
import { API_BASE_URL, WS_URL, isMockMode, setMockMode } from '../config.js'

function Settings() {
  const [mock, setMock] = useState(isMockMode())

  const handleToggle = () => {
    const next = !mock
    setMockMode(next)
    setMock(next)
  }

  return (
    <main className="dashboard">
      <div className="dashboard-intro">
        <h1>Settings</h1>
        <p>Configure how EchoVerify talks to the detection backend.</p>
      </div>

      <section className="panel" aria-labelledby="mode-panel-title">
        <div className="panel-header">
          <h2 className="panel-title" id="mode-panel-title">
            <FlaskConical size={15} strokeWidth={2.2} />
            Detection mode
          </h2>
        </div>

        <p className="entry-panel-desc">
          Demo/Mock mode simulates realistic detection results locally, so the app works
          reliably even if the backend is unavailable — recommended for SIH demos. Switch to
          Real Backend mode once the FastAPI/WebSocket backend is deployed and reachable.
        </p>

        <div className="settings-toggle-row">
          <div>
            <span className="mini-stat-value">{mock ? 'Demo / Mock Mode' : 'Real Backend Mode'}</span>
            <p className="mini-stat-label" style={{ marginTop: 4 }}>
              {mock ? 'Using simulated detection data' : 'Using the configured API / WebSocket backend'}
            </p>
          </div>
          <button type="button" className="action-button action-button-primary settings-toggle-btn" onClick={handleToggle}>
            Switch to {mock ? 'Real Backend' : 'Demo Mode'}
          </button>
        </div>

        <p className="panel-footnote">
          This starts a new session in the selected mode — it won&apos;t change a live session
          that is already running.
        </p>
      </section>

      <section className="panel" aria-labelledby="backend-panel-title">
        <div className="panel-header">
          <h2 className="panel-title" id="backend-panel-title">
            <Server size={15} strokeWidth={2.2} />
            Backend configuration
          </h2>
        </div>

        <div className="mini-stat-row">
          <div className="mini-stat">
            <span className="mini-stat-label">API base URL</span>
            <span className="mini-stat-value settings-mono">{API_BASE_URL || 'Not configured'}</span>
          </div>
          <div className="mini-stat">
            <span className="mini-stat-label">WebSocket URL</span>
            <span className="mini-stat-value settings-mono">{WS_URL || 'Not configured'}</span>
          </div>
        </div>

        <p className="panel-footnote">
          Set <code>VITE_API_BASE_URL</code> and <code>VITE_WS_URL</code> in your <code>.env</code> file
          (see <code>.env.example</code>) to point EchoVerify at a real backend. No code changes needed.
        </p>
      </section>

      <section className="panel" aria-labelledby="about-panel-title">
        <div className="panel-header">
          <h2 className="panel-title" id="about-panel-title">
            <SettingsIcon size={15} strokeWidth={2.2} />
            About this prototype
          </h2>
        </div>
        <p className="panel-footnote">
          EchoVerify is an SIH hackathon prototype for AI-based voice spoofing, cloning, and
          impersonation detection. Session history is stored locally in this browser.
        </p>
      </section>
    </main>
  )
}

export default Settings

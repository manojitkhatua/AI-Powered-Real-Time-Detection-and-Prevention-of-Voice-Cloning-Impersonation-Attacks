import { NavLink } from 'react-router-dom'
import { ShieldCheck, LayoutDashboard, History, Settings } from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/history', label: 'History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function Header({ sessionId }) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand">
          <span className="brand-icon">
            <ShieldCheck size={20} strokeWidth={2} />
          </span>
          <div className="brand-text">
            <span className="brand-name">EchoVerify</span>
            <span className="brand-tag">AI Voice Security</span>
          </div>
        </div>

        <nav className="app-nav" aria-label="Primary">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `app-nav-link${isActive ? ' app-nav-link-active' : ''}`}
            >
              <Icon size={14} strokeWidth={2.2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="header-right">
          <div className="system-status">
            <span className="system-status-label">System status</span>
            <span className="system-status-value">
              <span className="status-pulse" aria-hidden="true" />
              Operational
            </span>
          </div>
          {sessionId && (
            <div className="session-chip">
              <span className="session-label">Session</span>
              <span className="session-value">{sessionId}</span>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

export default Header

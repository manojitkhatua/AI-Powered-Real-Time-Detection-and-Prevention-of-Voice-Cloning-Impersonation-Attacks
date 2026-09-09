import { NavLink } from 'react-router-dom'
import {
  ShieldCheck,
  LayoutDashboard,
  History,
  Settings,
  Activity,
} from 'lucide-react'

const NAV_ITEMS = [
  {
    to: '/',
    label: 'Dashboard',
    icon: LayoutDashboard,
    end: true,
  },
  {
    to: '/history',
    label: 'History',
    icon: History,
  },
  {
    to: '/settings',
    label: 'Settings',
    icon: Settings,
  },
]

function Header({ sessionId }) {
  return (
    <aside className="app-sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <ShieldCheck size={22} strokeWidth={2} />
        </div>

        <div className="brand-text">
          <span className="brand-name">EchoVerify</span>
          <span className="brand-tag">AI Voice Security</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav" aria-label="Primary navigation">
        <div className="sidebar-section-label">
          PLATFORM
        </div>

        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `sidebar-nav-link${isActive ? ' sidebar-nav-link-active' : ''}`
            }
          >
            <Icon size={19} strokeWidth={2} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom status */}
      <div className="sidebar-bottom">
        <div className="sidebar-status">
          <span className="status-dot" />
          <div>
            <span className="sidebar-status-title">
              System Operational
            </span>
            <span className="sidebar-status-subtitle">
              All services running
            </span>
          </div>
        </div>

        {sessionId && (
          <div className="sidebar-session">
            <div className="sidebar-session-label">
              ACTIVE SESSION
            </div>

            <div className="sidebar-session-value">
              <Activity size={14} />
              {sessionId}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <span>EchoVerify</span>
          <span>AI Security Platform</span>
        </div>
      </div>
    </aside>
  )
}

export default Header
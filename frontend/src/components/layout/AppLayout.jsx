import { useLiveDetection } from '../../context/LiveDetectionContext.jsx'
import Header from '../Header.jsx'
import GlobalLiveBar from '../GlobalLiveBar.jsx'

function AppLayout({ children }) {
  const { sessionId, isLive } = useLiveDetection()

  return (
    <div className="app-shell">
      <Header sessionId={isLive ? sessionId : undefined} />

      <div className="app-main">
        <GlobalLiveBar />

        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppLayout
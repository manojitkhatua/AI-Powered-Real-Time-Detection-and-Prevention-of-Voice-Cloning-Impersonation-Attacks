import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { LiveDetectionProvider } from './context/LiveDetectionContext.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      {/* LiveDetectionProvider sits above the router so a live session
          survives navigation between pages. */}
      <LiveDetectionProvider>
        <App />
      </LiveDetectionProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

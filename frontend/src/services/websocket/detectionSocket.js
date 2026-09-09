/**
 * Reusable WebSocket service for the live detection stream.
 *
 * This does NOT auto-connect on import — the mock engine (see
 * src/services/mock/liveMockEngine.js, used by LiveDetectionContext)
 * remains the default data source until a backend is available. The
 * context calls connect() explicitly when Real Backend Mode is active.
 */

const WS_URL = import.meta.env.VITE_WS_URL ?? ''

export class DetectionSocket {
  constructor() {
    this.socket = null
    this.listeners = {
      message: [],
      open: [],
      close: [],
      error: [],
    }
  }

  /**
   * Open the WebSocket connection. Safe to call once; subsequent calls
   * while already connected are ignored.
   */
  connect() {
    if (!WS_URL) {
      this._emit('error', new Error('VITE_WS_URL is not configured'))
      return
    }

    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return
    }

    this.socket = new WebSocket(WS_URL)

    this.socket.addEventListener('open', (event) => this._emit('open', event))
    this.socket.addEventListener('close', (event) => this._emit('close', event))
    this.socket.addEventListener('error', (event) => this._emit('error', event))
    this.socket.addEventListener('message', (event) => {
      try {
        const payload = JSON.parse(event.data)
        this._emit('message', payload)
      } catch (error) {
        this._emit('error', error)
      }
    })
  }

  /**
   * Register a listener for 'message' | 'open' | 'close' | 'error'.
   * Returns an unsubscribe function.
   */
  on(eventName, callback) {
    if (!this.listeners[eventName]) return () => {}
    this.listeners[eventName].push(callback)
    return () => {
      this.listeners[eventName] = this.listeners[eventName].filter((cb) => cb !== callback)
    }
  }

  send(payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload))
    }
  }

  close() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  _emit(eventName, payload) {
    this.listeners[eventName].forEach((cb) => cb(payload))
  }
}

// Shared singleton instance — components can import this directly, or
// construct their own DetectionSocket() for isolated usage/testing.
const detectionSocket = new DetectionSocket()
export default detectionSocket

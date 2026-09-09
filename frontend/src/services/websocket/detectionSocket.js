import { WS_URL } from '../../config.js'

export class DetectionSocket {
  constructor() {
    this.socket = null
    this.listeners = { message: [], open: [], close: [], error: [] }
  }

  connect(sessionId) {
    if (!sessionId) {
      this._emit('error', new Error('A session ID is required for WebSocket connection'))
      return
    }
    if (this.socket && this.socket.readyState === WebSocket.OPEN) return

    const base = WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    const url = `${base}/ws/${encodeURIComponent(sessionId)}`
    try {
      this.socket = new WebSocket(url)
      this.socket.binaryType = 'arraybuffer'
      this.socket.addEventListener('open', (event) => {
        this._emit('open', event)
        this.send({ type: 'start' })
      })
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
    } catch (error) {
      this._emit('error', error)
    }
  }

  on(eventName, callback) {
    if (!this.listeners[eventName]) return () => {}
    this.listeners[eventName].push(callback)
    return () => {
      this.listeners[eventName] = this.listeners[eventName].filter((cb) => cb !== callback)
    }
  }

  send(payload) {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(payload))
  }

  sendBinary(data) {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(data)
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

const detectionSocket = new DetectionSocket()
export default detectionSocket

import { API_BASE_URL } from '../../config.js'

async function request(path, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL || ''}${path}`, options)
    const text = await response.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch { data = text }

    if (!response.ok) {
      const message = data?.detail || data?.message || `Request failed with status ${response.status}`
      throw new Error(message)
    }
    return { data, error: null }
  } catch (error) {
    return { data: null, error }
  }
}

export function getHealth() {
  return request('/api/health')
}

export function analyzeAudioFile(file) {
  const formData = new FormData()
  // FastAPI backend expects the uploaded audio under the `audio` field.
  formData.append('audio', file, file.name)
  return request('/api/analyze', { method: 'POST', body: formData })
}

// Kept for compatibility with the existing context; live streaming now uses WebSocket.
export function sendAudioForDetection(audioChunk) {
  const formData = new FormData()
  formData.append('audio', audioChunk, 'live-audio.wav')
  return request('/api/analyze', { method: 'POST', body: formData })
}

export default { getHealth, analyzeAudioFile, sendAudioForDetection }

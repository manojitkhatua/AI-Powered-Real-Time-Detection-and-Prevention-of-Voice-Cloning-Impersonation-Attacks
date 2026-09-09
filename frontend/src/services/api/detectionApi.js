/**
 * REST integration layer for the detection backend.
 *
 * No real endpoint paths are assumed here — the backend team can fill
 * these in once their API is defined. Every function fails gracefully
 * and returns a consistent { data, error } shape so components never
 * need to wrap calls in their own try/catch.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  if (!API_BASE_URL) {
    return { data: null, error: new Error('VITE_API_BASE_URL is not configured') }
  }

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`)
    }

    const data = await response.json()
    return { data, error: null }
  } catch (error) {
    return { data: null, error }
  }
}

/**
 * Fetch the latest detection result for a session.
 * Placeholder path — replace once the backend defines its route.
 * @param {string} sessionId
 */
export function getDetection(sessionId) {
  return request(`/detections/${encodeURIComponent(sessionId)}`)
}

/**
 * Submit a raw audio chunk for detection over REST as a fallback to the
 * WebSocket stream. Placeholder path — replace once the backend defines
 * its route.
 * @param {Blob | ArrayBuffer} audioChunk
 * @param {string} sessionId
 */
export function sendAudioForDetection(audioChunk, sessionId) {
  const formData = new FormData()
  formData.append('audio', audioChunk)
  formData.append('session_id', sessionId)

  return request('/detections/analyze', {
    method: 'POST',
    headers: undefined, // let the browser set the multipart boundary
    body: formData,
  })
}

/**
 * Fetch the detection history/timeline for a session.
 * Placeholder path — replace once the backend defines its route.
 * @param {string} sessionId
 */
export function getDetectionHistory(sessionId) {
  return request(`/detections/${encodeURIComponent(sessionId)}/history`)
}

/**
 * Upload a complete audio file for a one-shot analysis (the "Analyze
 * Audio" flow on the Dashboard). Placeholder path — replace once the
 * backend defines its route.
 * @param {File} file
 */
export function analyzeAudioFile(file) {
  const formData = new FormData()
  formData.append('audio', file)

  return request('/detections/analyze-file', {
    method: 'POST',
    headers: undefined, // let the browser set the multipart boundary
    body: formData,
  })
}

export default {
  getDetection,
  sendAudioForDetection,
  getDetectionHistory,
  analyzeAudioFile,
}

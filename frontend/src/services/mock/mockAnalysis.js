/**
 * Deterministic mock analysis for the "Upload Audio" flow.
 *
 * Given the same file (name + size), this always returns the same result,
 * so a demo run behaves predictably. Values are derived from a simple hash
 * rather than random on every call.
 */

function hashString(input) {
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

function levelFromScore(score) {
  if (score < 30) return 'LOW'
  if (score < 55) return 'MEDIUM'
  if (score < 80) return 'HIGH'
  return 'CRITICAL'
}

const ACTION_BY_LEVEL = { LOW: 'MONITOR', MEDIUM: 'WARNING', HIGH: 'VERIFY', CRITICAL: 'BLOCK' }
const STATUS_BY_LEVEL = { LOW: 'REAL', MEDIUM: 'SUSPICIOUS', HIGH: 'SUSPICIOUS', CRITICAL: 'FAKE' }
const MESSAGE_BY_LEVEL = {
  LOW: 'Voice appears authentic and no significant signs of synthetic or cloned speech were detected.',
  MEDIUM: 'Potential signs of synthetic or manipulated speech were detected.',
  HIGH: 'Strong indicators of voice spoofing or synthetic generation were detected. Verification is recommended.',
  CRITICAL: 'The audio contains strong indicators of voice spoofing, synthetic generation, or voice cloning.',
}

/**
 * Simulate uploading and analyzing an audio file.
 * @param {File} file
 * @returns {Promise<{data: import('../../types/detection.js').DetectionEvent & {duration_estimate: number}, error: null}>}
 */
export function analyzeAudioFileMock(file) {
  const seed = hashString(`${file.name}:${file.size}`)
  const riskScore = seed % 100
  const riskLevel = levelFromScore(riskScore)
  const spoofProbability = Math.min(0.99, riskScore / 100 + ((seed % 7) - 3) / 100)
  const confidence = 0.82 + ((seed % 17) / 100)
  const processingLatencyMs = 900 + (seed % 1400)

  const result = {
    session_id: `UPLOAD-${seed.toString(36).toUpperCase().slice(0, 6)}`,
    file_name: file.name,
    voice_status: STATUS_BY_LEVEL[riskLevel],
    spoof_probability: Number(spoofProbability.toFixed(2)),
    risk_score: riskScore,
    risk_level: riskLevel,
    action: ACTION_BY_LEVEL[riskLevel],
    message: MESSAGE_BY_LEVEL[riskLevel],
    audio_window: 1.2,
    processing_latency: processingLatencyMs,
    saliency_level: riskLevel,
    anomaly_detected: riskLevel !== 'LOW',
    confidence: Number(confidence.toFixed(2)),
    duration_estimate: 4 + (seed % 40),
  }

  // Simulate realistic processing time so the loading state is visible.
  const delay = 1200 + (seed % 900)
  return new Promise((resolve) => {
    setTimeout(() => resolve({ data: result, error: null }), delay)
  })
}

export default analyzeAudioFileMock

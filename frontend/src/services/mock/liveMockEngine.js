/**
 * Mock engine for the "Live Detection" flow.
 *
 * Produces a continuous, realistic-looking stream of detection events via
 * a bounded random walk (not pure noise), so risk rises and falls smoothly
 * instead of jumping around unpredictably. Centralized here so no UI
 * component generates its own random values.
 */

const TICK_MS = 1800

function levelFromScore(score) {
  if (score < 30) return 'LOW'
  if (score < 55) return 'MEDIUM'
  if (score < 80) return 'HIGH'
  return 'CRITICAL'
}

const ACTION_BY_LEVEL = { LOW: 'MONITOR', MEDIUM: 'WARNING', HIGH: 'VERIFY', CRITICAL: 'BLOCK' }
const STATUS_BY_LEVEL = { LOW: 'REAL', MEDIUM: 'SUSPICIOUS', HIGH: 'SUSPICIOUS', CRITICAL: 'FAKE' }
const MESSAGE_BY_LEVEL = {
  LOW: 'Voice appears authentic',
  MEDIUM: 'Unusual voice characteristics detected',
  HIGH: 'Synthetic voice indicators detected',
  CRITICAL: 'Critical synthetic voice threat detected',
}

export function createLiveMockEngine({ sessionId = 'LIVE-SESSION', onEvent }) {
  let timer = null
  let windowIndex = 0
  let score = 15 + Math.round(Math.random() * 10)

  function step() {
    windowIndex += 1

    // Bounded random walk: most steps drift gently, occasional larger swing
    // to simulate a real anomaly appearing/resolving during a call.
    const drift = Math.random() < 0.12 ? (Math.random() < 0.5 ? -1 : 1) * (18 + Math.random() * 20)
      : (Math.random() - 0.5) * 12
    score = Math.max(3, Math.min(97, score + drift))

    const riskScore = Math.round(score)
    const riskLevel = levelFromScore(riskScore)
    const spoofProbability = Math.min(0.99, Math.max(0.01, riskScore / 100 + (Math.random() - 0.5) * 0.05))

    const event = {
      session_id: sessionId,
      voice_status: STATUS_BY_LEVEL[riskLevel],
      spoof_probability: Number(spoofProbability.toFixed(2)),
      risk_score: riskScore,
      risk_level: riskLevel,
      action: ACTION_BY_LEVEL[riskLevel],
      message: MESSAGE_BY_LEVEL[riskLevel],
      audio_window: Number((windowIndex * 1.2).toFixed(1)),
      processing_latency: 60 + Math.round(Math.random() * 45),
      saliency_level: riskLevel,
      anomaly_detected: riskLevel !== 'LOW' && Math.random() > 0.25,
    }

    onEvent(event)
  }

  return {
    start() {
      if (timer) return
      step()
      timer = setInterval(step, TICK_MS)
    },
    stop() {
      if (timer) clearInterval(timer)
      timer = null
    },
  }
}

export default createLiveMockEngine

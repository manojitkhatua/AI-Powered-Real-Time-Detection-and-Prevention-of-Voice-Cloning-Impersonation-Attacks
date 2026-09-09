/**
 * Central runtime configuration for EchoVerify.
 *
 * This is the single place that decides:
 *  - where the REST/WebSocket backend lives
 *  - whether the app is running in MOCK/DEMO mode or REAL BACKEND mode
 *
 * UI components and services should read from here rather than touching
 * import.meta.env or localStorage directly, so the mock/real switch never
 * requires rewriting components.
 */

const MOCK_MODE_STORAGE_KEY = 'echoverify.mockMode'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
export const WS_URL = import.meta.env.VITE_WS_URL ?? ''

// Default comes from the env var (falls back to true — safest for a demo).
// A runtime override can be set from the Settings page for quick toggling
// during a live SIH demo without rebuilding the app.
const ENV_DEFAULT_MOCK_MODE = (import.meta.env.VITE_USE_MOCK_MODE ?? 'true') !== 'false'

export function isMockMode() {
  try {
    const override = localStorage.getItem(MOCK_MODE_STORAGE_KEY)
    if (override === 'true') return true
    if (override === 'false') return false
  } catch {
    // localStorage unavailable (e.g. private browsing) — fall through to default
  }
  return ENV_DEFAULT_MOCK_MODE
}

export function setMockMode(value) {
  try {
    localStorage.setItem(MOCK_MODE_STORAGE_KEY, value ? 'true' : 'false')
  } catch {
    // ignore — non-persistent override for this tab only
  }
}

export function isBackendConfigured() {
  return Boolean(API_BASE_URL) || Boolean(WS_URL)
}

export default {
  API_BASE_URL,
  WS_URL,
  isMockMode,
  setMockMode,
  isBackendConfigured,
}

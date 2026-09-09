/** Central EchoVerify runtime configuration. */
const MOCK_MODE_STORAGE_KEY = 'echoverify.mockMode.v2'

// The current FastAPI backend is local during development.
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
export const WS_URL = (import.meta.env.VITE_WS_URL || '').replace(/\/$/, '')

// Real backend is the default for the current integrated prototype.
const ENV_DEFAULT_MOCK_MODE = false

export function isMockMode() {
  try {
    const override = localStorage.getItem(MOCK_MODE_STORAGE_KEY)
    if (override === 'true') return true
    if (override === 'false') return false
  } catch {
    // Fall through to the environment default.
  }
  return ENV_DEFAULT_MOCK_MODE
}

export function setMockMode(value) {
  try {
    localStorage.setItem(MOCK_MODE_STORAGE_KEY, value ? 'true' : 'false')
  } catch {
    // Ignore storage failures.
  }
}

export function isBackendConfigured() {
  return Boolean(API_BASE_URL) && Boolean(WS_URL)
}

export default { API_BASE_URL, WS_URL, isMockMode, setMockMode, isBackendConfigured }

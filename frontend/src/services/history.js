/**
 * Detection Session History — kept simple and local, as this is a frontend
 * prototype without a backend history endpoint. Stored in localStorage so
 * it survives page reloads during a demo. Uses a tiny pub/sub so any
 * component (e.g. the History page and the Dashboard) stays in sync.
 */

const STORAGE_KEY = 'echoverify.history'
const MAX_ENTRIES = 200

const listeners = new Set()

function readAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeAll(entries) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)))
  } catch {
    // ignore write failures (storage full/unavailable) — history is best-effort
  }
  listeners.forEach((cb) => cb(entries))
}

/**
 * @param {{
 *   type: 'upload' | 'live',
 *   riskLevel: string,
 *   verdict: string,
 *   score: number,
 *   detail?: string,
 *   sessionId?: string,
 * }} entry
 */
export function addHistoryEntry(entry) {
  const record = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: Date.now(),
    ...entry,
  }
  const all = [record, ...readAll()]
  writeAll(all)
  return record
}

export function getHistoryEntries() {
  return readAll()
}

export function clearHistory() {
  writeAll([])
}

export function subscribeHistory(callback) {
  listeners.add(callback)
  return () => listeners.delete(callback)
}

/** Groups entries into labeled buckets: Today, Yesterday, Earlier. */
export function groupHistoryByDay(entries) {
  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000

  const groups = { Today: [], Yesterday: [], Earlier: [] }
  entries.forEach((entry) => {
    if (entry.timestamp >= startOfToday) groups.Today.push(entry)
    else if (entry.timestamp >= startOfYesterday) groups.Yesterday.push(entry)
    else groups.Earlier.push(entry)
  })
  return groups
}

export default {
  addHistoryEntry,
  getHistoryEntries,
  clearHistory,
  subscribeHistory,
  groupHistoryByDay,
}

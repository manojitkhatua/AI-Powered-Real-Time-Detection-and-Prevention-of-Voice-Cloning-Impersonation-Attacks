import { useEffect, useState } from 'react'
import { getHistoryEntries, subscribeHistory } from '../services/history.js'

export function useHistory() {
  const [entries, setEntries] = useState(() => getHistoryEntries())

  useEffect(() => subscribeHistory(setEntries), [])

  return entries
}

export default useHistory

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { isMockMode } from '../config.js'
import createLiveMockEngine from '../services/mock/liveMockEngine.js'
import detectionSocket from '../services/websocket/detectionSocket.js'
import { getRecommendedAction, getRiskLabel } from '../services/riskPolicy.js'
import { addHistoryEntry } from '../services/history.js'

/**
 * Global live-detection state.
 *
 * This provider is mounted once, above the router, so starting a live
 * session on the Dashboard and then navigating to History/Settings never
 * tears down the microphone stream, the mock/live engine, or the running
 * timers. Every page reads from the same context instance.
 *
 * status: 'idle' | 'requesting-permission' | 'connecting' | 'live' | 'stopped' | 'error'
 */
const LiveDetectionContext = createContext(null)

function buildSummary({ sessionId, detectionHistory, startedAt, stoppedAt }) {
  if (detectionHistory.length === 0) {
    return {
      sessionId,
      finalRiskLevel: 'LOW',
      finalVerdict: 'REAL',
      finalRiskScore: 0,
      finalSpoofProbability: 0,
      durationSeconds: Math.max(0, Math.round((stoppedAt - startedAt) / 1000)),
      eventCount: 0,
      notableEvents: [],
      recommendedAction: 'MONITOR',
    }
  }

  const last = detectionHistory[detectionHistory.length - 1]
  const notableEvents = detectionHistory.filter((e) => e.anomaly_detected)

  return {
    sessionId,
    finalRiskLevel: last.risk_level,
    finalVerdict: last.voice_status,
    finalRiskScore: last.risk_score,
    finalSpoofProbability: last.spoof_probability,
    durationSeconds: Math.max(0, Math.round((stoppedAt - startedAt) / 1000)),
    eventCount: detectionHistory.length,
    notableEvents: notableEvents.slice(-5),
    recommendedAction: getRecommendedAction(last.risk_level),
  }
}

export function LiveDetectionProvider({ children }) {
  const [status, setStatus] = useState('idle')
  const [sessionId, setSessionId] = useState(null)
  const [startedAt, setStartedAt] = useState(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [currentDetection, setCurrentDetection] = useState(null)
  const [detectionHistory, setDetectionHistory] = useState([])
  const [error, setError] = useState(null)
  const [finalSummary, setFinalSummary] = useState(null)

  const mediaStreamRef = useRef(null)
  const recorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const audioSourceRef = useRef(null)
  const processorRef = useRef(null)
  const engineRef = useRef(null)
  const tickRef = useRef(null)
  const socketUnsubRef = useRef([])
  const historyRef = useRef([])
  const stoppingRef = useRef(false)

  useEffect(() => {
    historyRef.current = detectionHistory
  }, [detectionHistory])

  const cleanupMedia = useCallback(() => {
    if (recorderRef.current) {
      try {
        if (recorderRef.current.state !== 'inactive') recorderRef.current.stop()
      } catch {
        // recorder already stopped
      }
      recorderRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
  }, [])

  const cleanupEngine = useCallback(() => {
    if (engineRef.current) {
      engineRef.current.stop()
      engineRef.current = null
    }
    socketUnsubRef.current.forEach((unsub) => unsub())
    socketUnsubRef.current = []
    detectionSocket.close()
    if (tickRef.current) {
      clearInterval(tickRef.current)
      tickRef.current = null
    }
  }, [])

  const handleEvent = useCallback((event) => {
    setCurrentDetection(event)
    setDetectionHistory((prev) => [...prev, event])
  }, [])

  const handleFatalError = useCallback((type, message) => {
    cleanupEngine()
    cleanupMedia()
    setStatus('error')
    setError({ type, message })
  }, [cleanupEngine, cleanupMedia])

  const startLive = useCallback(async () => {
    if (status === 'live' || status === 'connecting' || status === 'requesting-permission') return

    setError(null)
    setFinalSummary(null)
    setDetectionHistory([])
    setCurrentDetection(null)
    stoppingRef.current = false
    setStatus('requesting-permission')

    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      setStatus('error')
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        setError({
          type: 'mic-denied',
          message: 'Microphone access is required for live voice detection. Please allow microphone permission and try again.',
        })
      } else if (err?.name === 'NotFoundError') {
        setError({ type: 'mic-unavailable', message: 'No microphone was found on this device.' })
      } else {
        setError({ type: 'mic-error', message: 'Unable to access the microphone in this browser.' })
      }
      return
    }

    mediaStreamRef.current = stream
    const newSessionId = `LIVE-${Date.now().toString(36).toUpperCase()}`
    setSessionId(newSessionId)
    setStartedAt(Date.now())
    setStatus('connecting')

    const mock = isMockMode()

    if (mock) {
      const engine = createLiveMockEngine({ sessionId: newSessionId, onEvent: handleEvent })
      engineRef.current = engine
      engine.start()
      setStatus('live')
    } else {
      // Real backend: WebSocket endpoint is /ws/{session_id}. The backend
      // expects raw PCM16 mono audio at 16 kHz, so MediaRecorder/WebM is not
      // suitable here.
      const offMessage = detectionSocket.on('message', (payload) => {
        if (payload?.type === 'detection') {
          handleEvent({
            ...payload,
            audio_window: Number(payload.window_index ?? 0) + 1,
            processing_latency: 0,
            anomaly_detected: Number(payload.spoof_probability ?? 0) >= 0.5,
            message: payload.risk_level === 'CRITICAL'
              ? 'Persistent synthetic voice indicators detected.'
              : payload.risk_level === 'HIGH'
                ? 'Synthetic voice indicators detected.'
                : 'No significant synthetic voice indicators detected.',
          })
        }
      })
      const offError = detectionSocket.on('error', () => {
        if (!stoppingRef.current) {
          handleFatalError('backend-unavailable', 'Live detection backend is unavailable. Check that the FastAPI server is running on port 8000.')
        }
      })
      const offClose = detectionSocket.on('close', () => {
        if (!stoppingRef.current) {
          handleFatalError('connection-lost', 'The live detection connection was lost.')
        }
      })
      const offOpen = detectionSocket.on('open', () => {
        // Socket sends the start message itself after opening.
      })
      socketUnsubRef.current = [offMessage, offError, offClose, offOpen]
      detectionSocket.connect(newSessionId)

      try {
        const AudioContextCtor = window.AudioContext || window.webkitAudioContext
        if (!AudioContextCtor) throw new Error('Web Audio API is not supported in this browser')

        const audioContext = new AudioContextCtor()
        await audioContext.resume()
        const sourceNode = audioContext.createMediaStreamSource(stream)
        const processor = audioContext.createScriptProcessor(4096, 1, 1)

        processor.onaudioprocess = (event) => {
          if (stoppingRef.current) return
          const input = event.inputBuffer.getChannelData(0)
          const targetRate = 16000
          const inputRate = audioContext.sampleRate
          const ratio = inputRate / targetRate
          const outputLength = Math.max(1, Math.floor(input.length / ratio))
          const output = new Int16Array(outputLength)

          for (let i = 0; i < outputLength; i += 1) {
            const position = i * ratio
            const index = Math.floor(position)
            const next = Math.min(index + 1, input.length - 1)
            const fraction = position - index
            const sample = input[index] * (1 - fraction) + input[next] * fraction
            const clamped = Math.max(-1, Math.min(1, sample))
            output[i] = clamped < 0 ? clamped * 32768 : clamped * 32767
          }

          detectionSocket.sendBinary(output.buffer)
        }

        sourceNode.connect(processor)
        processor.connect(audioContext.destination)
        audioContextRef.current = audioContext
        audioSourceRef.current = sourceNode
        processorRef.current = processor
        setStatus('live')
      } catch (err) {
        handleFatalError('audio-capture-error', err?.message || 'Unable to capture microphone audio.')
        return
      }
    }

    tickRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1)
    }, 1000)
  }, [status, handleEvent, handleFatalError])

  const stopLive = useCallback(() => {
    if (status !== 'live' && status !== 'connecting') return
    stoppingRef.current = true

    detectionSocket.send({ type: 'stop' })
    cleanupEngine()
    cleanupMedia()

    const summary = buildSummary({
      sessionId,
      detectionHistory: historyRef.current,
      startedAt: startedAt ?? Date.now(),
      stoppedAt: Date.now(),
    })
    setFinalSummary(summary)
    setStatus('stopped')

    addHistoryEntry({
      type: 'live',
      sessionId,
      riskLevel: summary.finalRiskLevel,
      verdict: summary.finalVerdict,
      score: summary.finalRiskScore,
      detail: `${getRiskLabel(summary.finalRiskLevel)} · ${summary.eventCount} windows analyzed`,
    })
  }, [status, sessionId, startedAt, cleanupEngine, cleanupMedia])

  const dismissSummary = useCallback(() => {
    setFinalSummary(null)
    setStatus('idle')
    setSessionId(null)
    setStartedAt(null)
    setElapsedSeconds(0)
    setCurrentDetection(null)
    setDetectionHistory([])
  }, [])

  const clearError = useCallback(() => {
    setError(null)
    setStatus('idle')
    setElapsedSeconds(0)
  }, [])

  // Clean up media/engine/timers if the whole app unmounts (e.g. hot reload).
  useEffect(() => () => {
    cleanupEngine()
    cleanupMedia()
  }, [cleanupEngine, cleanupMedia])

  const value = useMemo(() => ({
    status,
    isLive: status === 'live' || status === 'connecting',
    sessionId,
    startedAt,
    elapsedSeconds,
    currentDetection,
    detectionHistory,
    error,
    finalSummary,
    startLive,
    stopLive,
    dismissSummary,
    clearError,
  }), [status, sessionId, startedAt, elapsedSeconds, currentDetection, detectionHistory, error, finalSummary, startLive, stopLive, dismissSummary, clearError])

  return (
    <LiveDetectionContext.Provider value={value}>
      {children}
    </LiveDetectionContext.Provider>
  )
}

export function useLiveDetection() {
  const ctx = useContext(LiveDetectionContext)
  if (!ctx) throw new Error('useLiveDetection must be used within a LiveDetectionProvider')
  return ctx
}

export default LiveDetectionContext

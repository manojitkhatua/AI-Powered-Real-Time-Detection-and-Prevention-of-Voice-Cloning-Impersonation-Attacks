import { useRef, useState } from 'react'
import { UploadCloud, FileAudio, X, Loader2, AlertTriangle } from 'lucide-react'
import { isMockMode } from '../config.js'
import detectionApi from '../services/api/detectionApi.js'
import analyzeAudioFileMock from '../services/mock/mockAnalysis.js'
import { addHistoryEntry } from '../services/history.js'
import { getRiskLabel } from '../services/riskPolicy.js'

const ACCEPTED_TYPES = ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3', 'audio/webm', 'audio/ogg']

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function isAcceptedFile(file) {
  if (ACCEPTED_TYPES.includes(file.type)) return true
  // Some browsers report an empty type for wav/mp3 — fall back to extension.
  return /\.(wav|mp3|ogg|m4a|webm)$/i.test(file.name)
}

/**
 * @param {{ onResult: (result: object) => void, disabled?: boolean }} props
 */
function UploadPanel({ onResult, disabled }) {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('idle') // idle | processing | success | error
  const [errorMessage, setErrorMessage] = useState(null)
  const inputRef = useRef(null)

  const handleFileChosen = (chosen) => {
    if (!chosen) return
    if (!isAcceptedFile(chosen)) {
      setStatus('error')
      setErrorMessage('Unsupported file type. Please upload a WAV or MP3 audio file.')
      return
    }
    setFile(chosen)
    setStatus('idle')
    setErrorMessage(null)
  }

  const handleInputChange = (e) => {
    handleFileChosen(e.target.files?.[0] ?? null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    if (disabled) return
    handleFileChosen(e.dataTransfer.files?.[0] ?? null)
  }

  const handleRemove = () => {
    setFile(null)
    setStatus('idle')
    setErrorMessage(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleAnalyze = async () => {
    if (!file || status === 'processing') return
    setStatus('processing')
    setErrorMessage(null)

    const { data, error } = isMockMode()
      ? await analyzeAudioFileMock(file)
      : await detectionApi.analyzeAudioFile(file)

    if (error || !data) {
      setStatus('error')
      setErrorMessage(
        isMockMode()
          ? 'Analysis failed unexpectedly. Please try again.'
          : 'Could not reach the detection backend. Switch to Demo Mode in Settings, or try again once the backend is available.'
      )
      return
    }

    setStatus('success')
    onResult(data)
    addHistoryEntry({
      type: 'upload',
      sessionId: data.session_id,
      riskLevel: data.risk_level,
      verdict: data.voice_status,
      score: data.risk_score,
      detail: `${file.name} · ${getRiskLabel(data.risk_level)}`,
    })
  }

  return (
    <section className="panel entry-panel" aria-labelledby="upload-panel-title">
      <div className="panel-header">
        <h2 className="panel-title" id="upload-panel-title">
          <UploadCloud size={15} strokeWidth={2.2} />
          Upload audio
        </h2>
      </div>

      {!file ? (
        <label
          className="upload-dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <UploadCloud size={26} strokeWidth={1.6} />
          <span className="upload-dropzone-title">Drag and drop an audio file</span>
          <span className="upload-dropzone-sub">or click to browse · WAV, MP3</span>
          <input
            ref={inputRef}
            type="file"
            accept="audio/wav,audio/mpeg,audio/mp3,.wav,.mp3,.ogg,.m4a"
            onChange={handleInputChange}
            disabled={disabled}
            hidden
          />
        </label>
      ) : (
        <div className="upload-file-row">
          <div className="upload-file-info">
            <FileAudio size={18} strokeWidth={1.8} />
            <div>
              <span className="upload-file-name">{file.name}</span>
              <span className="upload-file-meta">{formatFileSize(file.size)}</span>
            </div>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={handleRemove}
            aria-label="Remove selected file"
            disabled={status === 'processing'}
          >
            <X size={16} strokeWidth={2} />
          </button>
        </div>
      )}

      {status === 'error' && errorMessage && (
        <div className="inline-error">
          <AlertTriangle size={14} strokeWidth={2.2} />
          <span>{errorMessage}</span>
        </div>
      )}

      <button
        type="button"
        className="action-button action-button-primary"
        onClick={handleAnalyze}
        disabled={!file || status === 'processing' || disabled}
      >
        {status === 'processing' ? (
          <>
            <Loader2 size={15} strokeWidth={2.4} className="spin" />
            Analyzing audio…
          </>
        ) : (
          'Analyze Audio'
        )}
      </button>
    </section>
  )
}

export default UploadPanel

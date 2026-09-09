import { useEffect, useRef } from 'react'
import { PhoneCall, KeyRound, UserCheck2, Fingerprint, X } from 'lucide-react'

const OPTIONS = [
  { icon: PhoneCall, label: 'Verified callback', desc: 'Call the number on file for this contact.' },
  { icon: KeyRound, label: 'Safe phrase', desc: 'Ask for a pre-agreed verification phrase.' },
  { icon: UserCheck2, label: 'Known contact', desc: 'Confirm identity through a trusted third party.' },
  { icon: Fingerprint, label: 'Secondary authentication', desc: 'Require a second factor before proceeding.' },
]

function VerificationModal({ open, onClose, onConfirm }) {
  const dialogRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    dialogRef.current?.focus()
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="modal-overlay" role="presentation" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="verification-modal-title"
        ref={dialogRef}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="verification-modal-title">Identity verification required</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} strokeWidth={2} />
          </button>
        </div>

        <p className="modal-message">
          Voice characteristics indicate elevated spoofing risk. Verify the caller using an independent channel.
        </p>

        <div className="verification-options">
          {OPTIONS.map(({ icon: Icon, label, desc }) => (
            <div className="verification-option" key={label}>
              <Icon size={17} strokeWidth={2} />
              <div>
                <span className="verification-option-label">{label}</span>
                <p className="verification-option-desc">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="modal-footnote">
          Verification must be completed before continuing the session.
        </p>

        <div className="modal-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="button" className="btn-primary" onClick={onConfirm}>Start Verification</button>
        </div>
      </div>
    </div>
  )
}

export default VerificationModal

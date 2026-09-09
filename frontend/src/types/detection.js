/**
 * Detection object shape produced by the AI voice detection backend.
 *
 * This file documents the contract between the detection engine and the
 * frontend. It is plain JavaScript (JSDoc typedef) rather than TypeScript,
 * so it works without a build step but still gives editors inline hints.
 *
 * @typedef {'REAL' | 'SUSPICIOUS' | 'FAKE'} VoiceStatus
 * @typedef {'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'} RiskLevel
 * @typedef {'MONITOR' | 'WARNING' | 'VERIFY' | 'BLOCK'} SecurityAction
 *
 * @typedef {Object} DetectionEvent
 * @property {string} session_id            - Identifier for the active call/session, e.g. "CALL-001".
 * @property {VoiceStatus} voice_status      - Current authenticity classification of the voice.
 * @property {number} spoof_probability      - Model confidence that the voice is synthetic, 0–1.
 * @property {number} risk_score             - Aggregate risk score, 0–100.
 * @property {RiskLevel} risk_level          - Categorical risk bucket derived from risk_score.
 * @property {SecurityAction} action         - Recommended/enforced security action for this window.
 * @property {string} message                - Human-readable summary of the detection result.
 * @property {number} audio_window           - Length, in seconds, of the audio window analyzed.
 * @property {number} processing_latency     - End-to-end processing time in milliseconds.
 * @property {boolean} anomaly_detected      - Whether an anomaly region was flagged for this window.
 */

// This file intentionally exports nothing executable — it exists purely
// as a shared reference for the shape of detection data flowing through
// the mock stream, REST API, and WebSocket service.
export {}

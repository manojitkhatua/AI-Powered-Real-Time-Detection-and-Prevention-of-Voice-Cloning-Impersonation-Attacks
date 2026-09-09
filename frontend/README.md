# EchoVerify — Frontend

AI-powered voice security platform for real-time detection of synthetic, cloned, spoofed,
or impersonated voices.

EchoVerify's frontend is the human-in-the-loop security layer for a voice-cloning detection
platform. It turns detection output (voice authenticity, spoof probability, risk score,
recommended action) into an enterprise SOC-style dashboard an analyst can act on in real
time — whether the audio comes from an uploaded file or a live microphone session.

## Tech stack

- React 18 + React Router 6
- Vite
- JavaScript / JSX (no TypeScript)
- Plain CSS with a design-token system (no Tailwind)
- lucide-react for icons
- Native `MediaDevices`/`MediaRecorder`, `fetch`, and `WebSocket` for capture and backend integration

## How to run

```bash
npm install
npm run dev
```

Then open the printed local URL (defaults to `http://localhost:5173`).

Other scripts:

```bash
npm run build     # production build to dist/
npm run preview   # preview the production build locally
```

## Core flows

- **Upload Audio** (Dashboard) — pick or drop a WAV/MP3 file, click *Analyze Audio*, and get
  a full result: verdict, authenticity/spoof scores, confidence, risk level, and recommended
  action.
- **Live Detection** (Dashboard) — click *Start Live Detection* to request microphone access
  and begin continuous analysis. Results update live: risk score, spoof probability, session
  duration, detection events, and a risk timeline.
- **Detection continues across navigation** — live state lives in a React Context mounted
  above the router (`LiveDetectionProvider`), not inside the Dashboard page. Navigate to
  History or Settings and the session keeps running; a compact **global live bar** stays
  pinned near the top of every page with the current risk, duration, and a Stop button.
- **Stop Detection** — from the Dashboard or the global live bar — cleans up the microphone
  stream, closes any WebSocket connection, and shows a final session summary (verdict, scores,
  duration, notable events, recommended action). The session is also saved to History.
- **History** — a simple local log of upload and live sessions (stored in `localStorage`),
  grouped by day.

## Architecture overview

```
src/
├── components/
│   ├── layout/AppLayout.jsx     shell: Header + GlobalLiveBar + page content
│   ├── GlobalLiveBar.jsx        persistent "live detection active" bar, shown on every page
│   ├── UploadPanel.jsx          file picker/dropzone + Analyze Audio flow
│   ├── LiveEntryPanel.jsx       Start Live Detection entry point + mic error states
│   ├── SessionSummaryModal.jsx  final summary shown after Stop Detection
│   └── ...                      detection-result panels (RiskBanner, VoiceStatusCard,
│                                 RiskScoreCard, SecurityAction, RiskTimeline, SaliencyMap,
│                                 UltraShortAnalysis, DetectionEvents, VerificationModal,
│                                 BlockedScreen, CallerPanel) — shared by both upload and
│                                 live results, so both flows render identically
├── context/
│   └── LiveDetectionContext.jsx  global live-session state: mic stream, engine, timers,
│                                  current/history detection data, error + summary state
├── pages/
│   ├── Dashboard.jsx  entry points + results (upload or live, whichever is active)
│   ├── History.jsx    local session history
│   └── Settings.jsx   mock/real mode toggle + backend URL info
├── services/
│   ├── api/detectionApi.js           REST integration layer (placeholder endpoints)
│   ├── websocket/detectionSocket.js  reusable WebSocket client (not auto-connected)
│   ├── mock/mockAnalysis.js          deterministic mock "Analyze Audio" result
│   ├── mock/liveMockEngine.js        realistic simulated live detection stream
│   ├── history.js                    localStorage-backed session history + pub/sub
│   └── riskPolicy.js                 single source of truth for risk → label/color/action
├── config.js            central mock/real mode + backend URL configuration
└── types/detection.js   JSDoc typedef documenting the detection object shape
```

Every result-display component reads the same detection object shape and the same
`riskPolicy.js`, regardless of whether the data came from an uploaded file, the mock engine,
or a real backend — so switching data sources never requires rewriting UI.

## Mock/Demo mode vs real backend

EchoVerify defaults to **Demo/Mock Mode**, so the full workflow (upload analysis, live
detection, risk timeline, session summary, history) works out of the box with no backend —
important for a reliable SIH demo.

- Toggle it at runtime from **Settings** in the app, or
- Set `VITE_USE_MOCK_MODE=false` in `.env` to default to Real Backend Mode.

In Real Backend Mode:
- `UploadPanel` calls `detectionApi.analyzeAudioFile(file)` (`POST /detections/analyze-file`).
- Live detection opens `detectionSocket` (WebSocket) to receive pushed results, and streams
  captured microphone chunks via `detectionApi.sendAudioForDetection()` (REST fallback) —
  see `src/services/websocket/detectionSocket.js` and `src/services/api/detectionApi.js`.
- No real endpoint paths are assumed; the backend team should fill in the actual routes and
  response shape (see `src/types/detection.js` for the expected contract). If the backend is
  unreachable, the UI shows a clear "backend unavailable" error and suggests switching back
  to Demo Mode — it never crashes or hangs.

### Environment variables

Copy `.env.example` to `.env` and set:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/detection
VITE_USE_MOCK_MODE=true
```

## Live detection integration, at a high level

1. `LiveDetectionProvider` (mounted once in `main.jsx`, above the router) owns all live
   session state — it never unmounts on navigation.
2. `startLive()` requests microphone permission via `getUserMedia`, then either:
   - starts `liveMockEngine` (Demo Mode) — a bounded random walk producing a realistic event
     every ~1.8s, or
   - connects `detectionSocket` and starts a `MediaRecorder` that periodically posts captured
     audio chunks to the backend (Real Backend Mode).
3. Every incoming detection event updates `currentDetection` and appends to
   `detectionHistory` — read by the Dashboard's result panels and by `GlobalLiveBar`.
4. `stopLive()` stops the recorder/engine, releases the microphone (`track.stop()`), closes
   the WebSocket if open, builds a final summary, saves it to History, and clears the active
   session.

Visualizations such as the spectro-temporal saliency map and the waveform are **frontend
representations** of what a detection model would report — they do not run any ML model
themselves.

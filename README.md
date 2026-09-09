# EchoVerify

### AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks

**SIH26104 — Smart India Hackathon 2026**

EchoVerify is an AI-powered voice security system designed to detect potential voice-cloning and synthetic-voice impersonation attacks during voice communication. It continuously analyzes audio, estimates the probability that a voice is synthetic, maintains a temporal risk score, and recommends or triggers security actions based on persistent suspicious behavior.

---

## 1. Problem Statement

### SIH26104

**AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks**

Voice-cloning technology can generate highly realistic speech that may be used to impersonate trusted individuals. Traditional security systems that rely only on caller identity or static authentication can therefore be bypassed.

EchoVerify addresses this problem by analyzing the voice itself and continuously evaluating whether the incoming speech contains characteristics associated with synthetic or cloned audio.

---

## 2. Solution

EchoVerify follows a continuous detection pipeline:

```text
Audio Input
     ↓
Audio Preprocessing
     ↓
2-Second Overlapping Windows
     ↓
MFCC Feature Extraction
     ↓
Temporal Feature Statistics
     ↓
PyTorch MLP Classifier
     ↓
Spoof Probability
     ↓
Temporal Risk Engine
     ↓
Risk Level + Security Action
```

The system does not make a decision from a single audio segment alone. Multiple consecutive predictions are combined by the temporal risk engine to identify persistent suspicious behavior.

---

## 3. Key Features

- Real-time voice analysis
- Voice-cloning / spoof detection
- MFCC-based audio feature extraction
- PyTorch neural-network classifier
- 2-second overlapping analysis windows
- Temporal risk scoring
- Risk levels: LOW, MEDIUM, HIGH, CRITICAL
- Security actions: MONITOR, WARNING, VERIFY, BLOCK
- REST API for uploaded audio
- WebSocket API for live audio
- Live detection timeline
- Window-by-window spoof probability
- Session-based detection
- Frontend dashboard for monitoring
- Known real/fake audio testing
- Unseen voice testing support

---

## 4. Current AI Model

The current prototype uses:

**MFCC + Temporal Statistics + PyTorch MLP**

### Audio Processing

```text
Sample Rate: 16 kHz
Channel: Mono
Analysis Window: 2 seconds
Hop: 1 second
```

This creates overlapping windows so the system can continuously monitor the voice.

### Feature Extraction

For each 2-second window, 20 MFCC coefficients are calculated.

For every MFCC coefficient, the following statistics are extracted:

```text
Mean
Standard Deviation
Minimum
Maximum
```

Therefore:

```text
20 MFCCs × 4 statistics = 80 features
```

### Neural Network

```text
80 input features
      ↓
Linear(80 → 128)
      ↓
ReLU
      ↓
Linear(128 → 64)
      ↓
ReLU
      ↓
Linear(64 → 1)
      ↓
Spoof Probability
```

The model contains approximately **18,689 trainable parameters**.

---

## 5. Temporal Risk Engine

The model produces a spoof probability for every audio window.

Instead of treating every prediction independently, EchoVerify maintains a temporal risk score.

```text
Current Model Probability
          +
Smoothed Probability
          +
Suspicious Persistence
          ↓
     Risk Score
```

Persistent suspicious predictions increase the risk score, while the persistence component decays when suspicious behavior is no longer observed.

### Risk Levels

| Risk Score | Risk Level | Action |
|---:|---|---|
| 0–30 | LOW | MONITOR |
| 31–60 | MEDIUM | WARNING |
| 61–85 | HIGH | VERIFY |
| 86–100 | CRITICAL | BLOCK |

These thresholds are prototype security-policy thresholds, not scientifically calibrated probabilities.

---

## 6. Backend

The backend is implemented using **Python, FastAPI and PyTorch**.

### Backend Structure

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── websocket.py
│   │
│   ├── audio/
│   │   ├── features.py
│   │   ├── features_temporal.py
│   │   ├── ingest.py
│   │   ├── prepare_temporal_data.py
│   │   ├── preprocessor.py
│   │   ├── speaker_split.py
│   │   ├── training_data.py
│   │   ├── validator.py
│   │   └── windowing.py
│   │
│   ├── models/
│   │   ├── evaluate.py
│   │   ├── inference.py
│   │   ├── mlp.py
│   │   ├── mlp_temporal.py
│   │   ├── train.py
│   │   └── train_temporal.py
│   │
│   ├── risk/
│   │   ├── risk_engine.py
│   │   └── test_pipeline.py
│   │
│   └── security/
│
├── tests/
├── requirements.txt
├── requirements-lock.txt
└── test_websocket.py
```

---

## 7. API

### Health Check

```http
GET /api/health
```

Example response:

```json
{
  "service": "EchoVerify Backend",
  "status": "online"
}
```

### Audio Analysis

```http
POST /api/analyze
```

Upload an audio file using the form field:

```text
audio
```

Supported formats:

```text
.wav
.mp3
.m4a
.flac
.ogg
```

Example response:

```json
{
  "session_id": "CALL-...",
  "filename": "voice.wav",
  "windows_analyzed": 599,
  "spoof_probability": 0.9869,
  "risk_score": 99.99,
  "risk_level": "CRITICAL",
  "action": "BLOCK",
  "voice_status": "SUSPICIOUS",
  "message": "Persistent synthetic voice indicators detected."
}
```

---

## 8. Real-Time WebSocket

EchoVerify also supports continuous audio streaming.

```text
ws://127.0.0.1:8000/ws/{session_id}
```

The frontend sends:

```text
PCM16
Mono
16 kHz
```

Audio is processed in overlapping 2-second windows with a 1-second hop.

A detection event contains information such as:

```json
{
  "type": "detection",
  "session_id": "CALL-...",
  "window_index": 0,
  "window_id": "...",
  "spoof_probability": 1.0,
  "voice_status": "FAKE",
  "risk_score": 84.0,
  "risk_level": "HIGH",
  "action": "VERIFY"
}
```

At the end of the session:

```json
{
  "type": "final",
  "session_id": "CALL-...",
  "status": "COMPLETED",
  "windows_analyzed": 1,
  "message": "Detection session completed."
}
```

---

## 9. Frontend

The frontend provides a dashboard for interacting with the detection system.

It supports:

- Audio upload
- Live microphone detection
- Caller monitoring
- Risk-level display
- Spoof probability visualization
- Detection timeline
- Window-by-window analysis
- Session status
- Security action display

The frontend communicates with the backend through:

```text
REST API
+
WebSocket
```

For live microphone detection, the browser converts microphone audio into **mono 16 kHz PCM16** before sending it to the WebSocket backend.

---

## 10. Project Structure

```text
EchoVerify/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── requirements-lock.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── raw/
│   │   └── AUDIO/
│   │       ├── REAL/
│   │       └── FAKE/
│   │
│   └── processed/
│
├── models/
│   ├── voice_antispoof_temporal_mlp.pt
│   └── temporal_mfcc_scaler.joblib
│
└── README.md
```

---

## 11. Dataset

The prototype was trained and evaluated using a voice anti-spoofing dataset containing real recordings and generated/converted fake recordings.

The available dataset contains recordings associated with:

```text
biden
linus
margot
musk
obama
ryan
taylor
trump
```

The prototype uses a **speaker-independent split**.

### Training speakers

```text
biden
linus
margot
musk
obama
ryan
```

### Validation speakers

```text
taylor
trump
```

Cross-partition fake recordings are excluded to reduce speaker leakage between training and validation.

---

## 12. Model Performance

The current temporal MLP achieved the following validation results at the selected threshold:

| Metric | Result |
|---|---:|
| Accuracy / Balanced Accuracy | 0.7788 |
| Precision | 0.7376 |
| Recall | 0.8656 |
| Specificity | 0.6920 |
| F1 Score | 0.7965 |
| ROC-AUC | 0.8620 |

Confusion matrix:

```text
                 Predicted
               Real    Fake

Actual Real     829     369
Actual Fake     161    1037
```

These results demonstrate the feasibility of the prototype, but they should not be interpreted as proof of production-level generalization.

---

## 13. Testing

The system has been tested using both known dataset recordings and unseen recordings.

### Fake voice

```text
biden-to-linus.wav
```

Observed result:

```text
Mean spoof probability: 0.9869
Fake windows: 573 / 599
Final classification: FAKE
```

### Real voice

```text
biden-original.wav
```

Observed result:

```text
Mean spoof probability: 0.0166
Fake windows: 1 / 599
Final classification: REAL
```

Additional testing can be performed using a newly recorded human voice that was not part of the training dataset.

---

## 14. Installation

### Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 15. Frontend Setup

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

The Vite development server proxies:

```text
/api → http://127.0.0.1:8000
/ws  → ws://127.0.0.1:8000
```

---

## 16. Running the Complete System

Start the backend first:

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Then start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Then either:

1. Upload a supported audio file, or
2. Start live microphone detection.

---

## 17. Security Decision Flow

```text
                 Voice Input
                     │
                     ▼
              Audio Analysis
                     │
                     ▼
             Spoof Probability
                     │
                     ▼
             Temporal Smoothing
                     │
                     ▼
           Persistence Evaluation
                     │
                     ▼
                Risk Score
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      LOW         MEDIUM        HIGH
    MONITOR       WARNING       VERIFY
                                   │
                                   ▼
                               CRITICAL
                                 BLOCK
```

The goal is to prevent a security decision from depending solely on one noisy prediction.

---

## 18. Why Temporal Analysis?

A cloned voice may not produce an identical model output in every short segment.

Therefore, EchoVerify analyzes consecutive overlapping windows.

```text
Window 1 → 0.91
Window 2 → 0.94
Window 3 → 0.96
Window 4 → 0.97
Window 5 → 0.95
```

Persistent high probabilities provide stronger evidence than one isolated spike.

This allows the system to move from simple classification toward **continuous voice-risk monitoring**.

---

## 19. Limitations

The current implementation is a **working prototype**, not a production-grade telecom security system.

Important limitations include:

- Limited dataset size and speaker diversity
- Current model is based primarily on MFCC features
- Model performance may change on unseen recording conditions
- Background noise and microphones can affect predictions
- Thresholds are prototype policy thresholds
- No production telecom/SIP integration
- No advanced speaker verification system
- No cryptographic caller authentication
- Real-time browser audio depends on microphone and browser behavior
- The current prototype does not implement the complete research architecture described in the broader design

Therefore, the system should be presented as a **prototype demonstrating real-time AI-based voice spoof detection and risk-based prevention**.

---

## 20. Future Scope

### Advanced AI

- CNN/RNN or Transformer-based temporal modeling
- Raw waveform models
- Spectrogram-based analysis
- Self-supervised speech representations
- Ensemble anti-spoofing models
- Better cross-dataset evaluation

### Security

- Speaker verification
- Caller identity verification
- Trusted-contact verification
- Challenge-response authentication
- Call termination or quarantine integration
- SIP/VoIP integration

### Production Deployment

- Cloud inference
- GPU/CPU optimized inference
- Scalable WebSocket sessions
- Monitoring and logging
- Model drift detection
- Continuous retraining

### Explainability

- Temporal anomaly visualization
- Feature-level explanations
- Segment-level evidence
- Confidence calibration

---

## 21. Research-to-Prototype Mapping

The broader research design explores advanced components such as continuous monitoring, temporal analysis, spoof detection, risk scoring and prevention.

The current prototype implements the most practical subset:

| Research Concept | Current Prototype |
|---|---|
| Continuous analysis | WebSocket streaming |
| Temporal analysis | Overlapping windows |
| Voice features | MFCC |
| AI spoof detection | PyTorch MLP |
| Temporal decision | Risk Engine |
| Risk classification | LOW → CRITICAL |
| Prevention | VERIFY / BLOCK |
| Dashboard | React frontend |

Advanced research components can be integrated in later versions.

---

## 22. Technology Stack

### Backend

```text
Python
FastAPI
PyTorch
NumPy
Librosa
Scikit-learn
Joblib
Uvicorn
```

### Frontend

```text
React
Vite
JavaScript
Web Audio API
WebSocket
CSS
```

### AI

```text
MFCC
Temporal Feature Statistics
PyTorch MLP
Temporal Risk Engine
```

---

## 23. Demo Flow

```text
1. Open EchoVerify dashboard
          ↓
2. Start a detection session
          ↓
3. Upload or stream a voice
          ↓
4. Audio is divided into overlapping windows
          ↓
5. MFCC features are extracted
          ↓
6. MLP predicts spoof probability
          ↓
7. Temporal engine calculates risk
          ↓
8. Dashboard updates in real time
          ↓
9. Security action is displayed
          ↓
10. System recommends VERIFY or BLOCK
```

---

## 24. Project Objective

EchoVerify demonstrates how **AI-based voice analysis can be combined with temporal reasoning and security policies** to detect and respond to voice-cloning impersonation attacks in real time.

> **Don't trust a voice because it sounds real. Continuously verify its behavior.**

---

## License

This project is developed as a prototype for **Smart India Hackathon 2026** under problem statement **SIH26104**.

import json
import uuid

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.models.inference import predict_audio_window
from backend.app.risk.risk_engine import TemporalRiskEngine


router = APIRouter()


# ============================================================
# Configuration
# ============================================================

SAMPLE_RATE = 16000

# 2-second analysis window
WINDOW_SAMPLES = SAMPLE_RATE * 2

# 1-second hop = 50% overlap
HOP_SAMPLES = SAMPLE_RATE


# ============================================================
# WebSocket Detection
# ============================================================

@router.websocket("/ws/{session_id}")
async def websocket_detection(
    websocket: WebSocket,
    session_id: str,
):
    await websocket.accept()

    risk_engine = TemporalRiskEngine()

    # Audio buffer for incoming PCM16 data
    audio_buffer = np.array(
        [],
        dtype=np.float32,
    )

    window_index = 0

    try:

        # ------------------------------------------------------
        # Connection
        # ------------------------------------------------------

        await websocket.send_json(
            {
                "type": "connection",
                "session_id": session_id,
                "status": "CONNECTED",
                "message": "Voice detection session started.",
            }
        )

        # ------------------------------------------------------
        # Receive messages
        # ------------------------------------------------------

        while True:

            message = await websocket.receive()

            # ==================================================
            # TEXT MESSAGE
            # ==================================================

            if "text" in message:

                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                message_type = data.get("type")

                # ------------------------------------------------
                # START
                # ------------------------------------------------

                if message_type == "start":

                    await websocket.send_json(
                        {
                            "type": "status",
                            "session_id": session_id,
                            "status": "ANALYZING",
                        }
                    )

                # ------------------------------------------------
                # STOP
                # ------------------------------------------------

                elif message_type == "stop":

                    await websocket.send_json(
                        {
                            "type": "final",
                            "session_id": session_id,
                            "status": "COMPLETED",
                            "windows_analyzed": window_index,
                            "message": (
                                "Detection session completed."
                            ),
                        }
                    )

                    break

                continue

            # ==================================================
            # BINARY AUDIO DATA
            # ==================================================

            if "bytes" in message:

                audio_bytes = message["bytes"]

                if not audio_bytes:
                    continue

                # ------------------------------------------------
                # Convert PCM16 → float32
                # ------------------------------------------------

                chunk = np.frombuffer(
                    audio_bytes,
                    dtype=np.int16,
                ).astype(np.float32)

                chunk /= 32768.0

                # ------------------------------------------------
                # Add chunk to buffer
                # ------------------------------------------------

                audio_buffer = np.concatenate(
                    [
                        audio_buffer,
                        chunk,
                    ]
                )

                # ------------------------------------------------
                # Process every available 2-second window
                # ------------------------------------------------

                while len(audio_buffer) >= WINDOW_SAMPLES:

                    window = audio_buffer[
                        :WINDOW_SAMPLES
                    ]

                    # ============================================
                    # MODEL B
                    # ============================================

                    spoof_probability, voice_status = (
                        predict_audio_window(
                            window,
                            sample_rate=SAMPLE_RATE,
                        )
                    )

                    # ============================================
                    # TEMPORAL RISK ENGINE
                    # ============================================

                    risk_result = risk_engine.update(
                        spoof_probability
                    )

                    # ============================================
                    # SEND LIVE RESULT
                    # ============================================

                    await websocket.send_json(
                        {
                            "type": "detection",
                            "session_id": session_id,
                            "window_index": window_index,
                            "window_id": str(uuid.uuid4()),
                            "spoof_probability": round(
                                float(
                                    spoof_probability
                                ),
                                4,
                            ),
                            "voice_status": voice_status,
                            "risk_score": round(
                                float(
                                    risk_result.risk_score
                                ),
                                2,
                            ),
                            "risk_level": (
                                risk_result.risk_level
                            ),
                            "action": risk_result.action,
                        }
                    )

                    window_index += 1

                    # ------------------------------------------------
                    # Move forward by 1 second.
                    # This creates 1-second overlap.
                    # ------------------------------------------------

                    audio_buffer = audio_buffer[
                        HOP_SAMPLES:
                    ]

    except WebSocketDisconnect:

        print(
            f"WebSocket disconnected: {session_id}"
        )

    except Exception as exc:

        print(
            f"WebSocket error "
            f"[{session_id}]: {exc}"
        )

        try:

            await websocket.send_json(
                {
                    "type": "error",
                    "session_id": session_id,
                    "message": str(exc),
                }
            )

        except Exception:
            pass
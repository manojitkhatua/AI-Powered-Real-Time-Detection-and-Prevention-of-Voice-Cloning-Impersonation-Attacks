import asyncio
import json
from pathlib import Path

import numpy as np
import websockets


PROJECT_ROOT = Path(__file__).resolve().parent

AUDIO_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "AUDIO"
    / "FAKE"
    / "biden-to-linus.wav"
)

WS_URL = "ws://127.0.0.1:8000/ws/CALL-FAKE-001"


async def test_websocket():

    print("=" * 60)
    print("EchoVerify WebSocket Audio Test")
    print("=" * 60)

    print(f"\nAudio: {AUDIO_FILE}")

    if not AUDIO_FILE.exists():
        print("\nERROR: Audio file not found.")
        return

    # ----------------------------------------------------------
    # Read WAV file
    # ----------------------------------------------------------

    import soundfile as sf

    audio, sample_rate = sf.read(
        str(AUDIO_FILE),
        dtype="float32",
    )

    # Convert stereo → mono
    if audio.ndim > 1:
        audio = np.mean(
            audio,
            axis=1,
        )

    print(f"Sample rate: {sample_rate}")
    print(f"Samples: {len(audio)}")
    print(f"Duration: {len(audio) / sample_rate:.2f}s")

    # ----------------------------------------------------------
    # Convert float32 → PCM16
    # ----------------------------------------------------------

    audio = np.clip(
        audio,
        -1.0,
        1.0,
    )

    audio_pcm16 = (
        audio * 32767
    ).astype(
        np.int16
    )

    # ----------------------------------------------------------
    # Connect
    # ----------------------------------------------------------

    async with websockets.connect(
        WS_URL,
        proxy=None,
    ) as websocket:

        response = await websocket.recv()

        print("\nCONNECTION:")
        print(
            json.dumps(
                json.loads(response),
                indent=2,
            )
        )

        # ------------------------------------------------------
        # Start
        # ------------------------------------------------------

        await websocket.send(
            json.dumps(
                {
                    "type": "start"
                }
            )
        )

        response = await websocket.recv()

        print("\nSTATUS:")
        print(
            json.dumps(
                json.loads(response),
                indent=2,
            )
        )

        # ------------------------------------------------------
        # Send audio in chunks
        # ------------------------------------------------------

        chunk_size = 3200  # 200 ms @ 16 kHz

        total_chunks = (
            len(audio_pcm16)
            + chunk_size
            - 1
        ) // chunk_size

        print(
            f"\nSending {total_chunks} "
            "audio chunks..."
        )

        detection_count = 0

        for start in range(
            0,
            len(audio_pcm16),
            chunk_size,
        ):

            chunk = audio_pcm16[
                start:start + chunk_size
            ]

            await websocket.send(
                chunk.tobytes()
            )

            # --------------------------------------------------
            # Check if backend has produced a result.
            # --------------------------------------------------

            try:

                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=0.05,
                )

                result = json.loads(
                    response
                )

                if result.get("type") == "detection":

                    detection_count += 1

                    print(
                        f"\nWINDOW "
                        f"{result['window_index']:03d} | "
                        f"Probability: "
                        f"{result['spoof_probability']:.4f} | "
                        f"Risk: "
                        f"{result['risk_score']:.2f} | "
                        f"{result['risk_level']} | "
                        f"{result['action']}"
                    )

            except asyncio.TimeoutError:
                pass

        # ------------------------------------------------------
        # Stop
        # ------------------------------------------------------

        await websocket.send(
            json.dumps(
                {
                    "type": "stop"
                }
            )
        )

        # Receive remaining messages
        while True:

            try:
                response = await asyncio.wait_for(websocket.recv(),timeout=1.0,)

                result = json.loads(response)

                print("\nSERVER:")

                print(
                    json.dumps(result,indent=2,))

                if result.get("type") == "final":
                    break

            except asyncio.TimeoutError:
                break

        print(
            f"\nTotal detection windows: "
            f"{detection_count}"
        )


if __name__ == "__main__":
    asyncio.run(
        test_websocket()
    )
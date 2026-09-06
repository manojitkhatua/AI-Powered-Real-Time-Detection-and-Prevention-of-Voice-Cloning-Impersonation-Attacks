import numpy as np


TARGET_SAMPLE_RATE = 16000
WINDOW_SECONDS = 2
HOP_SECONDS = 1


def create_audio_windows(
    audio: np.ndarray,
    sample_rate: int = TARGET_SAMPLE_RATE,
    window_seconds: int = WINDOW_SECONDS,
    hop_seconds: int = HOP_SECONDS,
):
    """
    Split continuous audio into overlapping windows.

    Default:
    - Window size: 2 seconds
    - Hop size: 1 second
    - Overlap: 1 second
    """

    window_size = int(sample_rate * window_seconds)
    hop_size = int(sample_rate * hop_seconds)

    if len(audio) < window_size:
        return [audio]

    windows = []

    for start in range(0, len(audio) - window_size + 1, hop_size):
        end = start + window_size
        window = audio[start:end]
        windows.append(window)

    return windows
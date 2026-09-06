import numpy as np
import librosa


TARGET_SAMPLE_RATE = 16000


def load_and_preprocess_audio(
    file_path: str,
    target_sr: int = TARGET_SAMPLE_RATE
) -> np.ndarray:
    """
    Load an audio file and prepare it for the voice anti-spoofing model.

    Steps:
    1. Load audio
    2. Convert to mono
    3. Resample to 16 kHz
    4. Normalize amplitude
    """

    audio, sample_rate = librosa.load(
        file_path,
        sr=target_sr,
        mono=True
    )

    audio = audio.astype(np.float32)

    # Normalize amplitude
    max_amplitude = np.max(np.abs(audio))

    if max_amplitude > 0:
        audio = audio / max_amplitude

    return audio
import numpy as np
import librosa


TARGET_SAMPLE_RATE = 16000
N_MFCC = 20
N_FFT = 512
HOP_LENGTH = 256


def extract_mfcc(
    audio: np.ndarray,
    sample_rate: int = TARGET_SAMPLE_RATE,
    n_mfcc: int = N_MFCC,
    n_fft: int = N_FFT,
    hop_length: int = HOP_LENGTH,
) -> np.ndarray:
    """
    Extract MFCC features from a preprocessed audio window.

    Returns:
        np.ndarray of shape:
        (n_mfcc, time_frames)
    """

    if audio is None or len(audio) == 0:
        raise ValueError("Audio input is empty.")

    if sample_rate <= 0:
        raise ValueError("Sample rate must be greater than zero.")

    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sample_rate,
        n_mfcc=n_mfcc,
        n_fft=n_fft,
        hop_length=hop_length,
    )

    return mfcc.astype(np.float32)


def prepare_mfcc_for_mlp(mfcc: np.ndarray) -> np.ndarray:
    """
    Convert MFCC matrix into a fixed-length feature vector
    suitable for the MLP.

    Input:
        (n_mfcc, time_frames)

    Output:
        (n_mfcc,)
    """

    if mfcc.ndim != 2:
        raise ValueError(
            f"Expected 2D MFCC matrix, got shape {mfcc.shape}"
        )

    # Mean pooling over time.
    feature_vector = np.mean(mfcc, axis=1)

    return feature_vector.astype(np.float32)
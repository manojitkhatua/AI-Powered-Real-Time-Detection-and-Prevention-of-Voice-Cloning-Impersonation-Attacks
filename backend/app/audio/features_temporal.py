import numpy as np


def prepare_mfcc_temporal_features(
    mfcc: np.ndarray,
) -> np.ndarray:
    """
    Convert MFCC matrix (n_mfcc, time_frames)
    into a fixed-size temporal-statistics vector.

    For each MFCC coefficient:
        mean
        std
        min
        max

    20 MFCCs -> 80 features.
    """

    if mfcc.ndim != 2:
        raise ValueError(
            f"Expected 2D MFCC matrix, got {mfcc.shape}"
        )

    mean = np.mean(mfcc, axis=1)
    std = np.std(mfcc, axis=1)
    minimum = np.min(mfcc, axis=1)
    maximum = np.max(mfcc, axis=1)

    features = np.concatenate(
        [mean, std, minimum, maximum]
    )

    return features.astype(np.float32)
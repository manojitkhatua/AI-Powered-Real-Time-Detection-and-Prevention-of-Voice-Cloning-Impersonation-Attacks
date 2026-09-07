from pathlib import Path
import sys

import joblib
import numpy as np
import torch


# ============================================================
# Project root
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Project imports
# ============================================================

from backend.app.audio.preprocessor import (
    load_and_preprocess_audio,
)

from backend.app.audio.windowing import (
    create_audio_windows,
)

from backend.app.audio.features import (
    extract_mfcc,
)

from backend.app.audio.features_temporal import (
    prepare_mfcc_temporal_features,
)

from backend.app.models.mlp_temporal import (
    VoiceAntiSpoofTemporalMLP,
)


# ============================================================
# Paths
# ============================================================

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "voice_antispoof_temporal_mlp.pt"
)

SCALER_PATH = (
    PROJECT_ROOT
    / "models"
    / "temporal_mfcc_scaler.joblib"
)


# ============================================================
# Device
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# Load model
# ============================================================

def load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found:\n{MODEL_PATH}"
        )

    if not SCALER_PATH.exists():
        raise FileNotFoundError(
            f"Scaler not found:\n{SCALER_PATH}"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=False,
    )

    model = VoiceAntiSpoofTemporalMLP(
        input_size=checkpoint.get(
            "input_size",
            80,
        )
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(DEVICE)
    model.eval()

    scaler = joblib.load(
        SCALER_PATH
    )

    threshold = float(
        checkpoint.get(
            "best_threshold",
            0.50,
        )
    )

    return (
        model,
        scaler,
        threshold,
    )


# ============================================================
# Load once
# ============================================================

MODEL, SCALER, MODEL_THRESHOLD = (
    load_model()
)


# ============================================================
# Predict one feature vector
# ============================================================

def predict_feature_vector(
    feature_vector: np.ndarray,
):
    """
    Run Model B on one 80-dimensional feature vector.

    Returns:
        spoof_probability: float
        voice_status: str
    """

    if feature_vector.shape != (80,):
        raise ValueError(
            "Expected feature vector shape "
            f"(80,), got {feature_vector.shape}"
        )

    # --------------------------------------------------------
    # Apply the exact scaler used during training.
    # --------------------------------------------------------

    scaled = SCALER.transform(
        feature_vector.reshape(1, -1)
    ).astype(
        np.float32
    )

    tensor = torch.from_numpy(
        scaled
    ).to(
        DEVICE
    )

    # --------------------------------------------------------
    # Model inference
    # --------------------------------------------------------

    with torch.no_grad():

        logit = MODEL(
            tensor
        ).squeeze()

        probability = torch.sigmoid(
            logit
        ).item()

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if probability >= MODEL_THRESHOLD:

        status = "FAKE"

    else:

        status = "REAL"

    return (
        float(probability),
        status,
    )


# ============================================================
# Predict one audio window
# ============================================================

def predict_audio_window(
    audio_window: np.ndarray,
    sample_rate: int = 16000,
):
    """
    Run complete Model B inference on
    one preprocessed audio window.
    """

    mfcc = extract_mfcc(
        audio_window,
        sample_rate=sample_rate,
    )

    feature_vector = (
        prepare_mfcc_temporal_features(
            mfcc
        )
    )

    return predict_feature_vector(
        feature_vector
    )


# ============================================================
# Predict an entire audio file
# ============================================================

def predict_audio_file(
    file_path: str,
):
    """
    Analyze all 2-second overlapping windows
    in an audio file.

    Returns one prediction per window.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"Audio file not found:\n{path}"
        )

    # --------------------------------------------------------
    # Preprocess
    # --------------------------------------------------------

    audio = load_and_preprocess_audio(
        str(path)
    )

    # --------------------------------------------------------
    # Create windows
    # --------------------------------------------------------

    windows = create_audio_windows(
        audio
    )

    results = []

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    for index, window in enumerate(
        windows
    ):

        probability, status = (
            predict_audio_window(
                window
            )
        )

        results.append(
            {
                "window_index": index,
                "spoof_probability": probability,
                "voice_status": status,
            }
        )

    return results


# ============================================================
# File-level summary
# ============================================================

def summarize_predictions(
    predictions,
):
    """
    Convert window-level predictions into
    a simple file-level summary.

    Uses the mean spoof probability across
    all analyzed windows.
    """

    if not predictions:

        raise ValueError(
            "No predictions available."
        )

    probabilities = np.asarray(
        [
            item["spoof_probability"]
            for item in predictions
        ],
        dtype=np.float32,
    )

    mean_probability = float(
        np.mean(probabilities)
    )

    max_probability = float(
        np.max(probabilities)
    )

    fake_windows = int(
        np.sum(
            probabilities
            >= MODEL_THRESHOLD
        )
    )

    total_windows = len(
        probabilities
    )

    fake_ratio = (
        fake_windows
        /
        total_windows
    )

    # --------------------------------------------------------
    # File-level decision
    #
    # We use the average probability as the
    # primary file-level signal.
    # --------------------------------------------------------

    if mean_probability >= MODEL_THRESHOLD:

        file_status = "FAKE"

    else:

        file_status = "REAL"

    return {
        "mean_spoof_probability":
            mean_probability,

        "max_spoof_probability":
            max_probability,

        "fake_windows":
            fake_windows,

        "total_windows":
            total_windows,

        "fake_window_ratio":
            float(fake_ratio),

        "voice_status":
            file_status,
    }


# ============================================================
# Main test
# ============================================================

if __name__ == "__main__":

    TEST_AUDIO = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "AUDIO"
    / "REAL"
    / "biden-original.wav"
    )

    print("=" * 60)
    print("EchoVerify - Model B Inference Test")
    print("=" * 60)

    print(
        f"Device: {DEVICE}"
    )

    if torch.cuda.is_available():

        print(
            f"GPU: "
            f"{torch.cuda.get_device_name(0)}"
        )

    print(
        f"Model threshold: "
        f"{MODEL_THRESHOLD:.2f}"
    )

    print()
    print(
        f"Testing audio:\n{TEST_AUDIO}"
    )

    # --------------------------------------------------------
    # Run inference
    # --------------------------------------------------------

    predictions = predict_audio_file(
        str(TEST_AUDIO)
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = summarize_predictions(
        predictions
    )

    print()
    print("=" * 60)
    print("INFERENCE RESULT")
    print("=" * 60)

    print(
        f"Total windows: "
        f"{summary['total_windows']}"
    )

    print(
        f"Mean spoof probability: "
        f"{summary['mean_spoof_probability']:.4f}"
    )

    print(
        f"Maximum spoof probability: "
        f"{summary['max_spoof_probability']:.4f}"
    )

    print(
        f"FAKE windows: "
        f"{summary['fake_windows']}"
    )

    print(
        f"FAKE window ratio: "
        f"{summary['fake_window_ratio']:.4f}"
    )

    print(
        f"Final voice status: "
        f"{summary['voice_status']}"
    )

    # --------------------------------------------------------
    # First few windows
    # --------------------------------------------------------

    print()
    print("First 5 window predictions:")

    for item in predictions[:5]:

        print(
            f"Window {item['window_index']:03d} | "
            f"Probability: "
            f"{item['spoof_probability']:.4f} | "
            f"Status: "
            f"{item['voice_status']}"
        )
from pathlib import Path
import sys

import joblib
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ============================================================
# Project root
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Project import
# ============================================================

from backend.app.models.mlp import VoiceAntiSpoofMLP


# ============================================================
# Paths
# ============================================================

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

VAL_X_PATH = PROCESSED_DIR / "val_X.npy"
VAL_Y_PATH = PROCESSED_DIR / "val_y.npy"

MODEL_PATH = MODEL_DIR / "voice_antispoof_mlp.pt"
SCALER_PATH = MODEL_DIR / "mfcc_scaler.joblib"


# ============================================================
# Configuration
# ============================================================

BATCH_SIZE = 1024

# Thresholds used for diagnostic comparison.
THRESHOLDS = [
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
]


# ============================================================
# Device
# ============================================================

def get_device():

    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(
            "Evaluation device:",
            torch.cuda.get_device_name(0),
        )
    else:
        device = torch.device("cpu")
        print("Evaluation device: CPU")

    return device


# ============================================================
# Load validation data
# ============================================================

def load_validation_data():

    required_files = [
        VAL_X_PATH,
        VAL_Y_PATH,
        MODEL_PATH,
        SCALER_PATH,
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{path}"
            )

    X_val = np.load(VAL_X_PATH)
    y_val = np.load(VAL_Y_PATH)

    scaler = joblib.load(
        SCALER_PATH
    )

    X_val = scaler.transform(
        X_val
    ).astype(
        np.float32
    )

    return X_val, y_val


# ============================================================
# Load model
# ============================================================

def load_model(device):

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model = VoiceAntiSpoofMLP(
        input_size=checkpoint.get(
            "input_size",
            20,
        )
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.to(device)
    model.eval()

    print(
        "Loaded checkpoint epoch:",
        checkpoint.get("epoch", "unknown"),
    )

    print(
        "Saved validation F1:",
        checkpoint.get(
            "best_val_f1",
            "unknown",
        ),
    )

    print(
        "Saved threshold:",
        checkpoint.get(
            "best_threshold",
            "unknown",
        ),
    )

    return model


# ============================================================
# Run inference
# ============================================================

def predict(
    model,
    X_val,
    device,
):

    probabilities = []

    total = len(X_val)

    for start in range(
        0,
        total,
        BATCH_SIZE,
    ):

        end = min(
            start + BATCH_SIZE,
            total,
        )

        batch = torch.from_numpy(
            X_val[start:end]
        ).to(
            device,
            non_blocking=True,
        )

        with torch.no_grad():

            logits = model(
                batch
            ).squeeze(1)

            probs = torch.sigmoid(
                logits
            )

        probabilities.extend(
            probs.cpu().numpy()
        )

    return np.asarray(
        probabilities,
        dtype=np.float32,
    )


# ============================================================
# Threshold metrics
# ============================================================

def calculate_threshold_metrics(
    y_true,
    probabilities,
    threshold,
):

    predictions = (
        probabilities >= threshold
    ).astype(
        np.int64
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1],
    ).ravel()

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    return {
        "threshold": threshold,
        "accuracy": accuracy_score(
            y_true,
            predictions,
        ),
        "balanced_accuracy":
            balanced_accuracy_score(
                y_true,
                predictions,
            ),
        "precision": precision_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "specificity": specificity,
        "f1": f1_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


# ============================================================
# Probability statistics
# ============================================================

def probability_statistics(
    y_true,
    probabilities,
):

    real_probs = probabilities[
        y_true == 0
    ]

    fake_probs = probabilities[
        y_true == 1
    ]

    print()
    print("=" * 60)
    print("PROBABILITY DISTRIBUTION")
    print("=" * 60)

    print(
        f"REAL samples: {len(real_probs)}"
    )

    print(
        f"REAL mean spoof probability: "
        f"{real_probs.mean():.4f}"
    )

    print(
        f"REAL median spoof probability: "
        f"{np.median(real_probs):.4f}"
    )

    print(
        f"REAL min: "
        f"{real_probs.min():.4f}"
    )

    print(
        f"REAL max: "
        f"{real_probs.max():.4f}"
    )

    print()

    print(
        f"FAKE samples: {len(fake_probs)}"
    )

    print(
        f"FAKE mean spoof probability: "
        f"{fake_probs.mean():.4f}"
    )

    print(
        f"FAKE median spoof probability: "
        f"{np.median(fake_probs):.4f}"
    )

    print(
        f"FAKE min: "
        f"{fake_probs.min():.4f}"
    )

    print(
        f"FAKE max: "
        f"{fake_probs.max():.4f}"
    )


# ============================================================
# Top-level metrics
# ============================================================

def overall_metrics(
    y_true,
    probabilities,
):

    auc = roc_auc_score(
        y_true,
        probabilities,
    )

    print()
    print("=" * 60)
    print("OVERALL RANKING METRIC")
    print("=" * 60)

    print(
        f"ROC-AUC: {auc:.4f}"
    )

    return auc


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print("EchoVerify - Model Diagnostic Evaluation")
    print("=" * 60)

    device = get_device()

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    X_val, y_val = (
        load_validation_data()
    )

    print()
    print(
        "Validation features:",
        X_val.shape,
    )

    print(
        "Validation labels:",
        y_val.shape,
    )

    print()
    print(
        "REAL:",
        int(np.sum(y_val == 0)),
    )

    print(
        "FAKE:",
        int(np.sum(y_val == 1)),
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model(
        device
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    print()
    print(
        "Generating validation predictions..."
    )

    probabilities = predict(
        model,
        X_val,
        device,
    )

    print(
        "Prediction generation: OK"
    )

    # --------------------------------------------------------
    # ROC-AUC
    # --------------------------------------------------------

    auc = overall_metrics(
        y_val,
        probabilities,
    )

    # --------------------------------------------------------
    # Probability statistics
    # --------------------------------------------------------

    probability_statistics(
        y_val,
        probabilities,
    )

    # --------------------------------------------------------
    # Threshold analysis
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("THRESHOLD ANALYSIS")
    print("=" * 60)

    print(
        "Threshold | Accuracy | Bal.Acc | "
        "Precision | Recall | Specificity | F1"
    )

    print("-" * 80)

    threshold_results = []

    for threshold in THRESHOLDS:

        metrics = calculate_threshold_metrics(
            y_val,
            probabilities,
            threshold,
        )

        threshold_results.append(
            metrics
        )

        print(
            f"{metrics['threshold']:>9.2f} | "
            f"{metrics['accuracy']:.4f}   | "
            f"{metrics['balanced_accuracy']:.4f}  | "
            f"{metrics['precision']:.4f}    | "
            f"{metrics['recall']:.4f} | "
            f"{metrics['specificity']:.4f}      | "
            f"{metrics['f1']:.4f}"
        )

    # --------------------------------------------------------
    # Best balanced accuracy
    # --------------------------------------------------------

    best_balanced = max(
        threshold_results,
        key=lambda x: x[
            "balanced_accuracy"
        ],
    )

    # --------------------------------------------------------
    # Best F1
    # --------------------------------------------------------

    best_f1 = max(
        threshold_results,
        key=lambda x: x["f1"],
    )

    print()
    print("=" * 60)
    print("BEST THRESHOLD RESULTS")
    print("=" * 60)

    print(
        f"Best Balanced Accuracy threshold: "
        f"{best_balanced['threshold']:.2f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{best_balanced['balanced_accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{best_balanced['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{best_balanced['recall']:.4f}"
    )

    print(
        f"Specificity: "
        f"{best_balanced['specificity']:.4f}"
    )

    print(
        f"F1: "
        f"{best_balanced['f1']:.4f}"
    )

    print()

    print(
        f"Best F1 threshold: "
        f"{best_f1['threshold']:.2f}"
    )

    print(
        f"F1: "
        f"{best_f1['f1']:.4f}"
    )

    # --------------------------------------------------------
    # Confusion matrix for balanced threshold
    # --------------------------------------------------------

    print()
    print(
        "Confusion Matrix "
        f"(threshold={best_balanced['threshold']:.2f}):"
    )

    print(
        np.array(
            [
                [
                    best_balanced["tn"],
                    best_balanced["fp"],
                ],
                [
                    best_balanced["fn"],
                    best_balanced["tp"],
                ],
            ]
        )
    )

    # --------------------------------------------------------
    # Final interpretation
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if auc < 0.50:

        print(
            "Model ranking is below random on "
            "the unseen-speaker validation set."
        )

    elif auc < 0.70:

        print(
            "Model shows weak separation between "
            "REAL and FAKE voices."
        )

    elif auc < 0.85:

        print(
            "Model shows moderate separation."
        )

    else:

        print(
            "Model shows strong separation."
        )

    if best_balanced[
        "balanced_accuracy"
    ] < 0.60:

        print(
            "Balanced classification performance "
            "is currently weak."
        )

    print()
    print(
        f"ROC-AUC: {auc:.4f}"
    )

    print(
        f"Best balanced accuracy: "
        f"{best_balanced['balanced_accuracy']:.4f}"
    )

    print(
        "Evaluation completed."
    )


if __name__ == "__main__":
    main()
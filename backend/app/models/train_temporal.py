from pathlib import Path
import random
import sys

import joblib
import numpy as np
import torch
import torch.nn as nn

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from sklearn.preprocessing import StandardScaler

from torch.utils.data import (
    DataLoader,
    TensorDataset,
    WeightedRandomSampler,
)


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

from backend.app.models.mlp_temporal import (
    VoiceAntiSpoofTemporalMLP,
)


# ============================================================
# Paths
# ============================================================

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

TRAIN_X_PATH = (
    PROCESSED_DIR / "train_X_temporal.npy"
)

TRAIN_Y_PATH = (
    PROCESSED_DIR / "train_y_temporal.npy"
)

VAL_X_PATH = (
    PROCESSED_DIR / "val_X_temporal.npy"
)

VAL_Y_PATH = (
    PROCESSED_DIR / "val_y_temporal.npy"
)

MODEL_PATH = (
    MODEL_DIR / "voice_antispoof_temporal_mlp.pt"
)

SCALER_PATH = (
    MODEL_DIR / "temporal_mfcc_scaler.joblib"
)


# ============================================================
# Configuration
# ============================================================

BATCH_SIZE = 1024
MAX_EPOCHS = 30
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
PATIENCE = 5
RANDOM_SEED = 42


# ============================================================
# Reproducibility
# ============================================================

def set_seed(seed=RANDOM_SEED):

    random.seed(seed)
    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ============================================================
# Device
# ============================================================

def get_device():

    if torch.cuda.is_available():

        device = torch.device("cuda")

        print(
            "Training device:",
            torch.cuda.get_device_name(0),
        )

    else:

        device = torch.device("cpu")

        print(
            "Training device: CPU"
        )

    return device


# ============================================================
# Load dataset
# ============================================================

def load_dataset():

    print()
    print("=" * 60)
    print("Loading Model B dataset")
    print("=" * 60)

    required = [
        TRAIN_X_PATH,
        TRAIN_Y_PATH,
        VAL_X_PATH,
        VAL_Y_PATH,
    ]

    for path in required:

        if not path.exists():

            raise FileNotFoundError(
                f"Missing file:\n{path}"
            )

    X_train = np.load(
        TRAIN_X_PATH
    )

    y_train = np.load(
        TRAIN_Y_PATH
    )

    X_val = np.load(
        VAL_X_PATH
    )

    y_val = np.load(
        VAL_Y_PATH
    )

    print(
        f"Train X: {X_train.shape}"
    )

    print(
        f"Train y: {y_train.shape}"
    )

    print(
        f"Val X:   {X_val.shape}"
    )

    print(
        f"Val y:   {y_val.shape}"
    )

    return (
        X_train,
        y_train,
        X_val,
        y_val,
    )


# ============================================================
# Scaling
# ============================================================

def scale_features(
    X_train,
    X_val,
):

    print()
    print(
        "Fitting Model B feature scaler..."
    )

    scaler = StandardScaler()

    X_train_scaled = (
        scaler.fit_transform(
            X_train
        )
    )

    X_val_scaled = (
        scaler.transform(
            X_val
        )
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        scaler,
        SCALER_PATH,
    )

    print(
        f"Scaler saved: {SCALER_PATH}"
    )

    return (
        X_train_scaled.astype(
            np.float32
        ),
        X_val_scaled.astype(
            np.float32
        ),
    )


# ============================================================
# Balanced sampler
# ============================================================

def create_balanced_sampler(
    y_train,
):

    counts = np.bincount(
        y_train
    )

    if len(counts) < 2:

        raise ValueError(
            "Both REAL and FAKE classes are required."
        )

    real_count = counts[0]
    fake_count = counts[1]

    print()
    print(
        "Training class distribution:"
    )

    print(
        f"REAL: {real_count}"
    )

    print(
        f"FAKE: {fake_count}"
    )

    class_weights = (
        len(y_train)
        /
        (
            2.0 * counts
        )
    )

    print(
        f"REAL sampling weight: "
        f"{class_weights[0]:.4f}"
    )

    print(
        f"FAKE sampling weight: "
        f"{class_weights[1]:.4f}"
    )

    sample_weights = np.array(
        [
            class_weights[int(label)]
            for label in y_train
        ],
        dtype=np.float64,
    )

    sampler = WeightedRandomSampler(
        torch.as_tensor(
            sample_weights,
            dtype=torch.double,
        ),
        num_samples=len(y_train),
        replacement=True,
    )

    return sampler


# ============================================================
# DataLoaders
# ============================================================

def create_dataloaders(
    X_train,
    y_train,
    X_val,
    y_val,
):

    train_dataset = TensorDataset(
        torch.from_numpy(X_train),
        torch.from_numpy(y_train).float(),
    )

    val_dataset = TensorDataset(
        torch.from_numpy(X_val),
        torch.from_numpy(y_val).float(),
    )

    sampler = create_balanced_sampler(
        y_train
    )

    pin_memory = (
        torch.cuda.is_available()
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        sampler=sampler,
        num_workers=0,
        pin_memory=pin_memory,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory,
    )

    return (
        train_loader,
        val_loader,
    )


# ============================================================
# Training
# ============================================================

def train_one_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device,
):

    model.train()

    total_loss = 0.0
    total_samples = 0

    for X_batch, y_batch in loader:

        X_batch = X_batch.to(
            device,
            non_blocking=True,
        )

        y_batch = y_batch.to(
            device,
            non_blocking=True,
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        logits = model(
            X_batch
        ).squeeze(1)

        loss = criterion(
            logits,
            y_batch,
        )

        loss.backward()

        optimizer.step()

        size = X_batch.size(0)

        total_loss += (
            loss.item() * size
        )

        total_samples += size

    return (
        total_loss /
        total_samples
    )


# ============================================================
# Predictions
# ============================================================

def predict(
    model,
    loader,
    device,
):

    model.eval()

    labels = []
    probabilities = []

    with torch.no_grad():

        for X_batch, y_batch in loader:

            X_batch = X_batch.to(
                device,
                non_blocking=True,
            )

            logits = model(
                X_batch
            ).squeeze(1)

            probs = torch.sigmoid(
                logits
            )

            labels.extend(
                y_batch.numpy()
            )

            probabilities.extend(
                probs.cpu().numpy()
            )

    return (
        np.asarray(
            labels,
            dtype=np.int64,
        ),
        np.asarray(
            probabilities,
            dtype=np.float32,
        ),
    )


# ============================================================
# Threshold search
# ============================================================

def find_best_threshold(
    labels,
    probabilities,
):

    best_threshold = 0.50
    best_balanced_accuracy = -1.0

    for threshold in np.arange(
        0.05,
        0.96,
        0.01,
    ):

        predictions = (
            probabilities >= threshold
        ).astype(np.int64)

        score = (
            balanced_accuracy_score(
                labels,
                predictions,
            )
        )

        if score > best_balanced_accuracy:

            best_balanced_accuracy = score
            best_threshold = float(
                threshold
            )

    return (
        best_threshold,
        best_balanced_accuracy,
    )


# ============================================================
# Metrics
# ============================================================

def calculate_metrics(
    labels,
    probabilities,
    threshold,
):

    predictions = (
        probabilities >= threshold
    ).astype(np.int64)

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    balanced_accuracy = (
        balanced_accuracy_score(
            labels,
            predictions,
        )
    )

    precision = precision_score(
        labels,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        labels,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        labels,
        predictions,
        zero_division=0,
    )

    auc = roc_auc_score(
        labels,
        probabilities,
    )

    cm = confusion_matrix(
        labels,
        predictions,
        labels=[0, 1],
    )

    tn, fp, fn, tp = cm.ravel()

    specificity = (
        tn / (tn + fp)
        if (tn + fp) > 0
        else 0.0
    )

    return {
        "accuracy": accuracy,
        "balanced_accuracy":
            balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
        "specificity": specificity,
        "confusion_matrix": cm,
    }


# ============================================================
# Main
# ============================================================

def main():

    set_seed()

    print("=" * 60)
    print(
        "EchoVerify - Model B Training"
    )
    print("=" * 60)

    device = get_device()

    (
        X_train,
        y_train,
        X_val,
        y_val,
    ) = load_dataset()

    (
        X_train,
        X_val,
    ) = scale_features(
        X_train,
        X_val,
    )

    (
        train_loader,
        val_loader,
    ) = create_dataloaders(
        X_train,
        y_train,
        X_val,
        y_val,
    )

    model = VoiceAntiSpoofTemporalMLP(
        input_size=80
    ).to(device)

    print()
    print("Model:")
    print(model)

    parameters = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    print(
        f"Trainable parameters: "
        f"{parameters}"
    )

    criterion = nn.BCEWithLogitsLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    best_auc = -1.0
    best_epoch = 0
    best_threshold = 0.50
    patience_counter = 0

    print()
    print("=" * 60)
    print("STARTING MODEL B TRAINING")
    print("=" * 60)

    for epoch in range(
        1,
        MAX_EPOCHS + 1,
    ):

        train_loss = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            device,
        )

        labels, probabilities = (
            predict(
                model,
                val_loader,
                device,
            )
        )

        threshold, _ = (
            find_best_threshold(
                labels,
                probabilities,
            )
        )

        metrics = calculate_metrics(
            labels,
            probabilities,
            threshold,
        )

        print(
            f"Epoch {epoch:02d}/{MAX_EPOCHS} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Threshold: {threshold:.2f} | "
            f"Accuracy: {metrics['accuracy']:.4f} | "
            f"Balanced Acc: {metrics['balanced_accuracy']:.4f} | "
            f"Precision: {metrics['precision']:.4f} | "
            f"Recall: {metrics['recall']:.4f} | "
            f"F1: {metrics['f1']:.4f} | "
            f"AUC: {metrics['auc']:.4f}"
        )

        # ----------------------------------------------------
        # Model selection uses ROC-AUC.
        # ----------------------------------------------------

        if metrics["auc"] > best_auc:

            best_auc = metrics["auc"]

            best_epoch = epoch

            best_threshold = threshold

            patience_counter = 0

            checkpoint = {
                "model_state_dict":
                    model.state_dict(),

                "input_size":
                    80,

                "best_auc":
                    best_auc,

                "best_threshold":
                    best_threshold,

                "epoch":
                    best_epoch,
            }

            torch.save(
                checkpoint,
                MODEL_PATH,
            )

            print(
                f"  ✓ Best Model B saved | "
                f"AUC={best_auc:.4f}"
            )

        else:

            patience_counter += 1

        if patience_counter >= PATIENCE:

            print()
            print(
                "Early stopping triggered."
            )

            break

    # ========================================================
    # Final evaluation
    # ========================================================

    print()
    print("=" * 60)
    print("LOADING BEST MODEL B")
    print("=" * 60)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    labels, probabilities = (
        predict(
            model,
            val_loader,
            device,
        )
    )

    threshold = (
        checkpoint["best_threshold"]
    )

    metrics = calculate_metrics(
        labels,
        probabilities,
        threshold,
    )

    # ========================================================
    # Final report
    # ========================================================

    print()
    print("=" * 60)
    print("MODEL B TRAINING COMPLETED")
    print("=" * 60)

    print(
        f"Best epoch: "
        f"{checkpoint['epoch']}"
    )

    print(
        f"Best threshold: "
        f"{threshold:.2f}"
    )

    print(
        f"Accuracy: "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"Specificity: "
        f"{metrics['specificity']:.4f}"
    )

    print(
        f"F1: "
        f"{metrics['f1']:.4f}"
    )

    print(
        f"ROC-AUC: "
        f"{metrics['auc']:.4f}"
    )

    print()
    print("Confusion Matrix:")

    print(
        metrics[
            "confusion_matrix"
        ]
    )

    print()
    print(
        f"Model saved: "
        f"{MODEL_PATH}"
    )

    print(
        f"Scaler saved: "
        f"{SCALER_PATH}"
    )

    print()
    print(
        "GPU:",
        (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "CPU"
        ),
    )


if __name__ == "__main__":
    main()
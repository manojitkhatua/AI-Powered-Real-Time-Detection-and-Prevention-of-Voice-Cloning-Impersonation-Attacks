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

from backend.app.models.mlp import VoiceAntiSpoofMLP


# ============================================================
# Paths
# ============================================================

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "models"

TRAIN_X_PATH = PROCESSED_DIR / "train_X.npy"
TRAIN_Y_PATH = PROCESSED_DIR / "train_y.npy"

VAL_X_PATH = PROCESSED_DIR / "val_X.npy"
VAL_Y_PATH = PROCESSED_DIR / "val_y.npy"

MODEL_PATH = MODEL_DIR / "voice_antispoof_mlp.pt"
SCALER_PATH = MODEL_DIR / "mfcc_scaler.joblib"


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
            f"Training device: "
            f"{torch.cuda.get_device_name(0)}"
        )

    else:

        device = torch.device("cpu")

        print("Training device: CPU")

    return device


# ============================================================
# Load processed dataset
# ============================================================

def load_dataset():

    print()
    print("=" * 60)
    print("Loading processed dataset")
    print("=" * 60)

    required_files = [
        TRAIN_X_PATH,
        TRAIN_Y_PATH,
        VAL_X_PATH,
        VAL_Y_PATH,
    ]

    for path in required_files:

        if not path.exists():

            raise FileNotFoundError(
                f"Required file not found:\n{path}"
            )

    X_train = np.load(TRAIN_X_PATH)
    y_train = np.load(TRAIN_Y_PATH)

    X_val = np.load(VAL_X_PATH)
    y_val = np.load(VAL_Y_PATH)

    print(f"Train X: {X_train.shape}")
    print(f"Train y: {y_train.shape}")

    print(f"Val X  : {X_val.shape}")
    print(f"Val y  : {y_val.shape}")

    return X_train, y_train, X_val, y_val


# ============================================================
# Feature scaling
# ============================================================

def scale_features(X_train, X_val):

    print()
    print("Fitting feature scaler...")

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_val_scaled = scaler.transform(
        X_val
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

def create_balanced_sampler(y_train):

    class_counts = np.bincount(
        y_train
    )

    if len(class_counts) < 2:

        raise ValueError(
            "Training data must contain REAL and FAKE classes."
        )

    real_count = class_counts[0]
    fake_count = class_counts[1]

    print()
    print("Training class distribution:")
    print(f"REAL: {real_count}")
    print(f"FAKE: {fake_count}")

    # Inverse-frequency class weights.
    class_weights = (
        len(y_train)
        /
        (
            2.0
            * class_counts
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
        weights=torch.as_tensor(
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

    pin_memory = torch.cuda.is_available()

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

    return train_loader, val_loader


# ============================================================
# Loss
# ============================================================

def create_loss_function():

    # Balanced sampler already handles class imbalance.
    # Do not apply another class-weighting mechanism here.

    return nn.BCEWithLogitsLoss()


# ============================================================
# Train one epoch
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

        batch_size = X_batch.size(0)

        total_loss += (
            loss.item()
            * batch_size
        )

        total_samples += batch_size

    return (
        total_loss
        /
        total_samples
    )


# ============================================================
# Get validation probabilities
# ============================================================

def get_validation_predictions(
    model,
    loader,
    device,
):

    model.eval()

    all_labels = []
    all_probabilities = []

    with torch.no_grad():

        for X_batch, y_batch in loader:

            X_batch = X_batch.to(
                device,
                non_blocking=True,
            )

            logits = model(
                X_batch
            ).squeeze(1)

            probabilities = torch.sigmoid(
                logits
            )

            all_labels.extend(
                y_batch.numpy()
            )

            all_probabilities.extend(
                probabilities.cpu().numpy()
            )

    labels = np.asarray(
        all_labels,
        dtype=np.int64,
    )

    probabilities = np.asarray(
        all_probabilities,
        dtype=np.float32,
    )

    return labels, probabilities


# ============================================================
# Find best classification threshold
# ============================================================

def find_best_threshold(
    labels,
    probabilities,
):

    best_threshold = 0.50
    best_f1 = -1.0

    for threshold in np.arange(
        0.05,
        0.96,
        0.01,
    ):

        predictions = (
            probabilities
            >= threshold
        ).astype(
            np.int64
        )

        score = f1_score(
            labels,
            predictions,
            zero_division=0,
        )

        if score > best_f1:

            best_f1 = score
            best_threshold = float(
                threshold
            )

    return (
        best_threshold,
        best_f1,
    )


# ============================================================
# Calculate metrics
# ============================================================

def calculate_metrics(
    labels,
    probabilities,
    threshold,
):

    predictions = (
        probabilities
        >= threshold
    ).astype(
        np.int64
    )

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
    )

    return {
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
        "confusion_matrix": cm,
    }


# ============================================================
# Main training
# ============================================================

def main():

    set_seed()

    print("=" * 60)
    print("EchoVerify - Improved MLP Training")
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

    model = VoiceAntiSpoofMLP(
        input_size=20
    ).to(device)

    print()
    print("Model:")
    print(model)

    print(
        "Trainable parameters:",
        sum(
            p.numel()
            for p in model.parameters()
            if p.requires_grad
        )
    )

    criterion = create_loss_function()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    best_f1 = -1.0

    best_epoch = 0

    epochs_without_improvement = 0

    best_threshold = 0.50

    print()
    print("=" * 60)
    print("STARTING IMPROVED TRAINING")
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
            get_validation_predictions(
                model,
                val_loader,
                device,
            )
        )

        threshold, tuned_f1 = (
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
        # Save best model
        # ----------------------------------------------------

        if metrics["f1"] > best_f1:

            best_f1 = metrics["f1"]

            best_epoch = epoch

            best_threshold = threshold

            epochs_without_improvement = 0

            checkpoint = {
                "model_state_dict":
                    model.state_dict(),

                "input_size":
                    20,

                "best_val_f1":
                    best_f1,

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
                f"  ✓ Best model saved | "
                f"F1={best_f1:.4f} | "
                f"Threshold={best_threshold:.2f}"
            )

        else:

            epochs_without_improvement += 1

        # ----------------------------------------------------
        # Early stopping
        # ----------------------------------------------------

        if (
            epochs_without_improvement
            >= PATIENCE
        ):

            print()
            print(
                f"Early stopping triggered "
                f"after {PATIENCE} epochs "
                f"without improvement."
            )

            break

    # ========================================================
    # Load best checkpoint
    # ========================================================

    print()
    print("=" * 60)
    print("LOADING BEST CHECKPOINT")
    print("=" * 60)

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    best_threshold = checkpoint[
        "best_threshold"
    ]

    labels, probabilities = (
        get_validation_predictions(
            model,
            val_loader,
            device,
        )
    )

    final_metrics = calculate_metrics(
        labels,
        probabilities,
        best_threshold,
    )

    # ========================================================
    # Final report
    # ========================================================

    print()
    print("=" * 60)
    print("IMPROVED TRAINING COMPLETED")
    print("=" * 60)

    print(
        f"Best epoch: "
        f"{checkpoint['epoch']}"
    )

    print(
        f"Best threshold: "
        f"{best_threshold:.2f}"
    )

    print(
        f"Accuracy: "
        f"{final_metrics['accuracy']:.4f}"
    )

    print(
        f"Balanced Accuracy: "
        f"{final_metrics['balanced_accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{final_metrics['precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{final_metrics['recall']:.4f}"
    )

    print(
        f"F1: "
        f"{final_metrics['f1']:.4f}"
    )

    print(
        f"ROC-AUC: "
        f"{final_metrics['auc']:.4f}"
    )

    print()
    print("Confusion Matrix:")
    print(
        final_metrics[
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
        "Training device:",
        (
            torch.cuda.get_device_name(0)
            if torch.cuda.is_available()
            else "CPU"
        ),
    )


if __name__ == "__main__":
    main()
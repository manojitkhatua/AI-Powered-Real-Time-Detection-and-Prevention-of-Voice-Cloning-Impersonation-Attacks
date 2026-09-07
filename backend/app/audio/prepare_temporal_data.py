from pathlib import Path
import json
import sys

import numpy as np


# ============================================================
# Project root
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Imports
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


# ============================================================
# Paths
# ============================================================

PROCESSED_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

SPLIT_MANIFEST = (
    PROCESSED_DIR / "speaker_split.json"
)

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


# ============================================================
# Load split
# ============================================================

def load_manifest():

    if not SPLIT_MANIFEST.exists():
        raise FileNotFoundError(
            f"Missing speaker split manifest:\n"
            f"{SPLIT_MANIFEST}"
        )

    with open(
        SPLIT_MANIFEST,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# Process files
# ============================================================

def process_records(
    records,
    split_name,
):

    features = []
    labels = []

    successful = 0
    failed = 0
    total_windows = 0

    print()
    print("=" * 60)
    print(f"Processing {split_name}")
    print("=" * 60)

    for index, record in enumerate(
        records,
        start=1,
    ):

        file_path = Path(
            record["path"]
        )

        label_name = record["label"]

        label = (
            0 if label_name == "REAL"
            else 1
        )

        try:

            audio = load_and_preprocess_audio(
                str(file_path)
            )

            windows = create_audio_windows(
                audio
            )

            for window in windows:

                mfcc = extract_mfcc(
                    window
                )

                vector = (
                    prepare_mfcc_temporal_features(
                        mfcc
                    )
                )

                if vector.shape != (80,):
                    raise ValueError(
                        f"Expected (80,), got "
                        f"{vector.shape}"
                    )

                features.append(vector)
                labels.append(label)

            successful += 1
            total_windows += len(windows)

            print(
                f"[{index}/{len(records)}] "
                f"{file_path.name} | "
                f"{label_name} | "
                f"{len(windows)} windows"
            )

        except Exception as exc:

            failed += 1

            print(
                f"[WARNING] Failed: "
                f"{file_path.name}"
            )

            print(
                f"Reason: {exc}"
            )

    if not features:
        raise RuntimeError(
            f"No features generated for "
            f"{split_name}"
        )

    X = np.asarray(
        features,
        dtype=np.float32,
    )

    y = np.asarray(
        labels,
        dtype=np.int64,
    )

    print()
    print(
        f"{split_name} successful: {successful}"
    )

    print(
        f"{split_name} failed: {failed}"
    )

    print(
        f"{split_name} windows: {total_windows}"
    )

    print(
        f"{split_name} X shape: {X.shape}"
    )

    print(
        f"{split_name} y shape: {y.shape}"
    )

    return X, y


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print(
        "EchoVerify - Model B Feature Generation"
    )
    print("=" * 60)

    manifest = load_manifest()

    train_records = manifest[
        "train_files"
    ]

    val_records = manifest[
        "validation_files"
    ]

    print(
        f"Training files: {len(train_records)}"
    )

    print(
        f"Validation files: {len(val_records)}"
    )

    # --------------------------------------------------------
    # Training
    # --------------------------------------------------------

    X_train, y_train = process_records(
        train_records,
        "TRAINING",
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    X_val, y_val = process_records(
        val_records,
        "VALIDATION",
    )

    # --------------------------------------------------------
    # Save Model B data
    # --------------------------------------------------------

    np.save(
        TRAIN_X_PATH,
        X_train,
    )

    np.save(
        TRAIN_Y_PATH,
        y_train,
    )

    np.save(
        VAL_X_PATH,
        X_val,
    )

    np.save(
        VAL_Y_PATH,
        y_val,
    )

    print()
    print("=" * 60)
    print("MODEL B FEATURE GENERATION COMPLETED")
    print("=" * 60)

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

    print()

    train_unique, train_counts = np.unique(
        y_train,
        return_counts=True,
    )

    print("TRAIN distribution:")

    for label, count in zip(
        train_unique,
        train_counts,
    ):

        name = (
            "REAL"
            if label == 0
            else "FAKE"
        )

        print(
            f"  {name}: {count}"
        )

    val_unique, val_counts = np.unique(
        y_val,
        return_counts=True,
    )

    print()
    print("VALIDATION distribution:")

    for label, count in zip(
        val_unique,
        val_counts,
    ):

        name = (
            "REAL"
            if label == 0
            else "FAKE"
        )

        print(
            f"  {name}: {count}"
        )


if __name__ == "__main__":
    main()
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
# Project imports
# ============================================================

from backend.app.audio.preprocessor import (
    load_and_preprocess_audio
)

from backend.app.audio.windowing import (
    create_audio_windows
)

from backend.app.audio.features import (
    extract_mfcc,
    prepare_mfcc_for_mlp,
)


# ============================================================
# Paths
# ============================================================

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

SPLIT_MANIFEST = (
    PROCESSED_DIR
    / "speaker_split.json"
)

TRAIN_X_PATH = (
    PROCESSED_DIR
    / "train_X.npy"
)

TRAIN_Y_PATH = (
    PROCESSED_DIR
    / "train_y.npy"
)

VAL_X_PATH = (
    PROCESSED_DIR
    / "val_X.npy"
)

VAL_Y_PATH = (
    PROCESSED_DIR
    / "val_y.npy"
)


# ============================================================
# Load speaker split
# ============================================================

def load_split_manifest():

    if not SPLIT_MANIFEST.exists():
        raise FileNotFoundError(
            f"Speaker split manifest not found:\n"
            f"{SPLIT_MANIFEST}"
        )

    with open(
        SPLIT_MANIFEST,
        "r",
        encoding="utf-8",
    ) as file:

        manifest = json.load(file)

    return manifest


# ============================================================
# Process records
# ============================================================

def process_records(
    records,
    split_name,
):

    features = []
    labels = []

    successful_files = 0
    failed_files = 0
    total_windows = 0

    print()
    print("=" * 60)
    print(f"Processing {split_name} data")
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
            0
            if label_name == "REAL"
            else 1
        )

        try:

            # ------------------------------------------------
            # Load + preprocess
            # ------------------------------------------------

            audio = (
                load_and_preprocess_audio(
                    str(file_path)
                )
            )

            # ------------------------------------------------
            # Windowing
            # ------------------------------------------------

            windows = (
                create_audio_windows(
                    audio
                )
            )

            # ------------------------------------------------
            # MFCC extraction
            # ------------------------------------------------

            for window in windows:

                mfcc = extract_mfcc(
                    window
                )

                feature_vector = (
                    prepare_mfcc_for_mlp(
                        mfcc
                    )
                )

                if feature_vector.shape != (20,):

                    raise ValueError(
                        "Unexpected feature vector "
                        f"shape: {feature_vector.shape}"
                    )

                features.append(
                    feature_vector
                )

                labels.append(
                    label
                )

            successful_files += 1

            total_windows += len(
                windows
            )

            print(
                f"[{index}/{len(records)}] "
                f"{file_path.name} | "
                f"{label_name} | "
                f"{len(windows)} windows"
            )

        except Exception as exc:

            failed_files += 1

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
            f"{split_name}."
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
        f"{split_name} successful files: "
        f"{successful_files}"
    )

    print(
        f"{split_name} failed files: "
        f"{failed_files}"
    )

    print(
        f"{split_name} total windows: "
        f"{total_windows}"
    )

    print(
        f"{split_name} feature shape: "
        f"{X.shape}"
    )

    print(
        f"{split_name} label shape: "
        f"{y.shape}"
    )

    return X, y


# ============================================================
# Save arrays
# ============================================================

def save_array(
    path,
    array,
):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    np.save(
        path,
        array,
    )

    print(
        f"Saved: {path}"
    )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 60)
    print(
        "EchoVerify - Speaker-Independent "
        "Feature Generation"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Load verified split
    # --------------------------------------------------------

    manifest = (
        load_split_manifest()
    )

    train_records = (
        manifest["train_files"]
    )

    validation_records = (
        manifest["validation_files"]
    )

    print()
    print(
        f"Training files: "
        f"{len(train_records)}"
    )

    print(
        f"Validation files: "
        f"{len(validation_records)}"
    )

    print()
    print(
        "Training speakers:"
    )

    print(
        "  "
        + ", ".join(
            manifest["training_speakers"]
        )
    )

    print()
    print(
        "Validation speakers:"
    )

    print(
        "  "
        + ", ".join(
            manifest["validation_speakers"]
        )
    )

    # --------------------------------------------------------
    # Generate training features
    # --------------------------------------------------------

    X_train, y_train = (
        process_records(
            train_records,
            "TRAINING",
        )
    )

    # --------------------------------------------------------
    # Generate validation features
    # --------------------------------------------------------

    X_val, y_val = (
        process_records(
            validation_records,
            "VALIDATION",
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("Saving processed datasets")
    print("=" * 60)

    save_array(
        TRAIN_X_PATH,
        X_train,
    )

    save_array(
        TRAIN_Y_PATH,
        y_train,
    )

    save_array(
        VAL_X_PATH,
        X_val,
    )

    save_array(
        VAL_Y_PATH,
        y_val,
    )

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL DATASET SUMMARY")
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

    print(
        "TRAIN class distribution:"
    )

    unique, counts = np.unique(
        y_train,
        return_counts=True,
    )

    for label, count in zip(
        unique,
        counts,
    ):

        name = (
            "REAL"
            if label == 0
            else "FAKE"
        )

        print(
            f"  {name}: {count}"
        )

    print()

    print(
        "VALIDATION class distribution:"
    )

    unique, counts = np.unique(
        y_val,
        return_counts=True,
    )

    for label, count in zip(
        unique,
        counts,
    ):

        name = (
            "REAL"
            if label == 0
            else "FAKE"
        )

        print(
            f"  {name}: {count}"
        )

    print()
    print("=" * 60)
    print(
        "SPEAKER-INDEPENDENT FEATURE "
        "GENERATION COMPLETED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
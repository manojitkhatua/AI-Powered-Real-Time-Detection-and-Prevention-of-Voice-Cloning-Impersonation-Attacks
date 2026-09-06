from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
CSV_FILE = RAW_DIR / "DATASET-balanced.csv"
AUDIO_DIR = RAW_DIR / "AUDIO"


EXPECTED_FEATURES = [
    "chroma_stft",
    "rms",
    "spectral_centroid",
    "spectral_bandwidth",
    "rolloff",
    "zero_crossing_rate",
]

EXPECTED_MFCCS = [
    f"mfcc{i}"
    for i in range(1, 21)
]

EXPECTED_LABEL = "LABEL"


def validate_dataset():

    print("=" * 60)
    print("EchoVerify - Dataset Validation")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Check CSV
    # --------------------------------------------------

    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Dataset CSV not found: {CSV_FILE}"
        )

    print(f"CSV file : {CSV_FILE}")

    # --------------------------------------------------
    # 2. Load CSV
    # --------------------------------------------------

    df = pd.read_csv(CSV_FILE)

    print(f"Rows     : {len(df)}")
    print(f"Columns  : {len(df.columns)}")

    # --------------------------------------------------
    # 3. Validate columns
    # --------------------------------------------------

    expected_columns = (
        EXPECTED_FEATURES
        + EXPECTED_MFCCS
        + [EXPECTED_LABEL]
    )

    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print("Columns  : OK")

    # --------------------------------------------------
    # 4. Check missing values
    # --------------------------------------------------

    missing_values = df.isnull().sum().sum()

    print(f"Missing values: {missing_values}")

    if missing_values > 0:
        print("WARNING: Dataset contains missing values.")
    else:
        print("Missing values: OK")

    # --------------------------------------------------
    # 5. Validate numeric features
    # --------------------------------------------------

    feature_columns = EXPECTED_FEATURES + EXPECTED_MFCCS

    non_numeric = [
        column
        for column in feature_columns
        if not pd.api.types.is_numeric_dtype(df[column])
    ]

    if non_numeric:
        raise ValueError(
            f"Non-numeric feature columns: {non_numeric}"
        )

    print("Feature types: OK")

    # --------------------------------------------------
    # 6. Validate labels
    # --------------------------------------------------

    labels = df[EXPECTED_LABEL].dropna().unique()

    print(f"Labels   : {list(labels)}")

    if len(labels) < 2:
        raise ValueError(
            "Dataset must contain at least two classes."
        )

    print("Labels   : OK")

    # --------------------------------------------------
    # 7. Check AUDIO directory
    # --------------------------------------------------

    if not AUDIO_DIR.exists():
        raise FileNotFoundError(
            f"Audio directory not found: {AUDIO_DIR}"
        )

    audio_files = list(AUDIO_DIR.rglob("*"))

    audio_files = [
        file for file in audio_files
        if file.is_file()
    ]

    print(f"Audio files found: {len(audio_files)}")

    if len(audio_files) == 0:
        raise ValueError(
            "No audio files found inside AUDIO directory."
        )

    print("Audio directory: OK")

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    print()
    print("=" * 60)
    print("DATASET VALIDATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    validate_dataset()
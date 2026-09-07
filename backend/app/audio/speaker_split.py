from pathlib import Path
import json
import re
import sys
import random


# ============================================================
# Project root
# ============================================================

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Paths
# ============================================================

AUDIO_DIR = PROJECT_ROOT / "data" / "raw" / "AUDIO"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SPLIT_MANIFEST = PROCESSED_DIR / "speaker_split.json"


# ============================================================
# Configuration
# ============================================================

SEED = 42

# Two completely unseen speakers for validation.
VALIDATION_SPEAKERS = {
    "taylor",
    "trump",
}


# ============================================================
# Helpers
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".flac",
    ".mp3",
    ".ogg",
    ".m4a",
}


def normalize_name(name: str) -> str:
    """
    Normalize speaker names so Biden, biden, BIDEN
    are treated as the same speaker.
    """

    return name.strip().lower()


def extract_speakers_from_filename(
    filename: str,
):
    """
    Identify speaker identities encoded in filenames.

    REAL:
        biden-original.wav
        linus-original.wav

    FAKE:
        biden-to-linus.wav
        linus-to-biden.wav

    Returns:
        tuple of one or two normalized speaker names.
    """

    stem = Path(filename).stem

    # --------------------------------------------------------
    # REAL format: <speaker>-original
    # --------------------------------------------------------

    real_match = re.fullmatch(
        r"(.+?)-original",
        stem,
        flags=re.IGNORECASE,
    )

    if real_match:
        speaker = normalize_name(
            real_match.group(1)
        )

        return (speaker,)

    # --------------------------------------------------------
    # FAKE format: <speaker>-to-<speaker>
    # --------------------------------------------------------

    fake_match = re.fullmatch(
        r"(.+?)-to-(.+)",
        stem,
        flags=re.IGNORECASE,
    )

    if fake_match:

        speaker_a = normalize_name(
            fake_match.group(1)
        )

        speaker_b = normalize_name(
            fake_match.group(2)
        )

        return (
            speaker_a,
            speaker_b,
        )

    raise ValueError(
        f"Cannot identify speaker(s) from filename: "
        f"{filename}"
    )


# ============================================================
# Collect files
# ============================================================

def collect_audio_files():

    if not AUDIO_DIR.exists():
        raise FileNotFoundError(
            f"AUDIO directory not found:\n{AUDIO_DIR}"
        )

    records = []

    for class_name in ["REAL", "FAKE"]:

        class_dir = AUDIO_DIR / class_name

        if not class_dir.exists():
            raise FileNotFoundError(
                f"Missing class directory:\n{class_dir}"
            )

        for path in class_dir.rglob("*"):

            if (
                path.is_file()
                and path.suffix.lower()
                in SUPPORTED_EXTENSIONS
            ):

                speakers = (
                    extract_speakers_from_filename(
                        path.name
                    )
                )

                records.append(
                    {
                        "path": str(path),
                        "filename": path.name,
                        "label": class_name,
                        "speakers": list(speakers),
                    }
                )

    return records


# ============================================================
# Find all speakers
# ============================================================

def find_all_speakers(records):

    speakers = set()

    for record in records:

        speakers.update(
            record["speakers"]
        )

    return sorted(speakers)


# ============================================================
# Validate speaker split
# ============================================================

def validate_speaker_configuration(
    all_speakers,
):

    missing = (
        VALIDATION_SPEAKERS
        - set(all_speakers)
    )

    if missing:
        raise ValueError(
            f"Validation speakers not found: "
            f"{sorted(missing)}"
        )

    training_speakers = (
        set(all_speakers)
        - VALIDATION_SPEAKERS
    )

    if not training_speakers:
        raise ValueError(
            "No training speakers remain."
        )

    return training_speakers


# ============================================================
# Create split
# ============================================================

def create_split(records):

    all_speakers = find_all_speakers(
        records
    )

    training_speakers = (
        validate_speaker_configuration(
            all_speakers
        )
    )

    validation_speakers = (
        set(VALIDATION_SPEAKERS)
    )

    print()
    print("=" * 60)
    print("SPEAKER-LEVEL SPLIT")
    print("=" * 60)

    print(
        f"All speakers: "
        f"{', '.join(all_speakers)}"
    )

    print()
    print(
        "Training speakers:"
    )

    print(
        "  "
        + ", ".join(
            sorted(training_speakers)
        )
    )

    print()
    print(
        "Validation speakers:"
    )

    print(
        "  "
        + ", ".join(
            sorted(validation_speakers)
        )
    )

    # --------------------------------------------------------
    # Partition records
    # --------------------------------------------------------

    train_records = []
    validation_records = []
    excluded_records = []

    for record in records:

        record_speakers = set(
            record["speakers"]
        )

        # ----------------------------------------------------
        # REAL sample
        # ----------------------------------------------------

        if record["label"] == "REAL":

            speaker = next(
                iter(record_speakers)
            )

            if speaker in training_speakers:

                train_records.append(
                    record
                )

            elif speaker in validation_speakers:

                validation_records.append(
                    record
                )

            else:

                excluded_records.append(
                    record
                )

        # ----------------------------------------------------
        # FAKE sample
        #
        # Both speaker identities must belong to
        # the same partition.
        # ----------------------------------------------------

        elif record["label"] == "FAKE":

            if record_speakers.issubset(
                training_speakers
            ):

                train_records.append(
                    record
                )

            elif record_speakers.issubset(
                validation_speakers
            ):

                validation_records.append(
                    record
                )

            else:

                excluded_records.append(
                    record
                )

    return (
        all_speakers,
        training_speakers,
        validation_speakers,
        train_records,
        validation_records,
        excluded_records,
    )


# ============================================================
# Print class distribution
# ============================================================

def print_distribution(
    records,
    name,
):

    real = sum(
        record["label"] == "REAL"
        for record in records
    )

    fake = sum(
        record["label"] == "FAKE"
        for record in records
    )

    print()
    print(
        f"{name} files:"
    )

    print(
        f"  REAL: {real}"
    )

    print(
        f"  FAKE: {fake}"
    )

    print(
        f"  TOTAL: {real + fake}"
    )


# ============================================================
# Save manifest
# ============================================================

def save_manifest(
    all_speakers,
    training_speakers,
    validation_speakers,
    train_records,
    validation_records,
    excluded_records,
):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "seed": SEED,
        "all_speakers": sorted(
            all_speakers
        ),
        "training_speakers": sorted(
            training_speakers
        ),
        "validation_speakers": sorted(
            validation_speakers
        ),
        "train_files": train_records,
        "validation_files": validation_records,
        "excluded_files": excluded_records,
    }

    with open(
        SPLIT_MANIFEST,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=2,
        )

    print()
    print(
        f"Manifest saved:\n"
        f"{SPLIT_MANIFEST}"
    )


# ============================================================
# Main
# ============================================================

def main():

    random.seed(SEED)

    print("=" * 60)
    print("EchoVerify - Speaker Independent Split")
    print("=" * 60)

    records = collect_audio_files()

    print(
        f"Audio files found: "
        f"{len(records)}"
    )

    (
        all_speakers,
        training_speakers,
        validation_speakers,
        train_records,
        validation_records,
        excluded_records,
    ) = create_split(records)

    # --------------------------------------------------------
    # Print statistics
    # --------------------------------------------------------

    print_distribution(
        train_records,
        "TRAINING",
    )

    print_distribution(
        validation_records,
        "VALIDATION",
    )

    print()
    print(
        f"Excluded files: "
        f"{len(excluded_records)}"
    )

    # --------------------------------------------------------
    # Show excluded cross-partition files
    # --------------------------------------------------------

    if excluded_records:

        print()
        print(
            "Cross-partition FAKE files excluded:"
        )

        for record in excluded_records:

            print(
                f"  {record['filename']} "
                f"-> "
                f"{', '.join(record['speakers'])}"
            )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_manifest(
        all_speakers,
        training_speakers,
        validation_speakers,
        train_records,
        validation_records,
        excluded_records,
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SPEAKER SPLIT COMPLETED")
    print("=" * 60)

    print(
        "No file is allowed to contain speakers "
        "from both partitions."
    )

    print(
        "The validation speakers are completely "
        "unseen during training."
    )


if __name__ == "__main__":
    main()
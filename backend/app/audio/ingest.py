from pathlib import Path
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATASET_ZIP = RAW_DIR / "KAGGLE.zip"


def ingest_dataset():
    """
    Extract KAGGLE.zip into data/raw/.

    This stage only performs dataset ingestion.
    No preprocessing or data analysis is performed here.
    """

    if not DATASET_ZIP.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_ZIP}"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("EchoVerify - Dataset Ingestion")
    print("=" * 60)

    print(f"Dataset : {DATASET_ZIP}")
    print(f"Size    : {DATASET_ZIP.stat().st_size / (1024 ** 3):.2f} GB")
    print(f"Target  : {RAW_DIR}")
    print()

    print("Extracting dataset...")

    with zipfile.ZipFile(DATASET_ZIP, "r") as zip_ref:
        zip_ref.extractall(RAW_DIR)

    print()
    print("Dataset ingestion completed successfully.")
    print(f"Raw data location: {RAW_DIR}")


if __name__ == "__main__":
    ingest_dataset()
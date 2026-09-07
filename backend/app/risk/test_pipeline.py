import sys
from pathlib import Path


# ============================================================
# PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_PATH = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_PATH))


# ============================================================
# IMPORTS
# ============================================================

from app.models.inference import predict_audio_file
from app.risk.risk_engine import TemporalRiskEngine


# ============================================================
# AUDIO FILES
# ============================================================

REAL_AUDIO = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "AUDIO"
    / "REAL"
    / "biden-original.wav"
)

FAKE_AUDIO = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "AUDIO"
    / "FAKE"
    / "biden-to-linus.wav"
)


# ============================================================
# TEST FUNCTION
# ============================================================

def run_test(audio_path: Path, test_name: str):

    print("\n")
    print("=" * 75)
    print(f"TEST: {test_name}")
    print(f"FILE: {audio_path.name}")
    print("=" * 75)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found:\n{audio_path}"
        )

    # --------------------------------------------------------
    # MODEL B
    # --------------------------------------------------------

    print("\nRunning Model B inference...")

    results = predict_audio_file(str(audio_path))

    if not isinstance(results, list):
        raise TypeError(
            f"Expected list from predict_audio_file(), "
            f"got {type(results)}"
        )

    print(f"Number of windows: {len(results)}")

    # --------------------------------------------------------
    # EXTRACT SPOOF PROBABILITIES
    # --------------------------------------------------------

    probabilities = []

    for item in results:

        if not isinstance(item, dict):
            raise TypeError(
                f"Expected dictionary for each window, "
                f"got {type(item)}"
            )

        if "spoof_probability" not in item:
            raise KeyError(
                "spoof_probability missing from model output"
            )

        probability = float(
            item["spoof_probability"]
        )

        probabilities.append(probability)

    # --------------------------------------------------------
    # MODEL STATISTICS
    # --------------------------------------------------------

    mean_probability = (
        sum(probabilities) / len(probabilities)
    )

    max_probability = max(probabilities)

    fake_windows = sum(
        1
        for probability in probabilities
        if probability >= 0.95
    )

    print("\nMODEL SUMMARY")
    print("-" * 75)

    print(
        f"Mean spoof probability : "
        f"{mean_probability:.4f}"
    )

    print(
        f"Maximum spoof probability: "
        f"{max_probability:.4f}"
    )

    print(
        f"Windows >= 0.95        : "
        f"{fake_windows}/{len(probabilities)}"
    )

    # --------------------------------------------------------
    # TEMPORAL RISK ENGINE
    # --------------------------------------------------------

    print("\nTEMPORAL RISK ENGINE")
    print("-" * 75)

    risk_engine = TemporalRiskEngine()

    final_state = None

    previous_level = None
    previous_action = None

    for index, probability in enumerate(probabilities):

        state = risk_engine.update(probability)

        final_state = state

        # RiskResult is an object
        risk_score = getattr(
            state,
            "risk_score",
            None
        )

        risk_level = getattr(
            state,
            "risk_level",
            None
        )

        action = getattr(
            state,
            "action",
            None
        )

        # Print:
        # first window
        # every 25 windows
        # risk changes
        # action changes

        if (
            index == 0
            or (index + 1) % 25 == 0
            or risk_level != previous_level
            or action != previous_action
        ):

            print(
                f"Window {index + 1:03d} | "
                f"Spoof={probability:.4f} | "
                f"Risk={risk_score:.2f} | "
                f"Level={risk_level} | "
                f"Action={action}"
            )

        previous_level = risk_level
        previous_action = action

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("\nFINAL RESULT")
    print("-" * 75)

    if final_state is not None:

        print(
            f"Final risk score : "
            f"{getattr(final_state, 'risk_score', None):.2f}"
        )

        print(
            f"Final risk level : "
            f"{getattr(final_state, 'risk_level', None)}"
        )

        print(
            f"Final action     : "
            f"{getattr(final_state, 'action', None)}"
        )

    print("=" * 75)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\nEchoVerify")
    print("Model B + Temporal Risk Engine Integration Test")

    # REAL VOICE
    run_test(
        REAL_AUDIO,
        "REAL VOICE"
    )

    # FAKE VOICE
    run_test(
        FAKE_AUDIO,
        "FAKE / CLONED VOICE"
    )

    print("\nAll tests completed successfully.")
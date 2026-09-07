from dataclasses import dataclass
from typing import Optional


# ============================================================
# Risk thresholds
# ============================================================
# Prototype policy:
#
# 0-30   -> LOW      -> MONITOR
# 31-60  -> MEDIUM   -> WARNING
# 61-85  -> HIGH     -> VERIFY
# 86-100 -> CRITICAL -> BLOCK
#
# These are prototype security-policy thresholds.
# They are not scientifically calibrated risk boundaries.
# ============================================================

LOW_MAX = 30.0
MEDIUM_MAX = 60.0
HIGH_MAX = 85.0


# ============================================================
# Temporal configuration
# ============================================================

# Higher alpha = current window has more influence.
SMOOTHING_ALPHA = 0.35

# How many consecutive suspicious windows increase
# the persistence component.
PERSISTENCE_WINDOW = 5

# Maximum persistence contribution to the risk score.
MAX_PERSISTENCE_BONUS = 20.0


# ============================================================
# Result object
# ============================================================

@dataclass
class RiskResult:
    """
    Result of one temporal-risk update.
    """

    spoof_probability: float
    smoothed_probability: float

    persistence_count: int
    persistence_bonus: float

    risk_score: float
    risk_level: str
    action: str

    message: str


# ============================================================
# Temporal Risk Engine
# ============================================================

class TemporalRiskEngine:
    """
    Convert sequential spoof probabilities into
    a stable security risk score.

    The engine is stateful.

    Example:

        probability 0.05
            -> low risk

        probability 0.90
            -> risk increases

        probability 0.95
        probability 0.97
        probability 0.98
            -> persistent evidence
            -> high/critical risk
    """

    def __init__(
        self,
        smoothing_alpha: float = SMOOTHING_ALPHA,
        persistence_window: int = PERSISTENCE_WINDOW,
    ):
        if not 0.0 < smoothing_alpha <= 1.0:
            raise ValueError(
                "smoothing_alpha must be between 0 and 1."
            )

        if persistence_window < 1:
            raise ValueError(
                "persistence_window must be >= 1."
            )

        self.smoothing_alpha = smoothing_alpha
        self.persistence_window = persistence_window

        self.smoothed_probability: Optional[float] = None

        self.persistence_count = 0

        self.window_count = 0

    # ========================================================
    # Reset
    # ========================================================

    def reset(self):
        """
        Reset the engine for a new call/session.
        """

        self.smoothed_probability = None
        self.persistence_count = 0
        self.window_count = 0

    # ========================================================
    # Validate probability
    # ========================================================

    @staticmethod
    def _validate_probability(
        spoof_probability: float,
    ) -> float:

        try:
            probability = float(
                spoof_probability
            )
        except (TypeError, ValueError) as exc:

            raise ValueError(
                "spoof_probability must be numeric."
            ) from exc

        if not 0.0 <= probability <= 1.0:

            raise ValueError(
                "spoof_probability must be between 0 and 1."
            )

        return probability

    # ========================================================
    # Temporal smoothing
    # ========================================================

    def _update_smoothed_probability(
        self,
        probability: float,
    ) -> float:
        """
        Exponential moving average.
        """

        if self.smoothed_probability is None:

            self.smoothed_probability = probability

        else:

            self.smoothed_probability = (
                self.smoothing_alpha * probability
                +
                (1.0 - self.smoothing_alpha)
                * self.smoothed_probability
            )

        return self.smoothed_probability

    # ========================================================
    # Persistence tracking
    # ========================================================

    def _update_persistence(
        self,
        probability: float,
    ) -> int:
        """
        Track consecutive suspicious windows.

        A window is considered suspicious when
        spoof probability >= 0.50.

        This persistence criterion is a prototype
        implementation decision.
        """

        if probability >= 0.50:

            self.persistence_count += 1

        else:

            # Gradual decay instead of an immediate reset.
            self.persistence_count = max(
                0,
                self.persistence_count - 1,
            )

        return self.persistence_count

    # ========================================================
    # Persistence bonus
    # ========================================================

    def _calculate_persistence_bonus(
        self,
    ) -> float:
        """
        Convert persistence into an additional risk
        contribution.

        Maximum contribution = 20 points.
        """

        if self.persistence_count <= 0:
            return 0.0

        ratio = min(
            self.persistence_count
            /
            self.persistence_window,
            1.0,
        )

        return (
            ratio
            * MAX_PERSISTENCE_BONUS
        )

    # ========================================================
    # Risk score
    # ========================================================

    def _calculate_risk_score(
        self,
        smoothed_probability: float,
        persistence_bonus: float,
    ) -> float:
        """
        Convert smoothed spoof probability into
        a 0-100 risk score.

        Core evidence:
            probability * 80

        Persistence:
            up to +20

        Therefore:
            maximum = 100.
        """

        base_risk = (
            smoothed_probability
            * 80.0
        )

        risk_score = (
            base_risk
            + persistence_bonus
        )

        return max(
            0.0,
            min(
                100.0,
                risk_score,
            ),
        )

    # ========================================================
    # Risk classification
    # ========================================================

    @staticmethod
    def _classify_risk(
        risk_score: float,
    ):
        """
        Map risk score to security policy.
        """

        if risk_score <= LOW_MAX:

            return (
                "LOW",
                "MONITOR",
            )

        if risk_score <= MEDIUM_MAX:

            return (
                "MEDIUM",
                "WARNING",
            )

        if risk_score <= HIGH_MAX:

            return (
                "HIGH",
                "VERIFY",
            )

        return (
            "CRITICAL",
            "BLOCK",
        )

    # ========================================================
    # Message generation
    # ========================================================

    @staticmethod
    def _generate_message(
        risk_level: str,
        action: str,
        persistence_count: int,
    ):

        if risk_level == "LOW":

            return (
                "Voice appears consistent with "
                "normal speech patterns."
            )

        if risk_level == "MEDIUM":

            return (
                "Synthetic voice indicators detected; "
                "continue monitoring."
            )

        if risk_level == "HIGH":

            return (
                "Persistent synthetic voice indicators "
                "detected. Verification required."
            )

        return (
            "Critical synthetic voice risk detected. "
            "High-risk action should be blocked."
        )

    # ========================================================
    # Update
    # ========================================================

    def update(
        self,
        spoof_probability: float,
    ) -> RiskResult:
        """
        Process one incoming Model B prediction.

        Args:
            spoof_probability:
                Model B output in range [0, 1].

        Returns:
            RiskResult
        """

        probability = (
            self._validate_probability(
                spoof_probability
            )
        )

        self.window_count += 1

        # ----------------------------------------------------
        # Temporal smoothing
        # ----------------------------------------------------

        smoothed_probability = (
            self._update_smoothed_probability(
                probability
            )
        )

        # ----------------------------------------------------
        # Persistence
        # ----------------------------------------------------

        persistence_count = (
            self._update_persistence(
                probability
            )
        )

        persistence_bonus = (
            self._calculate_persistence_bonus()
        )

        # ----------------------------------------------------
        # Risk
        # ----------------------------------------------------

        risk_score = (
            self._calculate_risk_score(
                smoothed_probability,
                persistence_bonus,
            )
        )

        # ----------------------------------------------------
        # Security classification
        # ----------------------------------------------------

        risk_level, action = (
            self._classify_risk(
                risk_score
            )
        )

        message = (
            self._generate_message(
                risk_level,
                action,
                persistence_count,
            )
        )

        return RiskResult(
            spoof_probability=probability,
            smoothed_probability=smoothed_probability,
            persistence_count=persistence_count,
            persistence_bonus=persistence_bonus,
            risk_score=risk_score,
            risk_level=risk_level,
            action=action,
            message=message,
        )


# ============================================================
# Demo / test
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("EchoVerify - Temporal Risk Engine Test")
    print("=" * 60)

    engine = TemporalRiskEngine()

    # --------------------------------------------------------
    # Simulated normal voice
    # --------------------------------------------------------

    normal_sequence = [
        0.01,
        0.02,
        0.03,
        0.04,
        0.02,
        0.05,
    ]

    print()
    print("NORMAL VOICE TEST")
    print("-" * 60)

    for index, probability in enumerate(
        normal_sequence,
        start=1,
    ):

        result = engine.update(
            probability
        )

        print(
            f"Window {index:02d} | "
            f"Spoof: {result.spoof_probability:.3f} | "
            f"Smooth: {result.smoothed_probability:.3f} | "
            f"Persistence: {result.persistence_count} | "
            f"Risk: {result.risk_score:6.2f} | "
            f"{result.risk_level:8s} | "
            f"{result.action}"
        )

    # --------------------------------------------------------
    # Reset for suspicious sequence
    # --------------------------------------------------------

    engine.reset()

    suspicious_sequence = [
        0.20,
        0.35,
        0.55,
        0.70,
        0.82,
        0.90,
        0.94,
        0.97,
        0.98,
    ]

    print()
    print("SUSPICIOUS / FAKE VOICE TEST")
    print("-" * 60)

    for index, probability in enumerate(
        suspicious_sequence,
        start=1,
    ):

        result = engine.update(
            probability
        )

        print(
            f"Window {index:02d} | "
            f"Spoof: {result.spoof_probability:.3f} | "
            f"Smooth: {result.smoothed_probability:.3f} | "
            f"Persistence: {result.persistence_count} | "
            f"Risk: {result.risk_score:6.2f} | "
            f"{result.risk_level:8s} | "
            f"{result.action}"
        )

    print()
    print("=" * 60)
    print("TEMPORAL RISK ENGINE TEST COMPLETED")
    print("=" * 60)
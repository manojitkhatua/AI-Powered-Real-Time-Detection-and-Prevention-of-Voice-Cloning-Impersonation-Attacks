import sys
import tempfile
import uuid
from pathlib import Path

# ------------------------------------------------------------
# Make backend/app imports work regardless of launch location
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = PROJECT_ROOT.parent

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.models.inference import predict_audio_file
from backend.app.risk.risk_engine import TemporalRiskEngine

from backend.app.api.schemas import (
    DetectionResponse,
    HealthResponse,
)


router = APIRouter(prefix="/api")


# ============================================================
# HEALTH
# ============================================================

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="online",
        service="EchoVerify Backend",
    )


# ============================================================
# AUDIO ANALYSIS
# ============================================================

@router.post(
    "/analyze",
    response_model=DetectionResponse,
)
async def analyze_audio(
    audio: UploadFile = File(...)
):
    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="No audio file provided.",
        )

    # --------------------------------------------------------
    # Basic extension validation
    # --------------------------------------------------------

    allowed_extensions = {
        ".wav",
        ".mp3",
        ".m4a",
        ".flac",
        ".ogg",
    }

    extension = Path(audio.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use WAV, MP3, M4A, FLAC, or OGG."
            ),
        )

    # --------------------------------------------------------
    # Save uploaded file temporarily
    # --------------------------------------------------------

    temp_path = None

    try:
        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded audio file is empty.",
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = Path(temp_file.name)

        # ----------------------------------------------------
        # Run Model B inference
        # ----------------------------------------------------

        predictions = predict_audio_file(
            str(temp_path)
        )

        if not predictions:
            raise HTTPException(
                status_code=422,
                detail="No audio windows could be analyzed.",
            )

        # ----------------------------------------------------
        # Extract spoof probabilities
        # ----------------------------------------------------

        probabilities = [
            float(item["spoof_probability"])
            for item in predictions
        ]

        # ----------------------------------------------------
        # Temporal Risk Engine
        # ----------------------------------------------------

        risk_engine = TemporalRiskEngine()

        final_risk = None

        for probability in probabilities:
            final_risk = risk_engine.update(
                probability
            )

        if final_risk is None:
            raise HTTPException(
                status_code=422,
                detail="Risk engine produced no result.",
            )

        # ----------------------------------------------------
        # Final values
        # ----------------------------------------------------

        final_risk_score = float(
            final_risk.risk_score
        )

        final_risk_level = str(
            final_risk.risk_level
        )

        final_action = str(
            final_risk.action
        )

        mean_probability = (
            sum(probabilities)
            / len(probabilities)
        )

        # ----------------------------------------------------
        # Determine final voice status
        # ----------------------------------------------------

        if final_action == "BLOCK":
            voice_status = "SUSPICIOUS"

        elif final_action == "VERIFY":
            voice_status = "SUSPICIOUS"

        elif final_risk_level == "MEDIUM":
            voice_status = "SUSPICIOUS"

        else:
            voice_status = "REAL"

        # ----------------------------------------------------
        # Human-readable message
        # ----------------------------------------------------

        if final_action == "BLOCK":
            message = (
                "Persistent synthetic voice indicators detected."
            )

        elif final_action == "VERIFY":
            message = (
                "Suspicious voice behavior detected. "
                "Caller verification recommended."
            )

        elif final_action == "WARNING":
            message = (
                "Unusual voice characteristics detected."
            )

        else:
            message = (
                "No significant synthetic voice indicators detected."
            )

        # ----------------------------------------------------
        # Session ID
        # ----------------------------------------------------

        session_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"

        return DetectionResponse(
            session_id=session_id,
            filename=audio.filename,
            windows_analyzed=len(probabilities),
            spoof_probability=round(
                mean_probability,
                4,
            ),
            risk_score=round(
                final_risk_score,
                2,
            ),
            risk_level=final_risk_level,
            action=final_action,
            voice_status=voice_status,
            message=message,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Audio analysis failed: {exc}",
        )

    finally:
        # ----------------------------------------------------
        # Delete temporary upload
        # ----------------------------------------------------

        if temp_path is not None:
            try:
                temp_path.unlink(
                    missing_ok=True
                )
            except Exception:
                pass
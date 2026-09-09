from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class DetectionResponse(BaseModel):
    session_id: str
    filename: str
    windows_analyzed: int
    spoof_probability: float
    risk_score: float
    risk_level: str
    action: str
    voice_status: str
    message: str
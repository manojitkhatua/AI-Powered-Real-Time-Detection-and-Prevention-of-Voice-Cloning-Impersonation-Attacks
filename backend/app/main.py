from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.api.websocket import router as websocket_router


app = FastAPI(
    title="EchoVerify",
    description=(
        "AI-powered real-time voice cloning "
        "and impersonation detection API"
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API
app.include_router(router)

# WebSocket
app.include_router(websocket_router)


@app.get("/")
def root():
    return {
        "service": "EchoVerify",
        "status": "online",
        "message": "Voice security backend is running.",
    }
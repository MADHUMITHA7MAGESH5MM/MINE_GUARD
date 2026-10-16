"""
Single FastAPI entry point for the whole Mineguard backend.
Run from project root with: uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from src.database.database import Base, engine, get_db
from src.database.models import Incident
from backend.schemas import (
    IncidentPredictionRequest,
    PredictionResponse,
    HazardBarrierMatrixItem,
)
from backend.model_service import model_service
from backend.routers import incidents_router, analytics_router

# Create DB tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MINEGUARD: Predictive AI Command Center API",
    description="Real-Time High-SIF Prevention, Persistence, Matrix & Analytics Endpoints",
    version="1.0.0",
)

# ---- CORS: allows React (Vite) frontend and IBM LinuxONE cloud tunnels ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# WEBSOCKET CONNECTION MANAGER
# ==========================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()
app.state.ws_manager = manager


# ==========================================================
# MOUNT ROUTERS
# ==========================================================

app.include_router(incidents_router.router)
app.include_router(analytics_router.router)


# ==========================================================
# CORE & PHASE 3 MATRIX ENDPOINTS
# ==========================================================

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "Mineguard SIF Inference Engine Operational",
        "architecture": "IBM LinuxONE s390x Ready",
    }


@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict SIF Risk, Rules, and Entities (no persistence)",
)
def predict_sif(payload: IncidentPredictionRequest):
    if not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report text cannot be empty.",
        )
    try:
        return model_service.predict(payload.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference pipeline failed: {str(e)}",
        )


@app.get(
    "/api/v1/matrix/hazard-barrier",
    response_model=List[HazardBarrierMatrixItem],
    tags=["matrix"],
    summary="Precursor Co-Occurrence Matrix (Hazard x Barrier Failure)",
)
def get_precursor_matrix(db: Session = Depends(get_db)):
    """
    Phase 3 Workflow Endpoint: Calculate co-occurrences between extracted hazards
    and failed controls (e.g., linking Roof Fall with No Roof Bolting).
    """
    high_incidents = (
        db.query(Incident.hazards, Incident.barrier_failures)
        .filter(Incident.sif_verdict == "HIGH")
        .all()
    )

    combo_counts = {}
    for hazards_str, barriers_str in high_incidents:
        hazards = [h.strip() for h in (hazards_str or "").split(";") if h.strip()]
        barriers = [b.strip() for b in (barriers_str or "").split(";") if b.strip()]
        for h in hazards:
            for b in barriers:
                key = (h, b)
                combo_counts[key] = combo_counts.get(key, 0) + 1

    results = [
        HazardBarrierMatrixItem(hazard=h, barrier_failure=b, count=c)
        for (h, b), c in combo_counts.items()
    ]
    return sorted(results, key=lambda x: x.count, reverse=True)[:25]


@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint (/ws/alerts) for broadcasting real-time panel status
    updates and high-SIF alerts to the Command Center dashboard.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
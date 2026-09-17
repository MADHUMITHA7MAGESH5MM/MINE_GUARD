"""
Single FastAPI entry point for the whole backend.
Run with: uvicorn main:app --reload --port 8000   (from inside the backend/ folder)
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.database.database import Base, engine
from backend.schemas import IncidentPredictionRequest, PredictionResponse
from backend.model_service import model_service

from backend.routers import incidents_router
from backend.routers import analytics_router

# Create DB tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OIL-INDIA SIF Prediction API",
    description="ML Inference, Persistence & Analytics Endpoints",
    version="1.0.0",
)

# ---- CORS: required for the React (Vite) frontend on a different port to
# be allowed to call this API at all. Without this, every fetch() from the
# browser fails with a CORS error regardless of whether the backend works. ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8443",
        "http://127.0.0.1:8443",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router.router)
app.include_router(analytics_router.router)


@app.get("/")
def health_check():
    return {"status": "online", "message": "SIF Inference Engine Operational"}


@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict SIF Risk, Rules, and Entities (no persistence)",
)
def predict_sif(payload: IncidentPredictionRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report text cannot be empty.")
    try:
        return model_service.predict(payload.text)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference pipeline failed: {str(e)}")

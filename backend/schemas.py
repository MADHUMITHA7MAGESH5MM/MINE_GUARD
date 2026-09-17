from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==========================================================
# ML INFERENCE REQUEST
# ==========================================================

class IncidentPredictionRequest(BaseModel):
    text: str


# ==========================================================
# ML INFERENCE RESPONSE
# ==========================================================

class PredictionResponse(BaseModel):
    sif_verdict: str
    sif_probability: float

    life_saving_rules: List[str] = []
    activities: List[str] = []
    locations: List[str] = []
    hazards: List[str] = []
    barrier_failures: List[str] = []


# ==========================================================
# INCIDENT CREATION
# ==========================================================

class IncidentCreateRequest(BaseModel):
    raw_text: str

    site: Optional[str] = None

    incident_type: Optional[str] = None
    severity: Optional[str] = None
    department: Optional[str] = None

    submitted_via: str = "text"


# ==========================================================
# INCIDENT RESPONSE
# ==========================================================

class IncidentResponse(BaseModel):
    id: int

    raw_text: str
    cleaned_text: Optional[str]

    site: Optional[str]
    incident_type: Optional[str]
    severity: Optional[str]
    department: Optional[str]
    submitted_via: str
    submitted_at: datetime

    sif_verdict: str
    sif_probability: float

    life_saving_rules: List[str]
    activities: List[str]
    locations: List[str]
    hazards: List[str]
    barrier_failures: List[str]

    reviewed_by_human: bool

    human_corrected_verdict: Optional[str]
    reviewer_notes: Optional[str]
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==========================================================
# HUMAN REVIEW
# ==========================================================

class IncidentReviewUpdate(BaseModel):
    human_corrected_verdict: Optional[str] = None
    reviewer_notes: Optional[str] = None


# ==========================================================
# ANALYTICS SUMMARY
# ==========================================================

class AnalyticsSummary(BaseModel):
    total_incidents: int
    high_sif_count: int
    low_sif_count: int
    review_pending_count: int
    high_sif_ratio: float
    avg_confidence: float


# ==========================================================
# SITE ANALYTICS
# ==========================================================

class SiteAnalyticsItem(BaseModel):
    site: str
    total_reports: int
    high_sif_count: int
    high_sif_density: float


# ==========================================================
# PATTERN ANALYTICS
# ==========================================================

class PatternAnalyticsItem(BaseModel):
    activity: str
    barrier_failure: str
    count: int
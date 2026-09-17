from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone

try:
    from src.database.database import Base
except ModuleNotFoundError:
    from database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core Incident Data
    raw_text = Column(String, nullable=False)
    cleaned_text = Column(String, nullable=True)
    site = Column(String, nullable=True)
    incident_type = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    department = Column(String, nullable=True)
    submitted_via = Column(String, default="text")
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Machine Learning Outputs
    sif_verdict = Column(String, nullable=False)
    sif_probability = Column(Float, nullable=False)
    
    # Extracted Entities (Stored as semicolon-separated strings)
    life_saving_rules = Column(String, nullable=True)
    activities = Column(String, nullable=True)
    locations = Column(String, nullable=True)
    hazards = Column(String, nullable=True)  # <--- NEW FIELD ADDED HERE
    barrier_failures = Column(String, nullable=True)
    
    # Human-in-the-Loop Tracking
    reviewed_by_human = Column(Boolean, default=False)
    human_corrected_verdict = Column(String, nullable=True)
    reviewer_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
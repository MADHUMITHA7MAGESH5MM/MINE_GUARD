"""
Incident endpoints: creation (with ML inference), historical retrieval with
filters, human-in-the-loop review updates, and bulk CSV uploads.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import pandas as pd
import io

from src.database.database import get_db
import src.database.crud as crud
from backend.schemas import (
    IncidentCreateRequest, IncidentResponse, IncidentReviewUpdate
)
from backend.model_service import model_service

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


def _split_field(value: str) -> List[str]:
    """Convert a stored semicolon-separated string field back into a list."""
    if not value:
        return []
    return [v.strip() for v in value.split(';') if v.strip()]


@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(payload: IncidentCreateRequest, db: Session = Depends(get_db)):
    """
    Runs the raw report text through the ML pipeline, then persists the
    full result (prediction + original submission) to the database.
    """
    # 1. Run inference via Naveena's service
    prediction = model_service.predict(payload.raw_text)

    # 2. Assemble the full record to persist
    incident_data = {
        "raw_text": payload.raw_text,
        "cleaned_text": prediction.get("cleaned_text"),

        "site": payload.site,
        "incident_type": payload.incident_type,
        "severity": payload.severity,
        "department": payload.department,

        "submitted_via": payload.submitted_via,
        "submitted_at": datetime.utcnow(),

        "sif_verdict": prediction["sif_verdict"],
        "sif_probability": prediction["sif_probability"],

        "life_saving_rules": ";".join(prediction.get("life_saving_rules", [])),
        "activities": ";".join(prediction.get("activities", [])),
        "locations": ";".join(prediction.get("locations", [])),
        "hazards": ";".join(prediction.get("hazards", [])),
        "barrier_failures": ";".join(prediction.get("barrier_failures", [])),

        "reviewed_by_human": False,
    }

    incident = crud.create_incident(db, incident_data)

    # 3. Convert list-string fields back to lists for the response
    return IncidentResponse(
        id=incident.id,
        raw_text=incident.raw_text,
        cleaned_text=incident.cleaned_text,

        site=incident.site,
        incident_type=incident.incident_type,
        severity=incident.severity,
        department=incident.department,

        submitted_via=incident.submitted_via,
        submitted_at=incident.submitted_at,

        sif_verdict=incident.sif_verdict,
        sif_probability=incident.sif_probability,

        life_saving_rules=_split_field(incident.life_saving_rules),
        activities=_split_field(incident.activities),
        locations=_split_field(incident.locations),
        hazards=_split_field(incident.hazards),
        barrier_failures=_split_field(incident.barrier_failures),

        reviewed_by_human=incident.reviewed_by_human,
        human_corrected_verdict=incident.human_corrected_verdict,
        reviewer_notes=incident.reviewer_notes,
        reviewed_at=incident.reviewed_at,
    )


@router.post("/bulk", status_code=201)
async def upload_bulk_incidents(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Parses a bulk CSV file, runs ML inference on each report, and saves to the DB.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are currently supported for bulk upload.")
        
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # FIX: Standardize all column headers to lowercase and remove spaces
        df.columns = df.columns.str.lower().str.strip()
        df = df.fillna("")
        
        success_count = 0
        
        for _, row in df.iterrows():
            # Check for multiple common naming conventions
            report_text = str(row.get("report", row.get("raw_text", row.get("description", row.get("incident", ""))))).strip()
            
            if not report_text:
                continue
                
            # 1. Run inference
            prediction = model_service.predict(report_text)
            
            # 2. Assemble data
            incident_data = {
                "raw_text": report_text,
                "cleaned_text": prediction.get("cleaned_text"),
                "site": str(row.get("site", "Unknown")),
                "incident_type": str(row.get("incident_type", "Incident")),
                "severity": str(row.get("severity", "Medium")),
                "department": str(row.get("department", "Operations")),
                "submitted_via": "bulk_upload",
                "submitted_at": datetime.utcnow(),
                "sif_verdict": prediction.get("sif_verdict", "LOW"),
                "sif_probability": float(prediction.get("sif_probability", 0.0)),
                "life_saving_rules": ";".join(prediction.get("life_saving_rules", [])),
                "activities": ";".join(prediction.get("activities", [])),
                "locations": ";".join(prediction.get("locations", [])),
                "hazards": ";".join(prediction.get("hazards", [])),
                "barrier_failures": ";".join(prediction.get("barrier_failures", [])),
                "reviewed_by_human": False,
            }
            
            crud.create_incident(db, incident_data)
            success_count += 1
            
        return {"status": "success", "processed": success_count, "message": f"Successfully ingested {success_count} reports."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk processing failed: {str(e)}")


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    sif_verdict: Optional[str] = Query(None, pattern="^(HIGH|LOW|REVIEW)$"),
    rule: Optional[str] = Query(None, description="Filter by a specific Life-Saving Rule"),
    reviewed_by_human: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Historical retrieval with filtering by SIF severity, rule category, and
    human-review status, plus pagination.
    """
    incidents = crud.get_incidents(
        db, skip=skip, limit=limit,
        sif_verdict=sif_verdict, rule=rule, reviewed_by_human=reviewed_by_human
    )
    return [
        IncidentResponse(
            id=i.id, raw_text=i.raw_text, cleaned_text=i.cleaned_text,
            site=i.site, incident_type=i.incident_type, severity=i.severity, department=i.department,
            submitted_via=i.submitted_via, submitted_at=i.submitted_at,
            sif_verdict=i.sif_verdict, sif_probability=i.sif_probability,
            life_saving_rules=_split_field(i.life_saving_rules),
            activities=_split_field(i.activities),
            locations=_split_field(i.locations),
            hazards=_split_field(i.hazards),
            barrier_failures=_split_field(i.barrier_failures),
            reviewed_by_human=i.reviewed_by_human,
            human_corrected_verdict=i.human_corrected_verdict,
            reviewer_notes=i.reviewer_notes, reviewed_at=i.reviewed_at,
        )
        for i in incidents
    ]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = crud.get_incident_by_id(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse(
        id=incident.id, raw_text=incident.raw_text, cleaned_text=incident.cleaned_text,
        site=incident.site, incident_type=incident.incident_type, severity=incident.severity, department=incident.department,
        submitted_via=incident.submitted_via, submitted_at=incident.submitted_at,
        sif_verdict=incident.sif_verdict, sif_probability=incident.sif_probability,
        life_saving_rules=_split_field(incident.life_saving_rules),
        activities=_split_field(incident.activities),
        locations=_split_field(incident.locations),
        hazards=_split_field(incident.hazards),
        barrier_failures=_split_field(incident.barrier_failures),
        reviewed_by_human=incident.reviewed_by_human,
        human_corrected_verdict=incident.human_corrected_verdict,
        reviewer_notes=incident.reviewer_notes, reviewed_at=incident.reviewed_at,
    )


@router.patch("/{incident_id}/review", response_model=IncidentResponse)
def review_incident(incident_id: int, payload: IncidentReviewUpdate, db: Session = Depends(get_db)):
    """
    Human-in-the-loop endpoint: a safety officer confirms or overrides the
    AI's verdict, especially for REVIEW-tier (borderline) predictions.
    """
    incident = crud.get_incident_by_id(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = {"reviewed_by_human": True, "reviewed_at": datetime.utcnow()}
    if payload.human_corrected_verdict is not None:
        update_data["human_corrected_verdict"] = payload.human_corrected_verdict
    if payload.reviewer_notes is not None:
        update_data["reviewer_notes"] = payload.reviewer_notes

    updated = crud.update_incident(db, incident_id, update_data)
    return IncidentResponse(
        id=updated.id, raw_text=updated.raw_text, cleaned_text=updated.cleaned_text,
        site=updated.site, incident_type=updated.incident_type, severity=updated.severity, department=updated.department,
        submitted_via=updated.submitted_via, submitted_at=updated.submitted_at,
        sif_verdict=updated.sif_verdict, sif_probability=updated.sif_probability,
        life_saving_rules=_split_field(updated.life_saving_rules),
        activities=_split_field(updated.activities),
        locations=_split_field(updated.locations),
        hazards=_split_field(updated.hazards),
        barrier_failures=_split_field(updated.barrier_failures),
        reviewed_by_human=updated.reviewed_by_human,
        human_corrected_verdict=updated.human_corrected_verdict,
        reviewer_notes=updated.reviewer_notes, reviewed_at=updated.reviewed_at,
    )
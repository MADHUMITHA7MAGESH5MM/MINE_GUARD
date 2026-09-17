from typing import Optional
from sqlalchemy.orm import Session

try:
    from src.database.models import Incident
except ModuleNotFoundError:
    from models import Incident


def get_incident_by_id(db: Session, incident_id: int):
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_incidents(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    sif_verdict: Optional[str] = None,
    rule: Optional[str] = None,
    reviewed_by_human: Optional[bool] = None,
):
    query = db.query(Incident)

    if sif_verdict:
        query = query.filter(Incident.sif_verdict == sif_verdict)
    if rule:
        query = query.filter(Incident.life_saving_rules.ilike(f"%{rule}%"))
    if reviewed_by_human is not None:
        query = query.filter(Incident.reviewed_by_human == reviewed_by_human)

    return query.offset(skip).limit(limit).all()


def create_incident(db: Session, incident_data: dict):
    """Creates a new incident from a dictionary payload."""
    db_incident = Incident(**incident_data)
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident


def update_incident(db: Session, incident_id: int, update_data: dict):
    """Dynamically updates an incident based on the provided dictionary."""
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        return None

    for key, value in update_data.items():
        setattr(incident, key, value)

    db.commit()
    db.refresh(incident)
    return incident
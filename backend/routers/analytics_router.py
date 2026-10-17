"""
Analytics endpoints feeding the Mineguard frontend dashboard:
- Summary KPIs
- Time-series trends (/trends)
- DGMS cause distribution (/cause-distribution)
- Workplace/place distribution (/place-distribution)
- Mining subsidiary risk ranking (/subsidiary-ranking & /sites)
- Hazard x Barrier co-occurrence matrix (/patterns & /hazard-barrier)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from datetime import datetime

from src.database.database import get_db
from src.database.models import Incident
from backend.schemas import (
    AnalyticsSummary,
    SiteAnalyticsItem,
    PatternAnalyticsItem,
    TrendPoint,
    CauseDistributionItem,
    PlaceDistributionItem,
    SubsidiaryRankItem,
    HazardBarrierMatrixItem,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Incident.id)).scalar() or 0
    high = db.query(func.count(Incident.id)).filter(Incident.sif_verdict == "HIGH").scalar() or 0
    low = db.query(func.count(Incident.id)).filter(Incident.sif_verdict == "LOW").scalar() or 0
    review_pending = (
        db.query(func.count(Incident.id))
        .filter(Incident.reviewed_by_human == False)
        .scalar() or 0
    )
    avg_conf = db.query(func.avg(Incident.sif_probability)).scalar() or 0.0

    return AnalyticsSummary(
        total_incidents=total,
        high_sif_count=high,
        low_sif_count=low,
        review_pending_count=review_pending,
        high_sif_ratio=round(high / total * 100, 1) if total else 0.0,
        avg_confidence=round(float(avg_conf), 3),
    )


@router.get("/sites", response_model=List[SiteAnalyticsItem])
def get_site_analytics(db: Session = Depends(get_db)):
    """Site hotspot ranking by HIGH SIF-potential density."""
    rows = (
        db.query(
            Incident.site,
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.sif_verdict == "HIGH", 1), else_=0)).label("high_count"),
        )
        .filter(Incident.site.isnot(None))
        .group_by(Incident.site)
        .all()
    )
    results = [
        SiteAnalyticsItem(
            site=r.site,
            total_reports=r.total,
            high_sif_count=int(r.high_count or 0),
            high_sif_density=round((r.high_count or 0) / r.total * 100, 1) if r.total else 0.0,
        )
        for r in rows
    ]
    return sorted(results, key=lambda x: x.high_sif_density, reverse=True)


@router.get("/patterns", response_model=List[PatternAnalyticsItem])
def get_pattern_analytics(db: Session = Depends(get_db)):
    """Recurring activity + barrier-failure combinations among HIGH SIF reports."""
    high_incidents = (
        db.query(Incident.activities, Incident.barrier_failures)
        .filter(Incident.sif_verdict == "HIGH")
        .all()
    )

    combo_counts = {}
    for activities_str, barriers_str in high_incidents:
        activities = [a.strip() for a in (activities_str or "").split(";") if a.strip()]
        barriers = [b.strip() for b in (barriers_str or "").split(";") if b.strip()]
        for a in activities:
            for b in barriers:
                key = (a, b)
                combo_counts[key] = combo_counts.get(key, 0) + 1

    results = [
        PatternAnalyticsItem(activity=a, barrier_failure=b, count=c)
        for (a, b), c in combo_counts.items()
    ]
    return sorted(results, key=lambda x: x.count, reverse=True)[:20]


@router.get("/trends", response_model=List[TrendPoint])
def get_sif_trends(db: Session = Depends(get_db)):
    """Time-series data for the SIF Event Trend chart (High-SIF vs. Low-Risk over time)."""
    records = (
        db.query(
            func.strftime("%Y-%m-%d", Incident.submitted_at).label("date_str"),
            func.sum(case((Incident.sif_verdict == "HIGH", 1), else_=0)).label("high_count"),
            func.sum(case((Incident.sif_verdict != "HIGH", 1), else_=0)).label("low_count"),
        )
        .group_by("date_str")
        .order_by("date_str")
        .all()
    )
    return [
        TrendPoint(
            date=r.date_str or datetime.utcnow().strftime("%Y-%m-%d"),
            high_sif=int(r.high_count or 0),
            low_risk=int(r.low_count or 0),
        )
        for r in records
    ]


@router.get("/cause-distribution", response_model=List[CauseDistributionItem])
def get_cause_distribution(db: Session = Depends(get_db)):
    """Aggregate incident counts by DGMS cause categories for the Pie/Donut chart."""
    records = (
        db.query(
            Incident.incident_type.label("cause"),
            func.count(Incident.id).label("count"),
        )
        .filter(Incident.incident_type.isnot(None))
        .group_by(Incident.incident_type)
        .all()
    )
    return [CauseDistributionItem(cause=r.cause, count=r.count) for r in records]


@router.get("/place-distribution", response_model=List[PlaceDistributionItem])
def get_place_distribution(db: Session = Depends(get_db)):
    """Output Belowground vs. Opencast vs. Surface ratios for the Bar chart."""
    records = (
        db.query(
            Incident.department.label("place"),
            func.count(Incident.id).label("count"),
        )
        .filter(Incident.department.isnot(None))
        .group_by(Incident.department)
        .all()
    )
    return [PlaceDistributionItem(place=r.place, count=r.count) for r in records]


@router.get("/subsidiary-ranking", response_model=List[SubsidiaryRankItem])
def get_subsidiary_ranking(db: Session = Depends(get_db)):
    """Rank mine operators/concessions (e.g., ECL, BCCL, SECL, SCCL) by risk index."""
    records = (
        db.query(
            Incident.site.label("subsidiary"),
            func.count(Incident.id).label("total"),
            func.sum(case((Incident.sif_verdict == "HIGH", 1), else_=0)).label("high_count"),
            func.avg(Incident.sif_probability).label("avg_prob"),
        )
        .filter(Incident.site.isnot(None))
        .group_by(Incident.site)
        .all()
    )
    results = [
        SubsidiaryRankItem(
            subsidiary=r.subsidiary,
            risk_index=round(float(r.avg_prob or 0.0) * 100, 2),
            total_incidents=r.total,
            high_sif_count=int(r.high_count or 0),
        )
        for r in records
    ]
    return sorted(results, key=lambda x: x.risk_index, reverse=True)


@router.get("/hazard-barrier", response_model=List[HazardBarrierMatrixItem])
def get_hazard_barrier_analytics(db: Session = Depends(get_db)):
    """Calculate co-occurrences between extracted hazards and failed controls."""
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
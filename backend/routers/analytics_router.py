"""
Analytics endpoints feeding the frontend dashboard (Dev E's Page 1 metrics,
Dev F's site heatmap and pattern discovery pages).

These use raw SQL/SQLAlchemy aggregation rather than pulling all rows into
Python and computing in pandas -- keeps this fast even as the incidents
table grows, and matches how a real backend should compute dashboard stats.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List

from src.database.database import get_db
from src.database.models import Incident          # Afreen/Madhu's SQLAlchemy model
from backend.schemas import AnalyticsSummary, SiteAnalyticsItem, PatternAnalyticsItem

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(Incident.id)).scalar() or 0
    high = db.query(func.count(Incident.id)).filter(Incident.sif_verdict == "HIGH").scalar() or 0
    low = db.query(func.count(Incident.id)).filter(Incident.sif_verdict == "LOW").scalar() or 0
    review_pending = db.query(
        func.count(Incident.id)
    ).filter(
        Incident.reviewed_by_human == False
    ).scalar() or 0
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
    """Site hotspot ranking by HIGH SIF-potential density -- the core
    'where should HSE focus interventions' output the problem statement asks for."""
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
            high_sif_count=r.high_count,
            high_sif_density=round(r.high_count / r.total * 100, 1) if r.total else 0.0,
        )
        for r in rows
    ]
    return sorted(results, key=lambda x: x.high_sif_density, reverse=True)


@router.get("/patterns", response_model=List[PatternAnalyticsItem])
def get_pattern_analytics(db: Session = Depends(get_db)):
    """
    Recurring activity + barrier-failure combinations among HIGH SIF reports.
    NOTE: activities/barrier_failures are stored as semicolon-joined strings,
    so this does the combination-counting in Python after a lighter DB query
    rather than trying to do it in raw SQL against a delimited string column.
    A future improvement: normalize these into their own related tables so
    this can become a pure SQL GROUP BY.
    """
    high_incidents = (
        db.query(Incident.activities, Incident.barrier_failures)
        .filter(Incident.sif_verdict == "HIGH")
        .all()
    )

    combo_counts = {}
    for activities_str, barriers_str in high_incidents:
        activities = [a.strip() for a in (activities_str or "").split(';') if a.strip()]
        barriers = [b.strip() for b in (barriers_str or "").split(';') if b.strip()]
        for a in activities:
            for b in barriers:
                key = (a, b)
                combo_counts[key] = combo_counts.get(key, 0) + 1

    results = [
        PatternAnalyticsItem(activity=a, barrier_failure=b, count=c)
        for (a, b), c in combo_counts.items()
    ]
    return sorted(results, key=lambda x: x.count, reverse=True)[:20]  # top 20 patterns
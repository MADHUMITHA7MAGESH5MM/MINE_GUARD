import os
import sys
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy.orm import Session
import random
from src.database.database import SessionLocal
from src.database.models import Incident
# If there are any other local imports (like crud or schemas), add 'src.' to them as well!

# Resolve project paths to ensure modules import cleanly regardless of execution context
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

# Add project root and src directory to Python path
for path in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "src")]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

# Module imports with fallback handling
try:
    from src.database.database import SessionLocal
    from src.database import crud
except ModuleNotFoundError:
    try:
        from database.database import SessionLocal
        import database.crud as crud
    except ModuleNotFoundError:
        from database import SessionLocal
        import crud

try:
    from backend.model_service import model_service
except ModuleNotFoundError:
    try:

        from backend.model_service import model_service
    except ModuleNotFoundError:
        try:
            from model_service import model_service
        except ModuleNotFoundError as e:
            print(f"[ERROR] Could not resolve model_service import path: {e}")
            sys.exit(1)


def resolve_csv_path(relative_path: str = "../../data/final_sif_1000.csv") -> str:
    """Dynamically resolves the CSV path relative to the script location or project root."""
    target_path = os.path.abspath(os.path.join(SCRIPT_DIR, relative_path))
    
    if not os.path.exists(target_path):
        fallback_path = os.path.join(PROJECT_ROOT, "data", "final_sif_1000.csv")
        if os.path.exists(fallback_path):
            return fallback_path
            
    return target_path


def seed_database(csv_path: str = "../../data/final_sif_1000.csv") -> None:
    """Reads safety reports from CSV, runs model inference, and seeds records to database."""
    resolved_csv = resolve_csv_path(csv_path)

    if not os.path.exists(resolved_csv):
        print(f"[ERROR] Could not locate CSV dataset at: {resolved_csv}")
        return

    db: Session = SessionLocal()

    sites = [
    "SECL - Churcha Colliery",
    "BCCL - Jharia Division",
    "ECL - Raniganj Area",
    "SCCL - Singareni Deep Seam",
    "NCL - Singrauli Opencast",
    "WCL - Nagpur Wardha Valley",
    "MCL - Talcher Concession"
]
    try:
        print(f"Reading dataset from {resolved_csv}...")
        df = pd.read_csv(resolved_csv)
        df = df.fillna("")

        success_count = 0
        total_rows = len(df)

        print("Starting ML inference pipeline. Processing records...")

        for index, row in df.iterrows():
            report_text = str(row.get("report", row.get("raw_text", ""))).strip()
            if not report_text:
                continue

            # Execute model inference
            prediction = model_service.predict(report_text)

            # Build standardized incident payload
            incident_data = {
                "raw_text": report_text,
                "cleaned_text": str(prediction.get("cleaned_text", "")),
                "site": random.choice(sites),
                "submitted_via": "batch_seed",
                "submitted_at": datetime.now(timezone.utc),
                "sif_verdict": str(prediction.get("sif_verdict", "LOW")),
                "sif_probability": float(prediction.get("sif_probability", 0.0)),
                "life_saving_rules": ";".join(prediction.get("life_saving_rules", [])),
                "activities": ";".join(prediction.get("activities", [])),
                "locations": ";".join(prediction.get("locations", [])),
                "hazards": ";".join(prediction.get("hazards", [])),
                "barrier_failures": ";".join(prediction.get("barrier_failures", [])),
                "reviewed_by_human": False
            }

            crud.create_incident(db, incident_data)
            success_count += 1

            if success_count % 50 == 0 or success_count == total_rows:
                print(f"Progress: {success_count}/{total_rows} incidents processed...")

        print(f"\n[SUCCESS] Successfully seeded {success_count} incidents into the database.")

    except Exception as e:
        print(f"[ERROR] Seeding process failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
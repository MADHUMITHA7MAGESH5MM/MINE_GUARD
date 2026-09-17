from src.database.database import SessionLocal
from src.database import crud, models

def test_database_suite():
    db = SessionLocal()
    print("--- 1. Testing Total Seed Count ---")
    total = db.query(models.Incident).count()
    print(f"Total rows in DB: {total}")
    assert total >= 1000, "Database row count is below target!"

    print("\n--- 2. Testing Pagination & Filtering ---")
    high_sif = crud.get_incidents(db, skip=0, limit=5, sif="HIGH")
    print(f"Retrieved {len(high_sif)} HIGH SIF records.")
    assert all(inc.sif == "HIGH" for inc in high_sif), "SIF filter mismatch!"

    print("\n--- 3. Testing Rule Tag Filtering ---")
    energy_rules = crud.get_incidents(db, limit=5, rule="Energy Isolation")
    print(f"Retrieved {len(energy_rules)} incidents matching 'Energy Isolation'.")

    print("\n--- 4. Testing Incident Insertion (Simulating Dev C/D API) ---")
    new_report = crud.create_incident(
        db=db,
        report="Test incident: loose flange leaking small mist near compressor skid.",
        sif="LOW",
        rules="Bypassing Safety Controls",
        reason="Minimal pressure release without ignition hazard.",
        confidence_score=0.91,
        site_location="Assam Asset"
    )
    print(f"Created incident ID #{new_report.id} with status: {new_report.verification_status}")
    assert new_report.id is not None, "Failed to create new record!"

    print("\n--- 5. Testing Human-in-the-Loop Override (Dev D HITL) ---")
    updated = crud.update_incident_verification(
        db=db,
        incident_id=new_report.id,
        status="Human-Verified",
        sif_override="HIGH"
    )
    print(f"Updated incident #{updated.id}: New SIF = {updated.sif}, Status = {updated.verification_status}")
    assert updated.sif == "HIGH" and updated.verification_status == "Human-Verified"

    db.close()
    print("\n[SUCCESS] All database components and CRUD queries passed verification!")

if __name__ == "__main__":
    test_database_suite()
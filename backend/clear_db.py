import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

for path in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "src")]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

from src.database.database import SessionLocal
from src.database.models import Incident

db = SessionLocal()

try:
    deleted = db.query(Incident).delete()
    db.commit()
    print(f"Deleted {deleted} incidents")
finally:
    db.close()
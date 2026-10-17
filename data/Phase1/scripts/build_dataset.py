"""
MINEGUARD - Mining Dataset Compiler
Extracts historical narratives and Had-Paras from DGMS SANKET reports
and Dataful dataset into unified dataset/mining_incidents.csv.
"""

import os
import re
import csv
import json
import requests
from pathlib import Path
from typing import List, Dict
import pandas as pd
import PyPDF2
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.incident_schema import (
    IncidentSchema, MineType, Shift, WorkerType,
    TARPLevel, CauseCode, get_tarp_level
)

DATA_DIR = Path("data")
OUTPUT_DIR = Path("dataset")
OUTPUT_FILE = OUTPUT_DIR / "mining_incidents.csv"

DGMS_REPORTS_URL = "https://www.dgms.gov.in/writereaddata/UploadFile/"
DATAFUL_CSV_URL = "https://dataful.in/api/datasets/21222/download"

HIGH_FATILITY_KEYWORDS = [
    "fatal", "death", "fatality", "serious injury", "severe",
    "roof fall", "gas explosion", "mine flooding", "collapse",
    "buried", "trapped", "electrocution", "run over"
]

MINOR_INCIDENT_KEYWORDS = [
    "near miss", "minor injury", "first aid", "no injury",
    "property damage", "equipment damage only"
]


def download_dataful_dataset() -> pd.DataFrame:
    print("[INFO] Downloading Dataful mining accidents dataset...")
    try:
        response = requests.get(DATAFUL_CSV_URL, timeout=30)
        response.raise_for_status()
        csv_path = DATA_DIR / "mining_accidents_dataful.csv"
        csv_path.write_bytes(response.content)
        df = pd.read_csv(csv_path)
        print(f"[INFO] Downloaded {len(df)} records from Dataful")
        return df
    except Exception as e:
        print(f"[WARN] Dataful download failed: {e}")
        return pd.DataFrame()


def download_dgms_reports() -> List[Path]:
    print("[INFO] Downloading DGMS SANKET reports...")
    dgms_dir = DATA_DIR / "dgms_reports"
    dgms_dir.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(DGMS_REPORTS_URL, timeout=30)
        pdf_links = re.findall(r'href="([^"]+\.pdf)"', response.text)
        for link in pdf_links[:10]:
            pdf_name = link.split("/")[-1]
            pdf_path = dgms_dir / pdf_name
            if not pdf_path.exists():
                pdf_url = DGMS_REPORTS_URL + link
                pdf_resp = requests.get(pdf_url, timeout=30)
                pdf_path.write_bytes(pdf_resp.content)
                print(f"[INFO] Downloaded {pdf_name}")
        return list(dgms_dir.glob("*.pdf"))
    except Exception as e:
        print(f"[WARN] DGMS download failed: {e}")
        return []


def extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"[WARN] PDF extraction failed for {pdf_path}: {e}")
        return ""


def label_sif(narrative: str) -> int:
    narrative_lower = narrative.lower()
    for kw in HIGH_FATILITY_KEYWORDS:
        if kw in narrative_lower:
            return 1
    for kw in MINOR_INCIDENT_KEYWORDS:
        if kw in narrative_lower:
            return 0
    return 0 if len(narrative_lower) < 100 else 1


def extract_hazards(narrative: str) -> List[str]:
    hazards = []
    hazard_keywords = {
        "roof instability": ["roof fall", "roof collapse", "roof instability"],
        "gas accumulation": ["methane", "gas accumulation", "gas leak"],
        "machinery failure": ["conveyor belt", "dumper", "excavator", "machinery"],
        "flooding": ["flooding", "water ingress", "mine flooding"],
        "electrocution": ["electrocution", "electrical", "shock"],
    }
    for hazard, keywords in hazard_keywords.items():
        if any(kw in narrative.lower() for kw in keywords):
            hazards.append(hazard)
    return hazards


def extract_failed_controls(narrative: str) -> List[str]:
    controls = []
    control_keywords = {
        "no roof bolting": ["no roof bolting", "inadequate support", "no support"],
        "no gas monitoring": ["no gas monitoring", "gas detector malfunction", "no sensor"],
        "no permit to work": ["no permit", "permit not issued", "no authorization"],
        "inadequate training": ["inadequate training", "untrained", "no training"],
        "poor ventilation": ["poor ventilation", "ventilation failure", "no airflow"],
    }
    for control, keywords in control_keywords.items():
        if any(kw in narrative.lower() for kw in keywords):
            controls.append(control)
    return controls


def build_unified_dataset(dgms_pdfs: List[Path], dataful_df: pd.DataFrame) -> pd.DataFrame:
    incidents = []
    print("[INFO] Processing DGMS PDF reports...")
    for pdf in dgms_pdfs:
        text = extract_text_from_pdf(pdf)
        if not text:
            continue
        narratives = re.split(r'(?=Accident\s+Report|Incident\s+Report)', text)
        for narrative in narratives:
            if len(narrative.strip()) < 50:
                continue
            sif_label = label_sif(narrative)
            incident = IncidentSchema(
                narrative=narrative.strip()[:1000],
                mine_type=MineType.UNDERGROUND.value if "underground" in narrative.lower() else MineType.OPENCAST.value,
                cause_code=CauseCode.OTHER.value,
                workplace="Unknown",
                shift=Shift.RELAY_1.value,
                worker_type=WorkerType.DEPARTMENTAL.value,
                sif_score=0.9 if sif_label == 1 else 0.2,
                tarp_level=get_tarp_level(0.9 if sif_label == 1 else 0.2),
                sif_label=sif_label,
                mine_id="Unknown",
                hazards=extract_hazards(narrative),
                failed_controls=extract_failed_controls(narrative),
            )
            incidents.append(incident.to_dict())

    print("[INFO] Processing Dataful structured dataset...")
    for _, row in dataful_df.iterrows():
        narrative = f"Mining accident in {row.get('state', 'Unknown')} ({row.get('year', 'Unknown')}): {row.get('fatal_accidents', 0)} fatal accidents, {row.get('fatalities', 0)} fatalities, {row.get('serious_injuries', 0)} serious injuries."
        sif_label = 1 if row.get('fatalities', 0) > 0 else 0
        incident = IncidentSchema(
            narrative=narrative,
            mine_type=MineType.UNDERGROUND.value if "coal" in str(row.get('mine_type', '')).lower() else MineType.OPENCAST.value,
            cause_code=CauseCode.OTHER.value,
            workplace="Unknown",
            shift=Shift.RELAY_1.value,
            worker_type=WorkerType.DEPARTMENTAL.value,
            sif_score=0.9 if sif_label == 1 else 0.2,
            tarp_level=get_tarp_level(0.9 if sif_label == 1 else 0.2),
            sif_label=sif_label,
            mine_id=f"Mine_{row.get('state', 'Unknown')}",
            hazards=extract_hazards(narrative),
            failed_controls=extract_failed_controls(narrative),
        )
        incidents.append(incident.to_dict())

    df = pd.DataFrame(incidents)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[INFO] Saved {len(df)} incidents to {OUTPUT_FILE}")
    return df


def main():
    print("=" * 60)
    print("MINEGUARD - Phase 1: Data Preparation & Schema Alignment")
    print("=" * 60)
    dataful_df = download_dataful_dataset()
    dgms_pdfs = download_dgms_reports()
    unified_df = build_unified_dataset(dgms_pdfs, dataful_df)
    print("\n[INFO] Dataset Summary:")
    print(f"Total incidents: {len(unified_df)}")
    print(f"SIF (1): {unified_df['sif_label'].sum()}")
    print(f"Minor (0): {len(unified_df) - unified_df['sif_label'].sum()}")
    print(f"Underground: {len(unified_df[unified_df['mine_type'] == 'Underground'])}")
    print(f"Opencast: {len(unified_df[unified_df['mine_type'] == 'Opencast'])}")
    print("\n[INFO] Phase 1 complete. Output saved to dataset/mining_incidents.csv")


if __name__ == "__main__":
    main()

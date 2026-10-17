import os
import re
import pandas as pd
import PyPDF2

# Find the current directory (src) and go up one level to the root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Point directly to the data folder where your PDFs live
DATA_DIR = os.path.join(ROOT_DIR, "data")

PDF_FILES = [
    os.path.join(DATA_DIR, "sanket0404_2024.pdf"),
    os.path.join(DATA_DIR, "SANKETNonCoal_17042025.pdf"),
    os.path.join(DATA_DIR, "VOLUME_II_NON_COAL_2015.pdf")
]

# Save the output CSV back into the data folder
OUTPUT_CSV = os.path.join(DATA_DIR, "mining_incidents.csv")

HIGH_SIF_KEYWORDS = [
    "fatal", "death", "roof fall", "strata", "inundation",
    "explosion", "methane", "run over", "crushed"
]
BARRIER_KEYWORDS = [
    "support", "ventilation", "alarm", "permit",
    "lanyard", "testing", "berm"
]

def extract_incidents():
    incidents = []
    
    for pdf_path in PDF_FILES:
        if not os.path.exists(pdf_path):
            print(f"[WARN] File not found: {pdf_path}")
            continue
            
        print(f"[INFO] Processing {os.path.basename(pdf_path)}...")
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        chunks = re.split(r'\n\s*\n', full_text)
        for chunk in chunks:
            clean_chunk = chunk.replace('\n', ' ').strip()
            if len(clean_chunk) < 100:
                continue
                
            chunk_lower = clean_chunk.lower()
            sif_label = "HIGH" if any(k in chunk_lower for k in HIGH_SIF_KEYWORDS) else "LOW"
            rule = "Strata Control" if ("roof" in chunk_lower or "fall" in chunk_lower) else "Standard Operating Procedure"
            reason = "Barrier failure detected" if any(b in chunk_lower for b in BARRIER_KEYWORDS) else "Unsafe condition observed"
            
            incidents.append({
                "report": clean_chunk,
                "sif": sif_label,
                "rules": rule,
                "reason": reason
            })
            
    df = pd.DataFrame(incidents)
    df = df.drop_duplicates(subset=['report'])
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Generated {OUTPUT_CSV} with {len(df)} records.")

if __name__ == "__main__":
    extract_incidents()
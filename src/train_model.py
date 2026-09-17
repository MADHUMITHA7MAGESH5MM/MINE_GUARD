import re
import os
import joblib
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

# =============================================================================
# 1. OUTCOME STRIPPING
# =============================================================================
OUTCOME_PATTERNS = [
    r',?\s*no injury occurred\.?', r',?\s*no incident occurred\.?',
    r',?\s*no one was (hurt|injured)\.?', r',?\s*nothing happened\.?',
    r',?\s*without injury\.?', r',?\s*no harm (resulted|occurred)\.?',
    r',?\s*no (load drop|gas release|fire|exposure) occurred\.?',
    r',?\s*(was|were) hospitalized.*?\.', r',?\s*requiring (stitches|hospitalization)\.?',
]

def strip_outcome_clause(text: str) -> str:
    cleaned = text
    for pattern in OUTCOME_PATTERNS:
        cleaned = re.sub(pattern, '.', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    return cleaned.strip()

# =============================================================================
# 2. DOMAIN SAFETY RULES & OVERRIDE LOGIC
# =============================================================================
UNSAFE_ACT_REGEX = re.compile(
    r'\b(walked?\s*under|entered?.{0,40}without|reached?\s*into|opened?.*(live|energized|energised)|'
    r'without\s*switching|without\s*testing|without\s*gas|without\s*permit|'
    r'cracked?\s*under|bypassed?|standing?\s*on\s*surface|crossed?\s*under|'
    r'stood?\s*in|stood?\s*directly|no\s*helmet|unassisted|unsupervised|'
    r'running\s*conveyor|conveyorto|conveyor)\b',
    re.IGNORECASE
)

CONTROL_REGEX = re.compile(
    r'\b(exclusion\s*zone.*maintained|exclusion\s*zone\s*was\s*maintained|'
    r'followed?\s*full\s*permit|followed?\s*permit|locked?\s*out|'
    r'verified?\s*before|cleared?\s*of\s*flammables|gas-tested|waited?\s*for|'
    r'calibrated|toolbox\s*talk|handover\s*log|respected|barricaded)\b',
    re.IGNORECASE
)

MINOR_INCIDENT_REGEX = re.compile(
    r'\b(twisted\s*ankle|stepping\s*off|steppingoff|kerb|car\s*park|car-park|'
    r'paper\s*cut|canteen|canteen\s*break|walked?\s*to|scraped?\s*a\s*traffic\s*cone)\b',
    re.IGNORECASE
)

HIGH_ENERGY_REGEX = re.compile(
    r'\b(suspended load|confined space|live electrical|live line|'
    r'high voltage|energized|energised|hydrocarbon|flammable|'
    r'toxic gas|h2s|trench|excavation|working at height|'
    r'unguarded edge|crane|lifting operation)\b',
    re.IGNORECASE
)

def apply_domain_override(text: str, base_prob: float) -> float:

    unsafe_count = len(UNSAFE_ACT_REGEX.findall(text))
    control_count = len(CONTROL_REGEX.findall(text))
    minor_count = len(MINOR_INCIDENT_REGEX.findall(text))
    energy_count = len(HIGH_ENERGY_REGEX.findall(text))

    adjusted = base_prob

    adjusted += unsafe_count * 0.10
    adjusted += energy_count * 0.08

    adjusted -= control_count * 0.10
    adjusted -= minor_count * 0.08

    adjusted = max(0.0, min(1.0, adjusted))

    return adjusted

def extract_domain_features(texts):
    features = []

    for t in texts:
        unsafe = len(UNSAFE_ACT_REGEX.findall(t))
        control = len(CONTROL_REGEX.findall(t))
        minor = len(MINOR_INCIDENT_REGEX.findall(t))
        high_energy = len(HIGH_ENERGY_REGEX.findall(t))

        features.append([
            unsafe,
            control,
            minor,
            high_energy
        ])

    return np.array(features, dtype=np.float32)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "final_sif.csv")

    print("Loading dataset...")
    df = pd.read_csv(csv_path)
    df = df.drop_duplicates(subset='report').reset_index(drop=True)
    df['report_clean'] = df['report'].apply(strip_outcome_clause)

    y = df['sif'].map({'HIGH': 1, 'LOW': 0}).values

    print("Generating MiniLM embeddings...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    X_embed = encoder.encode(df['report_clean'].tolist(), show_progress_bar=False)
    X_domain = extract_domain_features(df['report_clean'].tolist())

    neg_count, pos_count = (y == 0).sum(), (y == 1).sum()
    pos_weight = neg_count / pos_count
    DECISION_THRESHOLD = 0.42

    # =============================================================================
    # 3. LEAK-FREE CROSS VALIDATION
    # =============================================================================
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_preds = np.zeros(len(y))
    y_probs = np.zeros(len(y))

    for train_idx, val_idx in skf.split(X_embed, y):
        train_texts = df['report_clean'].iloc[train_idx]
        val_texts = df['report_clean'].iloc[val_idx]

        fold_tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=300, stop_words='english')
        X_tr_tfidf = fold_tfidf.fit_transform(train_texts).toarray()
        X_val_tfidf = fold_tfidf.transform(val_texts).toarray()

        X_tr = np.hstack([X_embed[train_idx], X_tr_tfidf, X_domain[train_idx]])
        X_val = np.hstack([X_embed[val_idx], X_val_tfidf, X_domain[val_idx]])

        model = XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            scale_pos_weight=pos_weight,
            random_state=42
    )
        model.fit(X_tr, y[train_idx])
        
        raw_probs = model.predict_proba(X_val)[:, 1]
        
        # Apply domain override to validation fold
        final_probs = [apply_domain_override(txt, p) for txt, p in zip(val_texts, raw_probs)]
        y_probs[val_idx] = final_probs
        y_preds[val_idx] = (np.array(final_probs) >= DECISION_THRESHOLD).astype(int)

    print(f"\n--- Leak-Free Cross-Validation (Threshold = {DECISION_THRESHOLD}) ---")
    print(classification_report(y, y_preds, target_names=['Low SIF', 'High SIF']))

    # =============================================================================
    # 4. FINAL PRODUCTION MODEL TRAINING & PERSISTENCE
    # =============================================================================
    print("\nTraining final production pipeline on full dataset...")
    final_tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=300, stop_words='english')
    X_tfidf_full = final_tfidf.fit_transform(df['report_clean']).toarray()
    X_full = np.hstack([X_embed, X_tfidf_full, X_domain])

    final_xgb = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=3,
    gamma=0.1,
    scale_pos_weight=pos_weight,
    random_state=42
)
    final_xgb.fit(X_full, y)

    joblib.dump(final_tfidf, os.path.join(script_dir, "tfidf_vectorizer.pkl"))
    final_xgb.save_model(os.path.join(script_dir, "xgboost_sif_model.json"))
    print("Saved model and TF-IDF vectorizer successfully!")

    # =============================================================================
    # 5. LIVE BATTERY VERIFICATION
    # =============================================================================
    def predict_sif(reports, threshold=DECISION_THRESHOLD):
        cleaned = [strip_outcome_clause(r) for r in reports]
        embs = encoder.encode(cleaned, show_progress_bar=False)
        tfidfs = final_tfidf.transform(cleaned).toarray()
        doms = extract_domain_features(cleaned)
        X_in = np.hstack([embs, tfidfs, doms])
        raw_probs = final_xgb.predict_proba(X_in)[:, 1]
        
        final_probs = [apply_domain_override(txt, p) for txt, p in zip(cleaned, raw_probs)]
        preds = ["HIGH" if p >= threshold else "LOW" for p in final_probs]
        return list(zip(preds, final_probs))

    test_battery = [
    ("A rigger stepped inside the swing radius of a crane while guiding a suspended vessel section", "HIGH"),
    ("Workers observed a strong smell of gas near a compressor skid but continued troubleshooting", "HIGH"),
    ("An electrician removed the cover of an energized distribution board to check a loose connection", "HIGH"),
    ("A technician entered a vessel to inspect internal corrosion before atmospheric testing was completed", "HIGH"),
    ("A worker climbed onto an unprotected roof edge to retrieve a dropped tool", "HIGH"),
    ("Two mechanics worked beneath a raised excavator bucket supported only by hydraulic pressure", "HIGH"),
    ("A contractor bypassed a machine interlock to keep production running during maintenance", "HIGH"),
    ("A worker crossed through the path of a reversing dump truck instead of using the pedestrian route", "HIGH"),
    ("A welder began cutting near a diesel spill that had not yet been cleaned", "HIGH"),
    ("Personnel entered an unsupported trench after heavy rainfall softened the surrounding soil", "HIGH"),

    ("A crane lift was postponed until rigging inspections and permit approvals were completed", "LOW"),
    ("Workers remained outside the barricaded area while heavy lifting operations were underway", "LOW"),
    ("The electrical panel was isolated locked out and verified before maintenance started", "LOW"),
    ("Confined space entry was conducted after gas testing permit approval and standby assignment", "LOW"),
    ("The crew stopped work when high winds exceeded the safe limit for lifting operations", "LOW"),
    ("A driver used the designated route and followed a banksman's instructions while reversing", "LOW"),
    ("All flammable materials were removed before welding activities commenced", "LOW"),
    ("A damaged sling was identified during inspection and replaced before use", "LOW"),
    ("Workers used a secured platform with guardrails and full body harnesses for elevated work", "LOW"),
    ("The excavation was inspected shored and declared safe before entry", "LOW"),
]

    print("\n" + "="*80)
    print(f"LIVE BATTERY TEST (Threshold = {DECISION_THRESHOLD})")
    print("="*80)

    results = predict_sif([t[0] for t in test_battery])
    correct = 0
    for (text, expected), (pred, prob) in zip(test_battery, results):
        match = pred == expected
        correct += match
        mark = "OK" if match else "XX"
        print(f"{mark} expected={expected:<5} predicted={pred:<5} ({prob*100:5.1f}%) | {text[:65]}")

    print(f"\nBattery Accuracy: {correct}/{len(test_battery)} ({correct/len(test_battery)*100:.0f}%)")
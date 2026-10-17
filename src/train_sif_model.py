import re
import os
import joblib
from matplotlib import text
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from entity_extractor import build_enriched_text
from text_utils import strip_outcome_clause

# =============================================================================
# NOTE: a hand-coded UNSAFE_ACT_REGEX / CONTROL_REGEX / HIGH_ENERGY_REGEX
# override system was REMOVED here. It nudged probabilities up or down just
# by counting keyword matches, with no understanding of negation or context.
# Proof it was actively harmful: "All flammable materials were removed
# before welding activities commenced" -- a clearly LOW, well-controlled
# sentence -- was pushed to 100% HIGH purely because "flammable" appears,
# completely blind to "removed". A wrong answer at 100% confidence is worse
# for a live demo than an honest borderline one. Let the trained model (which
# DOES learn context, unlike static regex) make the call on its own.
# =============================================================================

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "..", "data", "mining_incidents.csv")
    model_dir = os.path.join(script_dir, "..", "models")
    os.makedirs(model_dir, exist_ok=True)

    print("Loading dataset...")
    df = pd.read_csv(csv_path)
    n_before = len(df)
    df = df.drop_duplicates(subset='report').reset_index(drop=True)
    print(f"Total rows: {n_before} | Unique: {len(df)} | Duplicates removed: {n_before - len(df)}")
    
    def safe_enrich(text):
        try:
            return build_enriched_text(text)
        except Exception:
            return text
    df['report_clean'] = (
        df['report']
        .apply(strip_outcome_clause)
        .apply(safe_enrich)
    )

    y = df['sif'].map({'HIGH': 1, 'LOW': 0}).values

    print("Generating MiniLM embeddings...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    X_embed = encoder.encode(df['report_clean'].tolist(), show_progress_bar=False)

    neg_count, pos_count = (y == 0).sum(), (y == 1).sum()
    pos_weight = neg_count / pos_count
    print(f"scale_pos_weight = {pos_weight:.3f} (neg={neg_count}, pos={pos_count})")

    # =============================================================================
    # 2. LEAK-FREE CROSS VALIDATION (kept -- this was a genuine improvement:
    # TF-IDF is refit inside each fold on training text only, instead of once
    # on the whole dataset before splitting, which avoids letting validation-
    # fold vocabulary influence the fitted vectorizer)
    # =============================================================================
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_preds = np.zeros(len(y))

    for train_idx, val_idx in skf.split(X_embed, y):
        train_texts = df['report_clean'].iloc[train_idx]
        val_texts = df['report_clean'].iloc[val_idx]

        fold_tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=1000, stop_words='english')
        X_tr_tfidf = fold_tfidf.fit_transform(train_texts).toarray()
        X_val_tfidf = fold_tfidf.transform(val_texts).toarray()

        X_tr = np.hstack([X_embed[train_idx], X_tr_tfidf])
        X_val = np.hstack([X_embed[val_idx], X_val_tfidf])

        model = XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3, gamma=0.1,
            scale_pos_weight=pos_weight, random_state=42
        )
        model.fit(X_tr, y[train_idx])
        y_preds[val_idx] = model.predict(X_val)  # standard 0.5 threshold, no hand-picked override

    print("\n--- Cross-Validated Evaluation (standard 0.5 threshold, no regex override) ---")
    print(classification_report(y, y_preds, target_names=['Low SIF', 'High SIF']))

    # =============================================================================
    # 3. FINAL PRODUCTION MODEL TRAINING & PERSISTENCE
    # =============================================================================
    print("\nTraining final production pipeline on full dataset...")
    final_tfidf = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_features=1000, stop_words='english')
    X_tfidf_full = final_tfidf.fit_transform(df['report_clean']).toarray()
    X_full = np.hstack([X_embed, X_tfidf_full])

    final_xgb = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3, gamma=0.1,
        scale_pos_weight=pos_weight, random_state=42
    )
    final_xgb.fit(X_full, y)

    joblib.dump(final_tfidf, os.path.join(model_dir, "tfidf_vectorizer.pkl"))
    final_xgb.save_model(os.path.join(model_dir, "xgboost_sif_model.json"))
    print("Saved model and TF-IDF vectorizer successfully!")

    # =============================================================================
    # 4. LIVE BATTERY VERIFICATION -- same sentences, no override applied
    # =============================================================================
    def predict_sif(reports):
        cleaned = [safe_enrich(strip_outcome_clause(r)) for r in reports]
        embs = encoder.encode(cleaned, show_progress_bar=False)
        tfidfs = final_tfidf.transform(cleaned).toarray()
        X_in = np.hstack([embs, tfidfs])
        probs = final_xgb.predict_proba(X_in)[:, 1]
        preds = ["HIGH" if p >= 0.5 else "LOW" for p in probs]
        return list(zip(preds, probs))

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

    print("\n" + "=" * 80)
    print("LIVE BATTERY TEST (pure trained model, no override)")
    print("=" * 80)

    results = predict_sif([t[0] for t in test_battery])
    correct = 0
    for (text, expected), (pred, prob) in zip(test_battery, results):
        match = pred == expected
        correct += match
        mark = "OK" if match else "XX"
        print(f"{mark} expected={expected:<5} predicted={pred:<5} ({prob*100:5.1f}%) | {text[:65]}")

    print(f"\nBattery Accuracy: {correct}/{len(test_battery)} ({correct/len(test_battery)*100:.0f}%)")

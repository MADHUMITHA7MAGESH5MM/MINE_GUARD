"""
Combined inference pipeline. Loads the trained SIF classifier and the
Life-Saving Rule tagger, and exposes one function that takes raw report
text and returns the full structured output the dashboard needs.
"""
import os
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer
from xgboost import XGBClassifier
from entity_extractor import explain_report

from text_utils import strip_outcome_clause
from rule_tagger import RuleTaggerML, tag_report

_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")


class SIFPipeline:
    def __init__(self, model_dir: str = _MODEL_DIR):
        print("Loading encoder (first run downloads ~90MB, then cached)...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

        self.tfidf = joblib.load(os.path.join(model_dir, "tfidf_vectorizer.pkl"))

        self.xgb = XGBClassifier()
        self.xgb.load_model(os.path.join(model_dir, "xgboost_sif_model.json"))

        self.rule_tagger = RuleTaggerML().load(os.path.join(model_dir, "xgboost_sif_model_weighted"))

    def process(self, report_text: str) -> dict:
        cleaned = strip_outcome_clause(report_text)
        

        embed = self.encoder.encode([cleaned], show_progress_bar=False)
        tfidf_feat = self.tfidf.transform([cleaned]).toarray()
        X = np.hstack([embed, tfidf_feat])

        prob_high = float(self.xgb.predict_proba(X)[0][1])
        if prob_high >= 0.70:
            sif_label = "HIGH"
        elif prob_high >= 0.40:
            sif_label = "REVIEW"
        else:
            sif_label = "LOW"
        rules = tag_report(report_text, self.rule_tagger)
        entities = explain_report(report_text)

        return {
            "report": report_text,
            "report_clean": cleaned,
            "sif": sif_label,
            "sif_probability": round(prob_high, 4),
            "rules": rules,
            "activities": entities["activities"],
            "locations": entities["locations"],
            "hazards": entities["hazards"],
            "barrier_failures": entities["barrier_failures"],
        }

    def process_batch(self, report_texts: list) -> list:
        return [self.process(t) for t in report_texts]


if __name__ == "__main__":
    pipeline = SIFPipeline()

    demo_reports = [
        "Worker walked under a suspended load to retrieve a dropped tool, no injury occurred.",
        "Confined space entry was conducted after gas testing permit approval and standby assignment.",
        "A contractor bypassed a machine interlock to keep production running during maintenance.",
    ]

    print("\n--- Pipeline output ---")
    for r in demo_reports:
        result = pipeline.process(r)
        print(f"\nReport : {result['report']}")
        print(f"SIF    : {result['sif']} ({result['sif_probability']*100:.1f}%)")
        print(f"Rules  : {', '.join(result['rules'])}")

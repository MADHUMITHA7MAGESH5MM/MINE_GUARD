import os
import joblib
import numpy as np
from xgboost import XGBClassifier
from sentence_transformers import SentenceTransformer

# Import the extractor tools
from entity_extractor import extract_all_entities, build_enriched_text, explain_report
from text_utils import strip_outcome_clause

class SIFPipeline:
    def __init__(self, model_dir="models"):
        print("Loading MiniLM encoder...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Resolve paths to your models
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(base_dir, ".."))
        actual_model_dir = os.path.join(root_dir, model_dir)
        
        tfidf_path = os.path.join(actual_model_dir, "tfidf_vectorizer.pkl")
        xgb_path = os.path.join(actual_model_dir, "xgboost_sif_model.json")
        
        print("Loading TF-IDF and XGBoost models...")
        self.tfidf = joblib.load(tfidf_path)
        self.model = XGBClassifier()
        self.model.load_model(xgb_path)

    def process(self, text: str) -> dict:
        # 1. PROPERLY EXTRACT THE DICTIONARY (This fixes the TypeError!)
        entities = extract_all_entities(text)
        
        # 2. Enrich the text for the ML model (This returns a string)
        cleaned_text = strip_outcome_clause(text)
        enriched_text = build_enriched_text(cleaned_text)
        
        # 3. Create model inputs (Embeddings + TF-IDF)
        emb = self.encoder.encode([enriched_text], show_progress_bar=False)
        tfidf_feats = self.tfidf.transform([enriched_text]).toarray()
        X_in = np.hstack([emb, tfidf_feats])
        
        # 4. Make prediction
        prob = float(self.model.predict_proba(X_in)[0, 1])
        prediction = "HIGH" if prob >= 0.5 else "LOW"
        
        # 5. Extract rules & explanation for the Mining Domain
        rule = "Strata Control" if ("roof" in text.lower() or "fall" in text.lower() or "strata" in text.lower()) else "Standard Operating Procedure"
        reason = explain_report(text)
        
        # 6. Return the perfectly structured dictionary to model_service.py
        return {
            "sif": prediction,
            "probability": prob*100,
            "sif_probability": prob,
            "rules": [rule],
            "reason": reason,
            "hazards": entities.get("hazards", []),
            "barrier_failures": entities.get("barrier_failures", []),
            "activities": entities.get("activities", []),
            "locations": entities.get("locations", [])
        }
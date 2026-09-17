import os
import sys

# Ensure 'src' path is loaded correctly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from pipeline import SIFPipeline

class SIFModelService:
    def __init__(self):
        model_dir = os.path.join(PROJECT_ROOT, "models")
        self.pipeline = SIFPipeline(model_dir=model_dir)

    def predict(self, text: str) -> dict:
        """
        Executes prediction + entity extraction in a single pass.
        Can be called directly by Dev D: model_service.predict(text)
        """
        raw_res = self.pipeline.process(text)
        
        return {
            "cleaned_text": raw_res.get("report_clean"),
            "sif_verdict": raw_res.get("sif", "LOW"),
            "sif_probability": float(raw_res.get("sif_probability", 0.0)),
            "life_saving_rules": raw_res.get("rules", []),
            "activities": raw_res.get("activities", []),
            "locations": raw_res.get("locations", []),
            "hazards": raw_res.get("hazards", []),
            "barrier_failures": raw_res.get("barrier_failures", []),
        }

model_service = SIFModelService()
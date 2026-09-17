"""
Precursor entity extractor: pulls out HAZARD, LOCATION, and BARRIER_FAILURE
entities from report text for the dashboard's "recurring precursor pattern"
view.
"""
import spacy

print("Loading spaCy NLP Engine...")
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# =============================================================================
# Entity Patterns (Upgraded with Context & Lemmatization)
# =============================================================================
patterns = [
    # ---- EXCLUSIONS (Intercept job titles so they don't trigger HAZARDS) ----
    {"label": "PERSON", "pattern": [{"lower": "crane"}, {"lower": "operator"}]},
    {"label": "PERSON", "pattern": [{"lower": "rigger"}]},
    {"label": "PERSON", "pattern": [{"lower": "derrickman"}]},
    {"label": "PERSON", "pattern": [{"lower": "mechanic"}]},
    {"label": "PERSON", "pattern": [{"lower": "mud"}, {"lower": "logger"}]},
    {"label": "PERSON", "pattern": [{"lower": "scaffolding"}, {"lower": "lead"}]},

    # ---- HAZARD ----
    {"label": "HAZARD", "pattern": [{"lower": "suspended"}, {"lower": "load"}]},
    {"label": "HAZARD", "pattern": [{"lower": "confined"}, {"lower": "space"}]},
    {"label": "HAZARD", "pattern": [{"lower": {"in": ["live", "energized", "energised"]}}, {"lower": {"in": ["line", "wire", "board", "circuit", "panel", "distribution"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": {"in": ["480v", "11kv", "240v"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "flammable"}, {"lower": {"in": ["material", "materials", "vapor", "vapour", "liquid"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "hydrocarbon"}]},
    {"label": "HAZARD", "pattern": [{"lower": "h2s"}, {"lower": "spike"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "trench"}]},
    {"label": "HAZARD", "pattern": [{"lower": "excavation"}]},
    {"label": "HAZARD", "pattern": [{"lower": {"in": ["raised", "suspended"]}}, {"lower": {"in": ["bucket", "beam", "pipe", "vessel", "load"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "unguarded"}, {"lower": {"in": ["edge", "platform", "opening"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "gas"}, {"lower": {"in": ["leak", "release", "smell"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "rotating"}, {"lower": {"in": ["equipment", "table", "shaft"]}}]},
    {"label": "HAZARD", "pattern": [{"lower": "sparks"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "handheld"}, {"lower": "grinder"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "unsecured"}, {"lower": "scaffolding"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "tensioned"}, {"lower": "line"}]}, 
    {"label": "HAZARD", "pattern": [{"lemma": "snap"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "slipped"}, {"lower": "off"}]}, 
    
    # Dropped Objects 
    {"label": "HAZARD", "pattern": [{"lemma": "drop"}, {"is_alpha": True, "op": "*"}, {"lemma": {"in": ["tool", "object", "item", "wrench"]}}]},
    {"label": "HAZARD", "pattern": [{"lemma": {"in": ["tool", "object", "item", "wrench"]}}, {"is_alpha": True, "op": "*"}, {"lemma": "drop"}]},

    # Working at Height & Climbing
    {"label": "HAZARD", "pattern": [{"lower": "ladder"}]},
    {"label": "HAZARD", "pattern": [{"lower": "roof"}]},
    {"label": "HAZARD", "pattern": [{"lower": "working"}, {"lower": "at"}, {"lower": "height"}]},
    {"label": "HAZARD", "pattern": [{"lower": "fall"}, {"lower": "protection"}]},
    {"label": "HAZARD", "pattern": [{"lower": "harness"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": {"not_in": ["waist", "knee", "shoulder"]}}, {"lower": "height"}]}, 
    {"label": "HAZARD", "pattern": [{"lower": "elevated"}]},
    {"label": "HAZARD", "pattern": [{"lower": "top"},{"lower": "of"},{"lower": {"in": ["a", "the"]}, "op": "?"},{"lower": "tank"}]},
    {"label": "HAZARD", "pattern": [{"lower": "platform"}]},
    {"label": "HAZARD", "pattern": [{"lower": "scaffold"}]},
    {"label": "HAZARD", "pattern": [{"lower": "climbed"}]},

    # Lifting 
    {"label": "HAZARD", "pattern": [{"lower": "crane"}]},
    {"label": "HAZARD", "pattern": [{"lower": "lifting"}]},
    {"label": "HAZARD", "pattern": [{"lower": "hoist"}]},

    # Hot work
    {"label": "HAZARD", "pattern": [{"lower": "welding"}]},
    {"label": "HAZARD", "pattern": [{"lower": "grinding"}]},
    {"label": "HAZARD", "pattern": [{"lower": "cutting"}]},

    # ---- LOCATION ----
    {"label": "LOCATION", "pattern": [{"lower": "vessel"}]},
    {"label": "LOCATION", "pattern": [{"lower": "tank"}]},
    {"label": "LOCATION", "pattern": [{"lower": "compressor"}, {"lower": "skid"}]},
    {"label": "LOCATION", "pattern": [{"lower": "compressor"}, {"lower": "manifold"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "scaffold"}]},
    {"label": "LOCATION", "pattern": [{"lower": "pipeline"}]},
    {"label": "LOCATION", "pattern": [{"lower": "flare"}, {"lower": "deck"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "shaker"}, {"lower": "deck"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "nitrogen"}, {"lower": "purge"}, {"lower": "header"}]},
    {"label": "LOCATION", "pattern": [{"lower": "pump"}, {"lower": "house"}]},
    {"label": "LOCATION", "pattern": [{"lower": "pipe"}, {"lower": "rack"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "staging"}, {"lower": "area"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "substation"}]}, 
    {"label": "LOCATION", "pattern": [{"lower": "pig"}, {"lower": "launcher"}]}, 

    # ---- BARRIER_FAILURE ----
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "without"}, {"lower": "fall"}, {"lower": "protection"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "without"}, {"lower": "a", "op": "?"}, {"lower": "permit"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "without"}, {"lower": "a", "op": "?"}, {"lower": "harness"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "not"}, {"lower": "isolated"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lemma": "bypass"}, {"is_alpha": True, "op": "*"}, {"lower": "interlock"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "temporary"}, {"lower": "jumpers"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "no"}, {"lower": "exclusion"}, {"lower": "zone"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "unguarded"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "unsecured"}]}, 
    {"label": "BARRIER_FAILURE", "pattern": [{"lower": "failed"}, {"lower": "to"}, {"lower": "alarm"}]}, 
]
ruler.add_patterns(patterns)

# =============================================================================
# Activity Mapper 
# =============================================================================
ACTIVITY_MAP = {
    "confined space": "Confined Space Entry",
    "suspended load": "Lifting",
    "crane": "Lifting",
    "hoist": "Lifting",
    "trench": "Excavation",
    "excavation": "Excavation",
    "unguarded edge": "Working at Height",
    "working at height": "Working at Height",
    "ladder": "Working at Height",
    "roof": "Working at Height",
    "fall protection": "Working at Height",
    "height": "Working at Height",
    "climbed": "Working at Height",
    "harness": "Working at Height",
    "electrical panel": "Electrical Work",
    "switchgear": "Electrical Work",
    "energized board": "Electrical Work",
    "480v": "Electrical Work",
    "11kv": "Electrical Work",
    "welding": "Hot Work",
    "grinding": "Hot Work",
    "cutting": "Hot Work",
    "sparks": "Hot Work",
    "handheld grinder": "Hot Work",
    "interlock": "Mechanical Operation",
    "gas leak": "Process / Containment",
    "h2s spike": "Process / Containment",
    
    # Barrier Failure specific mappings
    "without fall protection": "Working at Height",
    "without harness": "Working at Height",
    "without exclusion zone": "Lifting",
}

def infer_activities(hazards, barrier_failures):
    activities = []
    combined = [item.lower().strip() for item in hazards + barrier_failures]

    for item in combined:
        if item in ACTIVITY_MAP:
            activities.append(ACTIVITY_MAP[item])
        else:
            for key, activity in ACTIVITY_MAP.items():
                if key in item:
                    activities.append(activity)

    activities = list(dict.fromkeys(activities))
    return activities if activities else ["Unknown"]

def explain_report(text: str) -> dict:
    doc = nlp(text)

    hazards, locations, barrier_failures = [], [], []
    for ent in doc.ents:
        if ent.label_ == "HAZARD":
            hazards.append(ent.text.title())
        elif ent.label_ == "LOCATION":
            locations.append(ent.text.title())
        elif ent.label_ == "BARRIER_FAILURE":
            barrier_failures.append(ent.text.title())

    activities = infer_activities(hazards, barrier_failures)

    hazards = list(dict.fromkeys(hazards))
    locations = list(dict.fromkeys(locations))
    barrier_failures = list(dict.fromkeys(barrier_failures))
    
    enriched_text = (
        f"{text} "
        f"HAZARD {' '.join(hazards)} "
        f"ACTIVITY {' '.join(activities)} "
        f"BARRIER {' '.join(barrier_failures)}"
    )

    return {
        "report": text,
        "enriched_text": enriched_text,
        "activities": activities,
        "locations": locations,
        "hazards": hazards,
        "barrier_failures": barrier_failures,
    }

def build_enriched_text(report: str) -> str:
    entities = explain_report(report)
    return entities["enriched_text"]
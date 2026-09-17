import spacy
from spacy.pipeline import EntityRuler

print("Loading spaCy NLP Engine...")
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

patterns = [
    # BARRIER FAILURES
    {"label": "BARRIER_FAILURE", "pattern": [{"LOWER": "without"}, {"LOWER": "fall"}, {"LOWER": "protection"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"LOWER": "no"}, {"LOWER": "harness"}]},
    {"label": "BARRIER_FAILURE", "pattern": [{"LOWER": "bypassing"}, {"LOWER": "the"}, {"LOWER": "interlock"}]},
    
    # HAZARDS
    #{"label": "HAZARD", "pattern": [{"LOWER": {"IN": ["480v", "11kv", "live", "energized"]}}]}, # Catch electrical
    #{"label": "HAZARD", "pattern": [{"LOWER": "dropped"}, {"LOWER": "tool"}]},
    #{"label": "HAZARD", "pattern": [{"LOWER": "suspended"}, {"LOWER": "load"}]},
    #{"label": "HAZARD", "pattern": [{"LOWER": "gas"}, {"LOWER": "leak"}]},
    # HAZARDS
    {"label": "HAZARD", "pattern": [{"LOWER": {"IN": ["480v", "11kv", "live", "energized"]}}]}, 
    {"label": "HAZARD", "pattern": [{"LEMMA": "drop"}, {"OP": "*", "LENGTH": {"<": 3}}, {"LEMMA": {"IN": ["tool", "object", "item"]}}]}, # Matches "dropped tool" OR "tool was dropped"
    {"label": "HAZARD", "pattern": [{"LEMMA": {"IN": ["tool", "object", "item"]}}, {"OP": "*", "LENGTH": {"<": 3}}, {"LEMMA": "drop"}]}, 
    {"label": "HAZARD", "pattern": [{"LOWER": "suspended"}, {"LOWER": "load"}]},
    {"label": "HAZARD", "pattern": [{"LOWER": "gas"}, {"LOWER": "leak"}]},
    
    # ENVIRONMENTAL
    {"label": "ENVIRONMENT", "pattern": [{"LOWER": "monsoon"}, {"LOWER": "rain"}]},
    {"label": "ENVIRONMENT", "pattern": [{"LOWER": "poor"}, {"LOWER": "visibility"}]},

    # LOCATIONS
    {"label": "LOCATION", "pattern": [{"LOWER": "flare"}, {"LOWER": "deck"}]},
    {"label": "LOCATION", "pattern": [{"LOWER": "compressor"}, {"LOWER": "skid"}]},
    {"label": "LOCATION", "pattern": [{"LOWER": "nitrogen"}, {"LOWER": "purge"}, {"LOWER": "header"}]}
]
ruler.add_patterns(patterns)

def explain_report_v2(text):
    doc = nlp(text)
    entities = {"HAZARD": [], "BARRIER_FAILURE": [], "LOCATION": [], "ENVIRONMENT": []}
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text.title())
            
    return entities
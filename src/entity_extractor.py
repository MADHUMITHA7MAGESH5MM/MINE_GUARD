import spacy
from typing import List, Dict

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- MINEGUARD SPECIFIC KEYWORDS ---

HAZARD_KEYWORDS = [
    "roof fall", "fall of side", "strata spalling", "inundation",
    "methane accumulation", "coal dust explosion", "dump slide",
    "highwall collapse", "dumper rollover", "heavy machinery run-over",
    "shotfiring", "misfire", "black damp", "white damp", "confined space"
]

BARRIER_KEYWORDS = [
    "roof bolting", "prop", "chock", "ventilation fan", "brattice",
    "methanometer", "audio-visual alarm", "ava", "berm", "safety belt",
    "permit to work", "loto", "gas testing", "pre-shift inspection",
    "no roof bolting", "inadequate roof support", "defunct audio-visual alarm",
    "substandard berm", "poor ventilation"
]

def extract_hazards(text: str) -> List[str]:
    """Extract known mining hazards based on exact/partial matches."""
    text_lower = text.lower()
    found = [h for h in HAZARD_KEYWORDS if h in text_lower]
    return found

def extract_barrier_failures(text: str) -> List[str]:
    """Extract known mining safety barrier failures."""
    text_lower = text.lower()
    found = [b for b in BARRIER_KEYWORDS if b in text_lower]
    return found

def extract_activities(text: str) -> List[str]:
    """
    Extract ongoing work activities using NLP chunking.
    Looks for verb phrases indicating active work (e.g., 'drilling', 'hauling').
    """
    doc = nlp(text)
    activities = []
    
    # Very simple activity heuristic: look for GERUND verbs (VBG) or
    # NOUNs that are objects of work-related verbs.
    # In a real system, you'd use custom NER or dependency parsing.
    
    # Approach 1: Look for "while [activity]" or "during [activity]"
    for token in doc:
        if token.lower_ in ["while", "during", "before", "after"]:
            # Grab the next few tokens as the activity
            activity_tokens = []
            for t in token.rights:
                if t.pos_ in ["NOUN", "VERB", "ADJ"]:
                    activity_tokens.append(t.text)
            if activity_tokens:
               activities.append(" ".join(activity_tokens))

    # Approach 2: Look for gerunds
    for token in doc:
        if token.tag_ == "VBG": # Verb, gerund or present participle
            activities.append(token.text)
            
    # Clean up and deduplicate
    unique_activities = list(set([a.lower() for a in activities if len(a) > 3]))
    return unique_activities

def extract_locations(text: str) -> List[str]:
    """Extract location entities (GPE, LOC, FAC)."""
    doc = nlp(text)
    locs = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]]
    return list(set(locs))

def extract_all_entities(text: str) -> Dict[str, List[str]]:
    """Return all extracted entities as a dictionary."""
    return {
        "hazards": extract_hazards(text),
        "barrier_failures": extract_barrier_failures(text),
        "activities": extract_activities(text),
        "locations": extract_locations(text)
    }

def build_enriched_text(text: str) -> str:
    """
    Append extracted keywords to the end of the text to help the ML model
    pick up on important features (especially if they are multi-word phrases
    that TF-IDF might miss).
    """
    entities = extract_all_entities(text)
    
    enrichment_parts = []
    if entities["hazards"]:
        enrichment_parts.append("HAZARDS: " + ", ".join(entities["hazards"]))
    if entities["barrier_failures"]:
        enrichment_parts.append("FAILURES: " + ", ".join(entities["barrier_failures"]))
        
    enrichment_str = " | ".join(enrichment_parts)
    
    if enrichment_str:
        return f"{text} [ENRICHED: {enrichment_str}]"
    return text

def explain_report(text: str) -> str:
    """
    Generate a human-readable explanation of the hazards and barrier failures.
    Required by pipeline.py and the database seeder.
    """
    entities = extract_all_entities(text)
    hazards = entities["hazards"]
    failures = entities["barrier_failures"]
    
    if failures and hazards:
        return f"Critical risk: '{hazards[0]}' combined with '{failures[0]}'."
    if failures:
        return f"Barrier breakdown: '{failures[0]}'."
    if hazards:
        return f"Hazard observed: '{hazards[0]}'."
        
    return "General safety observation without specific critical hazards."
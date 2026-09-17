import re

# Outcome-language patterns -- stripped so downstream models judge based on
# hazard + exposure, not on what happened to occur this particular time.
OUTCOME_PATTERNS = [
    r',?\s*no injury occurred\.?', r',?\s*no incident occurred\.?',
    r',?\s*no one was (hurt|injured)\.?', r',?\s*nothing happened\.?',
    r',?\s*without injury\.?', r',?\s*no harm (resulted|occurred)\.?',
    r',?\s*no (load drop|gas release|fire|exposure) occurred\.?',
    r',?\s*(was|were) hospitalized.*?\.', r',?\s*requiring (stitches|hospitalization)\.?',
]


def strip_outcome_clause(text: str) -> str:
    """Remove outcome-describing clauses so classification is based on hazard,
    exposure, and barrier status -- not on what happened to occur this time."""
    cleaned = text
    for pattern in OUTCOME_PATTERNS:
        cleaned = re.sub(pattern, '.', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\.\s*\.', '.', cleaned)
    return cleaned.strip()

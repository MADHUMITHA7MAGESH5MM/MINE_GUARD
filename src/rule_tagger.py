"""
Life-Saving Rule tagger.

Approach: hybrid keyword-matching (primary) + trained multi-label ML model
(secondary).
"""
import re
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from text_utils import strip_outcome_clause

# =============================================================================
# 1. KEYWORD DICTIONARY -- UPDATED WITH CONTEXTUAL RULES
# =============================================================================
RULE_KEYWORDS = {
    "Bypassing Safety Controls": [
        r"\bbypass(ed|ing)?\b", r"\bdefeat(ed|ing)?\b.*interlock", r"\bjumper(ed)?\b",
        r"\btape(d)?\b.*(switch|sensor|interlock|button)",  
        r"\bhold down\b.*switch", r"\boverrid(e|den|ing)\b", r"\bdisabl(e|ed|ing)\b",
        r"\bsilenc(e|ed|ing)\b.*alarm", r"\bremov(e|ed|ing)\b.*guard",
    ],
    "Confined Space": [
        r"\bconfined space\b", r"\bmanhole\b", r"\bsilo\b", r"\bexcavation\b", r"\btrench\b",
        r"\b(enter(ed|ing)?|inside|within)\b.{0,25}\b(tank|vessel|pit)\b", 
        r"\bgas test(ing|ed)?\b", r"\batmosphere\b", r"\bstandby attendant\b", r"\bshor(ing|ed)\b",
    ],
    "Driving": [
        r"\bdriv(e|er|ing)\b", r"\bvehicle\b", r"\btruck\b", r"\bseatbelt\b",
        r"\bspeed(ing)?\b", r"\brevers(e|ing)\b", r"\bpedestrian\b", r"\bhaul road\b",
        r"\btraffic\b", r"\bparking\b",
    ],
    "Energy Isolation": [
        r"\block ?out\b", r"\btag ?out\b", r"\bLOTO\b", r"\bisolat(e|ed|ion)\b",
        r"\bde-?energi[sz]ed\b", r"\blive (line|wire|electrical|junction)\b",
        r"\bbreaker\b", r"\bresidual (pressure|energy)\b", r"\bzero energy\b", 
        r"\bpurge(d)?\b(?!\s*header)" 
    ],
    "Hot Work": [
        r"\bweld(ing|er)?\b", r"\bcutting torch\b", r"\bhot work\b", r"\bspark(s)?\b",
        r"\bgrinding\b", r"\bflame\b", r"\bignit(e|ion)\b", r"\bflammable\b",
        r"\bcombustible\b", r"\bhydrocarbon\b", r"\bfire watch\b",
    ],
    "Line of Fire": [
        r"\bsuspended load\b", r"\b(under(neath)?|beneath) (a |the )?(suspended |raised |overhead )",
        r"\bline of fire\b", r"\bstruck.?by\b", r"\bcrush(ed|ing)?\b", r"\bpinch point\b",
        r"\bswing radius\b", r"\bdropped object\b", r"\boverhead\b", r"\bexclusion zone\b",
        r"\btensioned\b", r"\bsnapped\b"
    ],
    "Safe Mechanical Lifting": [
        r"\bcrane(?!\s+operator)\b", r"\blift(ing)?\b", r"\brigg(ing|er)\b", 
        r"\bsling\b", r"\bhoist\b", r"\bload chart\b", r"\boutrigger\b", 
        r"\btag line\b", r"\bforklift\b", r"\bslinger\b",
    ],
    "Work Authorization": [
        r"\bpermit\b", r"\bJSA\b", r"\brisk assessment\b", r"\bauthoriz(e|ed|ation)\b",
        r"\btoolbox talk\b", r"\bSIMOPS\b", r"\bwork order\b", r"\bHIRA\b",
    ],
    "Working at Height": [
        r"(?<!waist )(?<!knee )(?<!shoulder )\bheight\b", 
        r"\bscaffold\b", r"\bharness\b", r"\bfall (protection|arrest)\b",
        r"\bguardrail\b", r"\bladder\b", r"\broof\b", r"\belevated platform\b", r"\banchor point\b",
    ],
}

RULE_PATTERNS = {rule: re.compile("|".join(patterns), re.IGNORECASE)
                 for rule, patterns in RULE_KEYWORDS.items()}


def keyword_tag(text: str) -> list:
    return [rule for rule, pattern in RULE_PATTERNS.items() if pattern.search(text)]


# =============================================================================
# 2. ML BACKUP MODEL -- catches paraphrased cases the keywords miss
# =============================================================================
class RuleTaggerML:
    def __init__(self):
        self.vectorizer = None
        self.mlb = None
        self.model = None

    def fit(self, texts: list, rule_lists: list):
        self.mlb = MultiLabelBinarizer()
        Y = self.mlb.fit_transform(rule_lists)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=2000, stop_words='english')
        X = self.vectorizer.fit_transform(texts)
        self.model = OneVsRestClassifier(LogisticRegression(max_iter=1000, class_weight='balanced'))
        self.model.fit(X, Y)
        return self

    def predict(self, texts: list, threshold: float = 0.5) -> list:
        X = self.vectorizer.transform(texts)
        probs = self.model.predict_proba(X)
        results = []
        for row in probs:
            tags = [self.mlb.classes_[i] for i, p in enumerate(row) if p >= threshold]
            results.append(tags)
        return results

    def save(self, path_prefix: str):
        joblib.dump({'vectorizer': self.vectorizer, 'mlb': self.mlb, 'model': self.model},
                    f"{path_prefix}_rule_ml.pkl")

    def load(self, path_prefix: str):
        obj = joblib.load(f"{path_prefix}_rule_ml.pkl")
        self.vectorizer, self.mlb, self.model = obj['vectorizer'], obj['mlb'], obj['model']
        return self


# =============================================================================
# 3. COMBINED TAGGER -- keyword primary, ML fills gaps
# =============================================================================
def tag_report(text: str, ml_tagger: RuleTaggerML = None) -> list:
    cleaned = strip_outcome_clause(text)
    tags = set(keyword_tag(cleaned))

    if ml_tagger is not None and len(tags) == 0:
        ml_tags = ml_tagger.predict([cleaned])[0]
        tags.update(ml_tags)

    return sorted(tags) if tags else ["Unclassified"]


# =============================================================================
# 4. TRAINING ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "..", "data", "final_sif.csv")
    model_dir = os.path.join(script_dir, "..", "models")
    os.makedirs(model_dir, exist_ok=True)

    df = pd.read_csv(data_path)
    df['report_clean'] = df['report'].apply(strip_outcome_clause)
    rule_lists = df['rules'].apply(lambda r: [t.strip() for t in str(r).split(';')])

    print("Training ML backup rule tagger...")
    ml_tagger = RuleTaggerML().fit(df['report_clean'].tolist(), rule_lists.tolist())
    ml_tagger.save(os.path.join(model_dir, "xgboost_sif_model_weighted"))
    print("Saved rule tagger ML backup.")
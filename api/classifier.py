# api/classifier.py
# Loads ML model assets from Supabase Storage at startup.
# Exposes predict() and predict_proba() for use in routes.

import os
import io
import joblib
import tempfile
import numpy as np
import re
from dotenv import load_dotenv
from supabase import create_client

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ── Supabase client for Storage access ──
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Stopwords (inline — no NLTK download needed at runtime) ──
STOP_WORDS = {
    "i","me","my","myself","we","our","ours","ourselves","you","your",
    "yours","yourself","yourselves","he","him","his","himself","she",
    "her","hers","herself","it","its","itself","they","them","their",
    "theirs","themselves","what","which","who","whom","this","that",
    "these","those","am","is","are","was","were","be","been","being",
    "have","has","had","having","do","does","did","doing","a","an",
    "the","and","but","if","or","because","as","until","while","of",
    "at","by","for","with","about","against","between","into","through",
    "during","before","after","above","below","to","from","up","down",
    "in","out","on","off","over","under","again","further","then",
    "once","here","there","when","where","why","how","all","both",
    "each","few","more","most","other","some","such","no","nor","not",
    "only","own","same","so","than","too","very","s","t","can","will",
    "just","don","should","now","d","ll","m","o","re","ve","y","ain",
    "couldn","didn","doesn","hadn","hasn","haven","isn","ma","mightn",
    "mustn","needn","shan","shouldn","wasn","weren","won","wouldn"
}

# ── Module-level cache — loaded once at startup ──
_model   = None
_tfidf   = None
_le      = None


def _download_pkl(filename: str):
    """Download a .pkl file from Supabase Storage → load with joblib."""
    response = supabase.storage.from_("models").download(filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
        tmp.write(response)
        tmp_path = tmp.name
    obj = joblib.load(tmp_path)
    os.unlink(tmp_path)
    return obj


def load_classifier():
    """
    Called once in main.py lifespan at startup.
    Downloads and caches model, vectorizer, label encoder.
    Returns a dict stored in app.state.classifier.
    """
    global _model, _tfidf, _le

    print("  Loading tfidf_vectorizer.pkl ...")
    _tfidf = _download_pkl("tfidf_vectorizer.pkl")

    print("  Loading label_encoder.pkl ...")
    _le    = _download_pkl("label_encoder.pkl")

    print("  Loading model.pkl ...")
    _model = _download_pkl("model.pkl")

    return {
        "model"  : _model,
        "tfidf"  : _tfidf,
        "le"     : _le
    }


def clean_text(text: str) -> str:
    """
    Same cleaning pipeline used in B1.
    Must be identical — different cleaning = wrong predictions.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+',        '', text)
    text = re.sub(r'[^a-z\s]',      ' ', text)
    text = re.sub(r'\s+',            ' ', text).strip()

    tokens = [
        w for w in text.split()
        if w not in STOP_WORDS and len(w) > 2
    ]
    return ' '.join(tokens)


def predict(
    user_query : str,
    classifier : dict
) -> dict:
    """
    Full classification pipeline for one query.

    Args:
        user_query  : raw text from user
        classifier  : dict from app.state.classifier

    Returns dict:
        intent      : predicted intent label (string)
        confidence  : top class probability (0–100 float)
        all_probs   : dict of {intent: probability} for all 20 classes
        clean_query : cleaned version of input (for debugging)
    """
    model = classifier["model"]
    tfidf = classifier["tfidf"]
    le    = classifier["le"]

    # Step 1 — clean input
    cleaned = clean_text(user_query)

    # Step 2 — TF-IDF transform
    vec = tfidf.transform([cleaned])

    # Step 3 — predict label
    label     = model.predict(vec)[0]
    intent    = le.inverse_transform([label])[0]

    # Step 4 — confidence score
    proba      = model.predict_proba(vec)[0]
    confidence = round(float(proba.max()) * 100, 2)

    # Step 5 — all class probabilities (useful for debugging)
    all_probs = {
        le.inverse_transform([i])[0]: round(float(p) * 100, 2)
        for i, p in enumerate(proba)
    }

    return {
        "intent"      : intent,
        "confidence"  : confidence,
        "all_probs"   : all_probs,
        "clean_query" : cleaned
    }


def should_escalate(confidence: float) -> tuple[bool, str]:
    """
    Confidence gate — decides whether to serve solution or escalate.

    Args:
        confidence : float 0–100

    Returns:
        (escalate: bool, reason: str)
    """
    threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 60))

    if confidence < threshold:
        return True, (
            f"Confidence {confidence:.1f}% is below threshold {threshold:.0f}%. "
            f"Routing to support engineer for accurate resolution."
        )
    return False, ""
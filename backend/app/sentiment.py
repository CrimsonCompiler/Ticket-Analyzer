"""Tiny Hugging Face sentiment model loader and inference.

The model weights are baked into the Docker image during build (see
backend/Dockerfile). At runtime TRANSFORMERS_OFFLINE=1 forces the
transformers library to use the local HF_HOME cache, so the container
fails loudly if the weights are missing instead of silently
downloading them.
"""
import os
import threading
from typing import Tuple

from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .config import (
    HF_HOME,
    MODEL_NAME,
    SENTIMENT_CONFIDENCE_THRESHOLD,
    TRANSFORMERS_OFFLINE,
)

os.environ["HF_HOME"] = HF_HOME
os.environ["TRANSFORMERS_OFFLINE"] = TRANSFORMERS_OFFLINE

_lock = threading.Lock()
_tokenizer = None
_model = None


def _load() -> None:
    global _tokenizer, _model
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    _model.eval()


def load_model_once() -> None:
    """Load the model eagerly at backend startup so the first request
    is fast (PRD requirement)."""
    with _lock:
        if _model is None:
            _load()


def analyze(text: str) -> Tuple[str, float]:
    """Return (label, confidence).

    Label is one of POSITIVE, NEGATIVE, or UNCERTAIN. distilbert-sst-2
    only knows two classes, so any text that isn't a clear opinion
    (release notes, how-to instructions, neutral updates) gets a
    near-50/50 score. Below SENTIMENT_CONFIDENCE_THRESHOLD we report
    UNCERTAIN rather than picking a side the model doesn't believe in.
    The raw confidence is preserved so the UI can still show "53%
    negative" instead of hiding the signal completely.
    """
    if _model is None or _tokenizer is None:
        load_model_once()
    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = _model(**inputs)
    probs = outputs.logits.softmax(dim=-1).detach().squeeze().tolist()
    idx = int(probs.index(max(probs)))
    label = _model.config.id2label[idx]  # POSITIVE / NEGATIVE
    confidence = float(probs[idx])
    if confidence < SENTIMENT_CONFIDENCE_THRESHOLD:
        return "UNCERTAIN", confidence
    return label, confidence

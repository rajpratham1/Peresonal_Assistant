from __future__ import annotations

import pickle
from pathlib import Path

from backend.config import MODEL_PATH, VECTORIZER_PATH


class IntentModel:
    def __init__(self, model_path: Path = MODEL_PATH, vectorizer_path: Path = VECTORIZER_PATH):
        if not model_path.exists() or not vectorizer_path.exists():
            raise FileNotFoundError(
                "Intent model artifacts not found. Run `python -m backend.ml.train` first."
            )
        with model_path.open("rb") as model_file:
            self.model = pickle.load(model_file)
        with vectorizer_path.open("rb") as vectorizer_file:
            self.vectorizer = pickle.load(vectorizer_file)

    def predict(self, text: str) -> str:
        features = self.vectorizer.transform([text])
        return str(self.model.predict(features)[0])

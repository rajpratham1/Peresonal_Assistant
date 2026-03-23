from __future__ import annotations

import json
import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

from backend.config import ARTIFACTS_DIR, MODEL_PATH, TRAINING_DATA_PATH, VECTORIZER_PATH


def train() -> None:
    with TRAINING_DATA_PATH.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    texts, labels = zip(*dataset)

    vectorizer = CountVectorizer(ngram_range=(1, 2))
    features = vectorizer.fit_transform(texts)

    model = MultinomialNB()
    model.fit(features, labels)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as model_file:
        pickle.dump(model, model_file)
    with VECTORIZER_PATH.open("wb") as vectorizer_file:
        pickle.dump(vectorizer, vectorizer_file)


if __name__ == "__main__":
    train()

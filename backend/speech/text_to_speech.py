from __future__ import annotations

from functools import lru_cache

try:
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None


@lru_cache(maxsize=1)
def get_engine():
    if pyttsx3 is None:
        return None
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    return engine


def speak(text: str) -> None:
    if not text:
        return
    engine = get_engine()
    if engine is None:
        return
    engine.say(text)
    engine.runAndWait()

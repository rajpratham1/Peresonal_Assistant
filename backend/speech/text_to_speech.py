from __future__ import annotations

import io
import os
from functools import lru_cache

try:
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None

try:
    from gtts import gTTS
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    _mixer_initialized = False
except ImportError:  # pragma: no cover
    gTTS = None
    pygame = None
    _mixer_initialized = False


@lru_cache(maxsize=1)
def get_engine():
    if pyttsx3 is None:
        return None
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    voices = engine.getProperty("voices")
    # Prefer a higher-quality voice if available
    for v in voices:
        if "zira" in v.id.lower() or "david" in v.id.lower():
            engine.setProperty("voice", v.id)
            break
    return engine


def _ensure_mixer() -> bool:
    """Lazily initialise the pygame mixer once and keep it alive."""
    global _mixer_initialized
    if pygame is None:
        return False
    if not _mixer_initialized:
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            _mixer_initialized = True
        except Exception:
            return False
    return True


def _speak_hindi(text: str) -> None:
    if gTTS is None or not _ensure_mixer():
        _speak_english(text)
        return
    try:
        tts = gTTS(text=text, lang="hi")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        pygame.mixer.music.load(fp, 'mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception:
        # Fallback to English/default synthesised engine if network fails
        _speak_english(text)


def _speak_english(text: str) -> None:
    engine = get_engine()
    if engine is None:
        return
    engine.say(text)
    engine.runAndWait()


def speak(text: str, language: str = "en") -> None:
    if not text:
        return
    if language == "hi":
        _speak_hindi(text)
    else:
        _speak_english(text)

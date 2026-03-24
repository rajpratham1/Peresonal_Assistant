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
except ImportError:  # pragma: no cover
    gTTS = None
    pygame = None


@lru_cache(maxsize=1)
def get_engine():
    if pyttsx3 is None:
        return None
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    return engine


def _speak_hindi(text: str) -> None:
    if gTTS is None or pygame is None:
        _speak_english(text)
        return
    try:
        tts = gTTS(text=text, lang="hi")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        pygame.mixer.init()
        pygame.mixer.music.load(fp, 'mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    except Exception:
        # Fallback to English/default synthesized engine if network fails
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

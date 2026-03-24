from __future__ import annotations

import audioop
import json
from functools import lru_cache
import numpy as np

from backend.config import (
    SPEECH_BACKEND,
    VOSK_MODEL_PATH,
    WHISPER_COMPUTE_TYPE,
    WHISPER_MODEL_SIZE,
)

try:
    import pyaudio
    from vosk import KaldiRecognizer, Model
except ImportError:  # pragma: no cover
    pyaudio = None
    KaldiRecognizer = None
    Model = None

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover
    WhisperModel = None


@lru_cache(maxsize=1)
def load_model():
    if Model is None:
        raise RuntimeError("Vosk or PyAudio dependencies are not installed.")
    if not VOSK_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Vosk model not found at: {VOSK_MODEL_PATH}. "
            "Download a model and update VOSK_MODEL_PATH if needed."
        )
    return Model(str(VOSK_MODEL_PATH))


@lru_cache(maxsize=1)
def load_whisper_model():
    if WhisperModel is None:
        raise RuntimeError("faster-whisper is not installed.")
    return WhisperModel(WHISPER_MODEL_SIZE, compute_type=WHISPER_COMPUTE_TYPE)


def _capture_audio(
    sample_rate: int = 16000,
    chunk_size: int = 1024,
    silence_threshold: int = 700,
    max_silence_chunks: int = 8,
    min_chunks: int = 8,
) -> bytes:
    if pyaudio is None:
        raise RuntimeError("PyAudio is not installed.")

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size,
    )

    frames: list[bytes] = []
    heard_voice = False
    silent_chunks = 0

    try:
        stream.start_stream()
        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)
            rms = audioop.rms(data, 2)
            
            if rms > silence_threshold:
                if not heard_voice:
                    heard_voice = True
                    # Keep only last chunk for seamless preroll, dropping hours of silence
                    if frames:
                        frames = [frames[-1]]
                silent_chunks = 0
            elif heard_voice:
                silent_chunks += 1

            if heard_voice:
                frames.append(data)

            if heard_voice and len(frames) >= min_chunks and silent_chunks >= max_silence_chunks:
                break
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

    return b"".join(frames)


def _listen_vosk(sample_rate: int = 16000, chunk_size: int = 4000) -> str:
    if pyaudio is None or KaldiRecognizer is None:
        raise RuntimeError("Vosk or PyAudio dependencies are not installed.")

    recognizer = KaldiRecognizer(load_model(), sample_rate)
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk_size,
    )

    try:
        stream.start_stream()
        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                return result.get("text", "").strip()
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


def _listen_whisper(sample_rate: int = 16000, language: str = "en") -> str:
    audio_bytes = _capture_audio(sample_rate=sample_rate)
    if not audio_bytes:
        return ""
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    segments, _info = load_whisper_model().transcribe(audio_np, language=language, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text


def listen(sample_rate: int = 16000, chunk_size: int = 4000, language: str = "en") -> str:
    try:
        if SPEECH_BACKEND == "whisper":
            return _listen_whisper(sample_rate=sample_rate, language=language)
        return _listen_vosk(sample_rate=sample_rate, chunk_size=chunk_size)
    except Exception:
        if SPEECH_BACKEND == "whisper":
            return _listen_vosk(sample_rate=sample_rate, chunk_size=chunk_size)
        raise

def wait_for_wake_word(sample_rate: int = 16000, chunk_size: int = 4000, wake_word: str = "viru") -> None:
    """Blocks with ~0 CPU overhead until exact grammar wake word is spoken."""
    if pyaudio is None or KaldiRecognizer is None:
        return
        
    recognizer = KaldiRecognizer(load_model(), sample_rate, f'["{wake_word}", "[unk]"]')
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=chunk_size)
    
    try:
        stream.start_stream()
        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                if wake_word in res.get("text", ""):
                    break
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

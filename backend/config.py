from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

MODELS_DIR = BASE_DIR / "models"
VOSK_MODEL_PATH = Path(
    os.getenv("VOSK_MODEL_PATH", MODELS_DIR / "vosk-model-small-en-us-0.15")
)
SPEECH_BACKEND = os.getenv("SPEECH_BACKEND", "whisper").lower()
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
LLM_MODELS_DIR = MODELS_DIR / "llm"
LOCAL_LLM_ENABLED = os.getenv("LOCAL_LLM_ENABLED", "1").lower() in {"1", "true", "yes", "on"}
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5-7b-instruct")
LOCAL_LLM_TIMEOUT = int(os.getenv("LOCAL_LLM_TIMEOUT", "45"))

ML_DIR = BASE_DIR / "ml"
ARTIFACTS_DIR = ML_DIR / "artifacts"
TRAINING_DATA_PATH = ML_DIR / "training_data.json"
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"
VECTORIZER_PATH = ARTIFACTS_DIR / "vectorizer.pkl"

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "data.db"

APP_ALIASES = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "explorer": "explorer.exe",
    "edge": "msedge.exe",
    "chrome": "chrome.exe",
    "settings": "ms-settings:",
}

WEBSITE_ALIASES = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "spotify": "https://open.spotify.com",
}

FUZZY_TARGETS = {
    "you tube": "youtube",
    "utube": "youtube",
    "g mail": "gmail",
    "mail": "gmail",
    "edge browser": "edge",
    "whats app": "whatsapp",
    "whatsup": "whatsapp",
    "calc": "calculator",
}

DEFAULT_CONTACTS = [
    {
        "name": "papa",
        "phone": "6205015353",
        "whatsapp_name": "papa",
    },
    {
        "name": "baua ji",
        "phone": "8810328591",
        "whatsapp_name": "Baua ji",
    },
    {
        "name": "babu",
        "phone": "9931322271",
        "whatsapp_name": "Babu",
    },
]

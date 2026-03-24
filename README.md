# Offline Voice-Controlled Personal Assistant

An offline-first personal assistant built with Python. It supports:

- Offline speech-to-text with Whisper or Vosk
- Offline text-to-speech with `pyttsx3`
- Local intent detection with scikit-learn
- Optional local LLM command parsing with `llama.cpp`
- Local storage with SQLite
- System, app, file, email, and messaging actions
- A simple Tkinter GUI

## Structure

```text
backend/
  main.py
  config.py
  speech/
  ml/
  actions/
  database/
  utils/
frontend/
  gui.py
requirements.txt
```

## Setup

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Download a Vosk model and extract it into:

```text
backend/models/vosk-model-small-en-us-0.15
```

3. Train the intent model:

```powershell
python -m backend.ml.train
```

4. Run the desktop GUI:

```powershell
python -m frontend.gui
```

5. Run the voice assistant loop:

```powershell
python -m backend.main
```

## Notes

- Email sending uses SMTP credentials from environment variables.
- Messaging is implemented as local desktop automation with `pyautogui`.
- Destructive system actions require explicit command matches.
- The assistant is modular and intended to be expanded with more intents and actions.

## Better Hearing With Whisper

The default speech backend is now `Whisper` through `faster-whisper`.
It usually hears English commands better than Vosk.

Optional settings:

```powershell
$env:SPEECH_BACKEND="whisper"
$env:WHISPER_MODEL_SIZE="small"
$env:WHISPER_COMPUTE_TYPE="int8"
```

Fallback settings:

```powershell
$env:SPEECH_BACKEND="vosk"
```

If Whisper is not available, the assistant falls back to Vosk.

## Recommended Local LLM

The assistant can use a local `llama.cpp` server to understand more natural English.
Recommended model:

- `Qwen2.5-7B-Instruct` in GGUF format

This is optional, but it improves:

- natural voice commands
- casual English replies
- command extraction from messy speech

## Local LLM Setup

### 1. Download `llama.cpp`

Get `llama.cpp` from:

- https://github.com/ggml-org/llama.cpp

Build it or download a Windows release that includes `llama-server`.

### 2. Download a GGUF model

Download a quantized GGUF of:

- `Qwen2.5-7B-Instruct`

Place it anywhere on disk, for example:

```text
backend/models/llm/qwen2.5-7b-instruct-q4_k_m.gguf
```

### 3. Start the local model server

Example command:

```powershell
llama-server -m backend\models\llm\qwen2.5-7b-instruct-q4_k_m.gguf -c 4096 --host 127.0.0.1 --port 8080
```

### 4. Run this assistant

In a second terminal:

```powershell
.venv\Scripts\Activate.ps1
python -m backend.ml.train
python -m frontend.gui
```

## Environment Variables

These are optional:

```powershell
$env:LOCAL_LLM_ENABLED="1"
$env:LOCAL_LLM_URL="http://127.0.0.1:8080/v1/chat/completions"
$env:LOCAL_LLM_MODEL="qwen2.5-7b-instruct"
```

If `LOCAL_LLM_ENABLED` is off or the server is not reachable, the assistant falls back to the local rule-based and scikit-learn parser.

## Example Commands

With the local LLM running, commands can be more natural:

- `open youtube and play aaj ki raat`
- `open edge`
- `gmail`
- `call 9876543210`
- `set alarm for 12:30`
- `at 12:30 message alice saying hello`
- `find my resume file`
- `what can you do`
#

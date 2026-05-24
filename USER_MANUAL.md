# 📖 Viru AI Desktop Assistant — User Manual & Operations Guide

Welcome to the official user manual for **Viru**, your elite, offline-first personal assistant and web dashboard controller. This guide will walk you through setting up, running, configuring, and leveraging every aspect of Viru's agentic capabilities on your PC and mobile device.

---

## 📋 Table of Contents
1. [Introduction](#-1-introduction)
2. [System Requirements](#-2-system-requirements)
3. [Setup & Installation](#-3-setup--installation)
4. [Desktop Launcher vs. Web Dashboard](#-4-desktop-launcher-vs-web-dashboard)
5. [Feature Operating Guides](#-5-feature-operating-guides)
   - [Voice Recognition & Text-To-Speech](#voice-recognition--text-to-speech)
   - [Local LLM Brain & KV Caching](#local-llm-brain--kv-caching)
   - [Agentic OS Control & PyAutoGUI scripting](#agentic-os-control--pyautogui-scripting)
   - [Screen vision & OCR Clicking](#screen-vision--ocr-clicking)
   - [Infinite Memory (Local RAG)](#infinite-memory-local-rag)
   - [WhatsApp Background Automation](#whatsapp-background-automation)
   - [Google Calendar Sync](#google-calendar-sync)
6. [Mobile Access & Local LAN Configuration](#-6-mobile-access--local-lan-configuration)
7. [Troubleshooting & FAQs](#-7-troubleshooting--faqs)

---

## 🚀 1. Introduction
Viru is a private, offline-first AI desktop assistant. Unlike basic voice assistants that rely on external API calls, Viru hosts a local Large Language Model (Qwen 2.5 3B) and local machine learning models directly on your hardware. It runs local screen readers, indexes your desktop files, and automates OS actions natively, ensuring absolute privacy.

---

## 💻 2. System Requirements
* **Operating System**: Windows 10/11 (64-bit).
* **CPU**: Quad-core Intel/AMD processor (Optimized for Intel Alder Lake and newer architectures).
* **RAM**: 8GB Minimum (16GB recommended for optimal concurrent model loading).
* **Audio**: Active microphone (input) and speakers/headphones (output).
* **Network**: Local Wi-Fi connection (required only for LAN sharing with mobile devices).
* **System Utilities**: **FFmpeg** installed and added to your System PATH environment variables (required for audio transcription).

---

## 🛠️ 3. Setup & Installation

### Step 1: Clone or Extract the Project
Open a terminal in the folder where you want to host the assistant and run:
```powershell
git clone https://github.com/rajpratham1/Peresonal_Assistant.git
cd Peresonal_Assistant
```

### Step 2: Auto-Setup
Run the automated bootstrapper script:
```powershell
.\setup.bat
```
This script will:
1. Create a Python Virtual Environment (`.venv`).
2. Upgrade `pip` and install all required libraries (PyTorch, EasyOCR, Faster-Whisper, CustomTkinter, Flask, qrcode, Playwright).
3. Download the Vosk offline speech model.
4. Download the quantized Local LLM model (`qwen2.5-3b-instruct-q4_k_m.gguf`).
5. Initialize the SQLite database files.

---

## 🖥️ 4. Desktop Launcher vs. Web Dashboard

Viru can be run in two modes. You can run either or both concurrently:

### Option A: Premium Desktop GUI & System Tray
This runs Viru as a Windows desktop application.
* **Launch command**:
  ```powershell
  .\run.bat
  ```
* **Features**:
  - Minimizes directly to your Windows System Tray (Ghost Mode) to save screen space.
  - Active wake-word listening ("Viru") that uses 0% CPU when idle.
  - Glassmorphic interface with Assistant Chat, Settings, and Developer profile tabs.

### Option B: Responsive Web Dashboard & LAN Server
This hosts a web interface that can be accessed from your computer or any mobile device in the same local network.
* **Launch command**:
  ```powershell
  .\run_web.bat
  ```
* **Accessing on PC**: Open your browser to [http://localhost:5000](http://localhost:5000).
* **Accessing on Mobile**: Scan the QR code shown in the **Mobile Access** card, or type the LAN URL (e.g. `http://10.103.99.142:5000`) into your phone's browser.
* **Features**:
  - Live charts showing CPU, RAM, Disk, and Network usage.
  - Card-grid management for Notes, Contacts, Reminders, and Alarms.
  - Live directory file browser.
  - Screenshot gallery with OCR text extraction.
  - Persistent, searchable conversation history.

---

## 🧠 5. Feature Operating Guides

### Voice Recognition & Text-To-Speech
- **Wake Word**: Speak *"Viru"* followed by your command (e.g. *"Viru, open notepad"*). The Vosk listener filters out background noise and wakes up instantly.
- **Bilingual Support**: Say *"switch to Hindi"* or select **HI** in the web input bar to communicate in Hindi. Text-to-speech outputs will automatically adjust to standard Hindi accents.

### Local LLM Brain & KV Caching
The cognitive engine runs a Qwen 3B LLM locally via `llama-server.exe` on port `8080`.
- **Latency Optimization**: The system prompt is kept static, ensuring that llama.cpp hits its prefix KV cache. Consecutive chat response times are extremely low (~2 seconds).
- **Fallback**: If the local LLM server is not running, the system automatically falls back to an offline rule-based intent matching engine to process core commands.

### Agentic OS Control & PyAutoGUI Scripting
Viru does not just open apps; it can physically control them.
- **Example command**: *"Take control of my computer and draw a square in paint"*
- **How it works**: The local LLM generates executable Python code using `pyautogui`. The program asks for your confirmation (for security) and then moves your cursor, clicks buttons, and types text on your desktop in real-time.
- **Safety Tip**: Press `Ctrl + Alt + Del` or move the mouse cursor to any of the 4 corners of the screen to trigger PyAutoGUI's fail-safe and stop execution instantly.

### Screen Vision & OCR Clicking
- **Read Screen**: Say *"read my screen"* or click **📸 Screenshot** on the dashboard. Viru will capture the desktop, run PyTorch OCR, and read aloud whatever text it finds.
- **Context-Aware Clicks**: Ask *"click the Apply button"*. The vision engine locates the text coordinates on screen and clicks it for you.

### Infinite Memory (Local RAG)
- **Indexing Files**: Click **Sync Memory** in the Web UI or say *"Sync memory"*. Viru will scan the `.txt` and `.pdf` files on your Desktop and index them into `ChromaDB`.
- **Querying Memory**: Ask *"Who is referenced in my desktop notes?"* or *"What did I write in my shopping list?"* Viru retrieves the exact context and answers locally.
- **Bypass Feature**: If no files are indexed, the memory check is skipped in less than 1ms to save system resources.

### WhatsApp Background Automation
- **Setup**: On first run, a Chromium session will open. Scan the WhatsApp Web QR code to authenticate. The session is saved locally in `/whatsapp_session/`.
- **Command**: *"message John saying meeting at 5pm"* or *"schedule a WhatsApp message to Sarah at 18:30 saying happy birthday"*
- **Execution**: Run silently in headless Chrome via Playwright in the background without stealing your active window focus.

### Google Calendar Sync
- **Authentication**: On first calendar check, a browser window will open asking you to sign into your Google account and grant permissions. It saves OAuth tokens securely.
- **Command**: *"What meetings do I have today?"*

---

## 📲 6. Mobile Access & Local LAN Configuration

To connect your phone to the Web Dashboard:
1. Ensure your PC and mobile device are connected to the **same Wi-Fi router**.
2. Run `run_web.bat` on your PC.
3. Open `http://localhost:5000` on your PC.
4. Scan the QR code shown on the **Mobile Access** widget using your phone's camera, or type the IP address shown below it in your phone's web browser.

> [!NOTE]
> We use a socket interface connection to `8.8.8.8` to query the operating system's active routing table. This guarantees the dashboard shows the correct Wi-Fi IP address even if VirtualBox, WSL, or disconnected Ethernet adapters are active.

> [!IMPORTANT]
> **Windows Defender Firewall Resolution**:
> If your phone's browser fails to connect, Windows Firewall is blocking incoming network traffic on port `5000`.
> To fix this:
> 1. Open Windows Search and type **Allow an app through Windows Firewall**.
> 2. Click **Change Settings**.
> 3. Add `python.exe` (located in `.venv/Scripts/python.exe`) and check both **Private** and **Public** checkboxes.
> 4. Click **OK**.

---

## ❓ 7. Troubleshooting & FAQs

#### Q: The Web UI says "LLM Offline" in the bottom-left corner.
- **A**: The Flask server started but the local `llama-server.exe` was unable to bind to port `8080`. Go to your task manager, kill any lingering `llama-server.exe` processes, and restart `run_web.bat`.

#### Q: The voice listener is not hearing me.
- **A**: Verify that your microphone is set as the default recording device in Windows Sound Settings. Ensure no other application (like Zoom or Teams) is locking your microphone.

#### Q: Faster-Whisper is slow or throwing PyTorch warnings.
- **A**: By default, faster-whisper uses CPU integer quantization (`int8`). If you have a dedicated NVIDIA GPU with CUDA support, you can enable hardware acceleration by updating the environment variable in `backend/config.py`:
  `WHISPER_COMPUTE_TYPE = "float16"`

#### Q: How do I close everything?
- **A**: Close the terminal windows running the scripts, or right-click the **Viru** tray icon in your system tray and select **Exit**.

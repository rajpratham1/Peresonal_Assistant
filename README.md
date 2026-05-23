# 🤖 VIRU: The Ultimate AI Desktop Assistant & Web Dashboard

[![GitHub](https://img.shields.io/badge/Developer-Pratham_Kumar-cba6f7?style=for-the-badge&logo=github)](https://github.com/rajpratham1)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Elite_Ready-success?style=for-the-badge)](https://github.com/rajpratham1/Peresonal_Assistant)

**Viru** is a production-grade, autonomous, multi-modal personal assistant designed for desktop orchestration. Built with a **Local LLM Cognitive Engine**, a zero-dependency **Web Dashboard**, and a **Zero-CPU Wake Word** system, Viru transforms your computer into a self-aware agent capable of seeing, hearing, thinking, and executing complex workflows in real-time.

---

### 🌟 Key Features

#### 🧠 1. Cognitive Brain (Local LLM)
- Powered by **Qwen 2.5 3B (GGUF)** running locally via `llama.cpp` on port `8080`.
- **KV Prompt Caching & Compact Schema**: Sub-2-second response latency on CPU.
- **Private & Offline**: Your data never leaves your machine.

#### 🖥️ 2. Web Client & Dashboard (localhost:5000)
- **Glassmorphic Control Centre**: Sleek responsive design built with HTML5, Vanilla CSS, and JavaScript.
- **Real-Time System Monitor**: Live CPU/RAM usage charts (powered by Chart.js & Flask polling).
- **Clipboard & File Browser**: Navigate and open local files directly from the browser.
- **Screen Captures**: View, download, or perform OCR text extraction on captured screenshots.
- **SQLite Productivity Modules**: Manage notes, contacts, alarms, and reminders directly from the UI.
- **LAN Sharing**: Scans your local network and displays a QR code so you can access the dashboard from your phone on the same WiFi!

#### 👁️ 3. God-Mode Vision (Sight)
- **OCR Engine**: Uses `EasyOCR` and `PyTorch` to read text on any screen window.
- **Vision-Clicking**: Viru can find the coordinates of buttons/text and execute mouse clicks using `PyAutoGUI`.
- **Window Awareness**: Always contextually aware of which window is active.

#### 🎙️ 4. Multilingual Voice Core
- **Wake Word**: Strict grammar **Vosk** isolator ("Viru") with near **0% CPU usage** while idle.
- **Bi-Lingual**: Flawless switching between **Hindi** and **English**.
- **Speech Engine**: High-fidelity ASR via **Faster-Whisper** and natural TTS via `pyttsx3`.

#### ♾️ 5. Infinite Memory (Local RAG)
- **Vector Database**: Built-in `ChromaDB` and `LangChain` index your desktop files (PDFs, Docs, TXT).
- **Contextual Recall**: Bypasses heavy transformer imports when database is empty for zero overhead.

#### 🤖 6. Agentic Automation
- **WhatsApp Mastery**: Headless background automation via `Playwright` to send/schedule messages.
- **Google Sync**: Native OAuth2 integration for Google Calendar management.
- **Smart Home**: Generic Webhook bridge for IoT control.

---

### ⚠️ Cloud Deployment Warning

> [!CAUTION]
> **Do NOT deploy this project to public cloud hosting platforms (like Vercel, Heroku, Render, or Netlify).**
> It will NOT work properly there because:
> 1. **Local System Access**: It requires physical access to your operating system to execute commands, open directories, launch apps, and automate mouse/keyboard inputs via `pyautogui`.
> 2. **Audio Hardware**: Voice input/output requires physical audio device interfaces (microphone and speakers via `pyaudio`/`pyttsx3`) not present in cloud containers.
> 3. **Model Resource Demand**: Running a 3B LLM model locally requires dedicated local CPU/GPU/RAM. Free cloud tiers will crash immediately due to out-of-memory errors.
> 
> **Always run this project locally (localhost) or share it on your Local Area Network (LAN).**

---

### 🚀 Local Host Setup & Guide

#### 1. System Requirements
- Windows 10/11
- Python 3.10+
- FFmpeg (for voice processing, added to System PATH)
- 8GB+ RAM

#### 2. Installation Commands
Open PowerShell or Command Prompt and run the following:

```powershell
# Clone the repository
git clone https://github.com/rajpratham1/Peresonal_Assistant.git
cd Peresonal_Assistant

# Run the setup script (creates virtual environment, installs pip packages, downloads models)
.\setup.bat
```

#### 3. Starting the Desktop Client
To run the Tkinter GUI and system tray listener:
- **Via file explorer**: Double-click **`run.bat`**
- **Via command line**:
  ```powershell
  # Activate virtual environment
  .venv\Scripts\activate
  # Start loader
  python main_loader.py
  ```

#### 4. Starting the Web Client & Dashboard
To run the premium web dashboard:
- **Via file explorer**: Double-click **`run_web.bat`**
- **Via command line**:
  ```powershell
  # Activate virtual environment
  .venv\Scripts\activate
  # Launch the web server
  python web_server.py
  ```
  Once started, open your browser and navigate to: **`http://localhost:5000`**

---

### 👨‍💻 Developer
**Pratham Kumar**  
B.Tech CSE student, Web Developer, and Active AI Builder.  
[GitHub Profile](https://github.com/rajpratham1) | [Project Repository](https://github.com/rajpratham1/Peresonal_Assistant)

---

### ⚖️ License
This project is for educational and personal use. All local model usage respects the original Qwen and llama.cpp licenses.
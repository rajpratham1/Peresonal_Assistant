# 🤖 VIRU: The Ultimate AI Desktop Assistant
[![GitHub](https://img.shields.io/badge/Developer-Pratham_Kumar-cba6f7?style=for-the-badge&logo=github)](https://github.com/rajpratham1)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Elite_Ready-success?style=for-the-badge)](https://github.com/rajpratham1/Peresonal_Assistant)

**Viru** is a production-grade, autonomous, multi-modal personal assistant designed for mission-critical desktop orchestration. Built with a **Local LLM Cognitive Engine** and a **Zero-CPU Wake Word** system, Viru transforms your computer into a self-aware agent capable of seeing, hearing, thinking, and executing complex workflows in real-time.

---

### 🌟 Key "Elite" Features

#### 🧠 1. Cognitive Brain (Local LLM)
- Powered by **Qwen 2.5 3B (GGUF)** running locally via `llama.cpp`.
- **Latency-Free Control**: Auto-boots a local inference server on port `8080`.
- **Private & Offline**: Your data never leaves your machine.

#### 👁️ 2. God-Mode Vision (Sight)
- **OCR Engine**: Uses `EasyOCR` and `PyTorch` to read text on any screen window.
- **Vision-Clicking**: Viru can find the coordinates of buttons or text (e.g., *"Click the Apply button"*) and move your mouse to execute the click using `PyAutoGUI`.
- **Window Awareness**: Always knows which application is currently focused.

#### 🎙️ 3. Multilingual Voice Core
- **Wake Word**: Strict grammar **Vosk** isolator ("Viru") with near **0% CPU usage** while idle.
- **Bi-Lingual**: Flawless switching between **Hindi** and **English**.
- **Speech Engine**: High-fidelity ASR via **Faster-Whisper** and natural TTS via **gTTS**.

#### ♾️ 4. Infinite Memory (Local RAG)
- **Vector Database**: Built-in `ChromaDB` and `LangChain` index your local files (PDFs, Docs, TXT).
- **Contextual Recall**: Viru remembers your notes and documents to answer complex queries about your life/work.

#### 🌐 5. Live Intelligence (Internet Search)
- **Real-Time Search**: Integrated DuckDuckGo search bridge for live news, weather, and fact-checking.

#### 🤖 6. Agentic Automation
- **WhatsApp Mastery**: Headless automation via `Playwright` to send and schedule messages.
- **Google Sync**: Native OAuth2 integration for Google Calendar management.
- **Smart Home**: Generic Webhook bridge for IoT control.

---

### 🎨 Premium UI/UX
The interface is built with **CustomTkinter** featuring a modern, tabbed design:
- **Assistant Tab**: Real-time typing animations and chat history.
- **Settings Tab**: Customizable **Light/Dark modes** and accent themes (Blue/Green/Mauve).
- **Developer Tab**: Built-in profile card linking to your GitHub.

---

### 🚀 Getting Started

#### 1. Requirements
- Python 3.10+
- FFmpeg (for audio processing)
- At least 8GB of RAM (for the 3B model)

#### 2. Installation
```powershell
# Clone the repository
git clone https://github.com/rajpratham1/Peresonal_Assistant.git
cd Peresonal_Assistant

# Run the setup (Installs all dependencies & LLM binaries)
.\setup.bat
```

#### 3. Execution
Simply double-click **`run.bat`**. This will:
1. Boot the **System Tray (Ghost Mode)** listener.
2. Spin up the **Local LLM Server**.
3. Launch the **Modern GUI**.

---

### 🛠️ Tech Stack
- **AI/LLM**: `llama.cpp`, `LangChain`, `Chromadb`
- **CV/Vision**: `EasyOCR`, `PyTorch`
- **UI**: `CustomTkinter`, `PIL`
- **Automation**: `Playwright`, `PyAutoGUI`
- **Audio**: `Faster-Whisper`, `Vosk`, `Pyaudio`

---

### 👨‍💻 Developer
**Pratham Kumar**  
B.Tech CSE student, Web Developer, and Active AI Builder.  
[GitHub Profile](https://github.com/rajpratham1) | [Project Repository](https://github.com/rajpratham1/Peresonal_Assistant)

---

### ⚖️ License
This project is for educational and personal use. All local model usage respects the original Qwen and llama.cpp licenses.

> *"Building the future of personal desktop agents, one line of code at a time."*

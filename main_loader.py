import sys
import threading
import time
import subprocess
from pathlib import Path

# Add project root to path for relative imports
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.append(str(PROJECT_ROOT))

def ensure_llm_core():
    """Run the downloader to ensure the brain is present before booting."""
    print("Checking AI Brain status...")
    try:
        from backend.models.download_llm import main as download_main
        download_main()
    except Exception as e:
        print(f"Brain check failed: {e}")

def run_backend_tray():
    """Start the system tray icon listener."""
    from backend.main import main as backend_main
    backend_main()

def run_gui():
    """Start the CustomTkinter GUI."""
    import customtkinter as ctk
    from frontend.gui import AssistantGUI
    root = ctk.CTk()
    app = AssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    # 1. Ensure the LLM model and binaries are present
    ensure_llm_core()
    
    # 2. Start the Backend/Tray in a separate thread
    tray_thread = threading.Thread(target=run_backend_tray, daemon=True)
    tray_thread.start()
    
    # 3. Launch the GUI on the main thread
    time.sleep(2)  # Give the tray a moment to init
    run_gui()

"""
Viru AI Assistant – Unified Process Loader
------------------------------------------
Runs everything in ONE Python process:
  1. Checks / downloads AI brain (LLM model)
  2. Boots the local llama-server (port 8080)
  3. Creates a SINGLE Assistant instance (no DB lock, no mic conflict)
  4. Launches the GUI on the main thread
  5. Starts a system-tray icon in a background thread

Closing the window hides it to the system tray.
Right-click the tray icon → "Show Window" to restore,
or "Exit" to fully quit.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


# ── 1. Ensure LLM brain is present ────────────────────────────────────────────
def _ensure_brain():
    print("🧠 Checking AI Brain status…")
    try:
        from backend.models.download_llm import main as dl
        dl()
    except Exception as exc:
        print(f"   Brain check skipped: {exc}")


# ── 2. System-tray icon ────────────────────────────────────────────────────────
def _run_tray(gui_ref: dict):
    """
    Runs the pystray icon in its own thread.
    gui_ref['gui'] will be set once the GUI object is created.
    """
    try:
        import pystray
        from PIL import Image as PILImage, ImageDraw

        def _make_icon() -> PILImage.Image:
            img = PILImage.new("RGBA", (64, 64), (0, 0, 0, 0))
            d   = ImageDraw.Draw(img)
            d.ellipse((4, 4, 60, 60), fill=(203, 166, 247))   # Mauve circle
            d.ellipse((20, 20, 44, 44), fill=(30, 30, 46))    # Dark centre
            return img

        def _show(icon, item):
            g = gui_ref.get("gui")
            if g:
                g.root.after(0, g.show)

        def _exit(icon, item):
            g = gui_ref.get("gui")
            if g:
                g.voice_active = False
                try:
                    g.root.after(0, g.root.destroy)
                except Exception:
                    pass
            icon.stop()

        menu = pystray.Menu(
            pystray.MenuItem("Show Window", _show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Viru", _exit),
        )
        icon = pystray.Icon("Viru", _make_icon(), "Viru Assistant", menu)
        icon.run()

    except Exception as exc:
        print(f"   Tray unavailable: {exc}")


# ── 3. Wake-word listener (runs when GUI is hidden) ───────────────────────────
def _run_wake_word(gui_ref: dict, stop_event: threading.Event):
    """
    While the GUI is hidden, listen for the wake word.
    When heard, restore the window and activate voice mode.
    """
    try:
        from backend.speech.speech_to_text import wait_for_wake_word
        while not stop_event.is_set():
            g = gui_ref.get("gui")
            # Only listen when window is hidden
            if g and not g.root.winfo_viewable():
                try:
                    wait_for_wake_word(wake_word="virus")
                    if not stop_event.is_set():
                        g.root.after(0, g.show)
                        time.sleep(0.5)
                        if not g.voice_active:
                            g.root.after(0, g.toggle_voice)
                except Exception:
                    pass
            else:
                time.sleep(1)
    except Exception as exc:
        print(f"   Wake-word listener error: {exc}")


# ── Main entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Step 1 – brain check (fast if already downloaded)
    _ensure_brain()

    # Step 2 – shared Assistant (created before GUI so LLM server boots early)
    print("⚡ Initialising Assistant engine…")
    from backend.main import Assistant
    shared_assistant = Assistant()
    print("   Engine ready.")

    # Shared ref dict so threads can access the GUI once it's built
    gui_ref    = {}
    stop_event = threading.Event()

    # Step 3 – system tray (background thread)
    tray_thread = threading.Thread(target=_run_tray, args=(gui_ref,), daemon=True)
    tray_thread.start()

    # Step 4 – wake-word listener (background thread)
    ww_thread = threading.Thread(target=_run_wake_word,
                                 args=(gui_ref, stop_event), daemon=True)
    ww_thread.start()

    # Step 5 – GUI on main thread (blocking)
    import customtkinter as ctk
    from frontend.gui import AssistantGUI

    root = ctk.CTk()
    app  = AssistantGUI(root, assistant=shared_assistant)
    gui_ref["gui"] = app

    print("🚀 GUI launched. Close the window to minimise to tray.")
    root.mainloop()

    # Cleanup after window is destroyed
    stop_event.set()
    print("👋 Viru shut down cleanly.")

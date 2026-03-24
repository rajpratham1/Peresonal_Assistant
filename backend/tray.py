from __future__ import annotations
import threading

import pystray
from PIL import Image, ImageDraw

from backend.main import Assistant

# Store global reference to assistant engine
assistant_engine: Assistant | None = None
assistant_thread: threading.Thread | None = None

def create_system_tray_icon() -> Image.Image:
    """Generate a clean dark-mode icon for the system tray dynamically."""
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    dc = ImageDraw.Draw(image)
    # Draw a futuristic blue core circle representing the AI
    dc.ellipse((16, 16, 48, 48), fill=(43, 130, 201))
    return image

def start_assistant(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    global assistant_engine, assistant_thread
    if assistant_engine is None:
        def run():
            global assistant_engine
            assistant_engine = Assistant()
            assistant_engine.run()
        assistant_thread = threading.Thread(target=run, daemon=True)
        assistant_thread.start()

def stop_assistant(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    global assistant_engine
    if assistant_engine is not None:
        assistant_engine.close()
        assistant_engine = None

def exit_action(icon: pystray.Icon, item: pystray.MenuItem) -> None:
    stop_assistant(icon, item)
    icon.stop()

def main() -> None:
    """Initialize Ghost Mode: System tray icon with zero GUI overhead."""
    image = create_system_tray_icon()
    menu = pystray.Menu(
        pystray.MenuItem("Start Listening", start_assistant),
        pystray.MenuItem("Stop Listening", stop_assistant),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit Ghost Mode", exit_action)
    )
    icon = pystray.Icon("Viru Assistant Context", image, "Viru Assistant", menu)
    
    # Auto-start engine when ghost mode runs
    start_assistant(icon, None)
    
    # Blocks forever handling the system tray context
    icon.run()

if __name__ == "__main__":
    main()

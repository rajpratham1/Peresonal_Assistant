from __future__ import annotations

import time
import webbrowser


def send_desktop_message(target: str, message: str) -> None:
    try:
        import pyautogui
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pyautogui is not installed.") from exc

    if not target:
        raise ValueError("A messaging target is required.")
    if not message:
        raise ValueError("A message is required.")

    webbrowser.open("https://web.whatsapp.com")
    time.sleep(8)
    pyautogui.write(target, interval=0.04)
    pyautogui.press("enter")
    time.sleep(2)
    pyautogui.write(message, interval=0.03)
    pyautogui.press("enter")

from __future__ import annotations

import os
import subprocess


def shutdown() -> None:
    subprocess.run(["shutdown", "/s", "/t", "5"], check=False)


def restart() -> None:
    subprocess.run(["shutdown", "/r", "/t", "5"], check=False)


def lock_workstation() -> None:
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=False)


def sleep_system() -> None:
    subprocess.run(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        check=False,
    )


def take_screenshot(path: str) -> None:
    try:
        import pyautogui
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pyautogui is not installed.") from exc

    image = pyautogui.screenshot()
    image.save(path)


def set_volume(level: str) -> None:
    if level not in {"up", "down", "mute"}:
        raise ValueError("level must be up, down, or mute")
    script = {
        "up": "(new-object -com wscript.shell).SendKeys([char]175)",
        "down": "(new-object -com wscript.shell).SendKeys([char]174)",
        "mute": "(new-object -com wscript.shell).SendKeys([char]173)",
    }[level]
    subprocess.run(["powershell.exe", "-Command", script], check=False)


def open_folder(path: str) -> bool:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
        return True
    except OSError:
        return False

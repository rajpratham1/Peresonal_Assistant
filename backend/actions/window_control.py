from __future__ import annotations

import subprocess


def minimize_current_window() -> None:
    subprocess.run(
        [
            "powershell.exe",
            "-Command",
            '(new-object -com wscript.shell).SendKeys("% {SPACE}n")',
        ],
        check=False,
    )


def switch_window() -> None:
    subprocess.run(
        [
            "powershell.exe",
            "-Command",
            '(new-object -com wscript.shell).SendKeys("%{TAB}")',
        ],
        check=False,
    )

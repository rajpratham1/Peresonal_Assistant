from __future__ import annotations

import os
import subprocess
import webbrowser
from urllib.parse import quote_plus

from backend.config import APP_ALIASES, WEBSITE_ALIASES


def open_app(name: str) -> bool:
    target = APP_ALIASES.get(name.lower(), name)
    try:
        subprocess.Popen([target])
        return True
    except OSError:
        return False


def open_website(name: str) -> bool:
    target = WEBSITE_ALIASES.get(name.lower(), name)
    if not target.startswith(("http://", "https://")):
        target = f"https://{target}"
    return webbrowser.open(target)


def open_youtube_search(query: str) -> bool:
    if not query:
        return webbrowser.open(WEBSITE_ALIASES["youtube"])
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    return webbrowser.open(url)


def open_path(path: str) -> bool:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
        return True
    except OSError:
        return False

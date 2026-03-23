from __future__ import annotations

import webbrowser
from urllib.parse import quote_plus


def start_call(target: str) -> bool:
    cleaned = target.strip()
    if not cleaned:
        return False
    return webbrowser.open(f"tel:{quote_plus(cleaned)}")

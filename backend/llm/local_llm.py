from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from backend.config import LOCAL_LLM_ENABLED, LOCAL_LLM_MODEL, LOCAL_LLM_TIMEOUT, LOCAL_LLM_URL


@dataclass
class LLMResult:
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class LocalLLMClient:
    def __init__(self) -> None:
        self.enabled = LOCAL_LLM_ENABLED
        self.url = LOCAL_LLM_URL
        self.model = LOCAL_LLM_MODEL
        self.timeout = LOCAL_LLM_TIMEOUT

    def chat_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        if not self.enabled:
            return LLMResult(ok=False, error="Local LLM is disabled.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        request = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            return LLMResult(ok=False, error=str(exc))
        except Exception as exc:  # pragma: no cover
            return LLMResult(ok=False, error=str(exc))

        try:
            content = body["choices"][0]["message"]["content"]
            data = json.loads(content)
            return LLMResult(ok=True, data=data)
        except Exception as exc:  # pragma: no cover
            return LLMResult(ok=False, error=f"Invalid LLM response: {exc}")

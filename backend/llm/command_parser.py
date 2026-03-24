from __future__ import annotations

from typing import Any

from backend.llm.local_llm import LocalLLMClient


SYSTEM_PROMPT = """You are an offline desktop voice assistant command parser.
Convert the user's command into one JSON object only.
Do not explain anything.

Return this schema:
{
  "mode": "command" | "chat" | "unknown",
  "reply": "short assistant reply if mode is chat, else empty string",
  "action": "greeting|help|open_app|open_website|play_youtube|send_email|send_message|schedule_message|set_alarm|call|shutdown|restart|lock|sleep|time|create_note|search_file|save_contact|screenshot|volume_up|volume_down|volume_mute|open_folder|switch_window|minimize_window|python_automation|web_search|stop|unknown",
  "target": "string",
  "message": "string",
  "subject": "string",
  "query": "string",
  "time": "HH:MM 24-hour or empty",
  "note": "string",
  "code": "string (pure python code using pyautogui if action is python_automation)"
}

Rules:
- If the user wants YouTube content, use action play_youtube and put the song/video name in query.
- If the user asks you to take complete control, type into an app, move the mouse, simulate keystrokes, or do a complex OS task, use action python_automation and WRITE python code using pyautogui in the "code" param!.
- ALWAYS use `time.sleep(1)` between GUI actions if you write python automation code.
- If the user asks for a real-time fact, news, weather, or information you don't know, use action "web_search" and set the search string in the "query" param.
- You can use `from backend.actions.vision import find_text_coordinates` to find the (x,y) of a button/text on screen. Example: `coords = find_text_coordinates("Submit"); if coords: pyautogui.click(coords)`
- Use `from backend.actions.window_awareness import get_active_window_info` to get context.
- If the user says only the app/site name like 'edge' or 'gmail', infer the matching action.
- If the user wants to save a person, use action save_contact.
- If the user asks for volume, screenshot, folder open, or window switch, use the matching action.
- If the user is chatting casually, use mode chat and provide a short English reply.
- If no safe action is clear, use action unknown.
- Never invent email addresses, contact numbers, or times.
- Keep reply short.
"""


class LLMCommandParser:
    def __init__(self) -> None:
        self.client = LocalLLMClient()

    def parse(self, text: str) -> dict[str, Any] | None:
        context = ""
        try:
            from backend.database.vector_db import query_memory
            context = query_memory(text)
        except Exception:
            pass

        modified_prompt = SYSTEM_PROMPT
        if context:
            modified_prompt += f"\n\nHere is relevant context from the user's Infinite Memory desktop files so you can accurately answer or handle their query:\n{context}\n"

        result = self.client.chat_json(modified_prompt, text)
        if not result.ok or not result.data:
            return None
        return result.data

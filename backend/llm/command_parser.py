from __future__ import annotations

from typing import Any

from backend.llm.local_llm import LocalLLMClient


SYSTEM_PROMPT = """You are an offline desktop voice assistant command parser.
Convert the user's command into a compact JSON object. Do not explain anything.
ONLY include keys that have non-empty values. Omit any keys with empty strings or null values.

Available Keys:
- "mode": "command" | "chat" | "unknown" (Required)
- "reply": "short assistant reply (Only if mode is chat)"
- "action": "greeting|help|open_app|open_website|play_youtube|send_email|send_message|schedule_message|set_alarm|call|shutdown|restart|lock|sleep|time|create_note|search_file|save_contact|screenshot|volume_up|volume_down|volume_mute|open_folder|switch_window|minimize_window|python_automation|web_search|stop|unknown" (Only if mode is command)
- "target": "string target for the action"
- "message": "string message body"
- "subject": "string email subject"
- "query": "string search query"
- "time": "HH:MM 24-hour format"
- "note": "string note content"
- "code": "string Python script using pyautogui (Only if action is python_automation)"

Rules:
- If mode is chat, include ONLY "mode" and "reply".
- If mode is command, include "mode", "action", and ONLY the keys required for that action.
- If the user wants YouTube content, use action play_youtube and query.
- If the user asks you to take complete control, type into an app, move the mouse, simulate keystrokes, or do a complex OS task, use action python_automation and WRITE python code using pyautogui in the "code" param!.
- ALWAYS use `time.sleep(1)` between GUI actions if you write python automation code.
- If the user asks for a real-time fact, news, weather, or information you don't know, use action "web_search" and set the search string in the "query" param.
- You can use `from backend.actions.vision import find_text_coordinates` to find the (x,y) of a button/text on screen. Example: `coords = find_text_coordinates("Submit"); if coords: pyautogui.click(coords)`
- Use `from backend.actions.window_awareness import get_active_window_info` to get context.
- If the user says only the app/site name like 'edge' or 'gmail', infer the matching action.
- If the user wants to save a person, use action save_contact.
- If the user wants to set an alarm or schedule a message/reminder, use the matching action.
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
            # Extract only the actual query for memory lookup
            query = text
            if "USER_INPUT:" in text:
                query = text.split("USER_INPUT:")[-1].strip()
            context = query_memory(query)
        except Exception:
            pass

        # Relocate memory context to the user message prompt
        # This keeps the SYSTEM_PROMPT 100% static, enabling 100% KV cache hit rate.
        user_prompt = text
        if context:
            user_prompt = f"RELEVANT MEMORY DATA:\n{context}\n\n{text}"

        result = self.client.chat_json(SYSTEM_PROMPT, user_prompt)
        if not result.ok or not result.data:
            return None
        return result.data

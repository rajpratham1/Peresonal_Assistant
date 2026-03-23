from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import threading
import time

from backend.actions.app_control import open_app, open_path, open_website, open_youtube_search
from backend.actions.calling import start_call
from backend.actions.email import send_email
from backend.actions.messaging import send_desktop_message
from backend.actions.system_control import (
    lock_workstation,
    open_folder,
    restart,
    set_volume,
    shutdown,
    sleep_system,
    take_screenshot,
)
from backend.actions.window_control import minimize_current_window, switch_window
from backend.config import APP_ALIASES, PROJECT_ROOT, WEBSITE_ALIASES
from backend.database.db import (
    create_reminder,
    get_contact,
    get_due_reminders,
    init,
    log_command,
    mark_reminder_done,
    save_note,
    upsert_contact,
)
from backend.llm.command_parser import LLMCommandParser
from backend.ml.intent_model import IntentModel
from backend.ml.train import train
from backend.speech.speech_to_text import listen
from backend.speech.text_to_speech import speak
from backend.utils.parser import (
    extract_alarm_message,
    extract_call_target,
    extract_contact_fields,
    extract_email_fields,
    extract_message_fields,
    extract_note_content,
    extract_open_target,
    extract_scheduled_message,
    extract_youtube_query,
    find_file,
    fuzzy_normalize_target,
    normalize_text,
    parse_time_expression,
    split_compound_commands,
)


@dataclass
class DebugInfo:
    heard_text: str = ""
    llm_payload: dict | None = None
    route: str = ""
    intent: str = ""
    action_text: str = ""
    error: str = ""


@dataclass
class AssistantResponse:
    text: str
    should_exit: bool = False
    debug: DebugInfo = field(default_factory=DebugInfo)


@dataclass
class PendingConfirmation:
    command: str
    intent: str
    created_at: str


class Assistant:
    def __init__(self) -> None:
        init()
        self._ensure_model()
        self.intent_model = IntentModel()
        self.llm_parser = LLMCommandParser()
        self.pending_confirmation: PendingConfirmation | None = None
        self._scheduler_stop = threading.Event()
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    @staticmethod
    def _ensure_model() -> None:
        from backend.config import MODEL_PATH, VECTORIZER_PATH

        if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
            train()

    def predict_intent(self, text: str) -> str:
        normalized = normalize_text(text)
        exact_intents = {
            "hello": "greeting",
            "hi": "greeting",
            "hey": "greeting",
            "good morning": "greeting",
            "good evening": "greeting",
            "help": "help",
            "what can you do": "help",
            "commands": "help",
            "shutdown": "shutdown",
            "shutdown system": "shutdown",
            "restart": "restart",
            "restart system": "restart",
            "lock pc": "lock",
            "lock computer": "lock",
            "sleep pc": "sleep",
            "sleep computer": "sleep",
            "exit": "stop",
            "quit": "stop",
            "stop listening": "stop",
            "yes": "confirm_yes",
            "confirm": "confirm_yes",
            "do it": "confirm_yes",
            "cancel": "confirm_no",
            "no": "confirm_no",
        }
        if normalized in exact_intents:
            return exact_intents[normalized]
        if normalized.startswith("set alarm for ") or normalized.startswith("alarm for "):
            return "set_alarm"
        if normalized.startswith("save contact "):
            return "save_contact"
        if " message " in normalized and " saying " in normalized and parse_time_expression(normalized):
            return "schedule_message"
        if normalized.startswith("message "):
            return "send_message"
        if normalized.startswith("call "):
            return "call"
        if normalized.startswith("take screenshot"):
            return "screenshot"
        if normalized in {"volume up", "increase volume"}:
            return "volume_up"
        if normalized in {"volume down", "decrease volume"}:
            return "volume_down"
        if normalized in {"mute", "mute volume"}:
            return "volume_mute"
        if normalized in {"switch window", "next window"}:
            return "switch_window"
        if normalized in {"minimize window", "minimise window"}:
            return "minimize_window"
        if normalized.startswith("open folder "):
            return "open_folder"
        if "youtube" in normalized and "play " in normalized:
            return "play_youtube"
        if fuzzy_normalize_target(normalized) in APP_ALIASES:
            return "open_app"
        if fuzzy_normalize_target(normalized) in WEBSITE_ALIASES:
            return "open_website"
        return self.intent_model.predict(normalized)

    def handle_text(self, text: str, voice_response: bool = True) -> AssistantResponse:
        normalized = normalize_text(text)
        if not normalized:
            response = AssistantResponse("I did not hear a command.")
            if voice_response:
                speak(response.text)
            return response

        debug = DebugInfo(heard_text=normalized)
        confirmation_response = self._handle_confirmation(normalized, debug)
        if confirmation_response is not None:
            if voice_response and confirmation_response.text:
                speak(confirmation_response.text)
            return confirmation_response

        commands = split_compound_commands(normalized)
        responses: list[str] = []
        should_exit = False
        last_debug = debug

        for command in commands:
            response = self._handle_single_command(command)
            responses.append(response.text)
            last_debug = response.debug
            if response.should_exit:
                should_exit = True
                break

        final_response = AssistantResponse(
            " Then ".join([text for text in responses if text]),
            should_exit=should_exit,
            debug=last_debug,
        )
        if voice_response and final_response.text:
            speak(final_response.text)
        return final_response

    def _handle_confirmation(self, text: str, debug: DebugInfo) -> AssistantResponse | None:
        if self.pending_confirmation is None:
            return None

        intent = self.predict_intent(text)
        if intent == "confirm_yes":
            pending = self.pending_confirmation
            self.pending_confirmation = None
            debug.route = "confirmation"
            debug.intent = pending.intent
            debug.action_text = pending.command
            result = self._dispatch(pending.intent, pending.command, debug, confirmed=True)
            return result
        if intent == "confirm_no":
            self.pending_confirmation = None
            debug.route = "confirmation"
            debug.intent = "cancel"
            return AssistantResponse("Cancelled.", debug=debug)
        return AssistantResponse(
            "I am waiting for confirmation. Say yes to continue or cancel to stop.",
            debug=debug,
        )

    def _handle_single_command(self, command: str) -> AssistantResponse:
        llm_response = self._handle_llm_command(command)
        if llm_response is not None:
            log_command(command, "llm")
            return llm_response

        debug = DebugInfo(heard_text=command, route="fallback")
        intent = self.predict_intent(command)
        debug.intent = intent
        log_command(command, intent)
        return self._dispatch(intent, command, debug)

    def _handle_llm_command(self, text: str) -> AssistantResponse | None:
        payload = self.llm_parser.parse(text)
        if not payload:
            return None

        debug = DebugInfo(heard_text=text, llm_payload=payload, route="llm")
        mode = str(payload.get("mode", "")).strip().lower()
        action = str(payload.get("action", "")).strip().lower()
        debug.intent = action or mode

        if mode == "chat":
            reply = str(payload.get("reply", "")).strip() or "I am listening."
            return AssistantResponse(reply, debug=debug)
        if not action or action == "unknown":
            return None

        if action == "open_app":
            return self._dispatch("open_app", str(payload.get("target", "")).strip() or text, debug)
        if action == "open_website":
            return self._dispatch("open_website", str(payload.get("target", "")).strip() or text, debug)
        if action == "play_youtube":
            query = str(payload.get("query", "")).strip()
            return self._dispatch("play_youtube", f"play {query} on youtube", debug)
        if action == "create_note":
            return self._dispatch("create_note", str(payload.get("note", "")).strip() or text, debug)
        if action == "save_contact":
            target = str(payload.get("target", "")).strip()
            message = str(payload.get("message", "")).strip()
            subject = str(payload.get("subject", "")).strip()
            command = f"save contact {target}"
            if message:
                command += f" phone {message}"
            if subject:
                command += f" email {subject}"
            return self._dispatch("save_contact", command, debug)
        if action == "search_file":
            query = str(payload.get("query", "")).strip()
            return self._dispatch("search_file", f"search for a file {query}", debug)
        if action == "set_alarm":
            when = str(payload.get("time", "")).strip()
            message = str(payload.get("message", "")).strip()
            return self._dispatch("set_alarm", f"set alarm for {when} {message}".strip(), debug)
        if action == "schedule_message":
            when = str(payload.get("time", "")).strip()
            target = str(payload.get("target", "")).strip()
            message = str(payload.get("message", "")).strip()
            return self._dispatch("schedule_message", f"at {when} message {target} saying {message}", debug)
        if action == "call":
            return self._dispatch("call", f"call {str(payload.get('target', '')).strip()}", debug)
        if action == "send_email":
            target = str(payload.get("target", "")).strip()
            subject = str(payload.get("subject", "")).strip()
            message = str(payload.get("message", "")).strip()
            return self._dispatch("send_email", f"send email to {target} subject {subject} body {message}", debug)
        if action == "send_message":
            target = str(payload.get("target", "")).strip()
            message = str(payload.get("message", "")).strip()
            return self._dispatch("send_message", f"message {target} saying {message}", debug)
        if action == "open_folder":
            return self._dispatch("open_folder", f"open folder {str(payload.get('target', '')).strip()}", debug)
        return self._dispatch(action, text, debug)

    def _dispatch(
        self,
        intent: str,
        text: str,
        debug: DebugInfo | None = None,
        confirmed: bool = False,
    ) -> AssistantResponse:
        debug = debug or DebugInfo(heard_text=text, intent=intent)
        debug.action_text = text
        try:
            if intent == "greeting":
                return AssistantResponse("Hello. I am ready for your command.", debug=debug)

            if intent == "help":
                return AssistantResponse(
                    "You can ask me to open apps, websites, play YouTube, save contacts, message people, set alarms, search files, change volume, take screenshots, or control the system.",
                    debug=debug,
                )

            if intent == "save_contact":
                name, phone, email, whatsapp_name = extract_contact_fields(text)
                if not name:
                    return AssistantResponse(
                        "Try saying: save contact alice phone 9876543210 email alice@example.com whatsapp Alice.",
                        debug=debug,
                    )
                upsert_contact(name, phone=phone, email=email, whatsapp_name=whatsapp_name)
                return AssistantResponse(f"Saved contact {name}", debug=debug)

            if intent == "open_app":
                target = extract_open_target(text)
                if open_app(target):
                    return AssistantResponse(f"Opening {target}", debug=debug)
                return AssistantResponse(f"I could not open the app {target}", debug=debug)

            if intent == "open_website":
                target = extract_open_target(text)
                if open_website(target):
                    return AssistantResponse(f"Opening {target}", debug=debug)
                return AssistantResponse(f"I could not open the website {target}", debug=debug)

            if intent == "play_youtube":
                query = extract_youtube_query(text)
                if open_youtube_search(query or ""):
                    return AssistantResponse(
                        f"Opening YouTube results for {query}" if query else "Opening YouTube",
                        debug=debug,
                    )
                return AssistantResponse("I could not open YouTube", debug=debug)

            if intent == "send_email":
                recipient, subject, body = extract_email_fields(text)
                if recipient is None and "to " in text:
                    maybe_contact = normalize_text(text.split("to ", 1)[1].split(" subject", 1)[0].split(" body", 1)[0].strip())
                    contact = get_contact(maybe_contact)
                    recipient = contact["email"] if contact and contact["email"] else None
                if not recipient:
                    return AssistantResponse("Email address not found. Save a contact with email or include an email address.", debug=debug)
                if self._requires_confirmation(intent) and not confirmed:
                    return self._request_confirmation(intent, text, f"Ready to send email to {recipient}. Say yes to confirm.", debug)
                send_email(recipient, subject, body)
                return AssistantResponse(f"Email sent to {recipient}", debug=debug)

            if intent == "send_message":
                target, message = extract_message_fields(text)
                if not target:
                    return AssistantResponse("Try: message Alice saying hello.", debug=debug)
                target_name = self._resolve_contact_target(target)
                if self._requires_confirmation(intent) and not confirmed:
                    return self._request_confirmation(intent, f"message {target_name} saying {message}", f"Ready to message {target_name}. Say yes to confirm.", debug)
                send_desktop_message(target_name, message)
                return AssistantResponse(f"Message sent to {target_name}", debug=debug)

            if intent == "schedule_message":
                trigger_at, target, message = extract_scheduled_message(text)
                if not trigger_at or not target or not message:
                    return AssistantResponse("Try saying: at 12:30 message Alice saying meeting starts now.", debug=debug)
                target_name = self._resolve_contact_target(target)
                create_reminder(
                    kind="message",
                    target=target_name,
                    message=message,
                    trigger_at=trigger_at.isoformat(timespec="seconds"),
                )
                return AssistantResponse(f"Scheduled your message to {target_name} at {trigger_at.strftime('%H:%M')}", debug=debug)

            if intent == "set_alarm":
                trigger_at = parse_time_expression(text)
                if not trigger_at:
                    return AssistantResponse("Try saying: set alarm for 12:30.", debug=debug)
                create_reminder(
                    kind="alarm",
                    message=extract_alarm_message(text),
                    trigger_at=trigger_at.isoformat(timespec="seconds"),
                )
                return AssistantResponse(f"Alarm set for {trigger_at.strftime('%H:%M')}", debug=debug)

            if intent == "call":
                target = extract_call_target(text)
                if not target:
                    return AssistantResponse("Tell me whom to call.", debug=debug)
                call_target = self._resolve_contact_phone(target)
                if self._requires_confirmation(intent) and not confirmed:
                    return self._request_confirmation(intent, f"call {call_target}", f"Ready to call {call_target}. Say yes to confirm.", debug)
                if start_call(call_target):
                    return AssistantResponse(f"Starting a call to {call_target}", debug=debug)
                return AssistantResponse(f"I could not start a call to {call_target}", debug=debug)

            if intent == "shutdown":
                if not confirmed:
                    return self._request_confirmation(intent, text, "Shut down the PC? Say yes to confirm.", debug)
                shutdown()
                return AssistantResponse("Shutting down the PC", debug=debug)

            if intent == "restart":
                if not confirmed:
                    return self._request_confirmation(intent, text, "Restart the PC? Say yes to confirm.", debug)
                restart()
                return AssistantResponse("Restarting the PC", debug=debug)

            if intent == "lock":
                lock_workstation()
                return AssistantResponse("Locking the PC", debug=debug)

            if intent == "sleep":
                if not confirmed:
                    return self._request_confirmation(intent, text, "Put the PC to sleep? Say yes to confirm.", debug)
                sleep_system()
                return AssistantResponse("Putting the PC to sleep", debug=debug)

            if intent == "time":
                return AssistantResponse(f"The time is {datetime.now().strftime('%I:%M %p')}", debug=debug)

            if intent == "create_note":
                content = extract_note_content(text)
                save_note(content)
                return AssistantResponse("Note saved locally", debug=debug)

            if intent == "search_file":
                query = text.replace("find a file", "").replace("search for a file", "").strip()
                if not query:
                    return AssistantResponse("Tell me which file name to search for.", debug=debug)
                result = find_file(PROJECT_ROOT, query)
                if result and open_path(result):
                    return AssistantResponse(f"Found and opened {query}", debug=debug)
                if result:
                    return AssistantResponse(f"Found file at {result}", debug=debug)
                return AssistantResponse(f"I could not find a file matching {query}", debug=debug)

            if intent == "open_folder":
                folder = text.replace("open folder", "", 1).strip()
                if not folder:
                    return AssistantResponse("Tell me which folder to open.", debug=debug)
                target = Path(folder)
                if target.exists() and target.is_dir() and open_folder(str(target)):
                    return AssistantResponse(f"Opened folder {target}", debug=debug)
                return AssistantResponse(f"I could not open folder {folder}", debug=debug)

            if intent == "screenshot":
                screenshots_dir = PROJECT_ROOT / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                file_path = screenshots_dir / f"screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
                take_screenshot(str(file_path))
                return AssistantResponse(f"Screenshot saved to {file_path}", debug=debug)

            if intent == "volume_up":
                set_volume("up")
                return AssistantResponse("Volume increased", debug=debug)

            if intent == "volume_down":
                set_volume("down")
                return AssistantResponse("Volume decreased", debug=debug)

            if intent == "volume_mute":
                set_volume("mute")
                return AssistantResponse("Volume muted", debug=debug)

            if intent == "switch_window":
                switch_window()
                return AssistantResponse("Switched window", debug=debug)

            if intent == "minimize_window":
                minimize_current_window()
                return AssistantResponse("Minimized the current window", debug=debug)

            if intent == "confirm_yes":
                return AssistantResponse("Nothing is waiting for confirmation.", debug=debug)

            if intent == "confirm_no":
                return AssistantResponse("Nothing is waiting for confirmation.", debug=debug)

            if intent == "stop":
                return AssistantResponse("Stopping assistant", should_exit=True, debug=debug)

            return AssistantResponse("Command not recognized", debug=debug)
        except Exception as exc:  # pragma: no cover
            debug.error = str(exc)
            return AssistantResponse(f"Action failed: {exc}", debug=debug)

    def _request_confirmation(
        self,
        intent: str,
        command: str,
        prompt: str,
        debug: DebugInfo,
    ) -> AssistantResponse:
        self.pending_confirmation = PendingConfirmation(
            command=command,
            intent=intent,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        return AssistantResponse(prompt, debug=debug)

    @staticmethod
    def _requires_confirmation(intent: str) -> bool:
        return intent in {"shutdown", "restart", "sleep", "send_email", "send_message", "call"}

    @staticmethod
    def _resolve_contact_phone(target: str) -> str:
        contact = get_contact(normalize_text(target))
        if contact and contact["phone"]:
            return str(contact["phone"])
        return target

    @staticmethod
    def _resolve_contact_target(target: str) -> str:
        contact = get_contact(normalize_text(target))
        if contact:
            return str(contact["whatsapp_name"] or contact["name"])
        return target

    def run(self) -> None:
        speak("Assistant is ready")
        try:
            while True:
                command = listen()
                response = self.handle_text(command)
                if response.should_exit:
                    break
        finally:
            self.close()

    def close(self) -> None:
        self._scheduler_stop.set()
        if self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=1.5)

    def _scheduler_loop(self) -> None:
        while not self._scheduler_stop.is_set():
            due_reminders = get_due_reminders(datetime.now().isoformat(timespec="seconds"))
            for reminder in due_reminders:
                self._run_reminder(reminder)
                mark_reminder_done(int(reminder["id"]))
            time.sleep(1)

    def _run_reminder(self, reminder) -> None:
        kind = reminder["kind"]
        if kind == "alarm":
            speak(reminder["message"] or "Alarm time reached")
            return
        if kind == "message":
            target = reminder["target"] or ""
            message = reminder["message"] or ""
            try:
                send_desktop_message(target, message)
                speak(f"Scheduled message sent to {target}")
            except Exception:
                speak(f"I could not send the scheduled message to {target}")
            return


def main() -> None:
    assistant = Assistant()
    assistant.run()


if __name__ == "__main__":
    main()

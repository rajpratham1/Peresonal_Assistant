from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import ttk

from backend.main import Assistant, AssistantResponse
from backend.speech.speech_to_text import listen


class AssistantGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Offline Personal Assistant")
        self.root.geometry("920x640")

        self.assistant = Assistant()
        self.voice_enabled = False
        self.voice_thread: threading.Thread | None = None

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        self.command_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.debug_enabled_var = tk.BooleanVar(value=True)

        ttk.Label(frame, text="Command").pack(anchor="w")
        self.entry = ttk.Entry(frame, textvariable=self.command_var)
        self.entry.pack(fill="x", pady=(0, 12))
        self.entry.bind("<Return>", self.run_command)

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", pady=(0, 12))

        ttk.Button(button_row, text="Run", command=self.run_command).pack(side="left")
        ttk.Button(button_row, text="Clear", command=self.clear_output).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Start Voice", command=self.start_voice_mode).pack(side="left", padx=(8, 0))
        ttk.Button(button_row, text="Stop Voice", command=self.stop_voice_mode).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(button_row, text="Show Debug", variable=self.debug_enabled_var).pack(side="right")

        pane = ttk.Panedwindow(frame, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=1)

        ttk.Label(left, text="Assistant Output").pack(anchor="w")
        self.output = tk.Text(left, height=20, wrap="word")
        self.output.pack(fill="both", expand=True)

        ttk.Label(right, text="Debug").pack(anchor="w")
        self.debug_output = tk.Text(right, height=20, wrap="word")
        self.debug_output.pack(fill="both", expand=True)

        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(10, 0))
        ttk.Label(
            frame,
            text=(
                "Examples: open youtube and play aaj ki raat, save contact alice phone 9876543210 whatsapp Alice, "
                "message alice saying hello, set alarm for 12:30, volume up, take screenshot, shutdown."
            ),
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def run_command(self, *_args) -> None:
        command = self.command_var.get().strip()
        if not command:
            self.status_var.set("Enter a command.")
            return

        response = self.assistant.handle_text(command, voice_response=False)
        self._render_response(command, response)
        if response.should_exit:
            self.root.after(500, self.root.destroy)

    def start_voice_mode(self) -> None:
        if self.voice_enabled:
            self.status_var.set("Voice mode is already running.")
            return

        self.voice_enabled = True
        self.status_var.set("Voice mode started. Speak a command.")
        self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
        self.voice_thread.start()

    def stop_voice_mode(self) -> None:
        self.voice_enabled = False
        self.status_var.set("Voice mode will stop after the current listen cycle.")

    def _voice_loop(self) -> None:
        while self.voice_enabled:
            self._set_status("Listening...")
            try:
                command = listen()
            except Exception as exc:
                self.voice_enabled = False
                self._set_status(f"Voice mode failed: {exc}")
                return

            if not self.voice_enabled:
                break
            if not command:
                continue

            response = self.assistant.handle_text(command, voice_response=True)
            self.root.after(0, lambda c=command, r=response: self._render_response(c, r))

            if response.should_exit:
                self.voice_enabled = False
                self.root.after(500, self.root.destroy)
                return

        self._set_status("Voice mode stopped.")

    def _render_response(self, command: str, response: AssistantResponse) -> None:
        self.output.insert("end", f"You: {command}\nAssistant: {response.text}\n\n")
        self.output.see("end")
        self.status_var.set(response.text)

        if self.debug_enabled_var.get():
            debug_payload = {
                "heard_text": response.debug.heard_text,
                "route": response.debug.route,
                "intent": response.debug.intent,
                "action_text": response.debug.action_text,
                "llm_payload": response.debug.llm_payload,
                "error": response.debug.error,
            }
            self.debug_output.insert("end", json.dumps(debug_payload, indent=2) + "\n\n")
            self.debug_output.see("end")

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda value=text: self.status_var.set(value))

    def clear_output(self) -> None:
        self.output.delete("1.0", "end")
        self.debug_output.delete("1.0", "end")
        self.command_var.set("")
        self.status_var.set("Ready")

    def on_close(self) -> None:
        self.voice_enabled = False
        self.assistant.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    AssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

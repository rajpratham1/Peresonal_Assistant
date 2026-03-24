from __future__ import annotations

import json
import threading
import customtkinter as ctk

from backend.main import Assistant, AssistantResponse
from backend.speech.speech_to_text import listen

# Setup global styling for Modern UI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, text: str, is_user: bool, outcome_text: str | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Configure layout to push user messages right, assistant left
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        bubble_color = "#2b5278" if is_user else "#2c2c2e"
        text_color = "white"
        
        content_frame = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=15, border_width=0)
        
        if is_user:
            # User bubble on the right
            content_frame.grid(row=0, column=1, sticky="e", padx=(40, 10), pady=10)
        else:
            # Assistant bubble on the left
            content_frame.grid(row=0, column=0, sticky="w", padx=(10, 40), pady=10)
            
        msg_label = ctk.CTkLabel(
            content_frame, 
            text=text, 
            text_color=text_color, 
            wraplength=600, 
            justify="left" if not is_user else "right",
            font=("Inter", 14)
        )
        msg_label.pack(padx=15, pady=10)
        
        # Display Outcome pill below assistant message if an action was executed
        if outcome_text and not is_user:
            outcome_frame = ctk.CTkFrame(content_frame, fg_color="#1c1c1e", corner_radius=10)
            outcome_frame.pack(padx=10, pady=(0, 10), fill="x", expand=True)
            outcome_label = ctk.CTkLabel(
                outcome_frame,
                text=f"🎯 {outcome_text}",
                text_color="#a8a8b3",
                font=("Inter", 12, "italic"),
                wraplength=580,
                justify="left"
            )
            outcome_label.pack(padx=10, pady=5)


class AssistantGUI:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("Artificial Intelligence Assistant")
        self.root.geometry("800x700")
        self.root.minsize(500, 400)
        
        # Configure root to let chat history expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.assistant = Assistant()
        self.voice_enabled = False
        self.voice_thread: threading.Thread | None = None
        
        # -- Layout --
        # 1. Chat History Area
        self.chat_history = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        # 2. Input Area
        self.input_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        self.language_var = ctk.StringVar(value="English")
        self.lang_selector = ctk.CTkSegmentedButton(
            self.input_frame, 
            values=["English", "Hindi"],
            variable=self.language_var,
            command=self.change_language,
            font=("Inter", 12)
        )
        self.lang_selector.grid(row=0, column=0, padx=(0, 10))
        
        self.command_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(
            self.input_frame, 
            textvariable=self.command_var, 
            placeholder_text="Message assistant...", 
            height=45,
            corner_radius=22,
            font=("Inter", 14),
            border_width=1
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", self.run_command)
        
        self.voice_btn = ctk.CTkButton(
            self.input_frame, 
            text="🎙️ Listen", 
            width=100, 
            height=45, 
            corner_radius=22, 
            font=("Inter", 14, "bold"),
            command=self.toggle_voice
        )
        self.voice_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.send_btn = ctk.CTkButton(
            self.input_frame, 
            text="➤ Send", 
            width=80, 
            height=45, 
            corner_radius=22, 
            command=self.run_command,
            font=("Inter", 14)
        )
        self.send_btn.grid(row=0, column=3)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Introduction Message
        self.add_message("Hello! I am your offline personal assistant. You can text me or click Listen to speak.", is_user=False)

    def add_message(self, text: str, is_user: bool, outcome_text: str | None = None):
        """Append a new chat bubble to the scrollable frame."""
        bubble = ChatBubble(self.chat_history, text=text, is_user=is_user, outcome_text=outcome_text)
        bubble.pack(fill="x", padx=5, pady=2)
        
        # Auto-scroll to the bottom. _parent_canvas is internal but standard practice for fast jumping in CTk.
        self.root.update_idletasks()
        try:
            self.chat_history._parent_canvas.yview_moveto(1.0)
        except AttributeError:
            pass

    def change_language(self, value):
        self.assistant.language = "hi" if value == "Hindi" else "en"
        self.add_message(f"System language switched to {value}", is_user=False)

    def run_command(self, *_args) -> None:
        """Called when the user hits Return or Send button."""
        command = self.command_var.get().strip()
        if not command:
            return
            
        self.command_var.set("")
        self.add_message(command, is_user=True)
        
        # Process asynchronously so the GUI doesn't freeze
        threading.Thread(target=self._process_command, args=(command,), daemon=True).start()

    def _process_command(self, command: str):
        response = self.assistant.handle_text(command, voice_response=False)
        self.root.after(0, lambda r=response: self._render_response(r))

    def toggle_voice(self) -> None:
        """Switch between listening and idle state."""
        if self.voice_enabled:
            # Turning off
            self.voice_enabled = False
            self.voice_btn.configure(text="🎙️ Stopping...", fg_color="#b22222", hover_color="#8b1a1a")
        else:
            # Turning on
            self.voice_enabled = True
            self.voice_btn.configure(text="🔴 Listening", fg_color="#b22222", hover_color="#8b1a1a")
            self.voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
            self.voice_thread.start()

    def _voice_loop(self) -> None:
        while self.voice_enabled:
            lang_code = "hi" if self.language_var.get() == "Hindi" else "en"
            try:
                command = listen(language=lang_code)
            except Exception as exc:
                self.voice_enabled = False
                self.root.after(0, lambda e=exc: self.add_message(f"Voice engine error: {e}", is_user=False))
                break

            if not self.voice_enabled:
                break
                
            if not command:
                continue

            # Add User's spoken transcript
            self.root.after(0, lambda c=command: self.add_message(c, is_user=True))
            
            # Process & Reply
            response = self.assistant.handle_text(command, voice_response=True)
            self.root.after(0, lambda r=response: self._render_response(r))

            if response.should_exit:
                self.voice_enabled = False
                self.root.after(1000, self.root.destroy)
                return

        def _reset_btn():
            self.voice_btn.configure(text="🎙️ Listen", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
        
        self.root.after(0, _reset_btn)

    def _render_response(self, response: AssistantResponse) -> None:
        # Formulate outcome context
        outcome = None
        if response.debug.action_text or response.debug.intent:
            parts = []
            if response.debug.intent:
                parts.append(f"Intent: {response.debug.intent}")
            if response.debug.action_text:
                parts.append(f"Action: {response.debug.action_text}")
            outcome = " | ".join(parts)
            
        self.add_message(response.text, is_user=False, outcome_text=outcome)

        if response.should_exit:
            self.root.after(1000, self.root.destroy)

    def on_close(self) -> None:
        self.voice_enabled = False
        self.assistant.close()
        self.root.destroy()


def main() -> None:
    root = ctk.CTk()
    app = AssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

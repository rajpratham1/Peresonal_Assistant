"""
Viru AI Assistant – Premium Desktop GUI
Fixes applied:
  • Profile image fetched on a background thread (no startup freeze)
  • Typing animation uses root.after() – thread-safe, no Tkinter crashes
  • Closing the window hides to system tray instead of quitting
  • Status bar shows LLM state (online / offline)
  • Improved chat bubble wraplength and padding
"""
from __future__ import annotations

import threading
import time
import webbrowser
from io import BytesIO

import customtkinter as ctk
from PIL import Image

from backend.main import Assistant, AssistantResponse
from backend.speech.speech_to_text import listen

# ── Design Tokens ──────────────────────────────────────────────────────────────
DARK_BG     = "#1e1e2e"
DARKER_BG   = "#181825"
SURFACE     = "#24273a"
ACCENT      = "#cba6f7"   # Catppuccin Mauve
ACCENT2     = "#89dceb"   # Catppuccin Sky
SUCCESS     = "#a6e3a1"   # Catppuccin Green
WARNING     = "#fab387"   # Catppuccin Peach
USER_BUBBLE = "#313244"
AI_BUBBLE   = "#2a2a3e"
TEXT_MAIN   = "#cdd6f4"
TEXT_SUB    = "#7f849c"
FONT_BODY   = ("Outfit", 13)
FONT_BOLD   = ("Outfit", 13, "bold")
FONT_TITLE  = ("Outfit", 22, "bold")
FONT_SMALL  = ("Outfit", 11)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Chat Bubble ────────────────────────────────────────────────────────────────
class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, text: str, is_user: bool, outcome_text: str | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        bubble_color = USER_BUBBLE if is_user else AI_BUBBLE
        side_col     = 1 if is_user else 0
        anchor       = "e" if is_user else "w"
        pad          = (60, 10) if is_user else (10, 60)

        content = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=18,
                               border_width=1,
                               border_color=ACCENT if is_user else "#3b3b5c")
        content.grid(row=0, column=side_col, sticky=anchor, padx=pad, pady=(4, 0))

        # Role label
        role_text = "You" if is_user else "Viru"
        role_color = ACCENT if is_user else ACCENT2
        ctk.CTkLabel(content, text=role_text, text_color=role_color,
                     font=FONT_SMALL).pack(anchor="w", padx=14, pady=(8, 0))

        # Message text
        self.msg_label = ctk.CTkLabel(
            content, text=text, text_color=TEXT_MAIN,
            wraplength=520, justify="left", font=FONT_BODY
        )
        self.msg_label.pack(padx=14, pady=(2, 10))

        # Optional intent badge
        if outcome_text and not is_user:
            badge = ctk.CTkFrame(content, fg_color=DARKER_BG, corner_radius=8)
            badge.pack(padx=10, pady=(0, 8), fill="x")
            ctk.CTkLabel(badge, text=f"🎯 {outcome_text}",
                         text_color=TEXT_SUB, font=FONT_SMALL).pack(padx=10, pady=4)


# ── Main GUI Class ─────────────────────────────────────────────────────────────
class AssistantGUI:
    def __init__(self, root: ctk.CTk, assistant: Assistant | None = None) -> None:
        self.root = root
        self.root.title("Viru — AI Desktop Assistant")
        self.root.geometry("960x760")
        self.root.minsize(760, 540)
        self.root.configure(fg_color=DARK_BG)

        # Accept a shared Assistant instance or create one here
        self.assistant   = assistant or Assistant()
        self.voice_active = False
        self._typing_jobs: list[str] = []   # after() ids so we can cancel

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Boot message (typed in)
        self.add_message("System initialised. How can I help you today?", is_user=False)

        # Status bar – check LLM state after a short delay
        self.root.after(1500, self._refresh_status)

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # Top status bar
        self._status_bar = ctk.CTkFrame(self.root, fg_color=DARKER_BG,
                                        height=28, corner_radius=0)
        self._status_bar.pack(fill="x", side="top")
        self._status_label = ctk.CTkLabel(
            self._status_bar, text="● LLM: checking…", text_color=TEXT_SUB,
            font=FONT_SMALL
        )
        self._status_label.pack(side="left", padx=12, pady=4)
        ctk.CTkLabel(self._status_bar, text="Viru v2.0 Elite",
                     text_color=TEXT_SUB, font=FONT_SMALL).pack(side="right", padx=12)

        # Tabview
        self.tabview = ctk.CTkTabview(
            self.root,
            segmented_button_fg_color=DARKER_BG,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#b48fe0",
            segmented_button_unselected_color=DARKER_BG,
            fg_color=DARK_BG,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.chat_tab    = self.tabview.add("💬  Chat")
        self.settings_tab = self.tabview.add("⚙️  Settings")
        self.dev_tab     = self.tabview.add("👨‍💻  Developer")

        self._build_chat_tab()
        self._build_settings_tab()
        self._build_developer_tab()

    # ── Chat Tab ───────────────────────────────────────────────────────────────
    def _build_chat_tab(self):
        self.chat_tab.grid_rowconfigure(0, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)

        self.chat_history = ctk.CTkScrollableFrame(
            self.chat_tab, fg_color="transparent", scrollbar_button_color=ACCENT
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Input bar
        input_frame = ctk.CTkFrame(self.chat_tab, fg_color=SURFACE,
                                   corner_radius=16, border_width=1,
                                   border_color="#3b3b5c")
        input_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        input_frame.grid_columnconfigure(1, weight=1)

        # Language picker
        self.lang_var = ctk.StringVar(value="English")
        ctk.CTkSegmentedButton(
            input_frame, values=["English", "Hindi"],
            variable=self.lang_var, command=self._change_language,
            selected_color=ACCENT, selected_hover_color="#b48fe0",
            fg_color=DARKER_BG, width=150
        ).grid(row=0, column=0, padx=10, pady=10)

        # Text entry
        self.cmd_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(
            input_frame, textvariable=self.cmd_var,
            placeholder_text="Ask Viru anything…",
            height=44, corner_radius=12, font=FONT_BODY,
            border_color=ACCENT, border_width=1,
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=10)
        self.entry.bind("<Return>", self.run_command)

        # Voice button
        self.voice_btn = ctk.CTkButton(
            input_frame, text="🎙", width=44, height=44, corner_radius=12,
            fg_color=DARKER_BG, hover_color=ACCENT,
            border_color=ACCENT, border_width=1, font=("Outfit", 18),
            command=self.toggle_voice,
        )
        self.voice_btn.grid(row=0, column=2, padx=(0, 8), pady=10)

        # Send button
        ctk.CTkButton(
            input_frame, text="Send ➤", width=90, height=44, corner_radius=12,
            fg_color=ACCENT, text_color=DARKER_BG,
            hover_color="#b48fe0", font=FONT_BOLD,
            command=self.run_command,
        ).grid(row=0, column=3, padx=(0, 10), pady=10)

    # ── Settings Tab ──────────────────────────────────────────────────────────
    def _build_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.settings_tab, text="System Preferences",
                     font=FONT_TITLE, text_color=ACCENT).pack(pady=(20, 4))
        ctk.CTkLabel(self.settings_tab, text="Customise how Viru looks and behaves.",
                     text_color=TEXT_SUB, font=FONT_SMALL).pack(pady=(0, 20))

        card = ctk.CTkFrame(self.settings_tab, fg_color=SURFACE, corner_radius=16,
                            border_width=1, border_color="#3b3b5c")
        card.pack(padx=40, pady=10, fill="x")
        card.grid_columnconfigure(1, weight=1)

        def row(parent, label, widget_factory, r):
            ctk.CTkLabel(parent, text=label, text_color=TEXT_MAIN,
                         font=FONT_BODY).grid(row=r, column=0, sticky="w", padx=20, pady=12)
            w = widget_factory(parent)
            w.grid(row=r, column=1, sticky="e", padx=20, pady=12)

        row(card, "Appearance Mode", lambda p: ctk.CTkOptionMenu(
            p, values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode,
            fg_color=DARKER_BG, button_color=ACCENT), 0)

        row(card, "Accent Colour", lambda p: ctk.CTkOptionMenu(
            p, values=["blue", "green", "dark-blue"],
            command=ctk.set_default_color_theme,
            fg_color=DARKER_BG, button_color=ACCENT), 1)

        card2 = ctk.CTkFrame(self.settings_tab, fg_color=SURFACE, corner_radius=16,
                             border_width=1, border_color="#3b3b5c")
        card2.pack(padx=40, pady=10, fill="x")
        card2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card2, text="Performance & Memory",
                     font=FONT_BOLD, text_color=ACCENT).grid(row=0, column=0, columnspan=2,
                                                              sticky="w", padx=20, pady=(14, 4))

        def sw_row(parent, label, r):
            ctk.CTkLabel(parent, text=label, text_color=TEXT_MAIN,
                         font=FONT_BODY).grid(row=r, column=0, sticky="w", padx=20, pady=8)
            ctk.CTkSwitch(parent, text="", progress_color=ACCENT,
                          button_color=ACCENT).grid(row=r, column=1, sticky="e", padx=20)

        sw_row(card2, "Enable Ghost Mode (system tray persistence)", 1)
        sw_row(card2, "Auto-Sync Memory on Startup", 2)
        sw_row(card2, "Voice Response (TTS)", 3)

    # ── Developer Tab ─────────────────────────────────────────────────────────
    def _build_developer_tab(self):
        self.dev_tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.dev_tab, text="Developer Profile",
                     font=FONT_TITLE, text_color=ACCENT).pack(pady=(20, 4))
        ctk.CTkLabel(self.dev_tab, text="The mind behind Viru.",
                     text_color=TEXT_SUB, font=FONT_SMALL).pack(pady=(0, 16))

        card = ctk.CTkFrame(self.dev_tab, fg_color=SURFACE, corner_radius=20,
                            border_width=1, border_color="#3b3b5c")
        card.pack(padx=60, pady=10, fill="both", expand=True)

        # Placeholder avatar shown immediately; real photo loaded async
        self._avatar_label = ctk.CTkLabel(card, text="👤", font=("Outfit", 80))
        self._avatar_label.pack(pady=(28, 8))

        ctk.CTkLabel(card, text="Pratham Kumar",
                     font=("Outfit", 22, "bold"), text_color=TEXT_MAIN).pack()
        ctk.CTkLabel(card, text="@rajpratham1",
                     font=("Outfit", 15), text_color=ACCENT).pack(pady=(2, 0))

        bio = (
            "B.Tech CSE Student  •  Web Developer  •  AI Builder\n"
            "Building autonomous systems, one line at a time."
        )
        ctk.CTkLabel(card, text=bio, font=FONT_SMALL, text_color=TEXT_SUB,
                     justify="center").pack(pady=16)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=(0, 24))

        ctk.CTkButton(
            btn_frame, text="🐙  GitHub Profile", fg_color=ACCENT,
            text_color=DARKER_BG, hover_color="#b48fe0", font=FONT_BOLD,
            corner_radius=12, width=180, height=40,
            command=lambda: webbrowser.open("https://github.com/rajpratham1")
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="📁  Repository", fg_color=DARKER_BG,
            text_color=ACCENT, hover_color=SURFACE, font=FONT_BOLD,
            corner_radius=12, width=150, height=40,
            border_width=1, border_color=ACCENT,
            command=lambda: webbrowser.open("https://github.com/rajpratham1/Peresonal_Assistant")
        ).pack(side="left", padx=8)

        # Load photo in background so the GUI doesn't freeze
        threading.Thread(target=self._load_profile_photo, args=(card,), daemon=True).start()

    def _load_profile_photo(self, card: ctk.CTkFrame):
        try:
            import requests
            resp = requests.get("https://github.com/rajpratham1.png", timeout=6)
            img  = Image.open(BytesIO(resp.content)).convert("RGBA")
            ctk_img = ctk.CTkImage(img, size=(110, 110))
            # Update the label from the main thread
            self.root.after(0, lambda: self._avatar_label.configure(image=ctk_img, text=""))
            self._profile_img_ref = ctk_img  # keep reference
        except Exception:
            pass   # placeholder emoji stays

    # ── Status Bar ────────────────────────────────────────────────────────────
    def _refresh_status(self):
        """Ping the local LLM server and update the status bar colour."""
        import socket
        alive = socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex(('127.0.0.1', 8080)) == 0
        if alive:
            self._status_label.configure(
                text="● LLM: Online  (Qwen 2.5 3B on :8080)", text_color=SUCCESS)
        else:
            self._status_label.configure(
                text="● LLM: Offline  (start llama-server.exe or run run.bat)",
                text_color=WARNING)
        # Re-check every 15 s
        self.root.after(15_000, self._refresh_status)

    # ── Message Handling ──────────────────────────────────────────────────────
    def add_message(self, text: str, is_user: bool, outcome_text: str | None = None):
        bubble = ChatBubble(self.chat_history, text="", is_user=is_user,
                            outcome_text=outcome_text)
        bubble.pack(fill="x", padx=6, pady=2)

        if is_user:
            bubble.msg_label.configure(text=text)
        else:
            self._animate_typing(bubble.msg_label, text)

        self._scroll_to_bottom()

    def _animate_typing(self, label: ctk.CTkLabel, full_text: str, idx: int = 0):
        """Thread-safe character-by-character typing using root.after()."""
        if idx <= len(full_text):
            label.configure(text=full_text[:idx])
            job = self.root.after(8, lambda: self._animate_typing(label, full_text, idx + 1))
            self._typing_jobs.append(job)
        else:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self.root.update_idletasks()
        try:
            self.chat_history._parent_canvas.yview_moveto(1.0)
        except AttributeError:
            pass

    # ── Command Processing ────────────────────────────────────────────────────
    def run_command(self, *_):
        cmd = self.cmd_var.get().strip()
        if not cmd:
            return
        self.cmd_var.set("")
        self.add_message(cmd, is_user=True)
        threading.Thread(target=self._process, args=(cmd,), daemon=True).start()

    def _process(self, cmd: str):
        resp = self.assistant.handle_text(cmd, voice_response=False)
        self.root.after(0, lambda r=resp: self._render_response(r))

    def _render_response(self, resp: AssistantResponse):
        badge = f"Intent: {resp.debug.intent}" if resp.debug.intent else None
        self.add_message(resp.text, is_user=False, outcome_text=badge)
        if resp.should_exit:
            self.root.after(1200, self.on_close)

    # ── Voice ─────────────────────────────────────────────────────────────────
    def toggle_voice(self):
        if self.voice_active:
            self.voice_active = False
            self.voice_btn.configure(
                text="🎙", fg_color=DARKER_BG, border_color=ACCENT)
        else:
            self.voice_active = True
            self._pulse_voice_btn()
            threading.Thread(target=self._voice_loop, daemon=True).start()

    def _pulse_voice_btn(self, toggle: bool = True):
        if not self.voice_active:
            self.voice_btn.configure(text="🎙", fg_color=DARKER_BG)
            return
        color = "#f28fad" if toggle else ACCENT
        self.voice_btn.configure(fg_color=color, text="🔴")
        self.root.after(700, lambda: self._pulse_voice_btn(not toggle))

    def _voice_loop(self):
        lang = "hi" if self.lang_var.get() == "Hindi" else "en"
        while self.voice_active:
            try:
                cmd = listen(language=lang)
                if not self.voice_active:
                    break
                if cmd:
                    self.root.after(0, lambda c=cmd: self.add_message(c, is_user=True))
                    resp = self.assistant.handle_text(cmd, voice_response=True)
                    self.root.after(0, lambda r=resp: self._render_response(r))
            except Exception:
                break
        self.root.after(0, lambda: self.voice_btn.configure(
            text="🎙", fg_color=DARKER_BG, border_color=ACCENT))
        self.voice_active = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def _change_language(self, val: str):
        self.assistant.language = "hi" if val == "Hindi" else "en"

    def on_close(self):
        """Hide to system tray; don't destroy the window."""
        self.voice_active = False
        self.root.withdraw()

    def show(self):
        """Restore the window from tray."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()


# ── Standalone entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    root = ctk.CTk()
    app  = AssistantGUI(root)
    root.mainloop()

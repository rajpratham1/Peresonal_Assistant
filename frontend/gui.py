import json
import threading
import time
import requests
from io import BytesIO
from PIL import Image
import customtkinter as ctk

from backend.main import Assistant, AssistantResponse
from backend.speech.speech_to_text import listen

# Modern Aesthetic Constants
DARK_BG = "#1e1e2e"
DARKER_BG = "#181825"
ACCENT_COLOR = "#cba6f7" # Mauve
USER_BUBBLE = "#313244"
AI_BUBBLE = "#45475a"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, text: str, is_user: bool, outcome_text: str | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        bubble_color = USER_BUBBLE if is_user else AI_BUBBLE
        content_frame = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=15)
        
        if is_user:
            content_frame.grid(row=0, column=1, sticky="e", padx=(40, 10), pady=10)
        else:
            content_frame.grid(row=0, column=0, sticky="w", padx=(10, 40), pady=10)
            
        self.msg_label = ctk.CTkLabel(
            content_frame, 
            text=text, 
            text_color="white", 
            wraplength=550, 
            justify="left",
            font=("Outfit", 14)
        )
        self.msg_label.pack(padx=15, pady=10)
        
        if outcome_text and not is_user:
            outcome_frame = ctk.CTkFrame(content_frame, fg_color=DARKER_BG, corner_radius=10)
            outcome_frame.pack(padx=10, pady=(0, 10), fill="x")
            ctk.CTkLabel(outcome_frame, text=f"🎯 {outcome_text}", text_color="#bac2de", font=("Outfit", 12, "italic")).pack(padx=10, pady=5)

class AssistantGUI:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("Artificial Intelligence Assistant | Viru")
        self.root.geometry("900x750")
        self.root.configure(fg_color=DARK_BG)
        
        self.assistant = Assistant()
        self.voice_enabled = False
        self.pulsing = False
        
        # --- UI TABS ---
        self.tabview = ctk.CTkTabview(self.root, segmented_button_fg_color=DARKER_BG, segmented_button_selected_color=ACCENT_COLOR)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.chat_tab = self.tabview.add("Assistant")
        self.settings_tab = self.tabview.add("Settings")
        self.dev_tab = self.tabview.add("Developer")
        
        self._setup_chat_tab()
        self._setup_settings_tab()
        self._setup_developer_tab()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.add_message("System initiated. I am ready for your command.", is_user=False)

    def _setup_chat_tab(self):
        self.chat_tab.grid_rowconfigure(0, weight=1)
        self.chat_tab.grid_columnconfigure(0, weight=1)
        
        self.chat_history = ctk.CTkScrollableFrame(self.chat_tab, fg_color="transparent")
        self.chat_history.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.input_frame = ctk.CTkFrame(self.chat_tab, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(1, weight=1)
        
        self.language_var = ctk.StringVar(value="English")
        self.lang_selector = ctk.CTkSegmentedButton(self.input_frame, values=["English", "Hindi"], variable=self.language_var, command=self.change_language)
        self.lang_selector.grid(row=0, column=0, padx=(0, 10))
        
        self.command_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(self.input_frame, textvariable=self.command_var, placeholder_text="Ask me anything...", height=50, corner_radius=25, font=("Outfit", 14))
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", self.run_command)
        
        self.voice_btn = ctk.CTkButton(self.input_frame, text="🎙️ Listen", width=110, height=50, corner_radius=25, font=("Outfit", 14, "bold"), command=self.toggle_voice)
        self.voice_btn.grid(row=0, column=2, padx=(0, 10))
        
        self.send_btn = ctk.CTkButton(self.input_frame, text="➤", width=60, height=50, corner_radius=25, command=self.run_command, font=("Outfit", 18))
        self.send_btn.grid(row=0, column=3)

    def _setup_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.settings_tab, text="System Preferences", font=("Outfit", 24, "bold"), text_color=ACCENT_COLOR).pack(pady=20)
        
        # Appearance Mode
        ctk.CTkLabel(self.settings_tab, text="Appearance Mode", font=("Outfit", 14)).pack(pady=(10, 5))
        self.appearance_opt = ctk.CTkOptionMenu(self.settings_tab, values=["Dark", "Light", "System"], command=ctk.set_appearance_mode)
        self.appearance_opt.pack(pady=5)
        
        # Color Theme
        ctk.CTkLabel(self.settings_tab, text="Accent Color Theme", font=("Outfit", 14)).pack(pady=(20, 5))
        self.theme_opt = ctk.CTkOptionMenu(self.settings_tab, values=["blue", "green", "dark-blue"], command=ctk.set_default_color_theme)
        self.theme_opt.pack(pady=5)
        
        ctk.CTkLabel(self.settings_tab, text="Performance & Memory", font=("Outfit", 14, "bold"), text_color=ACCENT_COLOR).pack(pady=(30, 10))
        ctk.CTkSwitch(self.settings_tab, text="Enable Ghost Mode Persistence").pack(pady=5)
        ctk.CTkSwitch(self.settings_tab, text="Auto-Sync Memory on Startup").pack(pady=5)

    def _setup_developer_tab(self):
        self.dev_tab.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(self.dev_tab, text="Developer Profile", font=("Outfit", 24, "bold"), text_color=ACCENT_COLOR)
        title.pack(pady=20)
        
        card = ctk.CTkFrame(self.dev_tab, fg_color=DARKER_BG, corner_radius=20, border_width=1, border_color=AI_BUBBLE)
        card.pack(padx=50, pady=20, fill="both", expand=True)
        
        # Profile Photo Fetcher
        try:
            response = requests.get("https://github.com/rajpratham1.png")
            img_data = BytesIO(response.content)
            pil_image = Image.open(img_data)
            self.profile_img = ctk.CTkImage(pil_image, size=(120, 120))
            img_label = ctk.CTkLabel(card, image=self.profile_img, text="")
            img_label.pack(pady=(20, 10))
        except Exception:
            ctk.CTkLabel(card, text="👤", font=("Outfit", 80)).pack(pady=20)
            
        ctk.CTkLabel(card, text="Pratham Kumar", font=("Outfit", 22, "bold")).pack()
        ctk.CTkLabel(card, text="@rajpratham1", font=("Outfit", 16), text_color=ACCENT_COLOR).pack()
        
        bio = "B.Tech CSE student, web developer, and active builder.\nLinked to the public GitHub profile."
        ctk.CTkLabel(card, text=bio, font=("Outfit", 14), justify="center", wraplength=400).pack(pady=20)
        
        import webbrowser
        btn = ctk.CTkButton(card, text="Visit GitHub Profile", fg_color=ACCENT_COLOR, text_color=DARKER_BG, hover_color="white", command=lambda: webbrowser.open("https://github.com/rajpratham1"))
        btn.pack(pady=20)

    def add_message(self, text: str, is_user: bool, outcome_text: str | None = None):
        bubble = ChatBubble(self.chat_history, text="", is_user=is_user, outcome_text=outcome_text)
        bubble.pack(fill="x", padx=5, pady=2)
        
        if is_user:
            bubble.msg_label.configure(text=text)
        else:
            threading.Thread(target=self._type_text, args=(bubble.msg_label, text), daemon=True).start()
            
        self.root.update_idletasks()
        try: self.chat_history._parent_canvas.yview_moveto(1.0)
        except AttributeError: pass

    def _type_text(self, label, full_text):
        displayed = ""
        for char in full_text:
            displayed += char
            label.configure(text=displayed)
            time.sleep(0.01)

    def toggle_voice(self):
        if self.voice_enabled:
            self.voice_enabled = False
            self.pulsing = False
            self.voice_btn.configure(text="🎙️ Listen", fg_color=["#3a7ebf", "#1f538d"])
        else:
            self.voice_enabled = True
            self.pulsing = True
            self._start_pulse()
            threading.Thread(target=self._voice_loop, daemon=True).start()

    def _start_pulse(self):
        if not self.pulsing: return
        colors = ["#f28fad", ACCENT_COLOR]
        def animate(idx=0):
            if not self.pulsing: return
            self.voice_btn.configure(fg_color=colors[idx % 2])
            self.root.after(800, lambda: animate(idx + 1))
        animate()

    def _voice_loop(self):
        while self.voice_enabled:
            lang = "hi" if self.language_var.get() == "Hindi" else "en"
            try:
                cmd = listen(language=lang)
                if not self.voice_enabled: break
                if cmd:
                    self.root.after(0, lambda c=cmd: self.add_message(c, is_user=True))
                    resp = self.assistant.handle_text(cmd, voice_response=True)
                    self.root.after(0, lambda r=resp: self._render_response(r))
            except Exception: break
        self.root.after(0, lambda: self.voice_btn.configure(text="🎙️ Listen"))

    def run_command(self, *_):
        command = self.command_var.get().strip()
        if not command: return
        self.command_var.set("")
        self.add_message(command, is_user=True)
        threading.Thread(target=self._process_command, args=(command,), daemon=True).start()

    def _process_command(self, command: str):
        response = self.assistant.handle_text(command, voice_response=False)
        self.root.after(0, lambda r=response: self._render_response(r))

    def _render_response(self, response: AssistantResponse):
        outcome = f"Intent: {response.debug.intent}" if response.debug.intent else None
        self.add_message(response.text, is_user=False, outcome_text=outcome)
        if response.should_exit: self.root.after(1000, self.root.destroy)

    def change_language(self, val): self.assistant.language = "hi" if val == "Hindi" else "en"
    def on_close(self):
        self.voice_enabled = False
        self.assistant.close()
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = AssistantGUI(root)
    root.mainloop()

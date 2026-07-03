"""Dark, minimal settings window. Closing it hides it — app keeps running."""
import tkinter as tk

from . import config
from .recorder import Recorder

BG = "#111113"
CARD = "#1b1b1f"
FG = "#f2f2f2"
MUTED = "#9a9aa2"
ACCENT = "#ffffff"
FONT = ("Segoe UI", 11)
FONT_S = ("Segoe UI", 9)


class SettingsWindow:
    def __init__(self, root: tk.Tk, cfg: dict, on_change, learn_key):
        """on_change(cfg) called after any edit; learn_key(cb) arms key capture."""
        self.cfg = cfg
        self.on_change = on_change
        self.learn_key = learn_key
        self._picker = None

        self.win = tk.Toplevel(root)
        self.win.title("SpeechTyper")
        self.win.configure(bg=BG)
        self.win.geometry("360x680")
        self.win.resizable(False, True)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        pad = {"padx": 20, "anchor": "w"}
        tk.Label(self.win, text="SpeechTyper", bg=BG, fg=FG,
                 font=("Segoe UI", 15, "bold")).pack(pady=(18, 0), **pad)
        tk.Label(self.win, text="Hold your key, speak, release.",
                 bg=BG, fg=MUTED, font=FONT_S).pack(pady=(0, 10), **pad)

        # --- mode ---
        self._section("Mode")
        self.mode_var = tk.StringVar(value=cfg["mode"])
        row = tk.Frame(self.win, bg=BG)
        row.pack(fill="x", padx=20)
        self._mode_btns = {}
        for key, label in (("normal", "Normal"), ("casual", "casual")):
            b = tk.Label(row, text=label, font=FONT, cursor="hand2",
                         padx=16, pady=6)
            b.pack(side="left", padx=(0, 8))
            b.bind("<Button-1>", lambda e, k=key: self._set_mode(k))
            self._mode_btns[key] = b
        self._paint_modes()
        tk.Label(self.win, text="Normal: punctuation + capitalization."
                 "  casual: all lowercase, none.",
                 bg=BG, fg=MUTED, font=FONT_S, wraplength=320,
                 justify="left").pack(pady=(6, 2), **pad)

        # --- languages (chips + picker) ---
        self._section("Languages")
        self.chips = tk.Frame(self.win, bg=BG)
        self.chips.pack(fill="x", padx=20)
        self._render_langs()
        tk.Label(self.win, text="One language = fastest. Several = auto-detect.",
                 bg=BG, fg=MUTED, font=FONT_S).pack(pady=(4, 2), **pad)

        # --- microphone ---
        self._section("Microphone")
        self._devices = [(None, "System default")] + Recorder.list_devices()
        self.mic_var = tk.StringVar(value=cfg.get("input_device_name",
                                                  "System default"))
        names = [n for _, n in self._devices]
        if self.mic_var.get() not in names:
            self.mic_var.set("System default")
        mic_row = tk.Frame(self.win, bg=BG)
        mic_row.pack(fill="x", padx=20)
        self.mic_menu = tk.OptionMenu(mic_row, self.mic_var, *names,
                                      command=self._mic_changed)
        self.mic_menu.config(bg=CARD, fg=FG, activebackground=CARD,
                             activeforeground=FG, font=FONT_S,
                             highlightthickness=0, bd=0, width=26, anchor="w")
        self.mic_menu["menu"].config(bg=CARD, fg=FG, font=FONT_S)
        self.mic_menu.pack(side="left")
        refresh = tk.Label(mic_row, text="↻", bg=BG, fg=MUTED,
                           font=FONT, cursor="hand2", padx=10)
        refresh.pack(side="left")
        refresh.bind("<Button-1>", self._refresh_mics)

        # --- hotkey ---
        self._section("Push-to-talk key")
        row2 = tk.Frame(self.win, bg=BG)
        row2.pack(fill="x", padx=20)
        self.key_label = tk.Label(row2, text=cfg.get("hotkey_label", cfg["hotkey"]),
                                  bg=CARD, fg=FG, font=FONT, padx=14, pady=6)
        self.key_label.pack(side="left")
        self.learn_btn = tk.Label(row2, text="Learn key", bg=BG, fg=MUTED,
                                  font=FONT, cursor="hand2", padx=12, pady=6)
        self.learn_btn.pack(side="left", padx=8)
        self.learn_btn.bind("<Button-1>", self._learn)

        # --- sound ---
        self._section("Sound")
        self.mute_var = tk.BooleanVar(value=cfg.get("mute_while_listening", False))
        tk.Checkbutton(
            self.win, text="Mute system audio while listening",
            variable=self.mute_var, command=self._mute_changed,
            bg=BG, fg=FG, selectcolor=BG, activebackground=BG,
            activeforeground=FG, font=FONT_S, anchor="w",
            highlightthickness=0, bd=0,
        ).pack(fill="x", padx=20)

        # --- model ---
        self._section("Model")
        self.model_var = tk.StringVar(value=cfg["model"])
        row3 = tk.Frame(self.win, bg=BG)
        row3.pack(fill="x", padx=20)
        for key, label in (("base", "Fastest"), ("small", "Balanced")):
            rb = tk.Radiobutton(
                row3, text=label, value=key, variable=self.model_var,
                command=self._model_changed, bg=BG, fg=FG, selectcolor=BG,
                activebackground=BG, activeforeground=FG, font=FONT_S,
                highlightthickness=0, bd=0,
            )
            rb.pack(side="left", padx=(0, 12))

        tk.Label(self.win, text="Closing this window keeps SpeechTyper running"
                 " in the tray / menu bar.",
                 bg=BG, fg=MUTED, font=FONT_S, wraplength=320,
                 justify="left").pack(side="bottom", pady=12, **pad)

    # --- helpers ---
    def _section(self, title):
        tk.Label(self.win, text=title.upper(), bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(pady=(10, 4), padx=20,
                                                    anchor="w")

    def _paint_modes(self):
        for k, b in self._mode_btns.items():
            if k == self.mode_var.get():
                b.config(bg=ACCENT, fg="#0a0a0a")
            else:
                b.config(bg=CARD, fg=MUTED)

    def _set_mode(self, k):
        self.mode_var.set(k)
        self.cfg["mode"] = k
        self._paint_modes()
        self.on_change(self.cfg)

    # --- languages ---
    def _render_langs(self):
        for w in self.chips.winfo_children():
            w.destroy()
        row = tk.Frame(self.chips, bg=BG)
        row.pack(fill="x", anchor="w")
        used = 0
        for code in self.cfg["languages"]:
            name = config.LANG_NAMES.get(code, code)
            short = name.split(" ")[0] if len(name) > 16 else name
            chip = tk.Frame(row, bg=CARD)
            txt = tk.Label(chip, text=short, bg=CARD, fg=FG, font=FONT_S,
                           padx=8, pady=4)
            txt.pack(side="left")
            x = tk.Label(chip, text="×", bg=CARD, fg=MUTED, font=FONT_S,
                         padx=6, cursor="hand2")
            x.pack(side="left")
            x.bind("<Button-1>", lambda e, c=code: self._remove_lang(c))
            chip.pack(side="left", padx=(0, 6), pady=2)
            used += 1
            if used % 3 == 0:
                row = tk.Frame(self.chips, bg=BG)
                row.pack(fill="x", anchor="w")
        plus = tk.Label(row, text="+", bg=CARD, fg=FG, font=FONT,
                        padx=10, pady=2, cursor="hand2")
        plus.pack(side="left", pady=2)
        plus.bind("<Button-1>", self._open_picker)

    def _remove_lang(self, code):
        langs = [c for c in self.cfg["languages"] if c != code]
        self.cfg["languages"] = langs or ["en"]
        self._render_langs()
        self.on_change(self.cfg)

    def _open_picker(self, _e=None):
        if self._picker is not None and self._picker.winfo_exists():
            self._picker.lift()
            return
        p = tk.Toplevel(self.win)
        self._picker = p
        p.title("Add language")
        p.configure(bg=BG)
        p.geometry("280x380+%d+%d" % (self.win.winfo_x() + 40,
                                      self.win.winfo_y() + 120))
        tk.Label(p, text="ADD LANGUAGE", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).pack(pady=(12, 4), padx=14,
                                                    anchor="w")
        query = tk.StringVar()
        entry = tk.Entry(p, textvariable=query, bg=CARD, fg=FG, font=FONT,
                         insertbackground=FG, relief="flat")
        entry.pack(fill="x", padx=14, ipady=5)
        entry.focus_set()
        frame = tk.Frame(p, bg=BG)
        frame.pack(fill="both", expand=True, padx=14, pady=8)
        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        lb = tk.Listbox(frame, bg=CARD, fg=FG, font=FONT_S, relief="flat",
                        highlightthickness=0, selectbackground="#333",
                        yscrollcommand=sb.set, activestyle="none")
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)

        def available():
            return [(c, n) for c, n in config.LANGUAGES
                    if c not in self.cfg["languages"]]

        shown = []

        def refill(*_a):
            q = query.get().lower()
            lb.delete(0, "end")
            shown.clear()
            for c, n in available():
                if q in n.lower() or q in c:
                    lb.insert("end", f"  {n}")
                    shown.append(c)

        def choose(_e=None):
            sel = lb.curselection()
            if not sel:
                return
            self.cfg["languages"] = self.cfg["languages"] + [shown[sel[0]]]
            self._render_langs()
            self.on_change(self.cfg)
            refill()

        query.trace_add("write", refill)
        lb.bind("<Double-Button-1>", choose)
        lb.bind("<Return>", choose)
        refill()

    # --- mic ---
    def _mic_changed(self, name):
        idx = next((i for i, n in self._devices if n == name), None)
        self.cfg["input_device"] = idx
        self.cfg["input_device_name"] = name
        self.on_change(self.cfg)

    def _refresh_mics(self, _e=None):
        self._devices = [(None, "System default")] + Recorder.list_devices()
        menu = self.mic_menu["menu"]
        menu.delete(0, "end")
        for _, n in self._devices:
            menu.add_command(
                label=n, command=lambda v=n: (self.mic_var.set(v),
                                              self._mic_changed(v))
            )

    # --- misc ---
    def _mute_changed(self):
        self.cfg["mute_while_listening"] = self.mute_var.get()
        self.on_change(self.cfg)

    def _model_changed(self):
        self.cfg["model"] = self.model_var.get()
        self.on_change(self.cfg)

    def _learn(self, _e):
        self.learn_btn.config(text="Press any key…", fg=ACCENT)

        def done(spec, label):
            self.cfg["hotkey"] = spec
            self.cfg["hotkey_label"] = label
            self.on_change(self.cfg)
            self.win.after(0, lambda: (
                self.key_label.config(text=label),
                self.learn_btn.config(text="Learn key", fg=MUTED),
            ))

        self.learn_key(done)

    def show(self):
        self.win.deiconify()
        self.win.lift()
        try:
            import sys

            if sys.platform == "darwin":
                import AppKit

                AppKit.NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass

    def hide(self):
        self.win.withdraw()

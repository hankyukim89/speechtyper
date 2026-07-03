"""The black pill overlay: click-through, never steals focus."""
import math
import random
import sys
import tkinter as tk

PILL_W, PILL_H = 196, 46
BARS = 11
BAR_W = 3
BAR_GAP = 5
TRANSPARENT = "#0d100b"  # unlikely color used as Windows transparency key


class PillOverlay:
    """States: hidden | listening | processing | notice.

    The window stays mapped forever at alpha 0 — showing/hiding only animates
    alpha, which never activates the window or steals keyboard focus.
    """

    def __init__(self, root: tk.Tk, get_level):
        self._get_level = get_level
        self.state = "hidden"
        self._tick = 0
        self._alpha = 0.0
        self._alpha_target = 0.0
        self._notice_job = None

        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.0)
        except tk.TclError:
            pass

        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        x = (sw - PILL_W) // 2
        y = sh - PILL_H - 90
        self.win.geometry(f"{PILL_W}x{PILL_H}+{x}+{y}")

        if sys.platform == "darwin":
            try:
                self.win.attributes("-transparent", True)
                self.win.config(bg="systemTransparent")
                canvas_bg = "systemTransparent"
            except tk.TclError:
                canvas_bg = TRANSPARENT
        elif sys.platform == "win32":
            self.win.config(bg=TRANSPARENT)
            self.win.attributes("-transparentcolor", TRANSPARENT)
            canvas_bg = TRANSPARENT
        else:
            canvas_bg = TRANSPARENT

        self.canvas = tk.Canvas(
            self.win, width=PILL_W, height=PILL_H,
            bg=canvas_bg, highlightthickness=0, bd=0,
        )
        self.canvas.pack()
        self._draw_pill()
        self._bars = []
        self._levels = [0.0] * BARS
        self._make_bars()
        self._text = self.canvas.create_text(
            PILL_W // 2 + 6, PILL_H // 2, text="", fill="#f0f0f0",
            font=("Segoe UI", 10), state="hidden",
        )

        self.win.update_idletasks()
        if sys.platform == "darwin":
            self._macos_no_focus()
        elif sys.platform == "win32":
            self._windows_no_focus()

        self._animate()

    # --- platform: make the window inert ---
    def _macos_no_focus(self):
        try:
            import AppKit

            for w in AppKit.NSApp.windows():
                f = w.frame()
                if int(f.size.width) == PILL_W and int(f.size.height) == PILL_H:
                    w.setIgnoresMouseEvents_(True)
                    w.setLevel_(AppKit.NSStatusWindowLevel)
                    w.setCollectionBehavior_(
                        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                        | AppKit.NSWindowCollectionBehaviorStationary
                    )
        except Exception:
            pass

    def _windows_no_focus(self):
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
            )
        except Exception:
            pass

    # --- drawing ---
    def _draw_pill(self):
        c, r = self.canvas, PILL_H // 2
        w, h = PILL_W, PILL_H
        fill = "#0a0a0a"
        c.create_oval(0, 0, h, h, fill=fill, outline=fill)
        c.create_oval(w - h, 0, w, h, fill=fill, outline=fill)
        c.create_rectangle(r, 0, w - r, h, fill=fill, outline=fill)
        c.create_oval(20, h // 2 - 3, 26, h // 2 + 3, fill="#e8e8e8", outline="")

    def _make_bars(self):
        cx0 = 44
        mid = PILL_H // 2
        for i in range(BARS):
            x = cx0 + i * (BAR_W + BAR_GAP)
            bar = self.canvas.create_rectangle(
                x, mid - 2, x + BAR_W, mid + 2, fill="#ffffff", outline=""
            )
            self._bars.append(bar)

    def _bars_visible(self, on: bool):
        st = "normal" if on else "hidden"
        for b in self._bars:
            self.canvas.itemconfigure(b, state=st)
        self.canvas.itemconfigure(self._text, state="hidden" if on else "normal")

    # --- states ---
    def show_listening(self):
        self._cancel_notice()
        self.state = "listening"
        self._bars_visible(True)
        self._alpha_target = 1.0

    def show_processing(self):
        self.state = "processing"

    def show_notice(self, msg: str, ms: int = 2200):
        self._cancel_notice()
        self.state = "notice"
        self.canvas.itemconfigure(self._text, text=msg)
        self._bars_visible(False)
        self._alpha_target = 1.0
        self._notice_job = self.win.after(ms, self.hide)

    def hide(self):
        self._cancel_notice()
        self.state = "hidden"
        self._alpha_target = 0.0

    def _cancel_notice(self):
        if self._notice_job is not None:
            try:
                self.win.after_cancel(self._notice_job)
            except Exception:
                pass
            self._notice_job = None

    # --- animation loop ---
    def _animate(self):
        if abs(self._alpha - self._alpha_target) > 0.01:
            self._alpha += (self._alpha_target - self._alpha) * 0.35
            try:
                self.win.attributes("-alpha", round(self._alpha, 3))
            except tk.TclError:
                pass
        if self.state in ("listening", "processing"):
            self._tick += 1
            mid = PILL_H // 2
            level = self._get_level()
            for i, bar in enumerate(self._bars):
                if self.state == "listening":
                    jitter = random.uniform(0.35, 1.0)
                    center_bias = 1.0 - abs(i - BARS // 2) / (BARS * 0.85)
                    target = 2 + level * 17 * jitter * (0.5 + center_bias)
                else:
                    target = 3 + 6 * (
                        0.5 + 0.5 * math.sin(self._tick * 0.35 + i * 0.6)
                    )
                cur = self._levels[i]
                cur += (target - cur) * 0.45
                self._levels[i] = cur
                x0, _, x1, _ = self.canvas.coords(bar)
                self.canvas.coords(bar, x0, mid - cur, x1, mid + cur)
        self.win.after(33, self._animate)

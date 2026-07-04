"""First-run onboarding wizard: welcome → sign in → permissions →
model download → try it. 460px window, progress dots."""
import subprocess
import sys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QProgressBar,
                               QStackedWidget, QVBoxLayout, QWidget)

from . import theme
from .widgets import (GhostButton, Keycap, PrimaryButton, divider, label)

MODEL_MB = 147


class Onboarding(QWidget):
    finished = Signal(str)  # emits the signed-in email

    def __init__(self, cfg, ctrl):
        """ctrl needs: transcriber (.ready), start_try_capture(cb)/is_recording,
        hotkey label via cfg."""
        super().__init__()
        self.cfg = cfg
        self.ctrl = ctrl
        self.email = ""

        self.setWindowTitle("SpeechTyper Setup")
        self.setFixedWidth(460)
        self.setStyleSheet(f"background: {theme.BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        dots_row = QWidget()
        dl = QHBoxLayout(dots_row)
        dl.setContentsMargins(0, 20, 0, 0)
        dl.setSpacing(8)
        dl.addStretch(1)
        self._dots = []
        for _ in range(5):
            d = QLabel()
            d.setFixedSize(8, 8)
            self._dots.append(d)
            dl.addWidget(d)
        dl.addStretch(1)
        root.addWidget(dots_row)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self._build_welcome()
        self._build_signin()
        self._build_permissions()
        self._build_download()
        self._build_try()
        self._go(0)

    def _go(self, step):
        self._step = step
        for i, d in enumerate(self._dots):
            c = theme.ACCENT if i <= step else theme.BORDER_CARD
            d.setStyleSheet(f"background: {c}; border-radius: 4px;")
        self.stack.setCurrentIndex(step)
        if step == 2:
            self._start_permission_watch()
        else:
            self._stop_permission_watch()
        if step == 3:
            self._start_download_watch()
        self.adjustSize()

    def _page(self, center=True):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(44, 32, 44, 36)
        lay.setSpacing(0)
        self.stack.addWidget(w)
        return w, lay

    def _title(self, lay, text, sub=None):
        t = label(text, 22, theme.TEXT, 700)
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        if sub:
            s = label(sub, 14, theme.TEXT_2, wrap=True)
            s.setAlignment(Qt.AlignCenter)
            lay.addSpacing(6)
            lay.addWidget(s)

    # -- step 0: welcome --
    def _build_welcome(self):
        w, lay = self._page()
        lay.setContentsMargins(44, 36, 44, 40)
        logo = QLabel()
        logo.setPixmap(theme.svg_pixmap(theme.MIC_SVG, 52))
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo)
        lay.addSpacing(18)
        t = label("Welcome to SpeechTyper", 26, theme.TEXT, 700)
        t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        lay.addSpacing(10)
        s = label("Hold a key, speak, and your words are typed into any app. "
                  "Powered by premium speech AI.", 15, theme.TEXT_2, wrap=True)
        s.setAlignment(Qt.AlignCenter)
        lay.addWidget(s)
        lay.addSpacing(28)
        btn = PrimaryButton("Get started", 16)
        btn.clicked.connect(lambda: self._go(1))
        lay.addWidget(btn)
        lay.addSpacing(14)
        n = label("Takes about a minute", 13, theme.TEXT_MUTED)
        n.setAlignment(Qt.AlignCenter)
        lay.addWidget(n)

    # -- step 1: sign in --
    def _build_signin(self):
        w, lay = self._page()
        self._title(lay, "Sign in", "Your license is tied to your account.")
        lay.addSpacing(24)
        google = GhostButton("Continue with Google", 15)
        google.setIcon(theme.svg_icon(theme.GOOGLE_SVG, 18))
        google.clicked.connect(self._google)
        lay.addWidget(google)
        lay.addSpacing(10)
        self._email = QLineEdit()
        self._email.setPlaceholderText("Email address")
        self._email.setStyleSheet(
            f"QLineEdit {{ font-family: '{theme.FAMILY}'; font-size: 15px;"
            f" color: {theme.TEXT}; background: #ffffff; border: 1px solid"
            f" {theme.BORDER_INPUT}; border-radius: 8px; padding: 12px 14px; }}")
        self._email.returnPressed.connect(self._email_continue)
        lay.addWidget(self._email)
        lay.addSpacing(10)
        cont = PrimaryButton("Continue with email", 15)
        cont.setStyleSheet(cont.styleSheet().replace(theme.ACCENT, theme.DARK)
                           .replace(theme.ACCENT_HOVER, "#000000"))
        cont.clicked.connect(self._email_continue)
        lay.addWidget(cont)
        lay.addSpacing(18)
        n = label("7-day free trial. No card required.", 13, theme.TEXT_MUTED)
        n.setAlignment(Qt.AlignCenter)
        lay.addWidget(n)

    def _google(self):
        # Full Google OAuth needs the Firebase project (see README-v2).
        # Until it's configured, fall back to email capture.
        self._email.setFocus()
        self._email.setPlaceholderText("Enter your Google email")

    def _email_continue(self):
        email = self._email.text().strip()
        if "@" not in email:
            self._email.setStyleSheet(self._email.styleSheet().replace(
                theme.BORDER_INPUT, theme.RED))
            return
        self.email = email
        self._go(2)

    # -- step 2: permissions --
    def _build_permissions(self):
        w, lay = self._page()
        self._title(lay, "Two permissions",
                    "So SpeechTyper can hear you and type for you.")
        lay.addSpacing(22)

        def perm_row(svg, title, why, key):
            card = QWidget()
            card.setStyleSheet(
                f"background: #ffffff; border: 1px solid {theme.BORDER_CARD};"
                " border-radius: 10px;")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.setSpacing(14)
            ic = QLabel()
            ic.setPixmap(theme.svg_pixmap(svg, 22))
            ic.setStyleSheet("border: none;")
            cl.addWidget(ic)
            col = QVBoxLayout()
            col.setSpacing(1)
            t = label(title, 15, theme.TEXT, 600)
            t.setStyleSheet(t.styleSheet() + "border: none;")
            y = label(why, 13, theme.TEXT_2)
            y.setStyleSheet(y.styleSheet() + "border: none;")
            col.addWidget(t)
            col.addWidget(y)
            cl.addLayout(col)
            cl.addStretch(1)
            btn = PrimaryButton("Allow", 13)
            btn.setStyleSheet(btn.styleSheet().replace(
                "padding: 12px 18px", "padding: 7px 14px"))
            btn.clicked.connect(lambda: self._grant(key, btn))
            cl.addWidget(btn)
            setattr(self, f"_perm_{key}", btn)
            return card

        lay.addWidget(perm_row(theme.MIC_OUTLINE_SVG, "Microphone",
                               "To hear what you say", "mic"))
        lay.addSpacing(10)
        lay.addWidget(perm_row(theme.KEYBOARD_SVG, "Keyboard access",
                               "To type text for you", "kbd"))
        lay.addSpacing(18)
        note = label("On a Mac this opens System Settings — flip the switch "
                     "next to SpeechTyper and come back.", 13,
                     theme.TEXT_MUTED, wrap=True)
        note.setAlignment(Qt.AlignCenter)
        lay.addWidget(note)
        lay.addSpacing(20)
        cont = PrimaryButton("Continue", 15)
        cont.clicked.connect(lambda: self._go(3))
        lay.addWidget(cont)

    def _grant(self, key, btn):
        if key == "mic":
            # opening the input stream makes the OS show its mic prompt
            try:
                self.ctrl.recorder.start_stream()
                self._mark_permission_granted(btn)
                return
            except Exception:
                pass
            if sys.platform == "darwin":
                self._open_privacy_pane("Privacy_Microphone")
                btn.setText("Waiting…")
                return
            self._mark_permission_granted(btn)
            return

        # keyboard access (macOS Accessibility)
        if sys.platform != "darwin":
            self._mark_permission_granted(btn)
            return
        from ..hotkey import (accessibility_is_granted,
                              request_accessibility_permission)

        if accessibility_is_granted():
            self._mark_permission_granted(btn)
            return
        request_accessibility_permission()  # registers this build + prompts
        self._open_privacy_pane("Privacy_Accessibility")
        btn.setText("Waiting…")  # the watcher flips it once granted

    @staticmethod
    def _open_privacy_pane(pane):
        try:
            subprocess.Popen([
                "open",
                "x-apple.systempreferences:com.apple.preference.security"
                f"?{pane}"])
        except Exception:
            pass

    # poll while the permissions step is visible so the buttons flip to
    # "Granted" by themselves the moment the user enables the switch
    def _start_permission_watch(self):
        self._stop_permission_watch()
        self._perm_timer = QTimer(self)
        self._perm_timer.timeout.connect(self._tick_permissions)
        self._perm_timer.start(700)
        self._tick_permissions()

    def _stop_permission_watch(self):
        if getattr(self, "_perm_timer", None):
            self._perm_timer.stop()
            self._perm_timer = None

    def _tick_permissions(self):
        if sys.platform != "darwin":
            return
        from ..hotkey import accessibility_is_granted

        btn = getattr(self, "_perm_kbd", None)
        if btn and btn.isEnabled() and accessibility_is_granted():
            self._mark_permission_granted(btn)
            if hasattr(self.ctrl, "notify_accessibility_granted"):
                self.ctrl.notify_accessibility_granted()

    @staticmethod
    def _mark_permission_granted(btn):
        btn.setText("Granted")
        btn.setEnabled(False)
        btn.setStyleSheet(
            f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: 13px;"
            f" font-weight: 600; color: {theme.GREEN};"
            " background: transparent; border: none; }")

    # -- step 3: model download --
    def _build_download(self):
        w, lay = self._page()
        self._title(lay, "Setting up the speech engine",
                    "One-time download, about 150 MB.")
        lay.addSpacing(28)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setStyleSheet(
            f"QProgressBar {{ background: {theme.BORDER_ROW};"
            " border-radius: 4px; border: none; }"
            f"QProgressBar::chunk {{ background: {theme.ACCENT};"
            " border-radius: 4px; }")
        lay.addWidget(self._bar)
        lay.addSpacing(10)
        self._dl_label = label("0 MB of 147 MB", 13, theme.TEXT_MUTED)
        self._dl_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._dl_label)
        lay.addSpacing(24)
        self._dl_cont = PrimaryButton("Continue", 16)
        self._dl_cont.clicked.connect(lambda: self._go(4))
        self._dl_cont.hide()
        lay.addWidget(self._dl_cont)

    def _start_download_watch(self):
        self._pct = 0
        self._dl_timer = QTimer(self)
        self._dl_timer.timeout.connect(self._tick_download)
        self._dl_timer.start(200)

    def _tick_download(self):
        ready = self.ctrl.transcriber.ready
        if ready:
            self._pct = 100
        elif self._pct < 92:  # creep while faster-whisper downloads/loads
            self._pct += 1.2
        self._bar.setValue(int(self._pct))
        if self._pct >= 100:
            self._dl_label.setText(f"Done — {MODEL_MB} MB")
            self._dl_cont.show()
            self._dl_timer.stop()
            self.adjustSize()
        else:
            mb = int(self._pct * MODEL_MB / 100)
            self._dl_label.setText(f"{mb} MB of {MODEL_MB} MB")

    # -- step 4: try it --
    def _build_try(self):
        w, lay = self._page()
        self._title(lay, "Try it now")
        lay.addSpacing(8)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addStretch(1)
        row.addWidget(label("Hold", 15, theme.TEXT_2))
        row.addWidget(Keycap(self.cfg.get("hotkey_label", "Right Alt"), 14))
        row.addWidget(label(", say “hello world”, release.", 15, theme.TEXT_2))
        row.addStretch(1)
        lay.addLayout(row)
        lay.addSpacing(20)
        self.try_box = QLabel("Your words show up here")
        self.try_box.setAlignment(Qt.AlignCenter)
        self.try_box.setWordWrap(True)
        self.try_box.setMinimumHeight(60)
        self._set_try_style(muted=True)
        lay.addWidget(self.try_box)
        lay.addSpacing(18)
        fin = PrimaryButton("Finish setup", 16)
        fin.clicked.connect(self._finish)
        lay.addWidget(fin)
        lay.addSpacing(12)
        n = label("You can change the key any time in Settings.", 13,
                  theme.TEXT_MUTED)
        n.setAlignment(Qt.AlignCenter)
        lay.addWidget(n)

    def _set_try_style(self, muted):
        c = theme.TEXT_MUTED if muted else theme.TEXT
        self.try_box.setStyleSheet(
            f"font-family: '{theme.FAMILY}'; font-size: 16px; color: {c};"
            f" background: #ffffff; border: 1px dashed {theme.BORDER_INPUT};"
            " border-radius: 10px; padding: 18px;")

    def set_try_text(self, text, muted=False):
        """Called by the app while on the try-it step."""
        self.try_box.setText(text)
        self._set_try_style(muted)

    @property
    def on_try_step(self):
        return self.isVisible() and self._step == 4

    def _finish(self):
        # close BEFORE emitting: listeners check "is onboarding visible"
        # to decide whether the main window may open
        self.close()
        self.finished.emit(self.email)

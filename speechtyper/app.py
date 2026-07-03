"""SpeechTyper v2 — hold a key, speak, release, text appears. Fully offline.
Qt (PySide6) UI; the Python core (recorder/transcriber/hotkey/injector)
is unchanged from v1 apart from bug fixes."""
import queue
import subprocess
import sys
import threading
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from . import config, dictionary, history, sounds, translate
from .account import Account
from .formatter import format_text
from .hotkey import HotkeyListener, accessibility_is_granted
from .injector import deliver
from .mute import Muter
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import theme
from .ui.main_window import MainWindow
from .ui.onboarding import Onboarding
from .ui.overlay import PillOverlay
from .ui.tray import start_tray

MIN_HOLD_S = 0.15  # debounce: taps shorter than this never record/paste


class App:
    def __init__(self):
        self.cfg = config.load()
        self.account = Account()
        self.events = queue.Queue()
        self._press_t = 0.0

        self.qapp = QApplication(sys.argv)
        self.qapp.setQuitOnLastWindowClosed(False)
        theme.load_font()

        if sys.platform == "darwin":
            try:  # background accessory app: no Dock icon, never steals focus
                import AppKit

                AppKit.NSApplication.sharedApplication().setActivationPolicy_(
                    AppKit.NSApplicationActivationPolicyAccessory)
            except Exception:
                pass

        self.recorder = Recorder(get_device=lambda: self.cfg.get("input_device"))
        self.muter = Muter()
        self.transcriber = Transcriber(self.cfg["model"])
        self.transcriber.load_async()

        self.overlay = PillOverlay(lambda: self.recorder.level)
        self.window = MainWindow(self.cfg, self.account, self)
        self.onboarding = None

        self.hotkey = HotkeyListener(
            get_spec=lambda: self.cfg["hotkey"],
            on_press_start=lambda: self.events.put("start"),
            on_release=lambda: self.events.put("stop"),
        )
        self._waiting_for_accessibility = (
            sys.platform == "darwin" and not accessibility_is_granted()
        )
        if not self._waiting_for_accessibility:
            self.hotkey.start()

        self.tray = start_tray(self.qapp, self._open_window, self.quit)

        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)
        self._timer.start(25)

        self._permission_timer = QTimer()
        self._permission_timer.timeout.connect(self._poll_accessibility)

    # ---- controller interface used by the views ----
    def save_cfg(self, cfg):
        config.save(cfg)
        self.transcriber.set_model(cfg["model"])
        if cfg.get("input_device") != getattr(self, "_last_device", "?"):
            self._last_device = cfg.get("input_device")
            self.recorder.restart()

    def learn_key(self, cb):
        self.hotkey.learn_next_key(cb)

    def list_devices(self):
        return Recorder.list_devices()

    # ---- window management ----
    def _open_window(self):
        if self.onboarding and self.onboarding.isVisible():
            self.onboarding.raise_()
            return
        self.window.show_view("home")
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    # ---- push-to-talk flow (Qt main thread via queue) ----
    def _poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev == "start":
                    self._start_recording()
                elif ev == "stop":
                    self._stop_recording()
                elif isinstance(ev, tuple) and ev[0] == "text":
                    self._finish(ev[1], ev[2])
                elif isinstance(ev, tuple) and ev[0] == "_translating":
                    self.overlay.show_translating(ev[1])
        except queue.Empty:
            pass

    def _start_recording(self):
        if not self._allowed():
            return
        self._press_t = time.time()
        sounds.play_pop()
        self.recorder.begin()
        if self.cfg.get("mute_while_listening"):
            self.muter.mute_async(on_muted=self.recorder.drop_recorded)
        self.overlay.show_listening()
        self.window.set_status("Listening", theme.RED)
        if self._on_try_step():
            self.onboarding.set_try_text("Listening…", muted=True)

    def _stop_recording(self):
        self.muter.unmute_async()
        held = time.time() - self._press_t
        audio = self.recorder.end()
        if held < MIN_HOLD_S or audio.size == 0:
            # debounce: a tap, not a dictation — never record/paste
            self.overlay.hide_pill()
            self.window.set_status("Ready")
            return
        self.overlay.show_processing()
        self.window.set_status("Processing", theme.ACCENT)

        langs = list(self.cfg["languages"])
        mode = self.cfg["mode"]
        entries = self.cfg.get("dictionary", [])
        prompt = dictionary.build_prompt(entries)
        translating = self.cfg.get("translate_enabled", False)
        target = self.cfg.get("target_lang", "es")
        # target English → Whisper translates natively, free and offline
        task = "translate" if translating and target == "en" else "transcribe"

        def work():
            translated_to = None
            try:
                raw = self.transcriber.transcribe(
                    audio, langs, initial_prompt=prompt, task=task)
                raw = dictionary.apply_post_pass(raw, entries)
                text = format_text(raw, mode)
                if translating and target == "en":
                    translated_to = "en"
                elif translating and text.strip():
                    name = translate.TARGET_NAMES.get(target, target)
                    self.events.put(("_translating", name))
                    src = langs[0] if len(langs) == 1 else "en"
                    out = translate.translate(text.strip(), src, target)
                    if out.strip() and out.strip() != text.strip():
                        translated_to = target
                    text = format_text(out, mode)
            except Exception:
                text = ""
            self.events.put(("text", text, translated_to))

        threading.Thread(target=work, daemon=True).start()

    def _finish(self, text, translated_to):
        if self._on_try_step():
            self.overlay.hide_pill()
            self.window.set_status("Ready")
            self.onboarding.set_try_text(
                text.strip() if text.strip() else "Didn’t catch that — try again",
                muted=not text.strip())
            return
        if not text or not text.strip():
            self.overlay.show_notice("Didn’t catch that")
            self.window.set_status("Ready")
            return
        self.overlay.hide_pill()
        self.window.set_status("Ready")
        if deliver(text):
            if self.cfg.get("history_enabled", True):
                history.add(text.strip(), translated_to)

    def _allowed(self) -> bool:
        if self._on_try_step():
            return True
        if self.account.active:
            return True
        # trial over: dictation disabled, show the Account view
        self.overlay.show_notice("Trial ended — see Account")
        self.window.show_view("account")
        self.window.show()
        self.window.raise_()
        return False

    def _on_try_step(self):
        return self.onboarding is not None and self.onboarding.on_try_step

    # ---- lifecycle ----
    def quit(self):
        try:
            self.hotkey.stop()
            self.recorder.close()
        finally:
            self.qapp.quit()

    def run(self):
        try:
            self.recorder.start_stream()  # warm mic so the pill reacts instantly
        except Exception:
            pass
        if not self.cfg.get("onboarded") or not self.account.signed_in:
            self.onboarding = Onboarding(self.cfg, self)
            self.onboarding.finished.connect(self._onboarding_done)
            self.onboarding.show()
        else:
            self._open_window()
        if self._waiting_for_accessibility:
            self.window.set_status("Permission needed", theme.RED)
            self._permission_timer.start(1000)
            QTimer.singleShot(400, self._show_accessibility_warning)
        sys.exit(self.qapp.exec())

    def _show_accessibility_warning(self):
        """Explain why the global hotkey is unavailable and open Settings."""
        if accessibility_is_granted():
            self._poll_accessibility()
            return
        parent = self.onboarding if self.onboarding else self.window
        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Allow keyboard access")
        box.setText("SpeechTyper cannot detect your push-to-talk key yet.")
        box.setInformativeText(
            "Enable SpeechTyper in System Settings → Privacy & Security → "
            "Accessibility. The hotkey will start automatically once enabled."
        )
        box.setStandardButtons(QMessageBox.Open | QMessageBox.Cancel)
        if box.exec() == QMessageBox.Open:
            try:
                subprocess.Popen([
                    "open",
                    "x-apple.systempreferences:com.apple.preference.security"
                    "?Privacy_Accessibility",
                ])
            except Exception:
                pass

    def _poll_accessibility(self):
        if not self._waiting_for_accessibility:
            self._permission_timer.stop()
            return
        if accessibility_is_granted():
            self._waiting_for_accessibility = False
            self._permission_timer.stop()
            self.hotkey.start()
            self.window.set_status("Ready", theme.GREEN)

    def _onboarding_done(self, email):
        if email:
            self.account.sign_in(email)
        self.cfg["onboarded"] = True
        config.save(self.cfg)
        self._open_window()


def main():
    App().run()


if __name__ == "__main__":
    main()

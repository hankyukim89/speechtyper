"""Global push-to-talk listener with learn-key support."""
import sys
import threading

from pynput import keyboard


def accessibility_is_granted() -> bool:
    """Whether this process may monitor global keyboard events on macOS."""
    if sys.platform != "darwin":
        return True
    try:
        import ApplicationServices as app_services

        return bool(app_services.AXIsProcessTrusted())
    except Exception:
        return False


def request_accessibility_permission() -> bool:
    """Ask macOS to register/prompt this app for Accessibility permission."""
    if sys.platform != "darwin":
        return True
    try:
        import ApplicationServices as app_services

        options = {app_services.kAXTrustedCheckOptionPrompt: True}
        return bool(app_services.AXIsProcessTrustedWithOptions(options))
    except Exception:
        return False


def key_to_spec(key) -> tuple[str, str]:
    """Return (spec, human label) for a pynput key event."""
    if isinstance(key, keyboard.Key):
        return key.name, key.name.replace("_", " ").title()
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return key.char, f"'{key.char}'"
        if key.vk is not None:
            return f"vk:{key.vk}", f"Key code {key.vk}"
    return "", "Unknown"


def _matches(key, spec: str) -> bool:
    if not spec:
        return False
    if spec.startswith("vk:"):
        return getattr(key, "vk", None) == int(spec[3:])
    named = getattr(keyboard.Key, spec, None)
    if named is not None:
        return key == named
    return getattr(key, "char", None) == spec


class HotkeyListener:
    """Calls on_press_start once when the key goes down, on_release when it lifts."""

    def __init__(self, get_spec, on_press_start, on_release):
        self._get_spec = get_spec
        self._on_start = on_press_start
        self._on_release = on_release
        self._down = False
        self._learning = None  # callback when in learn mode
        self._listener = None

    def start(self):
        if self._listener is not None and self._listener.is_alive():
            return
        self._listener = keyboard.Listener(
            on_press=self._press, on_release=self._release
        )
        self._listener.daemon = True
        self._listener.start()

    def learn_next_key(self, callback):
        """Next key pressed becomes the hotkey; callback(spec, label)."""
        self._learning = callback

    def _press(self, key):
        if self._learning is not None:
            cb, self._learning = self._learning, None
            spec, label = key_to_spec(key)
            if spec:
                cb(spec, label)
            return
        if _matches(key, self._get_spec()) and not self._down:
            self._down = True
            self._on_start()

    def _release(self, key):
        if self._down and _matches(key, self._get_spec()):
            self._down = False
            self._on_release()

    def stop(self):
        if self._listener:
            self._listener.stop()

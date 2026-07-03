"""Mute system output while listening, restore after — only if WE muted it."""
import subprocess
import sys
import threading


class Muter:
    def __init__(self):
        self._we_muted = False
        self._lock = threading.Lock()
        self._win_volume = None

    def mute_async(self, on_muted=None):
        """on_muted() is called only if we actually muted live audio."""

        def work():
            if self.mute() and on_muted:
                on_muted()

        threading.Thread(target=work, daemon=True).start()

    def unmute_async(self):
        threading.Thread(target=self.unmute, daemon=True).start()

    def mute(self) -> bool:
        """Returns True if audio was playing and we just muted it."""
        with self._lock:
            try:
                if sys.platform == "darwin":
                    # single osascript call: mute AND report previous state
                    r = subprocess.run(
                        ["osascript",
                         "-e", "set prev to output muted of (get volume settings)",
                         "-e", "set volume with output muted",
                         "-e", "prev"],
                        capture_output=True, text=True, timeout=2,
                    )
                    if r.stdout.strip() == "false":
                        self._we_muted = True
                        return True
                elif sys.platform == "win32":
                    v = self._win()
                    if v is not None and not v.GetMute():
                        v.SetMute(1, None)
                        self._we_muted = True
                        return True
            except Exception:
                pass
        return False

    def unmute(self):
        with self._lock:
            if not self._we_muted:
                return
            self._we_muted = False
            try:
                if sys.platform == "darwin":
                    subprocess.run(
                        ["osascript", "-e", "set volume without output muted"],
                        timeout=2,
                    )
                elif sys.platform == "win32":
                    v = self._win()
                    if v is not None:
                        v.SetMute(0, None)
            except Exception:
                pass

    def _win(self):
        if self._win_volume is None:
            try:
                from ctypes import POINTER, cast

                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                dev = AudioUtilities.GetSpeakers()
                iface = dev.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
                )
                self._win_volume = cast(iface, POINTER(IAudioEndpointVolume))
            except Exception:
                return None
        return self._win_volume

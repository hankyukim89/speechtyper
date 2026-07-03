"""Local dictation history: last 20 entries in <config>/history.json."""
import json
import sys
import time

from . import config

MAX_ENTRIES = 20


def _path():
    return config.config_dir() / "history.json"


def load() -> list[dict]:
    p = _path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def add(text: str, translated_to: str | None = None):
    entries = load()
    entries.insert(0, {
        "text": text,
        "ts": time.time(),
        "app": frontmost_app(),
        "translated_to": translated_to,
    })
    del entries[MAX_ENTRIES:]
    try:
        _path().write_text(
            json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def clear():
    try:
        _path().write_text("[]", encoding="utf-8")
    except Exception:
        pass


def frontmost_app() -> str:
    """Name of the app the dictation landed in (best effort)."""
    try:
        if sys.platform == "darwin":
            import AppKit

            app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
            return str(app.localizedName()) if app else ""
        if sys.platform == "win32":
            import ctypes
            import ctypes.wintypes as wt

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            pid = wt.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
            if h:
                buf = ctypes.create_unicode_buffer(260)
                size = wt.DWORD(260)
                ctypes.windll.kernel32.QueryFullProcessImageNameW(
                    h, 0, buf, ctypes.byref(size)
                )
                ctypes.windll.kernel32.CloseHandle(h)
                name = buf.value.rsplit("\\", 1)[-1]
                return name.removesuffix(".exe").title()
    except Exception:
        pass
    return ""


def relative_time(ts: float) -> str:
    d = max(0, time.time() - ts)
    if d < 60:
        return "just now"
    if d < 3600:
        return f"{int(d // 60)} min ago"
    if d < 86400:
        h = int(d // 3600)
        return f"{h} h ago"
    days = int(d // 86400)
    return "yesterday" if days == 1 else f"{days} days ago"

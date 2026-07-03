"""System tray (Windows) / menu bar (macOS) icon."""
import sys

from PIL import Image, ImageDraw


def _icon_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6, 18, 58, 46], radius=14, fill=(10, 10, 10, 255))
    for i, h in enumerate((6, 12, 18, 12, 6)):
        x = 18 + i * 7
        d.rounded_rectangle([x, 32 - h, x + 3, 32 + h], radius=2,
                            fill=(255, 255, 255, 255))
    return img


def start_tray(on_settings, on_quit):
    """Returns the pystray Icon or None if unavailable."""
    try:
        import pystray
    except Exception:
        return None

    menu = pystray.Menu(
        pystray.MenuItem("Settings", lambda i, _: on_settings(), default=True),
        pystray.MenuItem("Quit SpeechTyper", lambda i, _: on_quit()),
    )
    icon = pystray.Icon("SpeechTyper", _icon_image(), "SpeechTyper", menu)
    try:
        icon.run_detached()
        return icon
    except Exception:
        if sys.platform != "darwin":
            import threading

            threading.Thread(target=icon.run, daemon=True).start()
            return icon
        return None

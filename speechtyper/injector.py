"""Deliver transcribed text: paste wherever the cursor is. No detection,
no guessing — everything is a text box.

v2 fixes:
- never paste when the transcript is empty/whitespace (the old code sent
  Cmd/Ctrl+V anyway, pasting whatever was in the user's clipboard)
- verify the clipboard actually holds the transcript before pasting
- restore the user's previous clipboard ~1s after the paste
"""
import sys
import threading
import time

import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()


def deliver(text: str) -> bool:
    """Paste `text` at the cursor. Returns False if nothing was delivered."""
    if not text or not text.strip():
        return False

    try:
        previous = pyperclip.paste()
    except Exception:
        previous = None

    pyperclip.copy(text)
    # wait until the clipboard really holds the transcript (Electron apps
    # and slow clipboard managers sync late); bail out rather than paste
    # stale contents
    deadline = time.time() + 1.0
    while True:
        try:
            if pyperclip.paste() == text:
                break
        except Exception:
            pass
        if time.time() >= deadline:
            return False
        time.sleep(0.03)

    time.sleep(0.12)  # let the copy settle before the paste keystroke
    mod = Key.cmd if sys.platform == "darwin" else Key.ctrl
    with _kb.pressed(mod):
        _kb.press("v")
        time.sleep(0.03)
        _kb.release("v")

    if previous is not None and previous != text:
        def restore():
            time.sleep(1.0)
            try:
                # only restore if nothing else claimed the clipboard meanwhile
                if pyperclip.paste() == text:
                    pyperclip.copy(previous)
            except Exception:
                pass

        threading.Thread(target=restore, daemon=True).start()
    return True

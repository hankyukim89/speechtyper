"""The soft '톡' pop sound, synthesized once and cached."""
import math
import struct
import subprocess
import sys
import threading
import wave

from . import config

RATE = 44100


def _synth_pop(path):
    """Short woody pop: two decaying sines + click transient, ~70 ms."""
    n = int(RATE * 0.07)
    samples = []
    for i in range(n):
        t = i / RATE
        env = math.exp(-t * 70.0)
        v = (
            0.55 * math.sin(2 * math.pi * 1180 * t)
            + 0.30 * math.sin(2 * math.pi * 640 * t)
        ) * env
        if i < 40:  # tiny attack click
            v += 0.25 * (1 - i / 40.0) * (1 if i % 2 == 0 else -1)
        samples.append(max(-1.0, min(1.0, v * 0.5)))
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples))


def _pop_path():
    p = config.config_dir() / "pop.wav"
    if not p.exists():
        _synth_pop(p)
    return p


def play_pop():
    """Non-blocking."""
    threading.Thread(target=_play, daemon=True).start()


def _play():
    try:
        p = str(_pop_path())
        if sys.platform == "darwin":
            subprocess.Popen(
                ["afplay", p],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform == "win32":
            import winsound

            winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            subprocess.Popen(
                ["aplay", "-q", p],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass

"""Microphone capture with live level metering."""
import threading

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


class Recorder:
    """Always-warm input stream; frames are kept only while recording."""

    def __init__(self, get_device=None):
        self._get_device = get_device or (lambda: None)
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()
        self.level = 0.0  # smoothed RMS 0..1, read by the overlay
        self._stream = None

    @staticmethod
    def list_devices():
        """[(index, name)] of available input devices."""
        out = []
        try:
            for i, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) > 0:
                    out.append((i, d["name"]))
        except Exception:
            pass
        return out

    def start_stream(self):
        if self._stream is not None and self._stream.active:
            return
        self.close()
        try:
            self._stream = self._open(self._get_device())
        except Exception:
            # the saved device may be unplugged or re-indexed since last
            # run — never let a stale index kill the microphone entirely
            self._stream = self._open(None)
        self._stream.start()

    def _open(self, device):
        return sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=512,
            device=device,
            callback=self._callback,
        )

    def restart(self):
        self.close()
        try:
            self.start_stream()
        except Exception:
            self._stream = None

    def _callback(self, indata, frames, time_info, status):
        mono = indata[:, 0]
        rms = float(np.sqrt(np.mean(mono * mono)))
        target = min(1.0, rms * 14.0)
        self.level = self.level * 0.6 + target * 0.4
        if self._recording:
            with self._lock:
                self._frames.append(mono.copy())

    def begin(self):
        with self._lock:
            self._frames = []
        self._recording = True
        try:
            self.start_stream()  # self-heals if the stream died or device changed
        except Exception:
            self.restart()

    def drop_recorded(self):
        """Discard everything captured so far (e.g. audio leaked before
        the system mute kicked in) without stopping the recording."""
        with self._lock:
            self._frames = []

    def end(self) -> np.ndarray:
        self._recording = False
        with self._lock:
            if not self._frames:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._frames)

    def close(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

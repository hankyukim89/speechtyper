"""Offline transcription via faster-whisper (CTranslate2)."""
import threading

import numpy as np


class Transcriber:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None
        self._ready = threading.Event()
        self._lock = threading.Lock()

    def load_async(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        from faster_whisper import WhisperModel

        with self._lock:
            self._model = WhisperModel(
                self.model_name, device="auto", compute_type="int8"
            )
            self._ready.set()

    def set_model(self, model_name: str):
        if model_name == self.model_name and self._model is not None:
            return
        self.model_name = model_name
        self._ready.clear()
        self._model = None
        self.load_async()

    @property
    def ready(self) -> bool:
        return self._ready.is_set()

    def transcribe(
        self,
        audio: np.ndarray,
        languages: list[str],
        initial_prompt: str | None = None,
        task: str = "transcribe",
    ) -> str:
        """Blocks until model ready. audio: float32 mono 16 kHz.
        task="translate" makes Whisper output English directly (free, offline).
        initial_prompt biases decoding toward the user's dictionary words."""
        if audio.size < 1600:  # under 0.1 s — ignore taps
            return ""
        # set_model() may clear the model between wait() and use; retry
        model = None
        while model is None:
            self._ready.wait()
            model = self._model
        language = languages[0] if len(languages) == 1 else None
        segments, _info = model.transcribe(
            audio,
            language=language,
            task=task,
            initial_prompt=initial_prompt or None,
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 250},
        )
        return " ".join(s.text.strip() for s in segments).strip()

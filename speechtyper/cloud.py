"""Cloud transcription over an OpenAI-compatible audio API.

Business model: customers transcribe through the owner-funded API (they
should never need to know a local engine exists); the local faster-whisper
engine remains as the admin option and as a silent fallback when the
network or API is unavailable.

Owner setup: paste your API key into OWNER_API_KEY (or set the
SPEECHTYPER_CLOUD_KEY environment variable / "cloud_api_key" in
settings.json, which take precedence). NOTE: a key shipped inside the app
can be extracted by a determined user — before wide release, point
BASE_URL at a small proxy (e.g. a Firebase Function) that checks the
user's entitlement and holds the real key server-side.
"""
import io
import json
import os
import urllib.request
import uuid
import wave

import numpy as np

# ---- owner configuration -------------------------------------------------
OWNER_API_KEY = ""                        # sk-...  (see module docstring)
BASE_URL = "https://api.openai.com/v1"    # any OpenAI-compatible endpoint
MODEL = "whisper-1"                       # supports transcribe + translate
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16000


def api_key(cfg: dict | None = None) -> str:
    return (
        os.environ.get("SPEECHTYPER_CLOUD_KEY", "")
        or (cfg or {}).get("cloud_api_key", "")
        or OWNER_API_KEY
    )


def configured(cfg: dict | None = None) -> bool:
    return bool(api_key(cfg))


def _wav_bytes(audio: np.ndarray) -> bytes:
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2").tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def transcribe(
    audio: np.ndarray,
    languages: list[str],
    initial_prompt: str | None = None,
    task: str = "transcribe",
    cfg: dict | None = None,
) -> str:
    """Send float32 mono 16 kHz audio to the cloud API; returns the text.
    Raises on any failure so the caller can fall back to the local engine."""
    key = api_key(cfg)
    if not key:
        raise RuntimeError("cloud API key not configured")

    endpoint = "translations" if task == "translate" else "transcriptions"
    fields = {"model": MODEL}
    if task != "translate" and len(languages) == 1:
        fields["language"] = languages[0]
    if initial_prompt:
        fields["prompt"] = initial_prompt

    boundary = uuid.uuid4().hex
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(
            f"--{boundary}\r\nContent-Disposition: form-data; "
            f'name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    body.write(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode()
    )
    body.write(_wav_bytes(audio))
    body.write(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{BASE_URL}/audio/{endpoint}",
        data=body.getvalue(),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("text", "").strip()

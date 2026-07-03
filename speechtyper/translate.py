"""Offline translation.

- Target English: handled upstream by Whisper's task="translate" (free).
- Other targets: Argos Translate (offline, open source). Language pairs
  download on demand, like the Whisper model. Argos is optional — if it
  isn't installed or the pair isn't available, we return the original text.
"""
import threading

_lock = threading.Lock()
_installed_pairs: set[tuple[str, str]] = set()

# Languages we offer as "Type in" targets. English is special-cased
# (Whisper translates to English natively).
TARGETS = [
    ("en", "English"), ("es", "Spanish"), ("ko", "Korean"),
    ("ja", "Japanese"), ("fr", "French"), ("de", "German"),
    ("pt", "Portuguese"), ("zh", "Chinese"), ("it", "Italian"),
]
TARGET_NAMES = dict(TARGETS)


def available() -> bool:
    try:
        import argostranslate  # noqa: F401
        return True
    except Exception:
        return False


def ensure_pair(src: str, dst: str) -> bool:
    """Download+install the Argos package for src→dst if needed. Blocking."""
    if (src, dst) in _installed_pairs:
        return True
    try:
        import argostranslate.package as pkg
        import argostranslate.translate as tr

        with _lock:
            langs = tr.get_installed_languages()
            have = {l.code for l in langs}
            if src in have and dst in have:
                a = next(l for l in langs if l.code == src)
                if a.get_translation(next(l for l in langs if l.code == dst)):
                    _installed_pairs.add((src, dst))
                    return True
            pkg.update_package_index()
            for p in pkg.get_available_packages():
                if p.from_code == src and p.to_code == dst:
                    pkg.install_from_path(p.download())
                    _installed_pairs.add((src, dst))
                    return True
    except Exception:
        pass
    return False


def translate(text: str, src: str, dst: str) -> str:
    """Translate text; falls back to the original on any failure."""
    if not text or src == dst:
        return text
    try:
        import argostranslate.translate as tr

        if not ensure_pair(src, dst):
            # try pivoting through English (Argos's hub language)
            if src != "en" and dst != "en" and ensure_pair(src, "en") \
                    and ensure_pair("en", dst):
                return tr.translate(tr.translate(text, src, "en"), "en", dst)
            return text
        return tr.translate(text, src, dst)
    except Exception:
        return text

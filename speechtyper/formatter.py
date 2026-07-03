"""Output formatting modes."""
import re

_PUNCT = r"[.,!?;:…。、，！？·]"


def format_text(text: str, mode: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    if mode == "casual":
        text = re.sub(_PUNCT, "", text).lower()
        text = re.sub(r"\s+", " ", text).strip()
    elif text[0].isalpha():
        # normal: whisper already punctuates/capitalizes; guarantee first letter
        text = text[0].upper() + text[1:]
    return text + " " if text else ""  # trailing space so dictations chain nicely

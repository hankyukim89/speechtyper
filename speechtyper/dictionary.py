"""Custom dictionary: bias Whisper toward the user's words, then fix
remaining mishearings with a fuzzy post-pass.

Two mechanisms (per the handoff):
1. initial_prompt — the word list joined into a natural sentence, fed to
   faster-whisper so decoding prefers those spellings.
2. post-pass — fuzzy-replace close matches of each word (and its
   "sounds like" hint) with the canonical spelling.
"""
import difflib
import re


def build_prompt(entries: list[dict]) -> str:
    words = [e["word"] for e in entries if e.get("word")]
    if not words:
        return ""
    return "Glossary: " + ", ".join(words) + "."


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _hint_words(hint: str) -> list[str]:
    # hints look like: sounds like "cube control"
    m = re.search(r"[\"“”'](.+?)[\"“”']", hint)
    return (m.group(1) if m else hint).split()


def apply_post_pass(text: str, entries: list[dict]) -> str:
    if not text or not entries:
        return text
    tokens = re.findall(r"\S+|\s+", text)  # keep whitespace runs
    words_idx = [i for i, t in enumerate(tokens) if t.strip()]

    for e in entries:
        word = e.get("word", "").strip()
        if not word:
            continue
        targets = [word]
        if e.get("hint"):
            joined = " ".join(_hint_words(e["hint"]))
            if joined:
                targets.append(joined)

        for target in targets:
            t_norm = _norm(target)
            if not t_norm:
                continue
            n_words = max(1, len(target.split()))
            i = 0
            while i < len(words_idx):
                span = words_idx[i:i + n_words]
                if len(span) < n_words:
                    break
                chunk = "".join(tokens[span[0]:span[-1] + 1])
                c_norm = _norm(chunk)
                if c_norm and c_norm != _norm(word):
                    ratio = difflib.SequenceMatcher(None, c_norm, t_norm).ratio()
                    if ratio >= 0.84:
                        trail = re.search(r"[.,!?;:]+$", chunk.strip())
                        repl = word + (trail.group(0) if trail else "")
                        if chunk.strip()[:1].isupper() and word[:1].islower():
                            repl = repl  # keep canonical casing (e.g. kubectl)
                        tokens[span[0]] = repl
                        for j in range(span[0] + 1, span[-1] + 1):
                            tokens[j] = ""
                i += 1
            words_idx = [i for i, t in enumerate(tokens) if t.strip()]
    return "".join(tokens)

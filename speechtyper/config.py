"""Settings persistence for SpeechTyper."""
import json
import os
import sys
from pathlib import Path

APP_NAME = "SpeechTyper"

DEFAULTS = {
    "hotkey": "alt_r",          # pynput Key name, "vk:<code>", or single char
    "hotkey_label": "Right Option (⌥)" if sys.platform == "darwin" else "Right Alt",
    "mode": "normal",            # "casual" | "normal"
    "languages": ["en"],         # ISO codes; >1 enables auto-detect between them
    "model": "base",             # "base" (fastest) | "small" (balanced)
    "input_device": None,        # sounddevice index; None = system default
    "input_device_name": "System default",
    "mute_while_listening": False,
    # v2
    "translate_enabled": False,
    "target_lang": "es",         # ISO code of the "Type in" language
    "dictionary": [],            # [{"word": str, "hint": str}]
    "history_enabled": True,
    "onboarded": False,
}

# All languages supported by Whisper.
LANGUAGES = [
    ("en", "English"), ("ko", "한국어 Korean"), ("ja", "日本語 Japanese"),
    ("zh", "中文 Chinese"), ("yue", "粵語 Cantonese"),
    ("es", "Español Spanish"), ("fr", "Français French"),
    ("de", "Deutsch German"), ("pt", "Português Portuguese"),
    ("it", "Italiano Italian"), ("ru", "Русский Russian"),
    ("vi", "Tiếng Việt Vietnamese"), ("hi", "हिन्दी Hindi"),
    ("ar", "العربية Arabic"), ("tr", "Türkçe Turkish"),
    ("nl", "Nederlands Dutch"), ("pl", "Polski Polish"),
    ("id", "Bahasa Indonesia"), ("th", "ไทย Thai"),
    ("sv", "Svenska Swedish"), ("uk", "Українська Ukrainian"),
    ("el", "Ελληνικά Greek"), ("he", "עברית Hebrew"),
    ("cs", "Čeština Czech"), ("ro", "Română Romanian"),
    ("da", "Dansk Danish"), ("fi", "Suomi Finnish"),
    ("no", "Norsk Norwegian"), ("nn", "Nynorsk Norwegian"),
    ("hu", "Magyar Hungarian"), ("ms", "Bahasa Melayu Malay"),
    ("ca", "Català Catalan"), ("bg", "Български Bulgarian"),
    ("hr", "Hrvatski Croatian"), ("sr", "Српски Serbian"),
    ("sk", "Slovenčina Slovak"), ("sl", "Slovenščina Slovenian"),
    ("lt", "Lietuvių Lithuanian"), ("lv", "Latviešu Latvian"),
    ("et", "Eesti Estonian"), ("fa", "فارسی Persian"),
    ("ur", "اردو Urdu"), ("bn", "বাংলা Bengali"),
    ("ta", "தமிழ் Tamil"), ("te", "తెలుగు Telugu"),
    ("kn", "ಕನ್ನಡ Kannada"), ("ml", "മലയാളം Malayalam"),
    ("mr", "मराठी Marathi"), ("gu", "ગુજરાતી Gujarati"),
    ("pa", "ਪੰਜਾਬੀ Punjabi"), ("ne", "नेपाली Nepali"),
    ("si", "සිංහල Sinhala"), ("km", "ខ្មែរ Khmer"),
    ("lo", "ລາວ Lao"), ("my", "မြန်မာ Burmese"),
    ("ka", "ქართული Georgian"), ("hy", "Հայերեն Armenian"),
    ("az", "Azərbaycan Azerbaijani"), ("kk", "Қазақ Kazakh"),
    ("uz", "Oʻzbek Uzbek"), ("tg", "Тоҷикӣ Tajik"),
    ("tk", "Türkmen Turkmen"), ("mn", "Монгол Mongolian"),
    ("bo", "བོད་སྐད Tibetan"), ("tl", "Tagalog Filipino"),
    ("jw", "Basa Jawa Javanese"), ("su", "Basa Sunda Sundanese"),
    ("sw", "Kiswahili Swahili"), ("am", "አማርኛ Amharic"),
    ("yo", "Yorùbá Yoruba"), ("ha", "Hausa"), ("so", "Soomaali Somali"),
    ("sn", "chiShona Shona"), ("ln", "Lingála Lingala"),
    ("mg", "Malagasy"), ("af", "Afrikaans"), ("sq", "Shqip Albanian"),
    ("mk", "Македонски Macedonian"), ("bs", "Bosanski Bosnian"),
    ("be", "Беларуская Belarusian"), ("is", "Íslenska Icelandic"),
    ("fo", "Føroyskt Faroese"), ("mt", "Malti Maltese"),
    ("cy", "Cymraeg Welsh"), ("ga", "Gaeilge Irish"),
    ("gl", "Galego Galician"), ("eu", "Euskara Basque"),
    ("oc", "Occitan"), ("br", "Brezhoneg Breton"),
    ("lb", "Lëtzebuergesch Luxembourgish"), ("la", "Latina Latin"),
    ("sa", "संस्कृतम् Sanskrit"), ("yi", "ייִדיש Yiddish"),
    ("ht", "Kreyòl Haitian Creole"), ("ps", "پښتو Pashto"),
    ("sd", "سنڌي Sindhi"), ("as", "অসমীয়া Assamese"),
    ("tt", "Татар Tatar"), ("ba", "Башҡорт Bashkir"),
    ("haw", "ʻŌlelo Hawaiʻi Hawaiian"), ("mi", "Te Reo Māori"),
]

LANG_NAMES = dict(LANGUAGES)


def config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".config"
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path() -> Path:
    return config_dir() / "settings.json"


def load() -> dict:
    cfg = dict(DEFAULTS)
    p = _path()
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


def save(cfg: dict) -> None:
    _path().write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

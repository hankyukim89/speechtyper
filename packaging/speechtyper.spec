# PyInstaller spec — build with:  pyinstaller packaging/speechtyper.spec
# --onedir on purpose: onefile is slow to start with CTranslate2.
import sys
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = [("../speechtyper/assets", "speechtyper/assets")]
binaries, hiddenimports = [], []
for pkg in ("faster_whisper", "ctranslate2", "tokenizers"):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    ["../speechtyper/__main__.py"],
    pathex=[".."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + ["pynput.keyboard._darwin", "pynput.mouse._darwin",
                                   "pynput.keyboard._win32", "pynput.mouse._win32"],
    hookspath=[],
    excludes=["tkinter"],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="SpeechTyper",
    console=False,
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="SpeechTyper")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="SpeechTyper.app",
        bundle_identifier="com.speechtyper.app",
        info_plist={
            "LSUIElement": True,  # menu-bar app, no Dock icon
            "NSMicrophoneUsageDescription":
                "SpeechTyper listens while you hold the push-to-talk key.",
            "NSAppleEventsUsageDescription":
                "SpeechTyper types your dictation into the active app.",
        },
    )

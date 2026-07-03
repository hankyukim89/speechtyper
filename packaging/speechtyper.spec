# PyInstaller spec — build with: pyinstaller packaging/speechtyper.spec
# --onedir on purpose: onefile is slow to start with CTranslate2.
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None
ROOT = Path(SPECPATH).parent

datas = [(str(ROOT / "speechtyper" / "assets"), "speechtyper/assets")]
binaries, hiddenimports = [], []
for pkg in ("faster_whisper", "ctranslate2", "tokenizers"):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

pynput_platform = "_darwin" if sys.platform == "darwin" else "_win32"

a = Analysis(
    [str(ROOT / "packaging" / "entrypoint.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        f"pynput.keyboard.{pynput_platform}",
        f"pynput.mouse.{pynput_platform}",
    ],
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
        codesign_identity=os.environ.get("SIGN_ID") or None,
        entitlements_file=str(ROOT / "packaging" / "entitlements.plist"),
        info_plist={
            "CFBundleShortVersionString": "2.0.0",
            "CFBundleVersion": "2.0.0",
            "LSUIElement": True,  # menu-bar app, no Dock icon
            "NSMicrophoneUsageDescription":
                "SpeechTyper listens while you hold the push-to-talk key.",
            "NSAppleEventsUsageDescription":
                "SpeechTyper types your dictation into the active app.",
        },
    )

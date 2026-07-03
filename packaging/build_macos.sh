#!/bin/zsh
# Build the terminal-free SpeechTyper.app and, when create-dmg is installed,
# a DMG. For distribution without Gatekeeper warnings, set SIGN_ID and the
# notarization variables documented below.
set -e
cd "$(dirname "$0")/.."
export PYINSTALLER_CONFIG_DIR="$PWD/.pyinstaller-cache"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q -r requirements.txt
fi

.venv/bin/python -m pip install -q pyinstaller
.venv/bin/pyinstaller --noconfirm --clean packaging/speechtyper.spec

codesign --verify --deep --strict --verbose=2 "dist/SpeechTyper.app"
echo "App ready: dist/SpeechTyper.app"

if ! command -v create-dmg >/dev/null 2>&1; then
  echo "create-dmg is not installed; skipping DMG creation."
  echo "Install it with 'brew install create-dmg' when preparing a release."
  exit 0
fi

rm -f "dist/SpeechTyper.dmg"
create-dmg --volname "SpeechTyper" \
  --app-drop-link 420 180 --icon "SpeechTyper.app" 120 180 \
  "dist/SpeechTyper.dmg" "dist/SpeechTyper.app"

if [ -n "$SIGN_ID" ] && [ -n "$APPLE_ID" ]; then
  xcrun notarytool submit dist/SpeechTyper.dmg \
    --apple-id "$APPLE_ID" --team-id "$TEAM_ID" \
    --password "$APP_SPECIFIC_PW" --wait
  xcrun stapler staple dist/SpeechTyper.dmg
fi
echo "Done: dist/SpeechTyper.dmg"

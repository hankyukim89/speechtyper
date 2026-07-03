#!/bin/zsh
# Build SpeechTyper.app and a DMG. Requires: pip install pyinstaller ;
# brew install create-dmg. For distribution without Gatekeeper warnings,
# set SIGN_ID (Developer ID Application cert) and notarize.
set -e
cd "$(dirname "$0")/.."

.venv/bin/pip install -q pyinstaller
.venv/bin/pyinstaller --noconfirm packaging/speechtyper.spec

if [ -n "$SIGN_ID" ]; then
  codesign --deep --force --options runtime \
    --entitlements packaging/entitlements.plist \
    -s "$SIGN_ID" "dist/SpeechTyper.app"
fi

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

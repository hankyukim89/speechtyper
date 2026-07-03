# SpeechTyper v2

Hold a key, speak, release — your words are typed into any app. Fully
offline dictation (faster-whisper), now with a professional Qt UI,
onboarding, translation, custom dictionary, history, and licensing.

## Run it

- **macOS (no Terminal window):** build once with
  `./packaging/build_macos.sh`, then double-click `dist/SpeechTyper.app`
- **Windows (no console window):** double-click `SpeechTyper.vbs`

`run.command` is the visible macOS developer launcher; `.command` files are
always opened by Terminal. The built `.app` is the professional launcher and
does not open Terminal. On Windows, `SpeechTyper.vbs` creates the virtual
environment on first run and starts the app through `pythonw`, with its
console hidden. Startup errors are logged to
`%LOCALAPPDATA%\SpeechTyper\launcher.log`; the visible `run.bat` remains
available for troubleshooting.

For customer distribution, use the packaged `SpeechTyper.dmg` and
`SpeechTyperSetup.exe` described below. Those builds are self-contained and
also launch without a terminal or console window.

First run creates a virtualenv, installs dependencies, and walks you
through the 5-step setup (sign-in, permissions, model download, try-it).
Signing in with `hankyukim89@gmail.com` gives the **admin** account: full
access, billing hidden. Any other email starts a 7-day trial.

## What's new in v2

- **PySide6 UI** matching the Claude Design handoff (Instrument Sans,
  indigo accent, 400px main window, in-window view swaps with ‹ Back).
- **Onboarding wizard** — welcome → sign in → permissions → model
  download → try it.
- **Translate while dictating** — target English uses Whisper's built-in
  translate (free, offline). Other targets use Argos Translate if
  installed (`pip install argostranslate`); language pairs download on
  demand. Pill shows "Translating to X…".
- **Dictionary** — words are fed to Whisper via `initial_prompt`, plus a
  fuzzy post-pass replaces "sounds like" mishearings with the canonical
  spelling. Persisted in `settings.json`.
- **History** — last 20 dictations in `history.json` (local only), with
  relative time + destination app; click to copy.
- **Accounts & licensing** — local trial/admin logic works today;
  entitlement is cached signed in `entitlement.json` (30-day offline
  grace once Firebase is wired).
- **Bug fixes** — empty transcripts no longer paste your old clipboard
  (pill shows "Didn't catch that"); the clipboard is verified before
  pasting and restored ~1s after; key taps under 150 ms are ignored.
- **Restyled pill overlay** — 220×52, click-through, never steals focus.

## Owner setup (to actually charge money)

Placeholders live in `speechtyper/account.py`:

1. **Firebase** — create a project, enable Auth (Google + email link),
   Firestore, and Functions. Paste the Web API key and project id into
   `FIREBASE_API_KEY` / `FIREBASE_PROJECT_ID`. Store each user's plan at
   `users/{uid}.plan` (`"trial" | "pro" | "lifetime" | "admin"`).
2. **Stripe** — create Payment Links for $49/yr and $99 one-time; paste
   into `STRIPE_LINKS`. Add a Firebase Cloud Function webhook on
   `checkout.session.completed` that reads `client_reference_id` (the
   Firebase UID) and sets the user's plan in Firestore.
3. Until both are configured the app runs in local mode: trials are
   enforced per-machine and admin emails always work.

## Packaging

- **Windows:** `pyinstaller packaging/speechtyper.spec` then compile
  `packaging/windows-installer.iss` with Inno Setup → `SpeechTyperSetup.exe`.
- **macOS:** `packaging/build_macos.sh` → `dist/SpeechTyper.dmg`. Set
  `SIGN_ID`/`APPLE_ID`/`TEAM_ID`/`APP_SPECIFIC_PW` to code-sign and
  notarize (needs the $99/yr Apple Developer ID).
- Whisper models (and Argos pairs) download on first run into the config
  dir, keeping installers small.

## Layout

- `speechtyper/` — the app. Core: `recorder.py`, `transcriber.py`,
  `hotkey.py`, `injector.py`, `formatter.py`, `mute.py`, `sounds.py`.
  v2 features: `dictionary.py`, `history.py`, `translate.py`, `account.py`.
  UI: `ui/` (theme, widgets, main_window, onboarding, overlay, tray).
- `packaging/` — installers. `README.md` — the original design handoff.
- Config dir: `~/.config/SpeechTyper` (macOS) / `%APPDATA%\SpeechTyper`
  (Windows): `settings.json`, `history.json`, `entitlement.json`.

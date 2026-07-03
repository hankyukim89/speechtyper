# Handoff: SpeechTyper v2 — ship-ready redesign

## Overview
SpeechTyper is an existing Python push-to-talk dictation app (tkinter + faster-whisper, fully offline). This handoff covers a complete v2: a professional new UI, first-run onboarding, translation, custom dictionary, history, accounts with an admin bypass, paid licensing, bug fixes, and one-click packaging for Windows and macOS.

The existing codebase lives in the user's `SpeechTyper/` folder (`speechtyper/` package: `app.py`, `overlay.py`, `settings_ui.py`, `recorder.py`, `transcriber.py`, `injector.py`, `hotkey.py`, `tray.py`, `config.py`, `formatter.py`, `mute.py`, `sounds.py`). Extend it — don't rewrite from scratch.

## About the Design Files
`SpeechTyper App.dc.html` (bundled here) is a **design reference created in HTML** — an interactive prototype showing intended look and behavior. It is NOT production code. Recreate these designs in the app's environment. Recommendation: the current tkinter UI cannot reach this fidelity comfortably — consider moving the windows to **PySide6/Qt** (keeps the Python core: recorder, transcriber, hotkey, injector all reusable) or **Tauri/Electron shell + Python sidecar** if the dev prefers web tech. PySide6 is the lower-risk path.

## Fidelity
**High-fidelity.** Recreate pixel-perfectly: colors, spacing, type sizes as specified below.

## Design Tokens
- Background: `#fbfbfc`; page/desktop: `#dfe0e6`; footer strips: `#f4f4f7`
- Borders/dividers: `#e4e4e9` (cards), `#ececf0` (row dividers), `#d6d6de` (inputs/keys)
- Text: primary `#17171b`, secondary `#66666e`, muted `#9a9aa2`
- Accent (indigo): `#4353c8`, hover `#3a49b5`, tint bg `#eceefb`, tint border `#cdd3f2`
- Success green: `#2fa36b`; record red: `#e05c5c`; dark pill/overlay: `#17171b`
- Font: **Instrument Sans** (Google Fonts), 400/500/600/700
- Type scale: window titles 22–26px/700, section rows 15px/500, body 14px, helper text 13px muted, section labels 11px/700 uppercase letter-spacing 0.06em. Nothing below 12px.
- Radius: windows 12px, cards/inputs 8–10px, chips/toggles 999px. Shadows: `0 24px 64px rgba(23,23,27,0.14)` on windows.
- Toggles: 44×26px pill, 20px knob; on = accent, off = `#d6d6de`
- Hotkey keycap: white bg, 1px `#d6d6de` border with 2px bottom border, 6px radius, accent-colored label

## Screens

### 1. Onboarding wizard (first run) — 460px wide window
5 steps with progress dots (8px, accent when done/current, `#e4e4e9` otherwise):
1. **Welcome** — mic logo, "Welcome to SpeechTyper", subtitle "Hold a key, speak, and your words are typed into any app. Everything runs on your computer — no internet needed after setup." Primary button "Get started". Note "Takes about a minute".
2. **Sign in** — "Continue with Google" (bordered white button with Google logo), email field + "Continue with email" (black button). Footer: "7-day free trial. No card required."
3. **Permissions** — two rows (Microphone / Keyboard access) each with icon, title, one-line reason, and a status: green "Granted" or accent "Allow" button. Mac note about System Settings.
4. **Model download** — progress bar (8px, accent on `#ececf0`), "One time only, about 150 MB. After this, SpeechTyper works fully offline." Label shows "X MB of 147 MB", then "Done — 147 MB" + Continue.
5. **Try it** — instruction to hold the key and say "hello world"; dashed drop-zone box shows live transcript; "Finish setup".

### 2. Main window — 400px wide
- Header: mic logo + name, right side green status dot + "Ready".
- Hero: `Hold [Right Alt] and speak` (20px/600, keycap style) + "Text is typed wherever your cursor is."
- Rows (15px/500, dividers `#ececf0`):
  - **Translate while dictating** + toggle; subtitle "Any language → Spanish" or "Off". When on, a second row appears: "Type in" + language chips (selected: tint bg/border, accent text; unselected: white, gray).
  - **Dictionary** → "N custom words ›"
  - **History** → "Last 20 dictations ›"
- Footer strip: left = plan label ("Trial — 4 days left" / "Admin — free"), right = accent "Settings" link.
- Closing the window hides to tray/menu bar (existing behavior).

### 3. Dictionary view (in-window, ‹ Back)
Copy: "Names and words SpeechTyper should spell exactly. Add a 'sounds like' hint if it keeps mishearing one." Input + accent "Add" button; list rows: word (15px/500) + gray hint text + × remove (red on hover).
**Implementation:** feed the word list into faster-whisper via `initial_prompt` (join words into a natural sentence) and additionally run a post-pass replacing fuzzy matches of "sounds like" hints with the canonical spelling. Persist in `settings.json`.

### 4. History view (‹ Back)
"Click any entry to copy it again. Stored only on this computer." Rows: transcript text (14px) + meta line (12px muted): relative time · app name or "translated to Spanish". Keep last 20 in a local JSON file; clicking copies to clipboard.

### 5. Settings view (‹ Back)
Sections (11px/700 uppercase labels): PUSH-TO-TALK KEY (keycap + "Change key" learn-mode), LANGUAGES I SPEAK (chips + "+ Add" → searchable picker, reuse existing language list from `config.py`), STYLE (segmented: "Sentences" / "lowercase, no punctuation" — maps to existing normal/casual modes), MICROPHONE (dropdown + refresh), ACCURACY (segmented: "Fast" = base model / "More accurate" = small), mute-while-talking toggle. Footer note: "Closing this window keeps SpeechTyper running in the tray. Quit from the tray icon."

### 6. Account view (‹ Back)
Avatar circle (tint bg, accent initial), email, plan line.
- **Customer:** plan cards — "Pro — yearly $49/year" (current, 2px accent border, floating "CURRENT — TRIAL" tag) and "Pro — lifetime $99 once". Primary button "Subscribe — $49/year". Footnote: "Runs on your computer — compare at $144/year elsewhere."
- **Admin:** tinted card "Admin account — Full access, no subscription. Customer-facing billing is hidden for you." No plan cards.

### 7. Pill overlay (existing `overlay.py`, restyle)
Keep click-through/no-focus logic. 220×52px pill, `#17171b`, 999px radius, shadow `0 8px 24px rgba(0,0,0,0.3)`. Listening: red 8px dot + white animated level bars (4px wide, 2px radius). Translating state: globe icon + "Translating to Spanish…" (13px, `#d6d6de`).

## Interactions & Behavior
- All view changes are in-window swaps (no new windows) with ‹ Back.
- Toggle animation: 150ms ease on knob position and track color.
- Try-it step: shows "Listening…" while key held, transcript on release.
- Simple-first principle: the main window shows only hotkey, translate, dictionary, history. Everything else lives in Settings.

## Features to implement (beyond UI)

### Bug fixes (priority)
1. **Empty-transcript paste bug:** `injector.deliver()` currently pastes even when transcription yields nothing → the user's old clipboard gets pasted. Guard: if transcript is empty/whitespace, do nothing (show pill notice "Didn't catch that"). Also verify the clipboard actually contains the transcript before sending Ctrl/Cmd+V, and restore the previous clipboard afterwards (README claims restore but `injector.py` never restores — save `pyperclip.paste()` first, restore ~1s after paste).
2. Debounce very short key taps (<150 ms) — don't record/paste at all.

### Translation
- Toggle + target language. If target is **English**: use Whisper's built-in `task="translate"` — free, offline.
- For other targets (Spanish, Korean, etc.): bundle **Argos Translate** (offline, open source); download language pairs on demand like the Whisper model. Pipeline: transcribe → translate → inject. Show "Translating to X…" pill state during the translate step.

### Accounts, admin, licensing
- **Firebase Auth** (Google + email link). On successful login fetch a custom claim / Firestore doc: `{plan: "trial"|"pro"|"lifetime"|"admin", trial_ends: ...}`. Cache the entitlement locally (signed JSON) so the app works offline for 30 days between checks.
- **Admin bypass:** account with `plan: "admin"` (the owner's email) → full features, billing UI hidden.
- **Payments: Stripe** Payment Links ($49/yr subscription + $99 one-time). Webhook (Firebase Cloud Function) sets the user's plan in Firestore. "Subscribe" button opens the payment link in the browser with the Firebase UID as `client_reference_id`.
- Trial: 7 days from first sign-in, no card. After expiry: dictation disabled, window shows the Account view.
- Owner setup needed: create Firebase project (enable Auth + Firestore + Functions) and a Stripe account; put the Firebase web config in the app and the Stripe secret in the Cloud Function env.

### Packaging (one-click launcher)
- **Windows:** PyInstaller `--onedir` (onefile is slow to start with CTranslate2) → wrap with **Inno Setup** → `SpeechTyperSetup.exe`, Start Menu + optional run-at-login.
- **macOS:** PyInstaller `.app` → DMG (`create-dmg`). Code-sign + notarize with an Apple Developer ID ($99/yr) to avoid Gatekeeper warnings. Request mic + accessibility via proper `Info.plist` usage strings.
- Whisper model (and Argos pairs) download on first run into the config dir — keeps installers small.
- Auto-start at login (optional toggle in Settings): Windows registry Run key / macOS LaunchAgent.

## State Management
`settings.json` (existing) gains: `translate_enabled`, `target_lang`, `dictionary: [{word, hint}]`, `history_enabled`. New files in config dir: `history.json` (last 20), `entitlement.json` (cached, signed). Runtime state: view (home/dictionary/history/settings/account), recording state (idle/listening/processing/translating).

## Assets
No external images. Icons are simple inline SVGs (mic, globe, gear, clock, book) — recreate as needed (in Qt: QSvgRenderer or qtawesome equivalents). Font: Instrument Sans (bundle the OTF/TTF, SIL Open Font License).

## Files
- `SpeechTyper App.dc.html` — interactive hi-fi prototype (onboarding + main window all views + overlay states). Open in a browser; click through it.
- `SpeechTyper Options.dc.html` — earlier direction exploration (1a was chosen).

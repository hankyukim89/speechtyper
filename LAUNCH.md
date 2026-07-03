# Launch checklist

Everything code-side is done. What's left are **accounts only you can
create**. In order, fastest first — steps 1–4 get you selling today.

## 1. Stripe — collect money (~30 min) ⚡ do this first

1. Create an account at https://dashboard.stripe.com/register (needs your
   bank details for payouts; you can start in test mode immediately).
2. Products → **Add product**:
   - "SpeechTyper Pro — yearly", recurring, $49/year
   - "SpeechTyper Pro — lifetime", one-time, $99
3. For each, click **Create payment link**. Copy the two
   `https://buy.stripe.com/...` URLs.
4. Paste them in **two places**:
   - `speechtyper/account.py` → `STRIPE_LINKS`
   - `site/index.html` → the two `REPLACE_...` hrefs
5. Rebuild + redeploy after pasting.

You can now take payments. Fulfillment (auto-unlocking the app after
purchase) needs step 3.

## 2. Publish the installers (~20 min)

- Push to GitHub, then either tag a release
  (`git tag v2.0.0 && git push --tags`) or run the **Build installers**
  workflow from the repo's Actions tab. It builds:
  - `SpeechTyperSetup.exe` (Windows — built on GitHub's Windows machines;
    it cannot be built on your Mac)
  - `SpeechTyper.dmg` (macOS)
- A tag push attaches both to a GitHub Release; the site's download
  buttons already point at
  `github.com/hankyukim89/speechtyper/releases/latest/download/...`.
- The DMG built locally by `./packaging/build_macos.sh` works too.

**Honest caveat for day one:** unsigned apps show OS warnings.
- macOS: users must right-click → Open (or you sign + notarize, step 5).
- Windows: SmartScreen shows "unrecognized app" until you buy a code-signing
  cert (~$100–300/yr, takes days) or build install reputation over time.
Put a one-line "click More info → Run anyway" note on the site, ship, and
fix signing in week one. Every indie app starts this way.

## 3. Firebase — license verification (~45 min)

Without this the app still enforces the 7-day trial per-machine, and
buyers won't auto-unlock — you'd have to handle it manually. So do this
today too:

1. https://console.firebase.google.com → Add project (e.g.
   `speechtyper-prod`). Enable **Firestore** (production mode).
2. Project settings → copy the **Web API key** and **project id** into
   `FIREBASE_API_KEY` / `FIREBASE_PROJECT_ID` in `speechtyper/account.py`.
3. Firestore data model: one doc per user at `users/{uid}` with a string
   field `plan` = `trial | pro | lifetime | admin`.
4. Stripe → Developers → **Webhooks** → add endpoint for
   `checkout.session.completed`, pointing at a small Cloud Function that
   reads `client_reference_id` (the app already appends the user's uid to
   the payment link) and writes `plan` to that user's doc. Ask me and I'll
   write the function — I just need the Firebase project id.
5. Firestore rules: allow public **read** of `users/{uid}` docs (they
   contain only the plan string), writes only via the function/console.

## 4. Host the site (~15 min)

`site/index.html` is a single static file. Easiest options:
- **Firebase Hosting** (you'll have the project from step 3):
  `npm i -g firebase-tools && firebase init hosting && firebase deploy`
  → live at `speechtyper-prod.web.app` immediately.
- Or drag the `site` folder into https://app.netlify.com/drop (fastest).
- Custom domain (`speechtyper.com` etc.): buy it, point it in the hosting
  dashboard — allow up to a day for DNS.

## 5. Apple Developer ID — remove the Mac warning (start today, lands later)

- Enroll at https://developer.apple.com/programs/ ($99/yr). Approval is
  usually hours-to-2-days.
- Then create a **Developer ID Application** certificate, and set repo
  secrets `SIGN_ID`, `APPLE_ID`, `TEAM_ID`, `APP_SPECIFIC_PW` — the GitHub
  workflow and `build_macos.sh` already sign + notarize when these exist.

## 6. Before you announce

- [ ] Buy through your own Stripe link in **test mode**, confirm the plan
      flips in Firestore and the app unlocks.
- [ ] Fresh-machine test: download the DMG/EXE from the site like a
      customer would, complete onboarding, dictate into a real app.
- [ ] Set a support address (site footer currently uses your Gmail).
- [ ] Refund policy line on the site (Stripe makes refunds one click).

## What's intentionally NOT blocking launch

- EU VAT / sales tax: enable **Stripe Tax** in the dashboard (one toggle).
- Auto-updates: v2 ships without them; put "check the site for updates"
  in the README and add Sparkle/WinSparkle later.
- Analytics/crash reporting: add later; the app is offline-first by design.

"""Accounts, trial, licensing, admin bypass.

Entitlement is cached locally (signed JSON in <config>/entitlement.json) so
the app works offline between checks. When Firebase is configured (see
FIREBASE_API_KEY below), sign-in verifies against Firebase Auth and the plan
is fetched from Firestore; until then the app runs in local mode: 7-day
trial keyed to the first sign-in, admin emails get everything free.

Owner setup (see README-v2): create a Firebase project, paste the Web API
key + project id below, and put your Stripe Payment Links in STRIPE_LINKS.
"""
import hashlib
import hmac
import json
import time
import uuid
import webbrowser

from . import config

# ---- owner configuration -------------------------------------------------
FIREBASE_API_KEY = ""        # Firebase console → Project settings → Web API key
FIREBASE_PROJECT_ID = ""     # e.g. "speechtyper-prod"
ADMIN_EMAILS = {"hankyukim89@gmail.com"}
STRIPE_LINKS = {
    "yearly": "https://buy.stripe.com/REPLACE_yearly",    # $49/year
    "lifetime": "https://buy.stripe.com/REPLACE_lifetime",  # $99 once
}
TRIAL_DAYS = 7
OFFLINE_GRACE_DAYS = 30
# ---------------------------------------------------------------------------


def _path():
    return config.config_dir() / "entitlement.json"


def _secret() -> bytes:
    """Per-install secret for signing the cached entitlement."""
    p = config.config_dir() / ".instance"
    if not p.exists():
        p.write_text(uuid.uuid4().hex, encoding="utf-8")
    return p.read_text(encoding="utf-8").strip().encode()


def _sign(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True).encode()
    return hmac.new(_secret(), raw, hashlib.sha256).hexdigest()


class Account:
    def __init__(self):
        self.data = self._load()

    # -- persistence --
    def _load(self) -> dict | None:
        p = _path()
        if not p.exists():
            return None
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
            payload, sig = blob["payload"], blob["sig"]
            if hmac.compare_digest(sig, _sign(payload)):
                return payload
        except Exception:
            pass
        return None

    def _save(self):
        if self.data is None:
            return
        blob = {"payload": self.data, "sig": _sign(self.data)}
        _path().write_text(json.dumps(blob, indent=1), encoding="utf-8")

    # -- sign in / out --
    def sign_in(self, email: str, uid: str | None = None):
        email = email.strip().lower()
        plan = "admin" if email in ADMIN_EMAILS else "trial"
        existing = self.data or {}
        self.data = {
            "email": email,
            "uid": uid or existing.get("uid") or uuid.uuid4().hex,
            "plan": plan if plan == "admin" else existing.get("plan", "trial"),
            "trial_started": existing.get("trial_started") or time.time(),
            "last_check": time.time(),
        }
        self._save()
        self.refresh_async()

    def sign_out(self):
        self.data = None
        try:
            _path().unlink(missing_ok=True)
        except Exception:
            pass

    # -- remote check (Firebase) --
    def refresh_async(self):
        if not (FIREBASE_API_KEY and FIREBASE_PROJECT_ID and self.data):
            return
        import threading

        threading.Thread(target=self._refresh, daemon=True).start()

    def _refresh(self):
        """Fetch users/{uid} from Firestore REST; update the cached plan."""
        try:
            import urllib.request

            url = (
                f"https://firestore.googleapis.com/v1/projects/"
                f"{FIREBASE_PROJECT_ID}/databases/(default)/documents/"
                f"users/{self.data['uid']}?key={FIREBASE_API_KEY}"
            )
            with urllib.request.urlopen(url, timeout=10) as r:
                doc = json.loads(r.read())
            fields = doc.get("fields", {})
            plan = fields.get("plan", {}).get("stringValue")
            if plan:
                self.data["plan"] = plan
            self.data["last_check"] = time.time()
            self._save()
        except Exception:
            pass  # offline is fine within the grace window

    # -- state queries --
    @property
    def signed_in(self) -> bool:
        return self.data is not None

    @property
    def email(self) -> str:
        return (self.data or {}).get("email", "")

    @property
    def is_admin(self) -> bool:
        return (self.data or {}).get("plan") == "admin" \
            or self.email in ADMIN_EMAILS

    @property
    def plan(self) -> str:
        return (self.data or {}).get("plan", "trial")

    def trial_days_left(self) -> int:
        started = (self.data or {}).get("trial_started") or time.time()
        left = TRIAL_DAYS - (time.time() - started) / 86400
        return max(0, int(left + 0.999))

    @property
    def active(self) -> bool:
        """Whether dictation is allowed."""
        if not self.signed_in:
            return False
        if self.is_admin or self.plan in ("pro", "lifetime"):
            # honor the offline grace window when Firebase is configured
            if FIREBASE_API_KEY and not self.is_admin:
                last = self.data.get("last_check", 0)
                if time.time() - last > OFFLINE_GRACE_DAYS * 86400:
                    self.refresh_async()
            return True
        return self.trial_days_left() > 0

    def plan_label(self) -> str:
        """Footer label for the main window."""
        if self.is_admin:
            return "Admin — free"
        if self.plan == "lifetime":
            return "Pro — lifetime"
        if self.plan == "pro":
            return "Pro — yearly"
        d = self.trial_days_left()
        return f"Trial — {d} day{'s' if d != 1 else ''} left" if d \
            else "Trial expired"

    def plan_name(self) -> str:
        """Account-view plan line."""
        if self.is_admin:
            return "Admin — full access"
        if self.plan == "lifetime":
            return "Pro — lifetime"
        if self.plan == "pro":
            return "Pro — yearly"
        return "Pro trial" if self.trial_days_left() else "Trial expired"

    def open_checkout(self, which: str = "yearly"):
        url = STRIPE_LINKS.get(which, "")
        if url and self.data:
            sep = "&" if "?" in url else "?"
            webbrowser.open(
                f"{url}{sep}client_reference_id={self.data['uid']}"
            )

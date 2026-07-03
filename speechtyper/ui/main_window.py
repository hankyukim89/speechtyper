"""Main 400px window: home / dictionary / history / settings / account.
All view changes are in-window swaps with ‹ Back (per handoff)."""
import pyperclip
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit,
                               QScrollArea, QSizePolicy, QStackedWidget,
                               QVBoxLayout, QWidget)

from .. import config, history, translate
from . import theme
from .widgets import (Chip, FlowLayout, GhostButton, Keycap, LinkLabel,
                      PrimaryButton, Segmented, Toggle, divider, label,
                      section_label)

INPUT_QSS = (
    f"QLineEdit {{ font-family: '{theme.FAMILY}'; font-size: 14px;"
    f" color: {theme.TEXT}; background: #ffffff; border: 1px solid"
    f" {theme.BORDER_INPUT}; border-radius: 8px; padding: 10px 12px; }}"
)

# Dropdown list styling shared by every combobox (language picker, mic).
COMBO_POPUP_QSS = (
    f"QComboBox QAbstractItemView {{ font-family: '{theme.FAMILY}';"
    f" font-size: 13px; color: {theme.TEXT}; background: #ffffff;"
    f" border: 1px solid {theme.BORDER_INPUT}; border-radius: 8px;"
    " padding: 4px; outline: 0; }"
    " QComboBox QAbstractItemView::item { padding: 7px 10px;"
    " border-radius: 6px; }"
    " QComboBox QAbstractItemView::item:selected {"
    f" background: {theme.TINT_BG}; color: {theme.ACCENT}; }}"
)


class ClickRow(QWidget):
    """Home-screen row: title left, chevron text right, whole row clickable."""

    def __init__(self, title, on_click, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._on_click = on_click
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 13, 0, 13)
        lay.addWidget(label(title, 15, theme.TEXT, 500))
        lay.addStretch(1)
        self.value = label("", 13, theme.TEXT_2)
        lay.addWidget(self.value)

    def mousePressEvent(self, _):
        self._on_click()


class MainWindow(QWidget):
    def __init__(self, cfg, account, ctrl):
        """ctrl: object with save_cfg(cfg), learn_key(cb), list_devices(),
        current status via .status_text"""
        super().__init__()
        self.cfg = cfg
        self.account = account
        self.ctrl = ctrl

        self.setWindowTitle("SpeechTyper")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background: {theme.BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header
        head = QWidget()
        hl = QHBoxLayout(head)
        hl.setContentsMargins(22, 16, 22, 16)
        logo = QLabel()
        logo.setPixmap(theme.svg_pixmap(theme.MIC_SVG, 22))
        hl.addWidget(logo)
        hl.addSpacing(2)
        hl.addWidget(label("SpeechTyper", 16, theme.TEXT, 600))
        hl.addStretch(1)
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(7, 7)
        self.status_dot.setStyleSheet(
            f"background: {theme.GREEN}; border-radius: 3px;")
        hl.addWidget(self.status_dot)
        hl.addSpacing(2)
        self.status_label = LinkLabel("Ready", theme.TEXT_2, 13, 400)
        self.status_label.setCursor(Qt.ArrowCursor)
        self.status_label.clicked.connect(self._status_clicked)
        hl.addWidget(self.status_label)
        root.addWidget(head)
        root.addWidget(divider())

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        root.addWidget(self.stack, 1)

        self._views = {}
        self._build_all()
        self.show_view("home")

    # ---- infrastructure ----
    def set_status(self, text, color=theme.GREEN):
        self.status_label.setText(text)
        self.status_dot.setStyleSheet(
            f"background: {color}; border-radius: 3px;")
        needs_permission = text == "Permission needed"
        self.status_label.setCursor(
            Qt.PointingHandCursor if needs_permission else Qt.ArrowCursor)
        self.status_label.setToolTip(
            "Open Accessibility settings" if needs_permission else "")

    def _status_clicked(self):
        if self.status_label.text() == "Permission needed":
            self.ctrl.request_accessibility_access()

    def _page(self, name):
        w = QWidget()
        self._views[name] = w
        self.stack.addWidget(w)
        return w

    def show_view(self, name):
        # rebuild dynamic views so they always reflect current state
        if name in ("home", "dictionary", "history", "settings", "account"):
            getattr(self, f"_fill_{name}")()
        self.stack.setCurrentWidget(self._views[name])
        self.adjustSize()

    def _back_header(self, lay, title):
        row = QHBoxLayout()
        row.setSpacing(10)
        back = LinkLabel("‹ Back", theme.ACCENT, 14, 500)
        back.clicked.connect(lambda: self.show_view("home"))
        row.addWidget(back)
        row.addWidget(label(title, 17, theme.TEXT, 600))
        row.addStretch(1)
        lay.addLayout(row)

    def _clear(self, widget):
        old = widget.layout()
        if old is not None:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self._clear_layout(item.layout())
            QWidget().setLayout(old)

    def _clear_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _build_all(self):
        for name in ("home", "dictionary", "history", "settings", "account"):
            self._page(name)

    def save(self):
        self.ctrl.save_cfg(self.cfg)

    # =================== HOME ===================
    def _fill_home(self):
        w = self._views["home"]
        self._clear(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # hero
        hero = QWidget()
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(22, 26, 22, 26)
        hv.setSpacing(8)
        line = QHBoxLayout()
        line.setSpacing(8)
        line.addStretch(1)
        line.addWidget(label("Hold", 20, theme.TEXT, 600))
        line.addWidget(Keycap(self.cfg.get("hotkey_label", "Right Alt"), 17))
        line.addWidget(label("and speak", 20, theme.TEXT, 600))
        line.addStretch(1)
        hv.addLayout(line)
        sub = label("Text is typed wherever your cursor is.", 14, theme.TEXT_2)
        sub.setAlignment(Qt.AlignCenter)
        hv.addWidget(sub)
        lay.addWidget(hero)
        lay.addWidget(divider())

        rows = QWidget()
        rl = QVBoxLayout(rows)
        rl.setContentsMargins(22, 6, 22, 6)
        rl.setSpacing(0)

        # translate row
        tr_row = QHBoxLayout()
        tr_row.setContentsMargins(0, 13, 0, 13)
        tcol = QVBoxLayout()
        tcol.setSpacing(2)
        tcol.addWidget(label("Translate while dictating", 15, theme.TEXT, 500))
        on = self.cfg.get("translate_enabled", False)
        tgt = translate.TARGET_NAMES.get(self.cfg.get("target_lang", "es"), "Spanish")
        self._tr_sub = label(f"Any language → {tgt}" if on else "Off",
                             13, theme.TEXT_2)
        tcol.addWidget(self._tr_sub)
        tr_row.addLayout(tcol)
        tr_row.addStretch(1)
        tog = Toggle(on)
        tog.toggled.connect(self._toggle_translate)
        tr_row.addWidget(tog)
        rl.addLayout(tr_row)
        rl.addWidget(divider())

        # language chips (only when translate on)
        if on:
            chip_row = QHBoxLayout()
            chip_row.setContentsMargins(0, 12, 0, 12)
            chip_row.setSpacing(10)
            chip_row.addWidget(label("Type in", 13, theme.TEXT_2))
            cur = self.cfg.get("target_lang", "es")
            shown = ["es", "ko", "ja"]
            if cur not in shown:
                shown[0] = cur
            for code in shown:
                c = Chip(translate.TARGET_NAMES.get(code, code), code == cur)
                c.clicked.connect(lambda _=False, code=code: self._pick_target(code))
                chip_row.addWidget(c)
            chip_row.addStretch(1)
            rl.addLayout(chip_row)
            rl.addWidget(divider())

        dic = ClickRow("Dictionary", lambda: self.show_view("dictionary"))
        n = len(self.cfg.get("dictionary", []))
        dic.value.setText(f"{n} custom word{'s' if n != 1 else ''} ›")
        rl.addWidget(dic)
        rl.addWidget(divider())
        his = ClickRow("History", lambda: self.show_view("history"))
        his.value.setText("Last 20 dictations ›")
        rl.addWidget(his)
        lay.addWidget(rows)

        # footer strip
        foot = QWidget()
        foot.setStyleSheet(
            f"background: {theme.FOOTER}; border-top: 1px solid {theme.BORDER_ROW};")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(22, 14, 22, 14)
        plan = LinkLabel(self.account.plan_label(), theme.TEXT_2, 13, 400)
        plan.clicked.connect(lambda: self.show_view("account"))
        fl.addWidget(plan)
        fl.addStretch(1)
        settings = LinkLabel("Settings", theme.ACCENT, 13, 600)
        settings.clicked.connect(lambda: self.show_view("settings"))
        fl.addWidget(settings)
        lay.addWidget(foot)

    def _toggle_translate(self, on):
        self.cfg["translate_enabled"] = on
        self.save()
        self._fill_home()
        self.adjustSize()

    def _pick_target(self, code):
        self.cfg["target_lang"] = code
        self.save()
        self._fill_home()

    # =================== DICTIONARY ===================
    def _fill_dictionary(self):
        w = self._views["dictionary"]
        self._clear(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 16, 22, 22)
        lay.setSpacing(0)
        self._back_header(lay, "Dictionary")

        intro = label(
            "Names and words SpeechTyper should spell exactly. Add a "
            "“sounds like” hint if it keeps mishearing one.",
            13, theme.TEXT_2, wrap=True)
        lay.addSpacing(8)
        lay.addWidget(intro)
        lay.addSpacing(14)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._dict_input = QLineEdit()
        self._dict_input.setPlaceholderText("Add a word or name")
        self._dict_input.setStyleSheet(INPUT_QSS)
        self._dict_input.returnPressed.connect(self._add_word)
        add_row.addWidget(self._dict_input, 1)
        add_btn = PrimaryButton("Add", 14)
        add_btn.setStyleSheet(add_btn.styleSheet().replace(
            "padding: 12px 18px", "padding: 10px 16px"))
        add_btn.clicked.connect(self._add_word)
        add_row.addWidget(add_btn)
        lay.addLayout(add_row)

        hint_row = QHBoxLayout()
        hint_row.setSpacing(8)
        self._hint_input = QLineEdit()
        self._hint_input.setPlaceholderText("Sounds like… (optional)")
        self._hint_input.setStyleSheet(INPUT_QSS)
        self._hint_input.returnPressed.connect(self._add_word)
        hint_row.addWidget(self._hint_input, 1)
        lay.addSpacing(8)
        lay.addLayout(hint_row)
        lay.addSpacing(14)

        for i, e in enumerate(self.cfg.get("dictionary", [])):
            row = QHBoxLayout()
            row.setContentsMargins(0, 11, 0, 11)
            word_lab = label(e.get("word", ""), 15, theme.TEXT, 500)
            row.addWidget(word_lab)
            if e.get("hint"):
                row.addSpacing(10)
                row.addWidget(label(e["hint"], 13, theme.TEXT_MUTED))
            row.addStretch(1)
            x = LinkLabel("×", theme.TEXT_MUTED, 15, 400)
            x.clicked.connect(lambda i=i: self._remove_word(i))
            row.addWidget(x)
            lay.addLayout(row)
            lay.addWidget(divider())
        lay.addStretch(1)

    def _add_word(self):
        word = self._dict_input.text().strip()
        if not word:
            return
        hint = self._hint_input.text().strip()
        if hint and not hint.lower().startswith("sounds like"):
            hint = f"sounds like “{hint}”"
        self.cfg.setdefault("dictionary", []).insert(
            0, {"word": word, "hint": hint})
        self.save()
        self._fill_dictionary()

    def _remove_word(self, index):
        try:
            del self.cfg["dictionary"][index]
        except (KeyError, IndexError):
            return
        self.save()
        self._fill_dictionary()

    # =================== HISTORY ===================
    def _fill_history(self):
        w = self._views["history"]
        self._clear(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 16, 22, 22)
        lay.setSpacing(0)
        self._back_header(lay, "History")
        lay.addSpacing(8)
        lay.addWidget(label(
            "Click any entry to copy it again. Stored only on this computer.",
            13, theme.TEXT_2, wrap=True))
        lay.addSpacing(10)

        entries = history.load()
        if not entries:
            lay.addSpacing(10)
            lay.addWidget(label("No dictations yet.", 14, theme.TEXT_MUTED))
        area_widget = QWidget()
        al = QVBoxLayout(area_widget)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(0)
        for e in entries:
            item = QWidget()
            item.setCursor(Qt.PointingHandCursor)
            il = QVBoxLayout(item)
            il.setContentsMargins(0, 11, 0, 11)
            il.setSpacing(3)
            txt = e.get("text", "")
            shown = txt if len(txt) <= 120 else txt[:117] + "…"
            il.addWidget(label(shown, 14, theme.TEXT, wrap=True))
            meta = history.relative_time(e.get("ts", 0))
            if e.get("translated_to"):
                name = translate.TARGET_NAMES.get(e["translated_to"],
                                                  e["translated_to"])
                meta += f" · translated to {name}"
            elif e.get("app"):
                meta += f" · {e['app']}"
            il.addWidget(label(meta, 12, theme.TEXT_MUTED))
            item.mousePressEvent = (
                lambda _ev, t=txt, it=item: self._copy_history(t))
            al.addWidget(item)
            al.addWidget(divider())
        if len(entries) > 6:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            scroll.setStyleSheet("background: transparent;")
            scroll.setWidget(area_widget)
            scroll.setFixedHeight(420)
            lay.addWidget(scroll)
        else:
            lay.addWidget(area_widget)
        lay.addStretch(1)

    def _copy_history(self, text):
        try:
            pyperclip.copy(text)
            self.set_status("Copied", theme.ACCENT)
            QTimer.singleShot(1500, lambda: self.set_status("Ready"))
        except Exception:
            pass

    # =================== SETTINGS ===================
    def _fill_settings(self):
        w = self._views["settings"]
        self._clear(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(0)
        self._back_header(lay, "Settings")

        # push-to-talk key
        lay.addSpacing(10)
        lay.addWidget(section_label("Push-to-talk key"))
        lay.addSpacing(8)
        key_row = QHBoxLayout()
        key_row.setSpacing(10)
        self._keycap = Keycap(self.cfg.get("hotkey_label", "Right Alt"))
        key_row.addWidget(self._keycap)
        self._change_key = LinkLabel("Change key", theme.ACCENT, 13, 500)
        self._change_key.clicked.connect(self._learn_key)
        key_row.addWidget(self._change_key)
        key_row.addStretch(1)
        lay.addLayout(key_row)

        # languages I speak
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(16)
        lay.addWidget(section_label("Languages I speak"))
        lay.addSpacing(8)
        chips = FlowLayout(hspacing=6, vspacing=8)
        for code in self.cfg.get("languages", ["en"]):
            name = config.LANG_NAMES.get(code, code).split()[-1]
            c = Chip(f"{name} ×", True)
            c.clicked.connect(lambda _=False, code=code: self._remove_lang(code))
            chips.addWidget(c)
        self._lang_picker = QComboBox()
        self._lang_picker.setStyleSheet(
            f"QComboBox {{ font-family: '{theme.FAMILY}'; font-size: 13px;"
            f" font-weight: 500; color: {theme.TEXT_2}; background: #ffffff;"
            f" border: 1px solid {theme.BORDER_INPUT}; border-radius: 13px;"
            f" padding: 5px 12px; }}" + COMBO_POPUP_QSS)
        self._lang_picker.addItem("+ Add")
        for code, name in config.LANGUAGES:
            if code not in self.cfg.get("languages", []):
                self._lang_picker.addItem(name, code)
        self._lang_picker.activated.connect(self._add_lang)
        chips.addWidget(self._lang_picker)
        chip_host = QWidget()
        chip_host.setLayout(chips)
        lay.addWidget(chip_host)
        lay.addSpacing(6)
        lay.addWidget(label("One language is fastest. Several switch "
                            "automatically.", 12, theme.TEXT_MUTED))

        # style
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(16)
        lay.addWidget(section_label("Style"))
        lay.addSpacing(8)
        style = Segmented(["Sentences", "lowercase, no punctuation"],
                          0 if self.cfg.get("mode", "normal") == "normal" else 1)
        style.changed.connect(self._set_mode)
        lay.addWidget(style)

        # microphone
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(16)
        lay.addWidget(section_label("Microphone"))
        lay.addSpacing(8)
        self._mic = QComboBox()
        self._mic.setStyleSheet(
            f"QComboBox {{ font-family: '{theme.FAMILY}'; font-size: 14px;"
            f" color: {theme.TEXT}; background: #ffffff; border: 1px solid"
            f" {theme.BORDER_INPUT}; border-radius: 8px; padding: 10px 12px; }}"
            + COMBO_POPUP_QSS)
        self._mic.addItem("System default", None)
        for idx, name in self.ctrl.list_devices():
            self._mic.addItem(name, idx)
        cur = self.cfg.get("input_device")
        pos = self._mic.findData(cur)
        self._mic.setCurrentIndex(pos if pos >= 0 else 0)
        self._mic.activated.connect(self._set_mic)
        lay.addWidget(self._mic)

        # accuracy
        lay.addSpacing(16)
        lay.addWidget(divider())
        lay.addSpacing(16)
        lay.addWidget(section_label("Accuracy"))
        lay.addSpacing(8)
        acc = Segmented(["Fast", "More accurate"],
                        0 if self.cfg.get("model", "base") == "base" else 1)
        acc.changed.connect(self._set_model)
        lay.addWidget(acc)

        # mute toggle
        lay.addSpacing(14)
        lay.addWidget(divider())
        mute_row = QHBoxLayout()
        mute_row.setContentsMargins(0, 16, 0, 6)
        mute_row.addWidget(label("Mute other sound while I talk", 14,
                                 theme.TEXT, 500))
        mute_row.addStretch(1)
        mute = Toggle(self.cfg.get("mute_while_listening", False))
        mute.toggled.connect(self._set_mute)
        mute_row.addWidget(mute)
        lay.addLayout(mute_row)
        lay.addSpacing(10)
        lay.addWidget(label(
            "Closing this window keeps SpeechTyper running in the tray. "
            "Quit from the tray icon.", 12, theme.TEXT_MUTED, wrap=True))
        lay.addSpacing(6)
        lay.addStretch(1)

    def _learn_key(self):
        self._change_key.setText("Press any key…")
        def done(spec, lab):
            self.cfg["hotkey"] = spec
            self.cfg["hotkey_label"] = lab
            self.save()
            QTimer.singleShot(0, lambda: (
                self._keycap.setText(lab),
                self._change_key.setText("Change key")))
        self.ctrl.learn_key(done)

    def _remove_lang(self, code):
        langs = self.cfg.get("languages", [])
        if len(langs) > 1 and code in langs:
            langs.remove(code)
            self.save()
            self._fill_settings()

    def _add_lang(self, row):
        code = self._lang_picker.itemData(row)
        if code and code not in self.cfg["languages"]:
            self.cfg["languages"].append(code)
            self.save()
            self._fill_settings()

    def _set_mode(self, i):
        self.cfg["mode"] = "normal" if i == 0 else "casual"
        self.save()

    def _set_model(self, i):
        self.cfg["model"] = "base" if i == 0 else "small"
        self.save()

    def _set_mic(self, row):
        self.cfg["input_device"] = self._mic.itemData(row)
        self.cfg["input_device_name"] = self._mic.itemText(row)
        self.save()

    def _set_mute(self, on):
        self.cfg["mute_while_listening"] = on
        self.save()

    # =================== ACCOUNT ===================
    def _fill_account(self):
        w = self._views["account"]
        self._clear(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(22, 16, 22, 22)
        lay.setSpacing(0)
        self._back_header(lay, "Account")

        a = self.account
        head = QHBoxLayout()
        head.setContentsMargins(0, 12, 0, 12)
        head.setSpacing(12)
        avatar = QLabel((a.email[:1] or "?").upper())
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            f"font-family: '{theme.FAMILY}'; font-size: 15px; font-weight: 600;"
            f" color: {theme.ACCENT}; background: {theme.TINT_BG};"
            " border-radius: 19px;")
        head.addWidget(avatar)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(label(a.email or "Not signed in", 15, theme.TEXT, 500))
        col.addWidget(label(a.plan_name(),
                            13, theme.ACCENT if a.is_admin else theme.GREEN))
        head.addLayout(col)
        head.addStretch(1)
        lay.addLayout(head)
        lay.addWidget(divider())

        if a.is_admin:
            card = QLabel(
                "<div style='font-size:14px; font-weight:600;"
                f" color:{theme.ACCENT};'>Admin account</div>"
                f"<div style='font-size:13px; color:{theme.TEXT_2};"
                " margin-top:3px;'>Full access, no subscription. "
                "Customer-facing billing is hidden for you.</div>")
            card.setWordWrap(True)
            card.setStyleSheet(
                f"font-family: '{theme.FAMILY}'; background: {theme.TINT_BG};"
                f" border: 1px solid {theme.TINT_BORDER}; border-radius: 10px;"
                " padding: 14px 16px;")
            lay.addSpacing(14)
            lay.addWidget(card)
        else:
            lay.addSpacing(18)
            lay.addWidget(section_label("Your plan"))
            lay.addSpacing(10)
            trial = a.trial_days_left()
            on_trial = a.plan == "trial"
            tag = ("CURRENT — TRIAL" if on_trial and trial else
                   "CURRENT" if a.plan == "pro" else "")
            yearly = QLabel(
                (f"<div style='font-size:11px; font-weight:600; color:#fff;"
                 f" background:{theme.ACCENT}; display:inline;'>&nbsp;{tag}&nbsp;"
                 "</div>" if tag and a.plan != "lifetime" else "") +
                "<table width='100%'><tr>"
                "<td style='font-size:15px; font-weight:600;'>Pro — yearly</td>"
                "<td align='right' style='font-size:15px; font-weight:600;'>"
                f"$49<span style='font-size:13px; color:{theme.TEXT_MUTED};"
                " font-weight:400;'>/year</span></td></tr></table>"
                f"<div style='font-size:13px; color:{theme.TEXT_2};'>"
                "Unlimited dictation, translation, all languages."
                + (f" {trial} day{'s' if trial != 1 else ''} left in trial."
                   if on_trial and trial else "") + "</div>")
            yearly.setWordWrap(True)
            yearly.setStyleSheet(
                f"font-family: '{theme.FAMILY}'; color: {theme.TEXT};"
                " background: #ffffff; border: 2px solid"
                f" {theme.ACCENT if a.plan != 'lifetime' else theme.BORDER_CARD};"
                " border-radius: 10px; padding: 14px 16px;")
            lay.addWidget(yearly)
            lay.addSpacing(10)
            life = QLabel(
                "<table width='100%'><tr>"
                "<td style='font-size:15px; font-weight:600;'>Pro — lifetime</td>"
                "<td align='right' style='font-size:15px; font-weight:600;'>"
                f"$99<span style='font-size:13px; color:{theme.TEXT_MUTED};"
                " font-weight:400;'> once</span></td></tr></table>"
                f"<div style='font-size:13px; color:{theme.TEXT_2};'>"
                "Pay once, yours forever.</div>")
            life.setWordWrap(True)
            life.setStyleSheet(
                f"font-family: '{theme.FAMILY}'; color: {theme.TEXT};"
                " background: #ffffff; border:"
                f" {'2px solid ' + theme.ACCENT if a.plan == 'lifetime' else '1px solid ' + theme.BORDER_CARD};"
                " border-radius: 10px; padding: 14px 16px;")
            life.setCursor(QCursor(Qt.PointingHandCursor))
            life.mousePressEvent = lambda _: a.open_checkout("lifetime")
            lay.addWidget(life)
            if a.plan not in ("pro", "lifetime"):
                lay.addSpacing(14)
                sub = PrimaryButton("Subscribe — $49/year")
                sub.clicked.connect(lambda: a.open_checkout("yearly"))
                lay.addWidget(sub)
                lay.addSpacing(10)
                note = label("Runs on your computer — compare at $144/year "
                             "elsewhere.", 12, theme.TEXT_MUTED)
                note.setAlignment(Qt.AlignCenter)
                lay.addWidget(note)
        lay.addStretch(1)

    # closing hides to tray (existing behavior)
    def closeEvent(self, ev):
        ev.ignore()
        self.hide()

"""The black pill overlay, restyled per the v2 design: 220×52, #17171b,
click-through, never steals focus. States: listening / processing /
translating / notice."""
import math
import random
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from . import theme

PILL_W, PILL_H = 220, 52
BARS = 11


class PillOverlay(QWidget):
    def __init__(self, get_level):
        super().__init__()
        self._get_level = get_level
        self.state = "hidden"
        self._tick = 0
        self._levels = [2.0] * BARS
        self._text = ""
        self._opacity = 0.0
        self._target = 0.0

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
            | Qt.WindowTransparentForInput | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(PILL_W, PILL_H + 24)  # room for the drop shadow

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center().x() - PILL_W // 2,
                  screen.bottom() - PILL_H - 90)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)
        self._notice_timer = None

        self.setWindowOpacity(0.0)
        self.show()  # stays mapped; only opacity animates (never takes focus)
        if sys.platform == "darwin":
            self._macos_no_focus()

    def _macos_no_focus(self):
        try:
            import AppKit

            for w in AppKit.NSApp.windows():
                f = w.frame()
                if int(f.size.width) == PILL_W:
                    w.setIgnoresMouseEvents_(True)
                    w.setLevel_(AppKit.NSStatusWindowLevel)
                    w.setCollectionBehavior_(
                        AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                        | AppKit.NSWindowCollectionBehaviorStationary)
        except Exception:
            pass

    # ---- states ----
    def show_listening(self):
        self._cancel_notice()
        self.state = "listening"
        self._target = 1.0

    def show_processing(self):
        self._cancel_notice()
        self.state = "processing"
        self._target = 1.0

    def show_translating(self, lang_name):
        self._cancel_notice()
        self.state = "translating"
        self._text = f"Translating to {lang_name}…"
        self._target = 1.0

    def show_notice(self, msg, ms=2200):
        self._cancel_notice()
        self.state = "notice"
        self._text = msg
        self._target = 1.0
        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self.hide_pill)
        self._notice_timer.start(ms)

    def hide_pill(self):
        self._cancel_notice()
        self.state = "hidden"
        self._target = 0.0

    def _cancel_notice(self):
        if self._notice_timer:
            self._notice_timer.stop()
            self._notice_timer = None

    # ---- animation ----
    def _animate(self):
        if abs(self._opacity - self._target) > 0.01:
            self._opacity += (self._target - self._opacity) * 0.35
            self.setWindowOpacity(round(self._opacity, 3))
        if self.state in ("listening", "processing"):
            self._tick += 1
            level = self._get_level()
            for i in range(BARS):
                if self.state == "listening":
                    jitter = random.uniform(0.35, 1.0)
                    bias = 1.0 - abs(i - BARS // 2) / (BARS * 0.85)
                    tgt = 2 + level * 17 * jitter * (0.5 + bias)
                else:
                    tgt = 3 + 6 * (0.5 + 0.5 * math.sin(
                        self._tick * 0.35 + i * 0.6))
                self._levels[i] += (tgt - self._levels[i]) * 0.45
        if self._opacity > 0.02:
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # shadow: 0 8px 24px rgba(0,0,0,0.3)
        for i in range(8):
            a = int(18 * (1 - i / 8))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, a))
            p.drawRoundedRect(2 - i // 4, 8, PILL_W - 4 + i // 2,
                              PILL_H + i, PILL_H // 2, PILL_H // 2)
        p.setBrush(QColor(theme.DARK))
        p.drawRoundedRect(0, 4, PILL_W, PILL_H, PILL_H // 2, PILL_H // 2)

        mid = 4 + PILL_H // 2
        if self.state in ("listening", "processing"):
            # red dot + level bars
            p.setBrush(QColor(theme.RED))
            p.drawEllipse(20, mid - 4, 8, 8)
            p.setBrush(QColor("#ffffff"))
            x = 44
            for lv in self._levels:
                h = max(2.0, min(15.0, lv))
                p.drawRoundedRect(int(x), int(mid - h), 4, int(h * 2), 2, 2)
                x += 4 + 5
        elif self.state in ("translating", "notice"):
            if self.state == "translating":
                pm = theme.svg_pixmap(theme.GLOBE_SVG, 15, "#8b8d94")
                p.drawPixmap(30, mid - 8, pm)
                tx = 52
            else:
                tx = 24
            p.setPen(QColor(theme.BORDER_INPUT))
            f = QFont(theme.FAMILY)
            f.setPixelSize(13)
            p.setFont(f)
            p.drawText(tx, 8, PILL_W - tx - 16, PILL_H - 8,
                       Qt.AlignVCenter | Qt.AlignLeft
                       if self.state == "translating" else Qt.AlignCenter,
                       self._text)

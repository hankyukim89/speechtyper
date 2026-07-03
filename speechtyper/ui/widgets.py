"""Reusable widgets matching the v2 design: toggle, chips, keycap, buttons."""
from PySide6.QtCore import (Property, QEasingCurve, QPoint, QPropertyAnimation,
                            QRect, QSize, Qt, Signal)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QLayout,
                               QPushButton, QWidget)

from . import theme


class Toggle(QWidget):
    """44×26 pill toggle, 20px knob, 150ms ease (per handoff)."""
    toggled = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._pos = 21.0 if checked else 3.0
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def isChecked(self):
        return self._checked

    def setChecked(self, v, animate=True):
        if v == self._checked:
            return
        self._checked = v
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(21.0 if v else 3.0)
            self._anim.start()
        else:
            self.knobPos = 21.0 if v else 3.0

    def mousePressEvent(self, _):
        self.setChecked(not self._checked)
        self.toggled.emit(self._checked)

    def getKnobPos(self):
        return self._pos

    def setKnobPos(self, v):
        self._pos = v
        self.update()

    knobPos = Property(float, getKnobPos, setKnobPos)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = (self._pos - 3.0) / 18.0
        off, on = QColor(theme.BORDER_INPUT), QColor(theme.ACCENT)
        track = QColor(
            int(off.red() + (on.red() - off.red()) * t),
            int(off.green() + (on.green() - off.green()) * t),
            int(off.blue() + (on.blue() - off.blue()) * t),
        )
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, 44, 26, 13, 13)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(int(self._pos), 3, 20, 20)


class Chip(QPushButton):
    """Language chip: selected = tint bg/border + accent text."""

    def __init__(self, text, selected=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setSelected(selected)

    def setSelected(self, sel):
        self._selected = sel
        if sel:
            bg, fg, bd = theme.TINT_BG, theme.ACCENT, theme.TINT_BORDER
        else:
            bg, fg, bd = "#ffffff", theme.TEXT_2, theme.BORDER_INPUT
        self.setStyleSheet(
            f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: 13px;"
            f" font-weight: 500; padding: 6px 12px; border-radius: 13px;"
            f" background: {bg}; color: {fg}; border: 1px solid {bd}; }}"
        )


class Keycap(QLabel):
    """White keycap with 2px bottom border and accent label."""

    def __init__(self, text, size=15, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            f"QLabel {{ font-family: '{theme.FAMILY}'; font-size: {size}px;"
            f" font-weight: 600; color: {theme.ACCENT}; background: #ffffff;"
            f" border: 1px solid {theme.BORDER_INPUT}; border-bottom-width: 2px;"
            f" border-radius: 6px; padding: 3px 12px; }}"
        )


class PrimaryButton(QPushButton):
    def __init__(self, text, size=15, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: {size}px;"
            f" font-weight: 600; color: #ffffff; background: {theme.ACCENT};"
            f" border: none; border-radius: 8px; padding: 12px 18px; }}"
            f"QPushButton:hover {{ background: {theme.ACCENT_HOVER}; }}"
            f"QPushButton:disabled {{ background: {theme.BORDER_INPUT}; }}"
        )


class GhostButton(QPushButton):
    def __init__(self, text, size=14, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: {size}px;"
            f" font-weight: 500; color: {theme.TEXT}; background: #ffffff;"
            f" border: 1px solid {theme.BORDER_INPUT}; border-radius: 8px;"
            f" padding: 10px 16px; }}"
            f"QPushButton:hover {{ background: {theme.FOOTER}; }}"
        )


class LinkLabel(QLabel):
    clicked = Signal()

    def __init__(self, text, color=theme.ACCENT, size=13, weight=600, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"font-family: '{theme.FAMILY}'; font-size: {size}px;"
            f" font-weight: {weight}; color: {color}; background: transparent;"
        )

    def mousePressEvent(self, _):
        self.clicked.emit()


class Segmented(QWidget):
    """Two-option segmented control (STYLE / ACCURACY)."""
    changed = Signal(int)

    def __init__(self, options, index=0, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self._buttons = []
        for i, text in enumerate(options):
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=i: self.setIndex(i, emit=True))
            lay.addWidget(b)
            self._buttons.append(b)
        lay.addStretch(1)
        self._index = -1
        self.setIndex(index)

    def setIndex(self, index, emit=False):
        if index == self._index:
            return
        self._index = index
        for i, b in enumerate(self._buttons):
            if i == index:
                b.setStyleSheet(
                    f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: 13px;"
                    f" font-weight: 500; padding: 7px 14px; border-radius: 8px;"
                    f" background: {theme.ACCENT}; color: #ffffff; border: none; }}"
                )
            else:
                b.setStyleSheet(
                    f"QPushButton {{ font-family: '{theme.FAMILY}'; font-size: 13px;"
                    f" font-weight: 500; padding: 7px 14px; border-radius: 8px;"
                    f" background: #ffffff; color: {theme.TEXT_2};"
                    f" border: 1px solid {theme.BORDER_INPUT}; }}"
                )
        if emit:
            self.changed.emit(index)

    def index(self):
        return self._index


class FlowLayout(QLayout):
    """Left-to-right layout that wraps to a new line when the row is full.
    Keeps the language chips inside the fixed 400px window."""

    def __init__(self, parent=None, hspacing=6, vspacing=8):
        super().__init__(parent)
        self._items = []
        self._h = hspacing
        self._v = vspacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout(QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _layout(self, rect, test):
        x, y, row_h = rect.x(), rect.y(), 0
        for item in self._items:
            hint = item.sizeHint()
            if x > rect.x() and x + hint.width() > rect.right():
                x = rect.x()
                y += row_h + self._v
                row_h = 0
            if not test:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + self._h
            row_h = max(row_h, hint.height())
        return y + row_h - rect.y()


def section_label(text) -> QLabel:
    lab = QLabel(text.upper())
    lab.setStyleSheet(
        f"font-family: '{theme.FAMILY}'; font-size: 11px; font-weight: 700;"
        f" letter-spacing: 0.06em; color: {theme.TEXT_MUTED};"
        " background: transparent;"
    )
    return lab


def divider() -> QFrame:
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet(f"background: {theme.BORDER_ROW}; border: none;")
    return f


def label(text, size=14, color=theme.TEXT, weight=400, wrap=False) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(wrap)
    lab.setStyleSheet(
        f"font-family: '{theme.FAMILY}'; font-size: {size}px;"
        f" font-weight: {weight}; color: {color}; background: transparent;"
    )
    return lab

"""Styled modal dialogs matching the app design (replaces stock QMessageBox)."""
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from . import theme
from .widgets import GhostButton, PrimaryButton, label


class PermissionDialog(QDialog):
    """'Allow keyboard access' prompt. exec() truthy when Open was chosen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SpeechTyper")
        self.setModal(True)
        self.setFixedWidth(430)
        self.setStyleSheet(f"QDialog {{ background: {theme.BG}; }}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 26, 28, 24)
        lay.setSpacing(0)

        icon = QLabel()
        icon.setPixmap(theme.svg_pixmap(theme.KEYBOARD_SVG, 34))
        lay.addWidget(icon)
        lay.addSpacing(12)
        lay.addWidget(label("Turn on keyboard access", 18, theme.TEXT, 700))
        lay.addSpacing(8)
        body = label(
            "SpeechTyper needs Accessibility access to detect your "
            "push-to-talk key. In System Settings → Privacy & Security → "
            "Accessibility, turn on SpeechTyper.",
            13, theme.TEXT_2, wrap=True)
        lay.addWidget(body)
        lay.addSpacing(10)
        hint = label(
            "Already on but not working? Select SpeechTyper in that list, "
            "remove it with the “–” button, then relaunch the app and allow "
            "it again.", 12, theme.TEXT_MUTED, wrap=True)
        lay.addWidget(hint)
        lay.addSpacing(20)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btns.addStretch(1)
        later = GhostButton("Later", 14)
        later.clicked.connect(self.reject)
        btns.addWidget(later)
        open_btn = PrimaryButton("Open System Settings", 14)
        open_btn.clicked.connect(self.accept)
        btns.addWidget(open_btn)
        lay.addLayout(btns)

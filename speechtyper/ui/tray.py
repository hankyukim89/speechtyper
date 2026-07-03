"""System tray / menu-bar icon (QSystemTrayIcon replaces pystray)."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from . import theme


def _icon():
    pm = QPixmap(64, 64)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(0, 0, 0, 0))
    p.setBrush(QColor(theme.DARK))
    p.drawRoundedRect(6, 18, 52, 28, 14, 14)
    p.setBrush(QColor("#ffffff"))
    for i, h in enumerate((6, 12, 18, 12, 6)):
        x = 18 + i * 7
        p.drawRoundedRect(x, 32 - h, 3, h * 2, 1, 1)
    p.end()
    from PySide6.QtGui import QIcon

    icon = QIcon(pm)
    icon.setIsMask(True)  # adapts to macOS menu-bar dark/light
    return icon


def start_tray(parent, on_open, on_quit):
    tray = QSystemTrayIcon(_icon(), parent)
    tray.setToolTip("SpeechTyper")
    menu = QMenu()
    open_act = QAction("Open SpeechTyper", menu)
    open_act.triggered.connect(lambda _checked=False: on_open())
    quit_act = QAction("Quit SpeechTyper", menu)
    quit_act.setShortcut(QKeySequence.Quit)
    quit_act.setShortcutContext(Qt.ApplicationShortcut)
    quit_act.triggered.connect(lambda _checked=False: on_quit())
    menu.addAction(open_act)
    menu.addSeparator()
    menu.addAction(quit_act)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: on_open()
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()
    return tray

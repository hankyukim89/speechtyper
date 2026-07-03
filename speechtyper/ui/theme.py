"""Design tokens from the v2 handoff + Instrument Sans loading + SVG icons."""
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# ---- colors ----
BG = "#fbfbfc"
DESKTOP = "#dfe0e6"
FOOTER = "#f4f4f7"
BORDER_CARD = "#e4e4e9"
BORDER_ROW = "#ececf0"
BORDER_INPUT = "#d6d6de"
TEXT = "#17171b"
TEXT_2 = "#66666e"
TEXT_MUTED = "#9a9aa2"
ACCENT = "#4353c8"
ACCENT_HOVER = "#3a49b5"
TINT_BG = "#eceefb"
TINT_BORDER = "#cdd3f2"
GREEN = "#2fa36b"
RED = "#e05c5c"
DARK = "#17171b"

FAMILY = "Instrument Sans"
_loaded = False


def load_font():
    global FAMILY, _loaded
    if _loaded:
        return
    _loaded = True
    p = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "InstrumentSans.ttf"
    if p.exists():
        fid = QFontDatabase.addApplicationFont(str(p))
        fams = QFontDatabase.applicationFontFamilies(fid)
        if fams:
            FAMILY = fams[0]


def font(size: int, weight: int = 400) -> QFont:
    f = QFont(FAMILY)
    f.setPixelSize(size)
    f.setWeight(QFont.Weight(weight))
    return f


# ---- inline SVG icons (per handoff: no external images) ----
MIC_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="9" y="3" width="6" height="11" rx="3" fill="{c}"/>'
    '<path d="M5.5 11a6.5 6.5 0 0 0 13 0" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
    '<path d="M12 17.5V21" stroke="{c}" stroke-width="2" stroke-linecap="round"/></svg>'
)
MIC_OUTLINE_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="9" y="3" width="6" height="11" rx="3" stroke="{c}" stroke-width="1.8"/>'
    '<path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21" stroke="{c}" stroke-width="1.8" stroke-linecap="round"/></svg>'
)
KEYBOARD_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="3" y="5" width="18" height="14" rx="2" stroke="{c}" stroke-width="1.8"/>'
    '<path d="M7 15h6" stroke="{c}" stroke-width="1.8" stroke-linecap="round"/></svg>'
)
GLOBE_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="12" cy="12" r="9" stroke="{c}" stroke-width="1.8"/>'
    '<path d="M3.5 12h17M12 3.5c2.4 2.3 3.7 5.2 3.7 8.5s-1.3 6.2-3.7 8.5c'
    '-2.4-2.3-3.7-5.2-3.7-8.5s1.3-6.2 3.7-8.5Z" stroke="{c}" stroke-width="1.8"/></svg>'
)
GOOGLE_SVG = (
    '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
    '<path fill="#4285F4" d="M22.6 12.3c0-.8-.1-1.5-.2-2.3H12v4.5h6a5.1 5.1 0 0 1-2.2 3.4v2.8h3.6c2.1-2 3.2-4.9 3.2-8.4Z"/>'
    '<path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.8c-1 .7-2.3 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.6H2.1v2.9A11 11 0 0 0 12 23Z"/>'
    '<path fill="#FBBC05" d="M5.8 14a6.6 6.6 0 0 1 0-4.2V6.9H2.1a11 11 0 0 0 0 10l3.7-2.9Z"/>'
    '<path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.2-3.2A11 11 0 0 0 2.1 6.9L5.8 9.8c.9-2.7 3.3-4.4 6.2-4.4Z"/></svg>'
)


def svg_pixmap(svg: str, size: int, color: str = ACCENT, dpr: float = 2.0) -> QPixmap:
    data = QByteArray(svg.replace("{c}", color).encode())
    renderer = QSvgRenderer(data)
    pm = QPixmap(QSize(int(size * dpr), int(size * dpr)))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def svg_icon(svg: str, size: int, color: str = ACCENT) -> QIcon:
    return QIcon(svg_pixmap(svg, size, color))

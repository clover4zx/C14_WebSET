"""
theme.py
Central place for colors, fonts, and the global stylesheet. Any page
that uses Card, LabeledInput, primary_button, etc. from widgets.py
depends on app.setStyleSheet(STYLESHEET) being called once in main.py
— otherwise these widgets still work, they just render unstyled.

NOTE on colours with transparency: Qt reads 8-digit hex as #AARRGGBB
(alpha FIRST), not #RRGGBBAA like web CSS. Use rgba(...) or the
rgba() helper below instead, or the colour comes out completely wrong.
"""

BG_DARK = "#12161c"
BG_PANEL = "#1a2029"
BG_PANEL_ALT = "rgba(32, 39, 50, 80)"
ACCENT = "#3ddc97"
ACCENT_WARN = "#f2c14e"
ACCENT_DANGER = "#e5484d"
ACCENT_INFO = "#5fb0e0"
ACCENT_HIGH = "#f0883e"
TEXT_PRIMARY = "#e6e9ef"
TEXT_MUTED = "#8b93a7"
BORDER = "#2a3140"

SIDEBAR_BG = "#24133D"
SIDEBAR_ACTIVE = "#33205A"

FONT_FAMILY = "Segoe UI, Arial, sans-serif"

# Colour for each finding severity — used by charts and tables
SEVERITY_COLOURS = {
    "Critical": ACCENT_DANGER,
    "High": ACCENT_HIGH,
    "Medium": ACCENT_WARN,
    "Low": ACCENT_INFO,
}

# Colour for each scan status — used by the Recent Scans table
STATUS_COLOURS = {
    "Completed": ACCENT,
    "Running": ACCENT_INFO,
    "Failed": ACCENT_DANGER,
}


def rgba(hex_color: str, alpha: int) -> str:
    """Turn '#3ddc97' + alpha (0-255) into 'rgba(61, 220, 151, alpha)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


STYLESHEET = f"""
/* ---------- Base ---------- */
/* Only the window gets the dark background; every widget inside it
   stays transparent so cards, sidebar etc. show through properly. */
QWidget {{
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {BG_DARK};
}}

QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    selection-background-color: {SIDEBAR_ACTIVE};
}}

/* ---------- Sidebar ---------- */
#Sidebar {{
    background-color: {SIDEBAR_BG};
}}

#SidebarTitle {{
    font-size: 18px;
    font-weight: 700;
    padding: 18px 16px 0px 16px;
}}

#SidebarSubtitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    padding: 0px 16px 14px 16px;
}}

#NavButton {{
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    padding: 10px 16px;
}}

#NavButton:hover {{
    background-color: {SIDEBAR_ACTIVE};
}}

#NavButton:checked {{
    background-color: {SIDEBAR_ACTIVE};
    border-left: 3px solid {ACCENT};
    font-weight: 600;
}}

#NavButton:disabled {{
    color: {TEXT_MUTED};
}}

#NavBadge {{
    background-color: {rgba(ACCENT, 51)};
    color: {ACCENT};
    border: 1px solid {rgba(ACCENT, 136)};
    border-radius: 9px;
    font-size: 10px;
    font-weight: 700;
    padding: 0px 6px;
    margin-right: 10px;
}}

#SidebarFooter {{
    color: {TEXT_MUTED};
    font-size: 10px;
    padding: 8px 16px;
}}

/* ---------- Page headings ---------- */
#PageTitle {{
    font-size: 20px;
    font-weight: 600;
}}

#PageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

/* ---------- Cards ---------- */
QFrame.Card {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QLabel.SectionHeader {{
    font-size: 15px;
    font-weight: 600;
    padding-top: 4px;
}}

/* Dashboard summary cards */
#StatTitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
    font-weight: 600;
}}

#StatValue {{
    font-size: 30px;
    font-weight: 700;
}}

#StatValue[severity="warning"]  {{ color: {ACCENT_WARN}; }}
#StatValue[severity="critical"] {{ color: {ACCENT_DANGER}; }}
#StatValue[severity="info"]     {{ color: {ACCENT_INFO}; }}

/* ---------- Buttons ---------- */
QPushButton.Primary {{
    background-color: {ACCENT};
    color: #0a0e12;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
}}

QPushButton.Primary:hover {{
    background-color: #34c886;
}}

QPushButton.Secondary {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 9px 18px;
}}

QPushButton.Secondary:hover {{
    background-color: {BG_PANEL_ALT};
}}

/* ---------- Tabs ---------- */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    top: -1px;
}}

QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_MUTED};
    padding: 8px 20px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {BG_PANEL_ALT};
    color: {TEXT_PRIMARY};
    font-weight: 600;
}}

/* Secondary text, e.g. labels next to values, result counts */
#MutedText {{
    color: {TEXT_MUTED};
}}

/* ---------- Tables ---------- */
QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: transparent;
    selection-background-color: {SIDEBAR_ACTIVE};
    selection-color: {TEXT_PRIMARY};
}}

QTableWidget::item {{
    padding: 0px 8px;
    border-bottom: 1px solid {BORDER};
}}

QHeaderView, QTableCornerButton::section {{
    background-color: transparent;
    border: none;
}}

QHeaderView::section {{
    background-color: transparent;
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
}}

/* ---------- Inputs ---------- */
QCheckBox {{
    spacing: 8px;
    padding: 4px 0px;
}}
"""
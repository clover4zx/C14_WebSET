"""
theme.py
Central place for colors, fonts, and the global stylesheet.
Keeping this separate means any teammate can re-skin WebSET without
touching layout code.
"""

# Palette - dark, "security tool" feel
BG_DARK = "#12161c"
BG_PANEL = "#1a2029"
BG_PANEL_ALT = "#20273250"
ACCENT = "#3ddc97"        # green = safe / go
ACCENT_WARN = "#f2c14e"   # amber = warnings
ACCENT_DANGER = "#e5484d" # red = critical findings
TEXT_PRIMARY = "#e6e9ef"
TEXT_MUTED = "#8b93a7"
BORDER = "#2a3140"

FONT_FAMILY = "Segoe UI, Arial, sans-serif"

STYLESHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

/* Sidebar */
#Sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER};
}}

#SidebarTitle {{
    font-size: 18px;
    font-weight: 600;
    padding: 20px 16px 4px 16px;
    color: {ACCENT};
}}

#SidebarSubtitle {{
    font-size: 11px;
    color: {TEXT_MUTED};
    padding: 0px 16px 18px 16px;
}}

QPushButton#NavButton {{
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-left: 3px solid transparent;
    background-color: transparent;
    color: {TEXT_MUTED};
    font-size: 13px;
    font-weight: 500;
}}

QPushButton#NavButton:hover {{
    background-color: {BG_PANEL_ALT};
    color: {TEXT_PRIMARY};
}}

QPushButton#NavButton:checked {{
    background-color: {BG_PANEL_ALT};
    color: {TEXT_PRIMARY};
    border-left: 3px solid {ACCENT};
    font-weight: 600;
}}

/* Top bar */
#TopBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}

#PageTitle {{
    font-size: 20px;
    font-weight: 600;
}}

#PageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

/* Cards */
QFrame.Card {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QLabel.CardValue {{
    font-size: 26px;
    font-weight: 700;
}}

QLabel.CardLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QLabel.SectionHeader {{
    font-size: 15px;
    font-weight: 600;
    padding-top: 4px;
}}

/* Table */
QTableWidget {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    gridline-color: {BORDER};
    selection-background-color: {BG_PANEL_ALT};
}}

QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_MUTED};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}

/* Buttons */
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

/* Status pill labels (severity tags) */
QLabel.Pill {{
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}
"""
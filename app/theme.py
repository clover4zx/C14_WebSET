"""
theme.py
Central place for colors, fonts, and the global stylesheet. Any page
that uses Card, LabeledInput, primary_button, etc. from widgets.py
depends on app.setStyleSheet(STYLESHEET) being called once in GUI.py's
main block — otherwise these widgets still work, they just render
unstyled (plain grey boxes instead of the dark card/pill look).
"""

BG_DARK = "#12161c"
BG_PANEL = "#1a2029"
BG_PANEL_ALT = "#20273250"
ACCENT = "#3ddc97"
ACCENT_WARN = "#f2c14e"
ACCENT_DANGER = "#e5484d"
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

#PageTitle {{
    font-size: 20px;
    font-weight: 600;
}}

#PageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

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

QCheckBox {{
    spacing: 8px;
    padding: 4px 0px;
}}
"""
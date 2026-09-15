"""
widgets.py
Common, reusable UI components for WebSET. Every page (Dashboard, Passive
Scan, Active Scan, Manual Injection, Case Management, Reports, Settings)
should be built out of these instead of raw QPushButton/QLabel calls, so
the whole app stays visually consistent no matter who builds which page.

Sections:
    - Navigation      : make_nav_button
    - Layout           : page_header, Card, section_header
    - Buttons          : primary_button, secondary_button, danger_button, icon_button
    - Inputs           : LabeledInput, LabeledCombo, SearchBar
    - Data display     : StatCard, severity_pill, status_pill, DataTable
    - Feedback         : Banner, ConfirmDialog
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import theme


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
def make_nav_button(text: str, icon_char: str) -> QPushButton:
    """Checkable sidebar navigation button."""
    btn = QPushButton(f"  {icon_char}   {text}")
    btn.setObjectName("NavButton")
    btn.setCheckable(True)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(42)
    return btn


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def page_header(title: str, subtitle: str, action: QWidget = None) -> QFrame:
    """Top bar for a page: title + subtitle, with an optional action widget
    (e.g. a primary button) docked to the right."""
    frame = QFrame()
    frame.setObjectName("TopBar")
    frame.setMinimumHeight(64)

    layout = QHBoxLayout(frame)
    layout.setContentsMargins(24, 10, 24, 10)

    text_box = QVBoxLayout()
    text_box.setSpacing(2)
    title_lbl = QLabel(title)
    title_lbl.setObjectName("PageTitle")
    subtitle_lbl = QLabel(subtitle)
    subtitle_lbl.setObjectName("PageSubtitle")
    text_box.addWidget(title_lbl)
    text_box.addWidget(subtitle_lbl)

    layout.addLayout(text_box)
    layout.addStretch()
    if action is not None:
        layout.addWidget(action)

    return frame


class Card(QFrame):
    """A bordered, rounded panel. Use as a container for any grouped content
    (forms, tables, summaries) so it matches the dashboard's stat cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(10)

    def add(self, widget: QWidget):
        self.body.addWidget(widget)
        return widget


def section_header(text: str) -> QLabel:
    """Bold label used to divide a page into sections, e.g. 'Recent Findings'."""
    lbl = QLabel(text)
    lbl.setProperty("class", "SectionHeader")
    return lbl


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
def primary_button(text: str) -> QPushButton:
    """High-emphasis action, e.g. 'Start Scan', 'Save Case'. One per view, max."""
    btn = QPushButton(text)
    btn.setProperty("class", "Primary")
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(36)
    return btn


def secondary_button(text: str) -> QPushButton:
    """Lower-emphasis action, e.g. 'Cancel', 'Export'."""
    btn = QPushButton(text)
    btn.setProperty("class", "Secondary")
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(36)
    return btn


def danger_button(text: str) -> QPushButton:
    """Destructive/high-risk action, e.g. 'Delete Case', 'Run Active Scan'."""
    btn = QPushButton(text)
    btn.setProperty("class", "Primary")
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumHeight(36)
    btn.setStyleSheet(
        f"background-color: {theme.ACCENT_DANGER}; color: white;"
    )
    return btn


def icon_button(icon_char: str, tooltip: str = "") -> QPushButton:
    """Small square button for toolbars/table rows, e.g. a refresh or delete icon."""
    btn = QPushButton(icon_char)
    btn.setProperty("class", "Secondary")
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedSize(32, 32)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
class LabeledInput(QWidget):
    """A QLineEdit with a caption above it, e.g. 'Target URL'."""

    def __init__(self, label: str, placeholder: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        caption = QLabel(label)
        caption.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setMinimumHeight(34)
        self.field.setStyleSheet(
            f"background-color: {theme.BG_DARK}; border: 1px solid {theme.BORDER}; "
            f"border-radius: 6px; padding: 4px 10px;"
        )

        layout.addWidget(caption)
        layout.addWidget(self.field)

    def text(self) -> str:
        return self.field.text()

    def set_text(self, value: str):
        self.field.setText(value)


class LabeledCombo(QWidget):
    """A QComboBox with a caption above it, e.g. 'Severity'."""

    def __init__(self, label: str, options: list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        caption = QLabel(label)
        caption.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.combo = QComboBox()
        self.combo.addItems(options)
        self.combo.setMinimumHeight(34)
        self.combo.setStyleSheet(
            f"background-color: {theme.BG_DARK}; border: 1px solid {theme.BORDER}; "
            f"border-radius: 6px; padding: 4px 10px;"
        )

        layout.addWidget(caption)
        layout.addWidget(self.combo)

    def value(self) -> str:
        return self.combo.currentText()


class SearchBar(QWidget):
    """A search input with a magnifier prefix, for filtering tables of findings."""

    text_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "Search...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        self.setStyleSheet(
            f"background-color: {theme.BG_DARK}; border: 1px solid {theme.BORDER}; border-radius: 6px;"
        )
        self.setFixedHeight(34)

        icon = QLabel("🔍")
        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setStyleSheet("border: none; background: transparent;")
        self.field.textChanged.connect(self.text_changed.emit)

        layout.addWidget(icon)
        layout.addWidget(self.field)


# ---------------------------------------------------------------------------
# Data display
# ---------------------------------------------------------------------------
class StatCard(QFrame):
    """Small dashboard metric card, e.g. 'Critical Findings: 3'."""

    def __init__(self, label: str, value: str, accent: str = theme.ACCENT):
        super().__init__()
        self.setProperty("class", "Card")
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self.value_label = QLabel(value)
        self.value_label.setProperty("class", "CardValue")
        self.value_label.setStyleSheet(f"color: {accent};")

        caption = QLabel(label)
        caption.setProperty("class", "CardLabel")

        layout.addWidget(self.value_label)
        layout.addWidget(caption)

    def set_value(self, value: str):
        self.value_label.setText(value)


_SEVERITY_COLORS = {
    "Critical": theme.ACCENT_DANGER,
    "High": "#e07a3f",
    "Medium": theme.ACCENT_WARN,
    "Low": "#5fb0e0",
    "Info": theme.TEXT_MUTED,
}

_STATUS_COLORS = {
    "Open": theme.ACCENT_WARN,
    "Confirmed": theme.ACCENT_DANGER,
    "False Positive": theme.TEXT_MUTED,
    "Fixed": theme.ACCENT,
    "Ignored": theme.TEXT_MUTED,
}


def _pill(text: str, color: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "Pill")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {color}33; color: {color}; border: 1px solid {color}88;"
    )
    return lbl


def severity_pill(severity: str) -> QLabel:
    """Colored pill for Critical/High/Medium/Low/Info."""
    return _pill(severity, _SEVERITY_COLORS.get(severity, theme.TEXT_MUTED))


def status_pill(status: str) -> QLabel:
    """Colored pill for Open/Confirmed/False Positive/Fixed/Ignored."""
    return _pill(status, _STATUS_COLORS.get(status, theme.TEXT_MUTED))


class DataTable(QTableWidget):
    """Pre-styled table for findings/case lists. Pass column headers up front,
    then use set_rows() with a list of tuples to populate it."""

    def __init__(self, headers: list, parent=None):
        super().__init__(0, len(headers), parent)
        self.setHorizontalHeaderLabels(headers)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, len(headers)):
            self.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)

    def set_rows(self, rows: list):
        """rows: list of tuples. A cell value of QWidget (e.g. a pill) is embedded
        via setCellWidget; anything else becomes a QTableWidgetItem."""
        self.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            self.setRowHeight(r, 40)
            for c, value in enumerate(row_data):
                if isinstance(value, QWidget):
                    self.setCellWidget(r, c, value)
                else:
                    self.setItem(r, c, QTableWidgetItem(str(value)))


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
class Banner(QFrame):
    """Inline notification strip, e.g. scan-complete or error messages.
    kind: 'info' | 'success' | 'warning' | 'danger'"""

    _COLORS = {
        "info": "#5fb0e0",
        "success": theme.ACCENT,
        "warning": theme.ACCENT_WARN,
        "danger": theme.ACCENT_DANGER,
    }

    def __init__(self, text: str, kind: str = "info"):
        super().__init__()
        color = self._COLORS.get(kind, "#5fb0e0")
        self.setStyleSheet(
            f"background-color: {color}22; border: 1px solid {color}66; border-radius: 8px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-weight: 600; border: none; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


class ConfirmDialog(QDialog):
    """Reusable Yes/No confirmation, e.g. 'I am authorised to test this
    target' or 'Delete this case?'."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        msg = QLabel(message)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def ask(title: str, message: str, parent=None) -> bool:
        dlg = ConfirmDialog(title, message, parent)
        return dlg.exec_() == QDialog.Accepted
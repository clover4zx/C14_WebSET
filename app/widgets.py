"""
widgets.py
Common, reusable UI components. Pages should be built out of these
instead of raw QPushButton/QLabel calls, so every page looks
consistent no matter who builds it.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import theme


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def page_header(title: str, subtitle: str, action: QWidget = None) -> QFrame:
    frame = QFrame()
    layout = QHBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 10)

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
    """A bordered, rounded panel used to group related content."""

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
    lbl = QLabel(text)
    lbl.setProperty("class", "SectionHeader")
    return lbl


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
def primary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "Primary")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setMinimumHeight(36)
    return btn


def secondary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("class", "Secondary")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setMinimumHeight(36)
    return btn


def make_nav_button(label: str, icon: str = "") -> QPushButton:
    """A sidebar navigation button. Checkable, so the active page can
    stay highlighted (styled by #NavButton:checked in theme.py)."""
    text = f"{icon}  {label}" if icon else label
    btn = QPushButton(text)
    btn.setObjectName("NavButton")
    btn.setCheckable(True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
    """A QComboBox with a caption above it, e.g. 'Scan Profile'."""

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


def make_checkbox(label: str, checked: bool = False) -> QCheckBox:
    """A styled checkbox, for toggle options like 'Check HTTP Headers'."""
    box = QCheckBox(label)
    box.setChecked(checked)
    box.setCursor(Qt.CursorShape.PointingHandCursor)
    return box


class FileUploadBox(QWidget):
    """
    A file-upload row: a 'Browse...' button plus a label showing the
    chosen file's name. Used for things like letting the user attach a
    local HTML file for static analysis.

    file_selected(str) fires with just the file NAME (not the full path)
    whenever a file is chosen — that's what the backend team can connect
    to. The full path is available via self.file_path() if needed.

    file_filter controls what QFileDialog shows, e.g. "HTML Files (*.html *.htm)".
    """

    file_selected = pyqtSignal(str)

    def __init__(self, label: str, file_filter: str = "All Files (*)", parent=None):
        super().__init__(parent)
        self._file_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        caption = QLabel(label)
        caption.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        layout.addWidget(caption)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.browse_button = secondary_button("Browse...")
        self.browse_button.clicked.connect(self._on_browse)
        row.addWidget(self.browse_button)

        self.name_label = QLabel("No file selected")
        self.name_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")
        row.addWidget(self.name_label, stretch=1)

        layout.addLayout(row)

        self._file_filter = file_filter

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", self._file_filter)
        if not path:
            return  # user cancelled
        self._file_path = path
        file_name = path.split("/")[-1].split("\\")[-1]
        self.name_label.setText(file_name)
        self.name_label.setStyleSheet(f"color: {theme.TEXT_PRIMARY};")
        self.file_selected.emit(file_name)

    def file_name(self) -> str:
        """Just the file name, e.g. 'index.html'. Empty string if nothing chosen."""
        if not self._file_path:
            return ""
        return self._file_path.split("/")[-1].split("\\")[-1]

    def file_path(self) -> str:
        """The full path on disk. Empty string if nothing chosen."""
        return self._file_path


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
class Banner(QFrame):
    """Inline notification strip. kind: 'info' | 'success' | 'warning' | 'danger'"""

    _COLORS = {
        "info": theme.ACCENT_INFO,
        "success": theme.ACCENT,
        "warning": theme.ACCENT_WARN,
        "danger": theme.ACCENT_DANGER,
    }

    def __init__(self, text: str, kind: str = "info"):
        super().__init__()
        color = self._COLORS.get(kind, theme.ACCENT_INFO)
        # Qt reads 8-digit hex as #AARRGGBB, so use rgba() for transparency
        self.setStyleSheet(
            f"background-color: {theme.rgba(color, 34)}; "
            f"border: 1px solid {theme.rgba(color, 102)}; border-radius: 8px;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {color}; font-weight: 600; border: none; background: transparent;")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
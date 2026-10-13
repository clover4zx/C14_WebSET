"""
pages/settings_page.py
Shown when the "Settings" sidebar button is clicked: target scope,
authentication, and default scan configuration.

Layout:
    [ Target Scope               | Authentication & Network ]
    [ Scan Defaults                                         ]
    [ Storage & Logging                                     ]
    [ status banner            Restore Defaults | Save      ]

Pure front-end for now. Every setting lives in DEFAULTS below, which is
the single source of truth for the starting values. The backend team can:
    - read everything with get_settings()
    - load saved values into the form with apply_settings(dict)
    - listen for the settings_saved(dict) signal, emitted on every Save
    - ask is_target_allowed(url) before starting a scan
Nothing is written to disk here; persisting the dict is the backend's job.
"""

from urllib.parse import urlparse

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from app import theme
from app.widgets import (
    Banner,
    Card,
    LabeledCombo,
    LabeledInput,
    make_checkbox,
    page_header,
    primary_button,
    secondary_button,
    section_header,
)

SCAN_PROFILES = ["Quick", "Standard", "Thorough"]
LOG_LEVELS = ["Debug", "Info", "Warning", "Error"]
PROXY_SCHEMES = ("http://", "https://", "socks5://")

# The starting value of every setting. Restore Defaults puts the form back
# to exactly this; apply_settings() falls back to it for any missing key.
DEFAULTS = {
    "allowed_targets": ["localhost", "127.0.0.1", "dvwa.local", "juiceshop.local"],
    "restrict_to_allowed": True,
    "default_auth": "",
    "proxy": "",
    "user_agent": "WebSET/1.0",
    "scan_profile": "Standard",
    "timeout_s": 10,
    "max_pages": 25,
    "delay_ms": 250,
    "headless": True,
    "follow_redirects": True,
    "verify_tls": True,
    "db_path": "webset.db",
    "log_level": "Info",
}


class _LabeledTextArea(QWidget):
    """
    A multi-line text box with a caption above it, styled to match
    LabeledInput. Same text() / set_text() API as LabeledInput.
    (The Dynamic scan tab has an identical copy; if a third page needs one,
    move it into app/widgets.py.)
    """

    def __init__(self, label: str, placeholder: str = "", min_height: int = 90, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        caption = QLabel(label)
        caption.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px; font-weight: 600;")
        self.field = QPlainTextEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setMinimumHeight(min_height)
        self.field.setStyleSheet(
            f"background-color: {theme.BG_DARK}; color: {theme.TEXT_PRIMARY}; "
            f"border: 1px solid {theme.BORDER}; border-radius: 6px; padding: 4px 10px;"
        )

        layout.addWidget(caption)
        layout.addWidget(self.field)

    def text(self) -> str:
        return self.field.toPlainText()

    def set_text(self, value: str):
        self.field.setPlainText(value)


def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("MutedText")
    lbl.setWordWrap(True)
    return lbl


def _split_host_port(entry_or_url: str):
    """'http://dvwa.local:8080/x' / 'dvwa.local:8080' / 'dvwa.local' -> (host, port or None).
    Returns ('', None) if it can't be understood."""
    text = entry_or_url.strip()
    if not text:
        return "", None
    if "://" not in text:
        text = "//" + text
    try:
        parsed = urlparse(text)
        return (parsed.hostname or "").lower(), parsed.port
    except ValueError:   # e.g. a non-numeric or out-of-range port
        return "", None


class SettingsPage(QWidget):
    # Emitted with get_settings() every time Save succeeds.
    settings_saved = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(page_header(
            "Settings", "Target scope, authentication, and scan configuration"
        ))

        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        top_row.addWidget(self._build_scope_card(), 1)
        top_row.addWidget(self._build_auth_card(), 1)
        root.addLayout(top_row)

        root.addWidget(self._build_defaults_card())
        root.addWidget(self._build_storage_card())

        # --- status banner, updates on save / restore / validation problems ---
        self.status_banner = Banner("Using default settings. Nothing saved yet.", "info")
        root.addWidget(self.status_banner)

        # --- actions ---
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        self.restore_button = secondary_button("Restore Defaults")
        self.save_button = primary_button("Save Settings")
        self.restore_button.clicked.connect(self._on_restore)
        self.save_button.clicked.connect(self._on_save)
        actions_row.addWidget(self.restore_button)
        actions_row.addWidget(self.save_button)
        root.addLayout(actions_row)

        root.addStretch()

        self.apply_settings(DEFAULTS)

    # -----------------------------------------------------------------
    # Form
    # -----------------------------------------------------------------
    def _build_scope_card(self):
        card = Card()
        card.add(section_header("Target Scope"))
        card.add(_muted(
            "Only test systems you own or are explicitly authorised to test "
            "(e.g. DVWA, Juice Shop or your own lab)."
        ))

        self.allowed_targets_input = _LabeledTextArea(
            "Allowed Targets (one per line)",
            "dvwa.local\njuiceshop.local:3000\n*.lab.example.com",
            min_height=110,
        )
        card.add(self.allowed_targets_input)

        self.check_restrict = make_checkbox("Only allow scans of these targets", checked=True)
        card.add(self.check_restrict)
        return card

    def _build_auth_card(self):
        card = Card()
        card.add(section_header("Authentication & Network"))

        self.auth_input = LabeledInput(
            "Default Session Cookie / Auth Header (optional)",
            "e.g. PHPSESSID=abc123  or  Authorization: Bearer <token>",
        )
        card.add(self.auth_input)
        card.add(_muted("Saved in plain text. Use test-environment credentials only."))

        self.proxy_input = LabeledInput(
            "Proxy (optional)", "e.g. http://127.0.0.1:8080 to route via Burp / ZAP"
        )
        card.add(self.proxy_input)

        self.user_agent_input = LabeledInput("User-Agent", "WebSET/1.0")
        card.add(self.user_agent_input)
        return card

    def _build_defaults_card(self):
        card = Card()
        card.add(section_header("Scan Defaults"))
        card.add(_muted("Starting values for new scans. You can still change them per scan."))

        # The "1" after each widget is a stretch factor: all four get an
        # equal share of the row, and keep sharing it as the window resizes.
        row = QHBoxLayout()
        self.scan_profile_combo = LabeledCombo("Default Scan Profile", SCAN_PROFILES)
        self.timeout_input = LabeledInput("Request Timeout (s)", str(DEFAULTS["timeout_s"]))
        self.max_pages_input = LabeledInput("Max Pages to Crawl", str(DEFAULTS["max_pages"]))
        self.delay_input = LabeledInput("Delay Between Requests (ms)", str(DEFAULTS["delay_ms"]))
        for widget in (
            self.scan_profile_combo,
            self.timeout_input,
            self.max_pages_input,
            self.delay_input,
        ):
            row.addWidget(widget, 1)
        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)

        self.check_headless = make_checkbox("Run browser headless", checked=True)
        self.check_follow_redirects = make_checkbox("Follow redirects", checked=True)
        self.check_verify_tls = make_checkbox("Verify TLS certificates", checked=True)
        checks_row = QHBoxLayout()
        checks_row.addWidget(self.check_headless)
        checks_row.addWidget(self.check_follow_redirects)
        checks_row.addWidget(self.check_verify_tls)
        checks_row.addStretch()
        checks_wrap = QWidget()
        checks_wrap.setLayout(checks_row)
        card.add(checks_wrap)
        return card

    def _build_storage_card(self):
        card = Card()
        card.add(section_header("Storage & Logging"))

        row = QHBoxLayout()
        self.db_path_input = LabeledInput("Results Database (SQLite file)", DEFAULTS["db_path"])
        self.log_level_combo = LabeledCombo("Log Level", LOG_LEVELS)
        row.addWidget(self.db_path_input, 2)
        row.addWidget(self.log_level_combo, 1)
        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)
        return card

    # -----------------------------------------------------------------
    # Handlers
    # -----------------------------------------------------------------
    def _on_restore(self):
        self.apply_settings(DEFAULTS)
        self._set_banner("Defaults restored. Click Save Settings to keep them.", "info")

    def _on_save(self):
        error = self._validate()
        if error:
            self._set_banner(error, "warning")
            return

        settings = self.get_settings()
        self.settings_saved.emit(settings)
        self._set_banner(
            f"Settings saved ({len(settings['allowed_targets'])} allowed target(s), "
            f"default profile: {settings['scan_profile']}).",
            "success",
        )

    def _validate(self) -> str:
        """Returns a message describing the first problem found, or '' if the form is OK."""
        targets = self.allowed_targets()
        if self.check_restrict.isChecked() and not targets:
            return "Add at least one allowed target, or untick 'Only allow scans of these targets'."
        for entry in targets:
            host, _port = _split_host_port(entry)
            if not host or " " in entry:
                return f"'{entry}' isn't a valid target. Use a host name, IP, host:port or URL."

        for label, box, minimum in (
            ("Request timeout", self.timeout_input, 1),
            ("Max pages", self.max_pages_input, 1),
            ("Delay", self.delay_input, 0),
        ):
            text = box.text().strip()
            if text and (not text.isdigit() or int(text) < minimum):
                return f"{label} must be a whole number of at least {minimum}."

        proxy = self.proxy_input.text().strip()
        if proxy and not proxy.lower().startswith(PROXY_SCHEMES):
            return "Proxy must start with http://, https:// or socks5://."
        return ""

    def _set_banner(self, text: str, kind: str):
        parent_layout = self.status_banner.parentWidget().layout()
        idx = parent_layout.indexOf(self.status_banner)
        self.status_banner.setParent(None)
        new_banner = Banner(text, kind)
        parent_layout.insertWidget(idx, new_banner)
        self.status_banner = new_banner

    # -----------------------------------------------------------------
    # Helpers for the backend team
    # -----------------------------------------------------------------
    def allowed_targets(self) -> list:
        """The allowed-targets box as a clean list (blank lines dropped)."""
        lines = (line.strip() for line in self.allowed_targets_input.text().splitlines())
        return [line for line in lines if line]

    def is_target_allowed(self, url: str) -> bool:
        """True if a scan of `url` is permitted by the current form values.

        Always True when 'Only allow scans of these targets' is off. An entry
        matches on host name, so 'dvwa.local' allows http://dvwa.local/any/page.
        An entry with a port ('dvwa.local:8080') only matches that port, and
        '*.lab.example.com' matches any sub-domain of lab.example.com."""
        if not self.check_restrict.isChecked():
            return True
        host, port = _split_host_port(url)
        if not host:
            return False
        for entry in self.allowed_targets():
            entry_host, entry_port = _split_host_port(entry)
            if not entry_host:
                continue
            if entry_port is not None and entry_port != port:
                continue
            if entry_host == host:
                return True
            if entry_host.startswith("*.") and host.endswith(entry_host[1:]):
                return True
        return False

    @staticmethod
    def _to_int(text: str, default: int) -> int:
        text = text.strip()
        return int(text) if text.isdigit() else default

    def get_settings(self) -> dict:
        """Everything on this page as one plain dict. Same keys as DEFAULTS."""
        return {
            "allowed_targets": self.allowed_targets(),
            "restrict_to_allowed": self.check_restrict.isChecked(),
            "default_auth": self.auth_input.text().strip(),
            "proxy": self.proxy_input.text().strip(),
            "user_agent": self.user_agent_input.text().strip() or DEFAULTS["user_agent"],
            "scan_profile": self.scan_profile_combo.value(),
            "timeout_s": self._to_int(self.timeout_input.text(), DEFAULTS["timeout_s"]),
            "max_pages": self._to_int(self.max_pages_input.text(), DEFAULTS["max_pages"]),
            "delay_ms": self._to_int(self.delay_input.text(), DEFAULTS["delay_ms"]),
            "headless": self.check_headless.isChecked(),
            "follow_redirects": self.check_follow_redirects.isChecked(),
            "verify_tls": self.check_verify_tls.isChecked(),
            "db_path": self.db_path_input.text().strip() or DEFAULTS["db_path"],
            "log_level": self.log_level_combo.value(),
        }

    def apply_settings(self, settings: dict):
        """Fill the form from a dict (e.g. loaded from the database). Any
        missing key falls back to its default, so partial dicts are fine."""
        values = {**DEFAULTS, **settings}
        self.allowed_targets_input.set_text("\n".join(values["allowed_targets"]))
        self.check_restrict.setChecked(values["restrict_to_allowed"])
        self.auth_input.set_text(values["default_auth"])
        self.proxy_input.set_text(values["proxy"])
        self.user_agent_input.set_text(values["user_agent"])
        self.scan_profile_combo.combo.setCurrentText(values["scan_profile"])
        self.timeout_input.set_text(str(values["timeout_s"]))
        self.max_pages_input.set_text(str(values["max_pages"]))
        self.delay_input.set_text(str(values["delay_ms"]))
        self.check_headless.setChecked(values["headless"])
        self.check_follow_redirects.setChecked(values["follow_redirects"])
        self.check_verify_tls.setChecked(values["verify_tls"])
        self.db_path_input.set_text(values["db_path"])
        self.log_level_combo.combo.setCurrentText(values["log_level"])

    # -----------------------------------------------------------------
    # What the backend team can read off this page once it's wired up
    # (or just call self.get_settings() to get all of it as a dict):
    #
    #   self.allowed_targets()                  -> list[str], one entry per line
    #   self.check_restrict.isChecked()         -> bool, enforce the allow-list
    #   self.auth_input.text()                  -> str, default cookie / auth header
    #   self.proxy_input.text()                 -> str, proxy URL ("" if none)
    #   self.user_agent_input.text()            -> str
    #   self.scan_profile_combo.value()         -> str, "Quick"/"Standard"/"Thorough"
    #   self.timeout_input.text()               -> str, seconds (parse to int)
    #   self.max_pages_input.text()             -> str, crawl limit (parse to int)
    #   self.delay_input.text()                 -> str, ms between requests (parse to int)
    #   self.check_headless.isChecked()         -> bool
    #   self.check_follow_redirects.isChecked() -> bool
    #   self.check_verify_tls.isChecked()       -> bool
    #   self.db_path_input.text()               -> str, SQLite file path
    #   self.log_level_combo.value()            -> str, "Debug"/"Info"/"Warning"/"Error"
    #
    # To persist: connect to settings_saved(dict) and write the dict to the
    # database/config file. On start-up, read it back and call
    # apply_settings(saved) so the form shows the saved values.
    # -----------------------------------------------------------------
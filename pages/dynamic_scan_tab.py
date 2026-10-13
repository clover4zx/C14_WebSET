"""
pages/dynamic_scan_tab.py
The "Dynamic" tab inside the New Scan page. Built the same way as
static_scan_tab.py: a scrollable form made of Cards and the shared
widgets from app/widgets.py, styled entirely by app/theme.py.

Pure front-end for now — every input is exposed as a plain attribute so
the backend team can read values off this page without touching the UI
code (see get_config() and the notes at the bottom of this file).

Nothing in here runs a real scan yet — Run Dynamic Scan validates the
form and shows a banner confirming what would be sent to the backend.
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from app import theme
from app.widgets import (
    Banner,
    Card,
    FileUploadBox,
    LabeledCombo,
    LabeledInput,
    make_checkbox,
    make_scrollable,
    primary_button,
    secondary_button,
    section_header,
)


class _LabeledTextArea(QWidget):
    """
    A multi-line text box with a caption above it, styled to match
    LabeledInput. Used for the manual payload, which can be several lines.
    Has the same text() / set_text() / reset() methods as LabeledInput, so
    the form's Reset logic treats it like every other input.
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

    def reset(self):
        """Back to empty (the placeholder text shows again)."""
        self.field.clear()


class DynamicScanTab(QWidget):
    # Defaults used when a numeric box is left empty. They match the
    # placeholder text shown in each box.
    DEFAULT_TIMEOUT = 10
    DEFAULT_MAX_PAGES = 25
    DEFAULT_DELAY_MS = 250

    CUSTOM_PAYLOAD_SOURCE = "Custom file"

    def __init__(self):
        super().__init__()

        # Everything in the form is built inside `content`. make_scrollable()
        # wraps it in a scroll area: if the window is too short, a scrollbar
        # appears instead of the form being squashed or running off-screen.
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scrollable(content))

        # --- target ---
        root.addWidget(section_header("Target"))
        target_card = Card()
        self.target_input = LabeledInput("Target URL", "https://target.local")
        target_card.add(self.target_input)
        self.auth_input = LabeledInput(
            "Session Cookie / Auth Header (optional)",
            "e.g. PHPSESSID=abc123  or  Authorization: Bearer <token>",
        )
        target_card.add(self.auth_input)

        # Dynamic scans send real attack payloads, so the user has to
        # explicitly confirm they are allowed to test this target.
        self.check_authorized = make_checkbox(
            "I confirm I am authorised to test this target "
            "(e.g. DVWA, Juice Shop or my own test environment)"
        )
        target_card.add(self.check_authorized)
        root.addWidget(target_card)

        # --- scan configuration ---
        root.addWidget(section_header("Scan Configuration"))
        config_card = Card()

        # The "1" after each widget is a stretch factor: all four get an
        # equal share of the row, and keep sharing it as the window resizes.
        options_row = QHBoxLayout()
        self.timeout_input = LabeledInput("Request Timeout (s)", str(self.DEFAULT_TIMEOUT))
        self.scan_profile_combo = LabeledCombo(
            "Scan Profile", ["Quick", "Standard", "Thorough"]
        )
        self.max_pages_input = LabeledInput("Max Pages to Crawl", str(self.DEFAULT_MAX_PAGES))
        self.delay_input = LabeledInput("Delay Between Requests (ms)", str(self.DEFAULT_DELAY_MS))
        options_row.addWidget(self.timeout_input, 1)
        options_row.addWidget(self.scan_profile_combo, 1)
        options_row.addWidget(self.max_pages_input, 1)
        options_row.addWidget(self.delay_input, 1)
        options_wrap = QWidget()
        options_wrap.setLayout(options_row)
        config_card.add(options_wrap)

        # Browser options (the backend drives a Selenium browser)
        self.check_headless = make_checkbox("Run browser headless", checked=True)
        self.check_follow_redirects = make_checkbox("Follow redirects", checked=True)
        browser_row = QHBoxLayout()
        browser_row.addWidget(self.check_headless)
        browser_row.addWidget(self.check_follow_redirects)
        browser_row.addStretch()
        browser_wrap = QWidget()
        browser_wrap.setLayout(browser_row)
        config_card.add(browser_wrap)

        # Which vulnerability classes to test for — example options; add or
        # remove as the real dynamic-scan feature set gets decided.
        config_card.add(section_header("Vulnerability Checks"))

        checks_row_1 = QHBoxLayout()
        self.check_sqli = make_checkbox("SQL Injection", checked=True)
        self.check_xss = make_checkbox("Cross-Site Scripting (XSS)", checked=True)
        self.check_path_traversal = make_checkbox("Path Traversal / LFI", checked=True)
        self.check_open_redirect = make_checkbox("Open Redirect", checked=True)
        for box in (
            self.check_sqli,
            self.check_xss,
            self.check_path_traversal,
            self.check_open_redirect,
        ):
            checks_row_1.addWidget(box)
        checks_row_1.addStretch()
        checks_wrap_1 = QWidget()
        checks_wrap_1.setLayout(checks_row_1)
        config_card.add(checks_wrap_1)

        # Command injection is the most intrusive check, so it starts off.
        checks_row_2 = QHBoxLayout()
        self.check_command_injection = make_checkbox("Command Injection")
        self.check_csrf = make_checkbox("CSRF Token Checks", checked=True)
        checks_row_2.addWidget(self.check_command_injection)
        checks_row_2.addWidget(self.check_csrf)
        checks_row_2.addStretch()
        checks_wrap_2 = QWidget()
        checks_wrap_2.setLayout(checks_row_2)
        config_card.add(checks_wrap_2)

        root.addWidget(config_card)

        # --- payloads ---
        root.addWidget(section_header("Payloads"))
        payload_card = Card()
        self.payload_source_combo = LabeledCombo(
            "Payload Source", ["Built-in", "SecLists", self.CUSTOM_PAYLOAD_SOURCE]
        )
        self.payload_source_combo.combo.currentTextChanged.connect(self._on_payload_source_changed)
        payload_card.add(self.payload_source_combo)

        # Only shown when "Custom file" is chosen in the dropdown above.
        self.payload_file_upload = FileUploadBox(
            "Payload Wordlist", file_filter="Text Files (*.txt *.lst);;All Files (*)"
        )
        self.payload_file_upload.file_selected.connect(self._on_payload_file_selected)
        payload_card.add(self.payload_file_upload)
        self.payload_file_upload.setVisible(False)
        root.addWidget(payload_card)

        # --- manual payload injection ---
        root.addWidget(section_header("Manual Payload Injection (optional)"))
        manual_card = Card()

        manual_row = QHBoxLayout()
        self.manual_method_combo = LabeledCombo("HTTP Method", ["GET", "POST", "PUT"])
        self.manual_param_input = LabeledInput("Parameter / Field", "e.g. id, q, username")
        manual_row.addWidget(self.manual_method_combo, 1)
        manual_row.addWidget(self.manual_param_input, 2)
        manual_wrap = QWidget()
        manual_wrap.setLayout(manual_row)
        manual_card.add(manual_wrap)

        self.manual_payload_input = _LabeledTextArea(
            "Payload", "e.g. ' OR '1'='1   or   <script>alert(1)</script>"
        )
        manual_card.add(self.manual_payload_input)
        root.addWidget(manual_card)

        # --- status banner, updates when a file is picked or scan is run ---
        self.status_banner = Banner("No scan run yet.", "info")
        root.addWidget(self.status_banner)

        # --- actions ---
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        self.reset_button = secondary_button("Reset")
        self.run_button = primary_button("Run Dynamic Scan")
        self.reset_button.clicked.connect(self._on_reset)
        self.run_button.clicked.connect(self._on_run_scan)
        actions_row.addWidget(self.reset_button)
        actions_row.addWidget(self.run_button)
        root.addLayout(actions_row)

        root.addStretch()

        # Every control that Reset puts back to its starting state. Each of
        # these has a reset() method (see app/widgets.py). If you add a new
        # input to the form later, add it to this list and Reset covers it.
        self._form_widgets = [
            self.target_input,
            self.auth_input,
            self.check_authorized,
            self.timeout_input,
            self.scan_profile_combo,
            self.max_pages_input,
            self.delay_input,
            self.check_headless,
            self.check_follow_redirects,
            self.check_sqli,
            self.check_xss,
            self.check_path_traversal,
            self.check_open_redirect,
            self.check_command_injection,
            self.check_csrf,
            self.payload_source_combo,
            self.payload_file_upload,
            self.manual_method_combo,
            self.manual_param_input,
            self.manual_payload_input,
        ]

    # -----------------------------------------------------------------
    # Handlers — placeholder behaviour for now. The backend team can
    # replace _on_run_scan's body with a real call, using get_config()
    # (or reading the attributes documented below directly).
    # -----------------------------------------------------------------
    def _on_payload_source_changed(self, source: str):
        self.payload_file_upload.setVisible(source == self.CUSTOM_PAYLOAD_SOURCE)

    def _on_payload_file_selected(self, file_name: str):
        self._set_banner(f"Selected payload file: {file_name}", "success")

    def _on_reset(self):
        for widget in self._form_widgets:
            widget.reset()
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        error = self._validate()
        if error:
            self._set_banner(error, "warning")
            return

        config = self.get_config()
        self._set_banner(
            f"Dynamic scan requested for '{config['target_url']}' "
            f"(profile: {config['scan_profile']}, "
            f"{len(config['checks'])} check(s), "
            f"payloads: {config['payload_source']}).",
            "success",
        )

    def _validate(self) -> str:
        """Returns a message describing the first problem found, or '' if the form is OK."""
        target = self.target_input.text().strip()
        if not target:
            return "Enter a target URL first."
        if not target.lower().startswith(("http://", "https://")):
            return "Target URL must start with http:// or https://."
        if not self.check_authorized.isChecked():
            return "Confirm you are authorised to test this target before running a dynamic scan."
        if not self.selected_checks():
            return "Select at least one vulnerability check."
        for label, box, minimum in (
            ("Request timeout", self.timeout_input, 1),
            ("Max pages", self.max_pages_input, 1),
            ("Delay", self.delay_input, 0),
        ):
            text = box.text().strip()
            if text and (not text.isdigit() or int(text) < minimum):
                return f"{label} must be a whole number of at least {minimum}."
        if (
            self.payload_source_combo.value() == self.CUSTOM_PAYLOAD_SOURCE
            and not self.payload_file_upload.file_path()
        ):
            return "Choose a payload wordlist file, or switch the payload source."
        if self.manual_payload_input.text().strip() and not self.manual_param_input.text().strip():
            return "Enter the parameter/field to inject the manual payload into."
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
    def selected_checks(self) -> list:
        """Names of the ticked vulnerability checks, e.g. ['sqli', 'xss']."""
        options = (
            ("sqli", self.check_sqli),
            ("xss", self.check_xss),
            ("path_traversal", self.check_path_traversal),
            ("open_redirect", self.check_open_redirect),
            ("command_injection", self.check_command_injection),
            ("csrf", self.check_csrf),
        )
        return [name for name, box in options if box.isChecked()]

    @staticmethod
    def _to_int(text: str, default: int) -> int:
        text = text.strip()
        return int(text) if text.isdigit() else default

    def get_config(self) -> dict:
        """Everything on this page as one plain dict, ready to hand to the scanner."""
        return {
            "target_url": self.target_input.text().strip(),
            "auth": self.auth_input.text().strip(),
            "authorised": self.check_authorized.isChecked(),
            "timeout_s": self._to_int(self.timeout_input.text(), self.DEFAULT_TIMEOUT),
            "scan_profile": self.scan_profile_combo.value(),
            "max_pages": self._to_int(self.max_pages_input.text(), self.DEFAULT_MAX_PAGES),
            "delay_ms": self._to_int(self.delay_input.text(), self.DEFAULT_DELAY_MS),
            "headless": self.check_headless.isChecked(),
            "follow_redirects": self.check_follow_redirects.isChecked(),
            "checks": self.selected_checks(),
            "payload_source": self.payload_source_combo.value(),
            "payload_file": self.payload_file_upload.file_path(),
            "manual_injection": {
                "method": self.manual_method_combo.value(),
                "parameter": self.manual_param_input.text().strip(),
                "payload": self.manual_payload_input.text(),
            },
        }

    # -----------------------------------------------------------------
    # What the backend team can read off this page once it's wired up
    # (or just call self.get_config() to get all of it as a dict):
    #
    #   self.target_input.text()               -> str, the target URL
    #   self.auth_input.text()                 -> str, cookie / auth header ("" if none)
    #   self.check_authorized.isChecked()      -> bool, user confirmed they may test it
    #   self.timeout_input.text()              -> str, timeout in seconds (parse to int)
    #   self.scan_profile_combo.value()        -> str, "Quick"/"Standard"/"Thorough"
    #   self.max_pages_input.text()            -> str, crawl page limit (parse to int)
    #   self.delay_input.text()                -> str, ms between requests (parse to int)
    #   self.check_headless.isChecked()        -> bool, run Selenium headless
    #   self.check_follow_redirects.isChecked()-> bool
    #   self.check_sqli.isChecked()            -> bool
    #   self.check_xss.isChecked()             -> bool
    #   self.check_path_traversal.isChecked()  -> bool
    #   self.check_open_redirect.isChecked()   -> bool
    #   self.check_command_injection.isChecked()-> bool (off by default, most intrusive)
    #   self.check_csrf.isChecked()            -> bool
    #   self.payload_source_combo.value()      -> str, "Built-in"/"SecLists"/"Custom file"
    #   self.payload_file_upload.file_path()   -> str, wordlist path ("" if none chosen)
    #   self.manual_method_combo.value()       -> str, "GET"/"POST"/"PUT"
    #   self.manual_param_input.text()         -> str, parameter/field to inject into
    #   self.manual_payload_input.text()       -> str, the manual payload (can be multi-line)
    #
    # To hook in a real scan: replace the body of _on_run_scan with a call
    # into the scanning backend, passing get_config(). _validate() already
    # runs first, so the config it receives is known to be well-formed.
    # -----------------------------------------------------------------
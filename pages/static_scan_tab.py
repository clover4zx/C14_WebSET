"""
pages/static_scan_tab.py
The "Static" tab inside the New Scan page. Pure front-end for now —
every input here is exposed as a plain attribute/method so the backend
team can read values off this page without needing to touch the UI
code at all (see the bottom of this file for exactly what's exposed).

Nothing in here runs a real scan yet — Run Static Scan currently just
shows a banner confirming what would be sent to the backend.
"""

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from app.widgets import (
    Banner,
    Card,
    FileUploadBox,
    LabeledCombo,
    LabeledInput,
    make_checkbox,
    primary_button,
    secondary_button,
    section_header,
)


class StaticScanTab(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # --- target ---
        root.addWidget(section_header("Target"))
        target_card = Card()
        self.target_input = LabeledInput("Target URL", "https://target.local")
        target_card.add(self.target_input)
        root.addWidget(target_card)

        # --- example configuration options ---
        root.addWidget(section_header("Scan Configuration"))
        config_card = Card()

        options_row = QHBoxLayout()
        self.crawl_depth_input = LabeledInput("Crawl Depth", "3")
        self.timeout_input = LabeledInput("Request Timeout (s)", "10")
        self.scan_profile_combo = LabeledCombo(
            "Scan Profile", ["Quick", "Standard", "Thorough"]
        )
        options_row.addWidget(self.crawl_depth_input)
        options_row.addWidget(self.timeout_input)
        options_row.addWidget(self.scan_profile_combo)
        options_wrap = QWidget()
        options_wrap.setLayout(options_row)
        config_card.add(options_wrap)

        # Checkboxes for which checks to run — example options; add/remove
        # as the real static-scan feature set gets decided.
        checks_label = section_header("Checks to Run")
        config_card.add(checks_label)

        checks_row = QHBoxLayout()
        self.check_headers = make_checkbox("HTTP Headers", checked=True)
        self.check_tls = make_checkbox("TLS / SSL", checked=True)
        self.check_components = make_checkbox("Outdated Components", checked=True)
        self.check_exposed_files = make_checkbox("Exposed Files", checked=True)
        checks_row.addWidget(self.check_headers)
        checks_row.addWidget(self.check_tls)
        checks_row.addWidget(self.check_components)
        checks_row.addWidget(self.check_exposed_files)
        checks_row.addStretch()
        checks_wrap = QWidget()
        checks_wrap.setLayout(checks_row)
        config_card.add(checks_wrap)

        root.addWidget(config_card)

        # --- HTML file upload ---
        root.addWidget(section_header("Upload Target Page (optional)"))
        upload_card = Card()
        self.file_upload = FileUploadBox(
            "HTML File", file_filter="HTML Files (*.html *.htm)"
        )
        self.file_upload.file_selected.connect(self._on_file_selected)
        upload_card.add(self.file_upload)
        root.addWidget(upload_card)

        # --- status banner, updates when a file is picked or scan is run ---
        self.status_banner = Banner("No file selected. No scan run yet.", "info")
        root.addWidget(self.status_banner)

        # --- actions ---
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        self.reset_button = secondary_button("Reset")
        self.run_button = primary_button("Run Static Scan")
        self.reset_button.clicked.connect(self._on_reset)
        self.run_button.clicked.connect(self._on_run_scan)
        actions_row.addWidget(self.reset_button)
        actions_row.addWidget(self.run_button)
        root.addLayout(actions_row)

        root.addStretch()

    # -----------------------------------------------------------------
    # Handlers — placeholder behaviour for now. The backend team can
    # replace _on_run_scan's body with a real call, reading the same
    # values documented below.
    # -----------------------------------------------------------------
    def _on_file_selected(self, file_name: str):
        self._set_banner(f"Selected file: {file_name}", "success")

    def _on_reset(self):
        self.target_input.set_text("")
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        target = self.target_input.text().strip()
        if not target and not self.file_upload.file_name():
            self._set_banner("Enter a target URL or upload a file first.", "warning")
            return
        self._set_banner(
            f"Static scan requested for '{target or self.file_upload.file_name()}' "
            f"(profile: {self.scan_profile_combo.value()}).",
            "success",
        )

    def _set_banner(self, text: str, kind: str):
        parent_layout = self.status_banner.parentWidget().layout()
        idx = parent_layout.indexOf(self.status_banner)
        self.status_banner.setParent(None)
        new_banner = Banner(text, kind)
        parent_layout.insertWidget(idx, new_banner)
        self.status_banner = new_banner

    # -----------------------------------------------------------------
    # What the backend team can read off this page once it's wired up:
    #
    #   self.target_input.text()            -> str, the target URL
    #   self.crawl_depth_input.text()       -> str, crawl depth (parse to int)
    #   self.timeout_input.text()           -> str, timeout in seconds (parse to int)
    #   self.scan_profile_combo.value()     -> str, one of "Quick"/"Standard"/"Thorough"
    #   self.check_headers.isChecked()      -> bool
    #   self.check_tls.isChecked()          -> bool
    #   self.check_components.isChecked()   -> bool
    #   self.check_exposed_files.isChecked()-> bool
    #   self.file_upload.file_name()        -> str, e.g. "index.html" ("" if none chosen)
    #   self.file_upload.file_path()        -> str, full path on disk ("" if none chosen)
    #
    # To hook in a real scan: replace the body of _on_run_scan with a
    # call into the scanning backend, passing the values above.
    # -----------------------------------------------------------------
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
    make_scrollable,
    primary_button,
    secondary_button,
    section_header,
)


class StaticScanTab(QWidget):
    def __init__(self):
        super().__init__()

        # Everything in the form is built inside `content`. make_scrollable()
        # wraps it in a scroll area: if the window is too short, a scrollbar
        # appears instead of the form being squashed or running off-screen.
        # Width still follows the window, so inputs stretch sideways as it grows.
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
        root.addWidget(target_card)

        # --- example configuration options ---
        root.addWidget(section_header("Scan Configuration"))
        config_card = Card()

        # The "1" after each widget is a stretch factor: both get an equal
        # share of the row, and keep sharing it as the window is resized.
        options_row = QHBoxLayout()
        self.timeout_input = LabeledInput("Request Timeout (s)", "10")
        self.scan_profile_combo = LabeledCombo(
            "Scan Profile", ["Quick", "Standard", "Thorough"]
        )
        options_row.addWidget(self.timeout_input, 1)
        options_row.addWidget(self.scan_profile_combo, 1)
        options_wrap = QWidget()
        options_wrap.setLayout(options_row)
        config_card.add(options_wrap)

        # Checkboxes for which checks to run — example options; add/remove
        # as the real static-scan feature set gets decided.
        checks_label = section_header("Checks to Run")
        config_card.add(checks_label)

        checks_row = QHBoxLayout()
        self.check_headers = make_checkbox("Hardcoded Secrets", checked=True)
        self.check_tls = make_checkbox("Risky Code Patterns", checked=True)
        self.check_components = make_checkbox("Dependency Versions", checked=True)
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
        root.addWidget(section_header("Upload Source Code Archive"))
        upload_card = Card()
        self.file_upload = FileUploadBox(
            "Source Code ZIP", file_filter="ZIP Archives (*.zip)"
        )
        self.file_upload.file_selected.connect(self._on_file_selected)
        upload_card.add(self.file_upload)
        root.addWidget(upload_card)

        # --- status banner, updates when a file is picked or scan is run ---
        self.status_banner = Banner("Upload a source-code ZIP to run static analysis. The scanner does not execute uploaded code.", "info")
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

        # Every control that Reset puts back to its starting state. Each of
        # these has a reset() method (see app/widgets.py). If you add a new
        # input to the form later, add it to this list and Reset covers it.
        self._form_widgets = [
            self.target_input,
            self.timeout_input,
            self.scan_profile_combo,
            self.check_headers,
            self.check_tls,
            self.check_components,
            self.check_exposed_files,
            self.file_upload,
        ]

    # -----------------------------------------------------------------
    # Handlers: the source ZIP is passed to the integrated static analyzer.
    # -----------------------------------------------------------------
    def _on_file_selected(self, file_name: str):
        self._set_banner(f"Selected file: {file_name}", "success")

    def _on_reset(self):
        for widget in self._form_widgets:
            widget.reset()
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        zip_path = self.file_upload.file_path()
        if not zip_path:
            self._set_banner("Choose a source-code ZIP file first.", "warning")
            return
        if not zip_path.lower().endswith(".zip"):
            self._set_banner("The static analyzer accepts .zip archives only.", "warning")
            return
        from pages.scan_worker import ScanWorker
        self.run_button.setEnabled(False)
        self._set_banner("Static scan running… uploaded code will not be executed.", "info")
        self._worker = ScanWorker("static", zip_path, self)
        self._worker.finished_with_result.connect(self._on_scan_finished)
        self._worker.start()

    def _on_scan_finished(self, result):
        from pages.scan_results_dialog import ScanResultsDialog
        self.run_button.setEnabled(True)
        if result.get("ok"):
            self._set_banner(f"Static scan completed: {result.get('total_findings', 0)} finding(s).", "success")
        else:
            self._set_banner(f"Static scan failed: {result.get('error', 'Unknown error')}", "danger")
        ScanResultsDialog(result, self).exec()

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
    #   self.timeout_input.text()           -> str, timeout in seconds (parse to int)
    #   self.scan_profile_combo.value()     -> str, one of "Quick"/"Standard"/"Thorough"
    #   self.check_headers.isChecked()      -> bool
    #   self.check_tls.isChecked()          -> bool
    #   self.check_components.isChecked()   -> bool
    #   self.check_exposed_files.isChecked()-> bool
    #   self.file_upload.file_name()        -> str, e.g. "source.zip" ("" if none chosen)
    #   self.file_upload.file_path()        -> str, full path on disk ("" if none chosen)
    #
    # The current integrated static backend scans ZIP source archives; it does
    # not use the target URL, timeout, or individual checkbox options yet.
    #
    # The current implementation invokes pages.webset_core.run_static_scan().
    # -----------------------------------------------------------------
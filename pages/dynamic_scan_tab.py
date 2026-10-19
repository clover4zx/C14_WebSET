"""
pages/dynamic_scan_tab.py
The "Dynamic" tab inside the New Scan page.

Runs a PASSIVE (read-only) scan of a live website: you enter a URL, confirm
you're authorised to test it, and it fetches and analyses the page - looking
for outdated libraries, insecure forms, hardcoded secrets, risky links, etc.
It does NOT send attack payloads; it only reads the page.

Results are shown as a teal "Live Website Scan" report.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.widgets import (
    Banner,
    Card,
    LabeledInput,
    make_checkbox,
    make_scrollable,
    primary_button,
    secondary_button,
    section_header,
)

from pages.webset_core import run_passive_scan
from data.scan_history_data import add_scan_result


SEVERITY_COLORS = {
    "HIGH": "#c0392b",
    "MEDIUM": "#e67e22",
    "LOW": "#2980b9",
    "INFO": "#7f8c8d",
}


def _severity_chip(severity: str) -> QLabel:
    chip = QLabel(severity)
    chip.setStyleSheet(
        f"background:{SEVERITY_COLORS.get(severity, '#7f8c8d')};color:white;"
        "font-weight:bold;padding:3px 0;border-radius:4px;"
    )
    chip.setFixedWidth(78)
    chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return chip


def _finding_card(finding: dict, location_text: str) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(
        "QFrame{background:rgba(255,255,255,0.05);"
        "border:1px solid rgba(255,255,255,0.12);border-radius:6px;}"
        "QLabel{border:none;background:transparent;}"
    )
    row = QHBoxLayout(frame)
    row.setContentsMargins(10, 8, 10, 8)
    row.setSpacing(10)

    row.addWidget(_severity_chip(finding["severity"]), 0, Qt.AlignmentFlag.AlignTop)

    col = QVBoxLayout()
    col.setSpacing(2)
    title = QLabel(finding["category"])
    title.setStyleSheet("font-weight:bold;")
    loc = QLabel(location_text)
    loc.setWordWrap(True)
    loc.setStyleSheet("color:#9aa0b5;font-family:Consolas,'Courier New',monospace;")
    desc = QLabel(finding.get("description", ""))
    desc.setWordWrap(True)
    desc.setStyleSheet("color:#c7ccda;")
    col.addWidget(title)
    col.addWidget(loc)
    col.addWidget(desc)
    row.addLayout(col, 1)
    return frame


class DynamicScanTab(QWidget):
    DEFAULT_TIMEOUT = 10

    def __init__(self):
        super().__init__()

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scrollable(content))

        # --- target ---
        root.addWidget(section_header("Target (live website)"))
        target_card = Card()
        self.target_input = LabeledInput("Target URL", "http://127.0.0.1:8000/")
        target_card.add(self.target_input)

        # The user must confirm they're allowed to scan this target.
        self.check_authorized = make_checkbox(
            "I confirm I am authorised to test this target "
            "(e.g. my local demo page, DVWA or Juice Shop)"
        )
        target_card.add(self.check_authorized)
        root.addWidget(target_card)

        # --- scan settings (just one simple option) ---
        root.addWidget(section_header("Scan Settings"))
        settings_card = Card()
        self.timeout_input = LabeledInput("Request Timeout (seconds)", str(self.DEFAULT_TIMEOUT))
        settings_card.add(self.timeout_input)
        root.addWidget(settings_card)

        # --- status banner ---
        self.status_banner = Banner(
            "Enter a URL you are authorised to test. No scan run yet.", "info"
        )
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

        # --- results report (filled in after a scan) ---
        self.results_host = QWidget()
        self.results_box = QVBoxLayout(self.results_host)
        self.results_box.setContentsMargins(0, 0, 0, 0)
        self.results_box.setSpacing(8)
        root.addWidget(self.results_host)

        root.addStretch()

        self.last_result = None
        self._form_widgets = [
            self.target_input,
            self.check_authorized,
            self.timeout_input,
        ]

    # -----------------------------------------------------------------
    def _on_reset(self):
        for widget in self._form_widgets:
            widget.reset()
        self._clear_results()
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        target = self.target_input.text().strip()
        if not target:
            self._set_banner("Enter a target URL first.", "warning")
            return
        if not target.lower().startswith(("http://", "https://")):
            self._set_banner("Target URL must start with http:// or https://.", "warning")
            return
        if not self.check_authorized.isChecked():
            self._set_banner(
                "Confirm you are authorised to test this target first.", "warning"
            )
            return

        timeout = self.timeout_input.text().strip()
        timeout = int(timeout) if timeout.isdigit() and int(timeout) > 0 else self.DEFAULT_TIMEOUT

        self._set_banner(f"Scanning {target} (passive, read-only) ...", "info")

        result = run_passive_scan(target, timeout=timeout)
        self.last_result = result

        # Save this scan so it appears in Scan History.
        add_scan_result(result, "Dynamic", target, profile="Passive")

        if result["ok"]:
            s = result["summary"]
            self._set_banner(
                f"Live scan complete - {result['total_findings']} issues found "
                f"(HIGH {s['HIGH']}, MEDIUM {s['MEDIUM']}, "
                f"LOW {s['LOW']}, INFO {s['INFO']}).",
                "success",
            )
            self._render_results(result)
        else:
            self._clear_results()
            self._set_banner(f"Scan failed: {result['error']}", "warning")

    def _set_banner(self, text: str, kind: str):
        parent_layout = self.status_banner.parentWidget().layout()
        idx = parent_layout.indexOf(self.status_banner)
        self.status_banner.setParent(None)
        new_banner = Banner(text, kind)
        parent_layout.insertWidget(idx, new_banner)
        self.status_banner = new_banner

    # -----------------------------------------------------------------
    # Results rendering
    # -----------------------------------------------------------------
    def _clear_results(self):
        while self.results_box.count():
            item = self.results_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_results(self, result: dict):
        self._clear_results()

        header = QLabel("DYNAMIC  •  Live Website Scan")
        header.setStyleSheet(
            "background:#00b894;color:white;font-weight:bold;"
            "padding:7px 12px;border-radius:5px;"
        )
        self.results_box.addWidget(header)

        meta = result.get("meta", {})
        status = meta.get("status_code", "?")
        sub = QLabel(
            f"\U0001F310 {result['target']}    "
            f"HTTP {status}    •    live page fetched, read-only (no attacks sent)"
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa0b5;")
        self.results_box.addWidget(sub)

        for f in result["findings"]:
            self.results_box.addWidget(_finding_card(f, "\U0001F517 " + str(f["location"])))

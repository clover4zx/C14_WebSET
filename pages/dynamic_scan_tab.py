"""
pages/dynamic_scan_tab.py
The "Dynamic" tab inside the New Scan page.

Dynamic scanning = looking at a LIVE, running website. This runs the passive
scanner (via webset_core): it fetches the page over HTTP(S) and analyses it.
It is PASSIVE (read-only) - it never submits forms or sends attack payloads.

Results are shown as a "Live Website Scan" report, headed with the URL and its
HTTP status, where each finding points to a live page element or link - that's
what makes a dynamic scan distinct from reading static source code.

Only scan sites you are authorised to test (your local demo page, DVWA, or
OWASP Juice Shop).
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
    make_scrollable,
    primary_button,
    secondary_button,
    section_header,
)

from pages.webset_core import run_passive_scan


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
        root.addWidget(target_card)

        # --- status banner ---
        self.status_banner = Banner(
            "Enter a URL you are authorised to test "
            "(local demo page, DVWA, or Juice Shop). No scan run yet.",
            "info",
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

    # -----------------------------------------------------------------
    def _on_reset(self):
        self.target_input.reset()
        self._clear_results()
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        target = self.target_input.text().strip()
        if not target:
            self._set_banner("Enter a target URL first.", "warning")
            return

        # Scan runs on the main thread, so the window may pause briefly on a
        # remote site. The local demo page replies instantly.
        self._set_banner(f"Scanning {target} ...", "info")

        result = run_passive_scan(target)
        self.last_result = result

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

    def _set_banner(self, text: str, kind: str):
        parent_layout = self.status_banner.parentWidget().layout()
        idx = parent_layout.indexOf(self.status_banner)
        self.status_banner.setParent(None)
        new_banner = Banner(text, kind)
        parent_layout.insertWidget(idx, new_banner)
        self.status_banner = new_banner

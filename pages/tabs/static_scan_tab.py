"""
pages/static_scan_tab.py
The "Static" tab inside the New Scan page.

Static scanning = analysing a website's SOURCE CODE without running it.
Upload a .zip of source code; the static analyzer (via webset_core) reports
hardcoded secrets, risky code patterns, and exposed sensitive files.

Results are shown as a "Source Code Analysis" report, where each finding
points to a FILE and LINE NUMBER - that's what makes static analysis distinct
from a live (dynamic) scan.
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
    FileUploadBox,
    make_scrollable,
    primary_button,
    secondary_button,
    section_header,
)

import os

from scanner.webset_core import run_static_scan
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


class StaticScanTab(QWidget):
    def __init__(self):
        super().__init__()

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(make_scrollable(content))

        # --- source code upload ---
        root.addWidget(section_header("Upload Source Code (.zip)"))
        upload_card = Card()
        self.file_upload = FileUploadBox(
            "Source ZIP", file_filter="Zip archives (*.zip)"
        )
        self.file_upload.file_selected.connect(self._on_file_selected)
        upload_card.add(self.file_upload)
        root.addWidget(upload_card)

        # --- status banner ---
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

        # --- results report (filled in after a scan) ---
        self.results_host = QWidget()
        self.results_box = QVBoxLayout(self.results_host)
        self.results_box.setContentsMargins(0, 0, 0, 0)
        self.results_box.setSpacing(8)
        root.addWidget(self.results_host)

        root.addStretch()

        self.last_result = None

    # -----------------------------------------------------------------
    def _on_file_selected(self, file_name: str):
        self._set_banner(f"Selected file: {file_name}", "success")

    def _on_reset(self):
        self.file_upload.reset()
        self._clear_results()
        self._set_banner("Form reset.", "info")

    def _on_run_scan(self):
        zip_path = self.file_upload.file_path()
        if not zip_path:
            self._set_banner("Upload a .zip of source code first.", "warning")
            return

        self._set_banner("Analysing source code ...", "info")

        result = run_static_scan(zip_path)
        self.last_result = result

        # Save this scan so it appears in Scan History.
        add_scan_result(result, "Static", os.path.basename(zip_path), profile="Source ZIP")

        if result["ok"]:
            s = result["summary"]
            self._set_banner(
                f"Analysis complete - {result['total_findings']} issues found "
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

        header = QLabel("STATIC  •  Source Code Analysis")
        header.setStyleSheet(
            "background:#6c5ce7;color:white;font-weight:bold;"
            "padding:7px 12px;border-radius:5px;"
        )
        self.results_box.addWidget(header)

        meta = result.get("meta", {})
        tech = ", ".join(meta.get("tech_stack", [])) or "unknown"
        sub = QLabel(
            f"Scanned file: {meta.get('zip_file', result['target'])}   •   "
            f"Tech stack: {tech}   •   source code read, never executed"
        )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa0b5;")
        self.results_box.addWidget(sub)

        for f in result["findings"]:
            loc = f["location"]
            if f.get("line"):
                loc += f"  (line {f['line']})"
            self.results_box.addWidget(_finding_card(f, "\U0001F4C4 " + loc))

    def _set_banner(self, text: str, kind: str):
        parent_layout = self.status_banner.parentWidget().layout()
        idx = parent_layout.indexOf(self.status_banner)
        self.status_banner.setParent(None)
        new_banner = Banner(text, kind)
        parent_layout.insertWidget(idx, new_banner)
        self.status_banner = new_banner

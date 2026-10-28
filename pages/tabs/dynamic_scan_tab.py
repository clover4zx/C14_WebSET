"""
pages/tabs/dynamic_scan_tab.py
The "Dynamic" tab inside the New Scan page.

Always runs a PASSIVE (read-only) scan of a live website: you enter a URL,
confirm you're authorised to test it, and it fetches and analyses the page -
looking for outdated libraries, insecure forms, hardcoded secrets, risky
links, etc. It does NOT send attack payloads; it only reads the page.

Optionally, ticking "Enable active payload testing" also runs the ACTIVE
scanner (scanner/active_scanner.py): a headless Chrome browser, driven by
Selenium, submits harmless test payloads into forms and URL parameters and
checks the live DOM / response to confirm whether each one took effect
(e.g. a script actually executing, or a database error being exposed).
Because this submits real payloads, it is restricted to local/private
targets and stays behind its own checkbox and the same authorisation
confirmation.

The active scan runs on a background QThread so the GUI never freezes while
Chrome is working, and can be cancelled mid-scan.

Results are shown as "Live Website Scan" (passive) and, if run,
"Active Payload Testing" report sections.
"""

from PyQt6.QtCore import QThread, Qt, pyqtSignal
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

from scanner.webset_core import run_active_scan, run_passive_scan
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


# --------------------------------------------------------------------------- #
# Background worker: runs Selenium off the GUI thread.
# --------------------------------------------------------------------------- #

class _ActiveScanWorker(QThread):
    progress = pyqtSignal(str)
    finished_scan = pyqtSignal(dict)

    def __init__(self, target: str, timeout: int):
        super().__init__()
        self.target = target
        self.timeout = timeout
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        result = run_active_scan(
            self.target,
            timeout=self.timeout,
            progress=self.progress.emit,
            should_stop=lambda: self._cancelled,
        )
        self.finished_scan.emit(result)


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

        # Active testing is opt-in and submits real payloads, so it gets its
        # own checkbox on top of the authorisation confirmation above.
        self.check_active = make_checkbox(
            "Also run active payload testing (Selenium) - submits test "
            "payloads into forms/parameters and verifies results in a "
            "real browser. Local/private targets only."
        )
        target_card.add(self.check_active)
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
        self.cancel_button = secondary_button("Cancel")
        self.run_button = primary_button("Run Dynamic Scan")
        self.reset_button.clicked.connect(self._on_reset)
        self.cancel_button.clicked.connect(self._on_cancel)
        self.run_button.clicked.connect(self._on_run_scan)
        self.cancel_button.setVisible(False)
        actions_row.addWidget(self.reset_button)
        actions_row.addWidget(self.cancel_button)
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
        self._worker = None
        self._pending_target = None
        self._form_widgets = [
            self.target_input,
            self.check_authorized,
            self.check_active,
            self.timeout_input,
        ]

    # -----------------------------------------------------------------
    def _on_reset(self):
        if self._worker is not None:
            return  # don't reset mid-scan
        for widget in self._form_widgets:
            widget.reset()
        self._clear_results()
        self._set_banner("Form reset.", "info")

    def _on_cancel(self):
        if self._worker is not None:
            self._worker.cancel()
            self._set_banner("Cancelling active scan ...", "warning")

    def _on_run_scan(self):
        if self._worker is not None:
            return  # a scan is already running

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

        # --- step 1: passive scan (fast, runs on the GUI thread) ---
        self._set_banner(f"Scanning {target} (passive, read-only) ...", "info")
        self._clear_results()

        passive_result = run_passive_scan(target, timeout=timeout)
        add_scan_result(passive_result, "Dynamic", target, profile="Passive")
        self._render_results("passive", passive_result)

        if not self.check_active.isChecked():
            self.last_result = passive_result
            self._set_banner(self._passive_summary_text(passive_result), self._banner_kind(passive_result))
            return

        if not passive_result["ok"]:
            self.last_result = passive_result
            self._set_banner(
                f"Passive scan failed ({passive_result['error']}); skipping active scan.",
                "warning",
            )
            return

        # --- step 2: active scan (Selenium, runs on a background thread) ---
        self.last_result = passive_result
        self._pending_target = target
        self._set_running(True)
        self._set_banner(f"Starting active payload testing on {target} ...", "info")

        self._worker = _ActiveScanWorker(target, timeout)
        self._worker.progress.connect(lambda msg: self._set_banner(msg, "info"))
        self._worker.finished_scan.connect(self._on_active_scan_finished)
        self._worker.start()

    def _on_active_scan_finished(self, active_result: dict):
        self._set_running(False)
        self._worker = None

        add_scan_result(active_result, "Dynamic", self._pending_target, profile="Active")
        self.last_result = active_result

        if active_result["ok"]:
            self._render_results("active", active_result)
            s = active_result["summary"]
            note = " (stopped early - submission limit reached)" if active_result.get("meta", {}).get("truncated") else ""
            self._set_banner(
                f"Active scan complete{note} - {active_result['total_findings']} issues "
                f"confirmed (HIGH {s['HIGH']}, MEDIUM {s['MEDIUM']}, LOW {s['LOW']}).",
                "success" if active_result["total_findings"] == 0 or s["HIGH"] == 0 else "warning",
            )
        else:
            self._set_banner(f"Active scan failed: {active_result['error']}", "warning")

    def _set_running(self, running: bool):
        self.run_button.setEnabled(not running)
        self.reset_button.setEnabled(not running)
        self.cancel_button.setVisible(running)

    @staticmethod
    def _passive_summary_text(result: dict) -> str:
        if not result["ok"]:
            return f"Scan failed: {result['error']}"
        s = result["summary"]
        return (
            f"Live scan complete - {result['total_findings']} issues found "
            f"(HIGH {s['HIGH']}, MEDIUM {s['MEDIUM']}, LOW {s['LOW']}, INFO {s['INFO']})."
        )

    @staticmethod
    def _banner_kind(result: dict) -> str:
        if not result["ok"]:
            return "warning"
        return "success"

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

    def _render_results(self, kind: str, result: dict):
        if kind == "passive":
            header = QLabel("DYNAMIC  •  Live Website Scan (passive)")
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
        else:
            header = QLabel("DYNAMIC  •  Active Payload Testing (Selenium)")
            header.setStyleSheet(
                "background:#c0392b;color:white;font-weight:bold;"
                "padding:7px 12px;border-radius:5px;"
            )
            self.results_box.addWidget(header)

            meta = result.get("meta", {})
            sub = QLabel(
                f"\U0001F310 {result['target']}    "
                f"{meta.get('pages_tested', 0)} page(s), {meta.get('forms_tested', 0)} form(s), "
                f"{meta.get('payloads_sent', 0)} payload(s) submitted and verified in-browser"
            )
        sub.setWordWrap(True)
        sub.setStyleSheet("color:#9aa0b5;")
        self.results_box.addWidget(sub)

        if not result["findings"]:
            empty = QLabel("No issues confirmed." if kind == "active" else "No issues found.")
            empty.setStyleSheet("color:#9aa0b5;")
            self.results_box.addWidget(empty)

        for f in result["findings"]:
            self.results_box.addWidget(_finding_card(f, "\U0001F517 " + str(f["location"])))

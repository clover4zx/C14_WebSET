"""
pages/reports_page.py
Shown when the "Reports" sidebar button is clicked: set up a client-ready
report and see exactly what will go in it before exporting.

Layout:
    [ Report Details            | Scope                           ]
    [ Report Contents (what sections to include)                  ]
    [ Report Preview: severity chart + table of included findings ]
    [ status banner                         Reset | Generate      ]

The findings and scans come from data/cases_data.py and
data/scan_history_data.py (dummy data for now), so this file only
handles how the page LOOKS and how the scope filters work. Nothing here
writes a real report yet — Generate Report validates the form and shows
a banner. The backend team can call get_config() / selected_findings()
to get everything they need (see the bottom of this file).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import theme
from app.charts import SeverityBarChart
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
from data.cases_data import SEVERITY_ORDER, get_cases
from data.scan_history_data import get_scan_history

FORMAT_OPTIONS = ["PDF", "HTML", "Markdown", "JSON", "CSV"]
ALL_SCANS = "All scans"
# lowest first, so the default ("Low") includes everything
MIN_SEVERITY_OPTIONS = list(reversed(SEVERITY_ORDER))

# (column heading, key in each finding dict)
COLUMNS = [
    ("Severity", "severity"),
    ("Finding", "title"),
    ("OWASP Category", "owasp"),
    ("Case", "case_id"),
]
ROW_HEIGHT = 38


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()

        self._cases = []        # everything from the data layer
        self._scope_ids = []    # scan id for each scope dropdown entry (None = all scans)
        self._findings = []     # findings left after the scope filters, most severe first

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(page_header("Reports", "Export findings as a client-ready report"))

        # --- details + scope, side by side ---
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        top_row.addWidget(self._build_details_card(), 1)
        top_row.addWidget(self._build_scope_card(), 1)
        root.addLayout(top_row)

        root.addWidget(self._build_contents_card())
        root.addWidget(self._build_preview_card())

        # --- status banner, updates when the form is reset or a report is requested ---
        self.status_banner = Banner("No report generated yet.", "info")
        root.addWidget(self.status_banner)

        # --- actions ---
        actions_row = QHBoxLayout()
        actions_row.addStretch()
        self.reset_button = secondary_button("Reset")
        self.generate_button = primary_button("Generate Report")
        self.reset_button.clicked.connect(self._on_reset)
        self.generate_button.clicked.connect(self._on_generate)
        actions_row.addWidget(self.reset_button)
        actions_row.addWidget(self.generate_button)
        root.addLayout(actions_row)

        root.addStretch()

        # Every control that Reset puts back to its starting state. Each of
        # these has a reset() method (see app/widgets.py). If you add a new
        # input to the form later, add it to this list and Reset covers it.
        self._form_widgets = [
            self.title_input,
            self.client_input,
            self.author_input,
            self.format_combo,
            self.scope_combo,
            self.min_severity_combo,
            self.check_include_resolved,
            self.check_summary,
            self.check_chart,
            self.check_details,
            self.check_remediation,
            self.check_owasp,
            self.check_scan_info,
        ]

        self.refresh()

    # -----------------------------------------------------------------
    # Form
    # -----------------------------------------------------------------
    def _build_details_card(self):
        card = Card()
        card.add(section_header("Report Details"))

        self.title_input = LabeledInput("Report Title", "e.g. DVWA Security Assessment")
        card.add(self.title_input)

        row = QHBoxLayout()
        self.client_input = LabeledInput("Client / Organisation", "e.g. Acme Pty Ltd")
        self.author_input = LabeledInput("Prepared By", "e.g. Your name or team")
        row.addWidget(self.client_input, 1)
        row.addWidget(self.author_input, 1)
        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)

        self.format_combo = LabeledCombo("Export Format", FORMAT_OPTIONS)
        card.add(self.format_combo)
        return card

    def _build_scope_card(self):
        card = Card()
        card.add(section_header("Scope"))

        self.scope_combo = LabeledCombo("Scan", [ALL_SCANS])
        self.scope_combo.combo.currentIndexChanged.connect(self._update_preview)
        card.add(self.scope_combo)

        self.min_severity_combo = LabeledCombo("Minimum Severity", MIN_SEVERITY_OPTIONS)
        self.min_severity_combo.combo.currentTextChanged.connect(self._update_preview)
        card.add(self.min_severity_combo)

        self.check_include_resolved = make_checkbox("Include resolved cases", checked=True)
        self.check_include_resolved.toggled.connect(self._update_preview)
        card.add(self.check_include_resolved)
        return card

    def _build_contents_card(self):
        card = Card()
        card.add(section_header("Report Contents"))

        self.check_summary = make_checkbox("Executive summary", checked=True)
        self.check_chart = make_checkbox("Severity breakdown chart", checked=True)
        self.check_details = make_checkbox("Detailed findings", checked=True)
        self.check_remediation = make_checkbox("Remediation recommendations", checked=True)
        self.check_owasp = make_checkbox("OWASP Top 10 mapping", checked=True)
        self.check_scan_info = make_checkbox("Scan details appendix", checked=True)

        row = QHBoxLayout()
        for box in (
            self.check_summary,
            self.check_chart,
            self.check_details,
            self.check_remediation,
            self.check_owasp,
            self.check_scan_info,
        ):
            row.addWidget(box)
        row.addStretch()
        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)
        return card

    # -----------------------------------------------------------------
    # Preview
    # -----------------------------------------------------------------
    def _build_preview_card(self):
        card = Card()
        card.add(section_header("Report Preview"))

        self.preview_summary = QLabel()
        self.preview_summary.setObjectName("MutedText")
        card.add(self.preview_summary)

        chart_heading = QLabel("Findings by Severity")
        chart_heading.setObjectName("MutedText")
        card.add(chart_heading)
        self.preview_chart = SeverityBarChart()
        card.add(self.preview_chart)

        table = QTableWidget(0, len(COLUMNS))
        table.setHorizontalHeaderLabels([heading for heading, _ in COLUMNS])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        table.setShowGrid(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setWordWrap(False)   # long titles get "..." instead of wrapping
        # Fixed vertically: tables default to "Expanding", which would make
        # the card grab spare space and stay tall after the filters change
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column, (_heading, key) in enumerate(COLUMNS):
            mode = QHeaderView.ResizeMode.Stretch if key == "title" else QHeaderView.ResizeMode.ResizeToContents
            header.setSectionResizeMode(column, mode)
        self.preview_table = table
        card.add(table)

        self.empty_label = QLabel("No findings match the current scope.")
        self.empty_label.setObjectName("MutedText")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.empty_label)
        return card

    def _fill_table(self, findings):
        table = self.preview_table
        table.setRowCount(len(findings))
        for row, finding in enumerate(findings):
            for column, (_heading, key) in enumerate(COLUMNS):
                item = QTableWidgetItem(str(finding.get(key, "")))
                if key == "severity":
                    colour = theme.SEVERITY_COLOURS.get(finding["severity"], theme.TEXT_PRIMARY)
                    item.setForeground(QColor(colour))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if key == "case_id":
                    item.setForeground(QColor(theme.TEXT_MUTED))
                table.setItem(row, column, item)

        # tall enough for every row, so only the page scrolls, not the table
        header_height = table.horizontalHeader().sizeHint().height()
        table.setFixedHeight(header_height + max(len(findings), 1) * ROW_HEIGHT + 4)
        table.setVisible(bool(findings))
        self.empty_label.setVisible(not findings)

    # -----------------------------------------------------------------
    # Behaviour
    # -----------------------------------------------------------------
    def refresh(self):
        """Reload cases and scans from the data layer and re-apply the scope.
        main.py calls this each time the Reports page is opened."""
        self._cases = get_cases()

        # Only completed scans can have findings, so only those are offered.
        previous = self._selected_scan_id()
        scans = [scan for scan in get_scan_history() if scan["status"] == "Completed"]
        self._scope_ids = [None] + [scan["id"] for scan in scans]
        labels = [ALL_SCANS] + [f"{scan['id']} – {scan['target']}" for scan in scans]

        combo = self.scope_combo.combo
        combo.blockSignals(True)   # don't update the preview once per item added
        combo.clear()
        combo.addItems(labels)
        combo.setCurrentIndex(self._scope_ids.index(previous) if previous in self._scope_ids else 0)
        combo.blockSignals(False)

        self._update_preview()

    def _selected_scan_id(self):
        """Id of the scan picked in the Scope card, or None for 'All scans'."""
        index = self.scope_combo.combo.currentIndex()
        if 0 <= index < len(self._scope_ids):
            return self._scope_ids[index]
        return None

    def _collect_findings(self) -> list:
        """Every finding that passes the Scope card's filters, most severe first.

        A finding belongs to a scan if the case it sits in lists that scan
        (see data/cases_data.py)."""
        scan_id = self._selected_scan_id()
        min_rank = SEVERITY_ORDER.index(self.min_severity_combo.value())
        include_resolved = self.check_include_resolved.isChecked()

        findings = []
        for case in self._cases:
            if scan_id and scan_id not in case["scans"]:
                continue
            if case["status"] == "Resolved" and not include_resolved:
                continue
            for finding in case["findings"]:
                if SEVERITY_ORDER.index(finding["severity"]) <= min_rank:
                    findings.append({
                        **finding,
                        "case_id": case["id"],
                        "case_title": case["title"],
                        "case_status": case["status"],
                        "target": case["target"],
                    })
        findings.sort(key=lambda f: SEVERITY_ORDER.index(f["severity"]))  # stable sort
        return findings

    def _update_preview(self, *_args):
        self._findings = self._collect_findings()

        counts = {level: 0 for level in SEVERITY_ORDER}
        for finding in self._findings:
            counts[finding["severity"]] += 1
        self.preview_chart.set_data(counts)

        case_count = len({finding["case_id"] for finding in self._findings})
        self.preview_summary.setText(
            f"{len(self._findings)} finding(s) across {case_count} case(s) will be included."
        )
        self._fill_table(self._findings)

    # -----------------------------------------------------------------
    # Handlers — placeholder behaviour for now. The backend team can
    # replace _on_generate's body with a real export, using get_config()
    # and selected_findings().
    # -----------------------------------------------------------------
    def _on_reset(self):
        for widget in self._form_widgets:
            widget.reset()
        self._update_preview()
        self._set_banner("Form reset.", "info")

    def _on_generate(self):
        error = self._validate()
        if error:
            self._set_banner(error, "warning")
            return

        config = self.get_config()
        self._set_banner(
            f"Report '{config['title']}' requested as {config['format']} "
            f"({len(config['findings'])} finding(s), scope: {config['scope']}).",
            "success",
        )

    def _validate(self) -> str:
        """Returns a message describing the first problem found, or '' if the form is OK."""
        if not self.title_input.text().strip():
            return "Enter a report title first."
        if not self.selected_sections():
            return "Select at least one section to include in the report."
        if not self._findings:
            return "No findings match the current scope. Widen the scope before generating a report."
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
    def selected_sections(self) -> list:
        """Names of the ticked report sections, e.g. ['summary', 'chart']."""
        options = (
            ("summary", self.check_summary),
            ("chart", self.check_chart),
            ("details", self.check_details),
            ("remediation", self.check_remediation),
            ("owasp", self.check_owasp),
            ("scan_info", self.check_scan_info),
        )
        return [name for name, box in options if box.isChecked()]

    def selected_findings(self) -> list:
        """The findings that will go in the report (a copy, most severe first).
        Each has: title, severity, owasp, remediation, case_id, case_title,
        case_status, target."""
        return [dict(finding) for finding in self._findings]

    def get_config(self) -> dict:
        """Everything on this page as one plain dict, ready to hand to the exporter."""
        return {
            "title": self.title_input.text().strip(),
            "client": self.client_input.text().strip(),
            "prepared_by": self.author_input.text().strip(),
            "format": self.format_combo.value(),
            "scan_id": self._selected_scan_id(),          # None means all scans
            "scope": self.scope_combo.combo.currentText(),
            "min_severity": self.min_severity_combo.value(),
            "include_resolved": self.check_include_resolved.isChecked(),
            "sections": self.selected_sections(),
            "findings": self.selected_findings(),
        }

    # -----------------------------------------------------------------
    # What the backend team can read off this page once it's wired up
    # (or just call self.get_config() to get all of it as a dict):
    #
    #   self.title_input.text()                 -> str, report title
    #   self.client_input.text()                -> str, client / organisation ("" if none)
    #   self.author_input.text()                -> str, who prepared it ("" if none)
    #   self.format_combo.value()               -> str, "PDF"/"HTML"/"Markdown"/"JSON"/"CSV"
    #   self.scope_combo.combo.currentText()    -> str, "All scans" or "WS-011 – <target>"
    #   self.min_severity_combo.value()         -> str, "Low"/"Medium"/"High"/"Critical"
    #   self.check_include_resolved.isChecked() -> bool
    #   self.check_summary.isChecked()          -> bool, executive summary
    #   self.check_chart.isChecked()            -> bool, severity breakdown chart
    #   self.check_details.isChecked()          -> bool, detailed findings
    #   self.check_remediation.isChecked()      -> bool, remediation recommendations
    #   self.check_owasp.isChecked()            -> bool, OWASP Top 10 mapping
    #   self.check_scan_info.isChecked()        -> bool, scan details appendix
    #   self.selected_findings()                -> list of finding dicts that pass the scope
    #
    # To hook in a real export: replace the body of _on_generate with a call
    # into the report generator, passing get_config(). _validate() already
    # runs first, so the config it receives is known to be usable.
    # -----------------------------------------------------------------
"""
pages/cases_page.py
Shown when the "Cases" sidebar button is clicked.

A case groups related findings about one target or issue so the team
can track it until it's fixed.

Layout:
    [ Open ] [ In Progress ] [ Resolved ]           <- status counts
    [ Filters: search | Status | Severity    Showing X of Y ]
    [ Table of every case                                  ]
    [ Details of the selected case:                        ]
    [   info + change status | findings table | remediation ]

Cases come from data/cases_data.py (dummy data for now) — this file
only handles how they LOOK and how filtering/updating works.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
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
from app.widgets import (
    Card,
    LabeledCombo,
    LabeledInput,
    page_header,
    primary_button,
    section_header,
)
from data.cases_data import CASE_STATUSES, get_case_status_counts, get_cases, update_case_status


# (column heading, key in each case dict)
CASE_COLUMNS = [
    ("ID", "id"),
    ("Case", "title"),
    ("Target", "target"),
    ("Severity", "severity"),
    ("Status", "status"),
    ("Findings", "findings_count"),
    ("Assigned To", "assignee"),
    ("Updated", "updated"),
]

# (column heading, key in each finding dict)
FINDING_COLUMNS = [
    ("Finding", "title"),
    ("Severity", "severity"),
    ("OWASP Category", "owasp"),
]

# (status, colour name in theme.py's #StatValue rules)
STATUS_CARDS = [
    ("Open", "info"),
    ("In Progress", "warning"),
    ("Resolved", "success"),
]

ROW_HEIGHT = 38
SEVERITY_OPTIONS = ["All", "Critical", "High", "Medium", "Low"]


# ---------------------------------------------------------------------------
# Small helpers shared by both tables on this page
# ---------------------------------------------------------------------------
def make_table(columns, stretch_keys):
    """A read-only, row-selectable table styled like the rest of the app.
    Columns in stretch_keys share the spare width; the rest fit their contents."""
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels([heading for heading, _ in columns])
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    table.setCursor(Qt.CursorShape.PointingHandCursor)
    # Fixed vertically so the card doesn't grab spare space (see scan_history_page.py)
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    header = table.horizontalHeader()
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    for column, (_heading, key) in enumerate(columns):
        mode = QHeaderView.ResizeMode.Stretch if key in stretch_keys else QHeaderView.ResizeMode.ResizeToContents
        header.setSectionResizeMode(column, mode)
    return table


def coloured_item(text, colour, bold=True):
    """A table cell with coloured (and usually bold) text."""
    item = QTableWidgetItem(text)
    item.setForeground(QColor(colour))
    if bold:
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    return item


def fit_table_height(table, row_count):
    """Make the table exactly tall enough for its rows, so only the page scrolls."""
    header_height = table.horizontalHeader().sizeHint().height()
    table.setFixedHeight(header_height + max(row_count, 1) * ROW_HEIGHT + 4)


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------
class CasesPage(QWidget):
    def __init__(self):
        super().__init__()

        self._all_cases = []       # everything from the data layer
        self._visible_cases = []   # what's left after filters, in table order
        self._selected_case = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(page_header("Cases", "Organise findings by engagement or target"))
        root.addLayout(self._build_status_cards())
        root.addWidget(self._build_filters())
        root.addWidget(self._build_cases_table())
        root.addWidget(self._build_details())
        root.addStretch()

        self.refresh()

    # -----------------------------------------------------------------
    # Status count cards
    # -----------------------------------------------------------------
    def _build_status_cards(self):
        row = QGridLayout()
        row.setSpacing(16)
        self.status_counts = {}
        for column, (status, colour) in enumerate(STATUS_CARDS):
            card = Card()
            card.setFixedHeight(100)
            title = QLabel(f"{status} Cases")
            title.setObjectName("StatTitle")
            value = QLabel("–")
            value.setObjectName("StatValue")
            value.setProperty("severity", colour)
            card.add(title)
            card.add(value)
            card.body.addStretch()
            row.addWidget(card, 0, column)
            self.status_counts[status] = value
        return row

    # -----------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------
    def _build_filters(self):
        card = Card()
        row = QHBoxLayout()
        row.setSpacing(12)

        self.search_input = LabeledInput("Search", "Case title, ID or target, e.g. xss or CS-005")
        self.status_filter = LabeledCombo("Status", ["All"] + CASE_STATUSES)
        self.severity_filter = LabeledCombo("Severity", SEVERITY_OPTIONS)

        self.search_input.field.textChanged.connect(self._apply_filters)
        self.status_filter.combo.currentTextChanged.connect(self._apply_filters)
        self.severity_filter.combo.currentTextChanged.connect(self._apply_filters)

        self.result_count = QLabel()
        self.result_count.setObjectName("MutedText")
        self.result_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        row.addWidget(self.search_input, 3)
        row.addWidget(self.status_filter, 1)
        row.addWidget(self.severity_filter, 1)
        row.addWidget(self.result_count, 1)

        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)
        return card

    # -----------------------------------------------------------------
    # Cases table
    # -----------------------------------------------------------------
    def _build_cases_table(self):
        card = Card()
        card.add(section_header("All Cases"))

        self.cases_table = make_table(CASE_COLUMNS, stretch_keys=("title", "target"))
        self.cases_table.itemSelectionChanged.connect(self._on_case_selected)
        card.add(self.cases_table)

        self.empty_label = QLabel("No cases match your filters.")
        self.empty_label.setObjectName("MutedText")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.empty_label)
        return card

    def _fill_cases_table(self, cases):
        table = self.cases_table
        table.blockSignals(True)   # don't fire selection events while rebuilding
        table.setRowCount(len(cases))
        for row, case in enumerate(cases):
            for column, (_heading, key) in enumerate(CASE_COLUMNS):
                text = str(case.get(key, ""))
                if key == "severity":
                    item = coloured_item(text, theme.SEVERITY_COLOURS.get(text, theme.TEXT_PRIMARY))
                elif key == "status":
                    item = coloured_item(text, theme.CASE_STATUS_COLOURS.get(text, theme.TEXT_PRIMARY))
                elif key == "id":
                    item = coloured_item(text, theme.TEXT_MUTED, bold=False)
                else:
                    item = QTableWidgetItem(text)
                item.setToolTip(text)   # hover to see text that's been cut off with "..."
                table.setItem(row, column, item)
        table.blockSignals(False)

        fit_table_height(table, len(cases))
        table.setVisible(bool(cases))
        self.empty_label.setVisible(not cases)

    # -----------------------------------------------------------------
    # Details of the selected case
    # -----------------------------------------------------------------
    def _build_details(self):
        card = Card()
        self.details_title = section_header("Case Details")
        card.add(self.details_title)

        self.details_description = QLabel()
        self.details_description.setWordWrap(True)
        self.details_description.setObjectName("MutedText")
        card.add(self.details_description)

        top_row = QHBoxLayout()
        top_row.setSpacing(32)
        top_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        # left: label/value pairs
        info = QGridLayout()
        info.setHorizontalSpacing(16)
        info.setVerticalSpacing(8)
        self.detail_values = {}
        for row_index, (label, key) in enumerate([
            ("Target", "target"),
            ("Assigned To", "assignee"),
            ("Created", "created"),
            ("Last Updated", "updated"),
            ("Linked Scans", "scans"),
        ]):
            name = QLabel(label)
            name.setObjectName("MutedText")
            value = QLabel("–")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info.addWidget(name, row_index, 0, Qt.AlignmentFlag.AlignTop)
            info.addWidget(value, row_index, 1, Qt.AlignmentFlag.AlignTop)
            self.detail_values[key] = value
        info.setColumnStretch(1, 1)
        info_wrap = QWidget()
        info_wrap.setLayout(info)

        # right: change the case's status
        status_box = QVBoxLayout()
        status_box.setSpacing(8)
        self.status_select = LabeledCombo("Case Status", CASE_STATUSES)
        self.update_status_button = primary_button("Update Status")
        self.update_status_button.clicked.connect(self._on_update_status)
        self.status_message = QLabel()
        self.status_message.setObjectName("MutedText")
        status_box.addWidget(self.status_select)
        status_box.addWidget(self.update_status_button)
        status_box.addWidget(self.status_message)
        status_wrap = QWidget()
        status_wrap.setLayout(status_box)
        status_wrap.setMaximumWidth(280)

        top_row.addWidget(info_wrap, 1)
        top_row.addWidget(status_wrap)
        top_wrap = QWidget()
        top_wrap.setLayout(top_row)
        card.add(top_wrap)

        # findings in this case
        findings_heading = QLabel("Findings in this Case")
        findings_heading.setObjectName("StatTitle")
        card.add(findings_heading)

        self.findings_table = make_table(FINDING_COLUMNS, stretch_keys=("title",))
        self.findings_table.itemSelectionChanged.connect(self._on_finding_selected)
        card.add(self.findings_table)

        # remediation advice for the selected finding
        self.remediation_box = QLabel()
        self.remediation_box.setObjectName("CalloutBox")
        self.remediation_box.setWordWrap(True)
        self.remediation_box.setTextFormat(Qt.TextFormat.RichText)
        card.add(self.remediation_box)

        self.details_card = card
        return card

    def _show_details(self, case):
        self._selected_case = case
        self.details_card.setVisible(case is not None)
        if case is None:
            return

        self.details_title.setText(f"{case['id']}: {case['title']}")
        self.details_description.setText(case["description"])
        for key, label in self.detail_values.items():
            value = case.get(key)
            if isinstance(value, list):
                value = ", ".join(value)
            label.setText(str(value or "–"))

        self.status_select.combo.setCurrentText(case["status"])
        self.status_message.setText("")

        # findings table
        findings = case["findings"]
        table = self.findings_table
        table.blockSignals(True)
        table.setRowCount(len(findings))
        for row, finding in enumerate(findings):
            for column, (_heading, key) in enumerate(FINDING_COLUMNS):
                text = finding.get(key, "")
                if key == "severity":
                    item = coloured_item(text, theme.SEVERITY_COLOURS.get(text, theme.TEXT_PRIMARY))
                else:
                    item = QTableWidgetItem(text)
                item.setToolTip(text)
                table.setItem(row, column, item)
        table.blockSignals(False)
        fit_table_height(table, len(findings))

        # show remediation for the first finding by default
        if findings:
            table.selectRow(0)
            self._show_remediation(findings[0])

    def _show_remediation(self, finding):
        self.remediation_box.setText(
            f"<b>How to fix:</b> {finding['remediation']}"
        )

    # -----------------------------------------------------------------
    # Behaviour
    # -----------------------------------------------------------------
    def _apply_filters(self):
        search = self.search_input.text().strip().lower()
        status = self.status_filter.value()
        severity = self.severity_filter.value()

        self._visible_cases = [
            case for case in self._all_cases
            if (not search
                or search in case["title"].lower()
                or search in case["id"].lower()
                or search in case["target"].lower())
            and (status == "All" or case["status"] == status)
            and (severity == "All" or case["severity"] == severity)
        ]

        self._fill_cases_table(self._visible_cases)
        self.result_count.setText(f"Showing {len(self._visible_cases)} of {len(self._all_cases)} cases")

        # keep the same case selected if it's still visible, otherwise pick the first
        visible_ids = [case["id"] for case in self._visible_cases]
        keep_id = self._selected_case["id"] if self._selected_case else None
        row = visible_ids.index(keep_id) if keep_id in visible_ids else 0

        if self._visible_cases:
            self.cases_table.selectRow(row)
            self._show_details(self._visible_cases[row])
        else:
            self._show_details(None)

    def _on_case_selected(self):
        rows = self.cases_table.selectionModel().selectedRows()
        if rows:
            self._show_details(self._visible_cases[rows[0].row()])

    def _on_finding_selected(self):
        rows = self.findings_table.selectionModel().selectedRows()
        if rows and self._selected_case:
            self._show_remediation(self._selected_case["findings"][rows[0].row()])

    def _on_update_status(self):
        if not self._selected_case:
            return
        case_id = self._selected_case["id"]
        new_status = self.status_select.value()
        if new_status == self._selected_case["status"]:
            self.status_message.setText(f"{case_id} is already {new_status}.")
            return

        update_case_status(case_id, new_status)
        self.refresh()
        self.status_message.setText(f"{case_id} marked as {new_status}.")

    def refresh(self):
        """Reload cases from the data layer and update the page.
        main.py calls this each time the Cases page is opened."""
        self._all_cases = get_cases()

        # re-point the selected case at the fresh copy of it
        if self._selected_case:
            self._selected_case = next(
                (case for case in self._all_cases if case["id"] == self._selected_case["id"]), None
            )

        counts = get_case_status_counts()
        for status, label in self.status_counts.items():
            label.setText(str(counts.get(status, 0)))

        self._apply_filters()
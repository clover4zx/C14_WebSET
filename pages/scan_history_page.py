"""
pages/scan_history_page.py
Shown when the "Scan History" sidebar button is clicked.

Layout:
    [ Filters: search box | Status | Type          Showing X of Y ]
    [ Table of every past scan                                    ]
    [ Details of the selected scan (info + findings by severity)  ]

The list of scans comes from data/scan_history_data.py (dummy data for
now) — this file only handles how it LOOKS and how filtering works.
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
from app.charts import SeverityBarChart
from app.widgets import Card, LabeledCombo, LabeledInput, page_header, section_header
from data.scan_history_data import get_scan_history


# (column heading, key in each scan dict)
COLUMNS = [
    ("ID", "id"),
    ("Target", "target"),
    ("Type", "scan_type"),
    ("Profile", "profile"),
    ("Started", "date"),
    ("Duration", "duration"),
    ("Status", "status"),
    ("Findings", "findings"),
]
ROW_HEIGHT = 38

STATUS_OPTIONS = ["All", "Completed", "Running", "Failed"]
TYPE_OPTIONS = ["All", "Static", "Dynamic"]


class ScanHistoryPage(QWidget):
    def __init__(self):
        super().__init__()

        self._all_scans = []       # everything from the data layer
        self._visible_scans = []   # what's left after filters, in table order

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(page_header("Scan History", "Past scans and their results"))
        root.addWidget(self._build_filters())
        root.addWidget(self._build_table())
        root.addWidget(self._build_details())
        root.addStretch()

        self.refresh()

    # -----------------------------------------------------------------
    # Filters
    # -----------------------------------------------------------------
    def _build_filters(self):
        card = Card()
        row = QHBoxLayout()
        row.setSpacing(12)

        self.search_input = LabeledInput("Search", "Target URL or scan ID, e.g. dvwa or WS-011")
        self.status_filter = LabeledCombo("Status", STATUS_OPTIONS)
        self.type_filter = LabeledCombo("Type", TYPE_OPTIONS)

        self.search_input.field.textChanged.connect(self._apply_filters)
        self.status_filter.combo.currentTextChanged.connect(self._apply_filters)
        self.type_filter.combo.currentTextChanged.connect(self._apply_filters)

        self.result_count = QLabel()
        self.result_count.setObjectName("MutedText")
        self.result_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        row.addWidget(self.search_input, 3)
        row.addWidget(self.status_filter, 1)
        row.addWidget(self.type_filter, 1)
        row.addWidget(self.result_count, 1)

        wrap = QWidget()
        wrap.setLayout(row)
        card.add(wrap)
        return card

    # -----------------------------------------------------------------
    # Table
    # -----------------------------------------------------------------
    def _build_table(self):
        card = Card()
        card.add(section_header("All Scans"))

        table = QTableWidget(0, len(COLUMNS))
        table.setHorizontalHeaderLabels([heading for heading, _ in COLUMNS])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        table.setShowGrid(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setCursor(Qt.CursorShape.PointingHandCursor)
        table.setWordWrap(False)   # long URLs get "..." instead of wrapping
        # Fixed vertically: tables default to "Expanding", which would make
        # the card grab spare space and stay tall after filtering
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for column, (_heading, key) in enumerate(COLUMNS):
            mode = QHeaderView.ResizeMode.Stretch if key == "target" else QHeaderView.ResizeMode.ResizeToContents
            header.setSectionResizeMode(column, mode)

        table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table = table
        card.add(table)

        self.empty_label = QLabel("No scans match your filters.")
        self.empty_label.setObjectName("MutedText")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.add(self.empty_label)
        return card

    def _fill_table(self, scans):
        table = self.table
        table.blockSignals(True)   # don't fire selection events while rebuilding
        table.setRowCount(len(scans))
        for row, scan in enumerate(scans):
            for column, (_heading, key) in enumerate(COLUMNS):
                value = scan.get(key, "")
                if key == "duration" and not value:
                    value = "–"
                item = QTableWidgetItem(str(value))
                if key == "status":
                    item.setForeground(QColor(theme.STATUS_COLOURS.get(value, theme.TEXT_PRIMARY)))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if key == "id":
                    item.setForeground(QColor(theme.TEXT_MUTED))
                table.setItem(row, column, item)
        table.blockSignals(False)

        # tall enough for every row, so only the page scrolls, not the table
        header_height = table.horizontalHeader().sizeHint().height()
        table.setFixedHeight(header_height + max(len(scans), 1) * ROW_HEIGHT + 4)
        table.setVisible(bool(scans))
        self.empty_label.setVisible(not scans)

    # -----------------------------------------------------------------
    # Details of the selected scan
    # -----------------------------------------------------------------
    def _build_details(self):
        card = Card()
        self.details_title = section_header("Scan Details")
        card.add(self.details_title)

        row = QHBoxLayout()
        row.setSpacing(32)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        # left: label/value pairs
        info = QGridLayout()
        info.setHorizontalSpacing(16)
        info.setVerticalSpacing(8)
        self.detail_values = {}
        for row_index, (label, key) in enumerate([
            ("Target", "target"),
            ("Type", "scan_type"),
            ("Profile", "profile"),
            ("Started", "date"),
            ("Duration", "duration"),
            ("Status", "status"),
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

        # right: findings by severity for this one scan
        findings_box = QVBoxLayout()
        findings_box.setSpacing(6)
        findings_heading = QLabel("Findings by Severity")
        findings_heading.setObjectName("MutedText")
        self.details_chart = SeverityBarChart()
        self.details_note = QLabel()
        self.details_note.setWordWrap(True)
        findings_box.addWidget(findings_heading)
        findings_box.addWidget(self.details_chart)
        findings_box.addWidget(self.details_note)
        findings_wrap = QWidget()
        findings_wrap.setLayout(findings_box)

        row.addWidget(info_wrap, 1)
        row.addWidget(findings_wrap, 1)
        row_wrap = QWidget()
        row_wrap.setLayout(row)
        card.add(row_wrap)

        self.details_card = card
        return card

    def _show_details(self, scan):
        self.details_card.setVisible(scan is not None)
        if scan is None:
            return

        self.details_title.setText(f"Scan Details: {scan['id']}")
        for key, label in self.detail_values.items():
            label.setText(str(scan.get(key) or "–"))
        status_colour = theme.STATUS_COLOURS.get(scan["status"], theme.TEXT_PRIMARY)
        self.detail_values["status"].setStyleSheet(f"color: {status_colour}; font-weight: 600;")

        self.details_chart.set_data(scan["severity"])

        # explain an empty chart instead of leaving it blank
        if scan["status"] == "Running":
            self._set_note("Scan still running. Findings will appear when it finishes.", theme.ACCENT_INFO)
        elif scan["status"] == "Failed":
            self._set_note(f"Scan failed: {scan.get('error', 'unknown error')}", theme.ACCENT_DANGER)
        elif scan["findings"] == 0:
            self._set_note("No vulnerabilities found in this scan.", theme.ACCENT)
        else:
            self._set_note("", theme.TEXT_PRIMARY)

    def _set_note(self, text, colour):
        self.details_note.setText(text)
        self.details_note.setStyleSheet(f"color: {colour};")
        self.details_note.setVisible(bool(text))

    # -----------------------------------------------------------------
    # Behaviour
    # -----------------------------------------------------------------
    def _apply_filters(self):
        search = self.search_input.text().strip().lower()
        status = self.status_filter.value()
        scan_type = self.type_filter.value()

        self._visible_scans = [
            scan for scan in self._all_scans
            if (not search or search in scan["target"].lower() or search in scan["id"].lower())
            and (status == "All" or scan["status"] == status)
            and (scan_type == "All" or scan["scan_type"] == scan_type)
        ]

        self._fill_table(self._visible_scans)
        self.result_count.setText(f"Showing {len(self._visible_scans)} of {len(self._all_scans)} scans")

        # select the first row so the details panel always shows something
        if self._visible_scans:
            self.table.selectRow(0)
            self._show_details(self._visible_scans[0])
        else:
            self._show_details(None)

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self._show_details(self._visible_scans[rows[0].row()])

    def refresh(self):
        """Reload scans from the data layer and re-apply the filters.
        main.py calls this each time the Scan History page is opened."""
        self._all_scans = get_scan_history()
        self._apply_filters()
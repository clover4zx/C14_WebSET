"""
pages/dashboard_page.py
The page shown when the "Dashboard" sidebar button is clicked.

Layout:
    [ Total Scans ] [ Vulnerabilities ] [ Critical ] [ Open Cases ]
    [ Findings by Severity ]  [ Activity Over Time               ]
    [ Recent Scans table                                         ]

All numbers come from data/dashboard_data.py (dummy data for now) —
this file only handles how things LOOK, never where data comes from.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import theme
from app.charts import LineChart, SeverityBarChart
from app.widgets import Card, page_header, section_header
from data.dashboard_data import (
    get_activity_over_time,
    get_dashboard_summary,
    get_findings_by_severity,
    get_recent_scans,
)


# (key, card title, severity)
# - key:      must match a key returned by get_dashboard_summary()
# - severity: picks the number's colour in theme.py
#             ("neutral", "warning", "critical" or "info")
SUMMARY_CARDS = [
    ("total_scans", "Total Scans", "neutral"),
    ("vulnerabilities", "Vulnerabilities Found", "warning"),
    ("critical", "Critical Findings", "critical"),
    ("open_cases", "Open Cases", "info"),
]

# (column heading, key in each scan dict from get_recent_scans())
RECENT_SCAN_COLUMNS = [
    ("Target", "target"),
    ("Date", "date"),
    ("Type", "scan_type"),
    ("Status", "status"),
    ("Findings", "findings"),
]
RECENT_SCAN_ROWS = 5
TABLE_ROW_HEIGHT = 38


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.card_values = {}   # key -> the QLabel showing that card's number

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(page_header("Dashboard", "Security overview of your web applications"))
        root.addLayout(self._build_summary_cards())
        root.addLayout(self._build_charts_row())
        root.addWidget(self._build_recent_scans())
        root.addStretch()  # keeps everything at the top instead of stretching tall

        self.refresh()

    # -----------------------------------------------------------------
    # Row 1: summary cards
    # -----------------------------------------------------------------
    def _build_summary_cards(self):
        cards = QGridLayout()   # grid so the cards share the width evenly
        cards.setSpacing(16)
        for column, (key, title, severity) in enumerate(SUMMARY_CARDS):
            cards.addWidget(self._build_stat_card(key, title, severity), 0, column)
        return cards

    def _build_stat_card(self, key, title_text, severity):
        card = Card()
        card.setFixedHeight(120)

        title = QLabel(title_text)
        title.setObjectName("StatTitle")

        value = QLabel("–")            # placeholder until refresh() fills it in
        value.setObjectName("StatValue")
        value.setProperty("severity", severity)

        card.add(title)
        card.add(value)
        card.body.addStretch()

        self.card_values[key] = value
        return card

    # -----------------------------------------------------------------
    # Row 2: severity chart + activity chart
    # -----------------------------------------------------------------
    def _build_charts_row(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        severity_card = Card()
        severity_card.add(section_header("Findings by Severity"))
        self.severity_chart = SeverityBarChart()
        severity_card.add(self.severity_chart)
        severity_card.body.addStretch()

        activity_card = Card()
        activity_card.add(section_header("Activity Over Time"))
        self.activity_chart = LineChart()
        activity_card.add(self.activity_chart)

        # 2 : 3 split, so the line chart gets a bit more room
        row.addWidget(severity_card, 2)
        row.addWidget(activity_card, 3)
        return row

    # -----------------------------------------------------------------
    # Row 3: recent scans table
    # -----------------------------------------------------------------
    def _build_recent_scans(self):
        card = Card()
        card.add(section_header("Recent Scans"))

        table = QTableWidget(0, len(RECENT_SCAN_COLUMNS))
        table.setHorizontalHeaderLabels([heading for heading, _ in RECENT_SCAN_COLUMNS])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        table.setShowGrid(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)   # Target takes spare width
        for column in range(1, len(RECENT_SCAN_COLUMNS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

        # tall enough for every row, so the table never scrolls on its own
        table.setFixedHeight(header.sizeHint().height() + RECENT_SCAN_ROWS * TABLE_ROW_HEIGHT + 4)

        self.recent_scans_table = table
        card.add(table)
        return card

    def _fill_recent_scans(self, scans):
        table = self.recent_scans_table
        table.setRowCount(len(scans))
        for row, scan in enumerate(scans):
            for column, (_heading, key) in enumerate(RECENT_SCAN_COLUMNS):
                item = QTableWidgetItem(str(scan.get(key, "")))
                if key == "status":
                    colour = theme.STATUS_COLOURS.get(scan.get("status"), theme.TEXT_PRIMARY)
                    item.setForeground(QColor(colour))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(row, column, item)

    # -----------------------------------------------------------------
    # Updating everything
    # -----------------------------------------------------------------
    def refresh(self):
        """Re-read all dashboard data and update the page.
        main.py calls this each time the Dashboard is opened."""
        summary = get_dashboard_summary()
        for key in self.card_values:
            self.set_card_value(key, summary.get(key, "–"))

        self.severity_chart.set_data(get_findings_by_severity())

        activity = get_activity_over_time()
        self.activity_chart.set_data(activity["labels"], activity["series"])

        self._fill_recent_scans(get_recent_scans(RECENT_SCAN_ROWS))

    def set_card_value(self, key, new_value):
        """Update one card's number, e.g. set_card_value("critical", 7)."""
        self.card_values[key].setText(str(new_value))
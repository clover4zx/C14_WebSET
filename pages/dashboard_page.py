"""
pages/dashboard_page.py
The page shown when the "Dashboard" sidebar button is clicked.

Shows the security summary cards. The numbers come from
data/dashboard_data.py (dummy data for now) — this file only handles
how they LOOK, never where they come from.
"""

from PyQt6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from app.widgets import Card, page_header
from data.dashboard_data import get_dashboard_summary


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


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.card_values = {}   # key -> the QLabel showing that card's number

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 0)
        root.setSpacing(16)

        root.addWidget(page_header("Dashboard", "Security overview of your web applications"))

        # Grid so the cards share the width evenly
        cards = QGridLayout()
        cards.setSpacing(16)
        for column, (key, title, severity) in enumerate(SUMMARY_CARDS):
            cards.addWidget(self._build_stat_card(key, title, severity), 0, column)
        root.addLayout(cards)

        root.addStretch()  # keeps the cards at the top instead of stretching tall

        self.refresh()

    # -----------------------------------------------------------------
    # Building the UI
    # -----------------------------------------------------------------
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
    # Updating the numbers
    # -----------------------------------------------------------------
    def refresh(self):
        """Re-read the summary data and update every card.
        main.py calls this each time the Dashboard is opened."""
        summary = get_dashboard_summary()
        for key in self.card_values:
            self.set_card_value(key, summary.get(key, "–"))

    def set_card_value(self, key, new_value):
        """Update one card's number, e.g. set_card_value("critical", 7)."""
        self.card_values[key].setText(str(new_value))
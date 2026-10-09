"""
pages/dynamic_scan_tab.py
The "Dynamic" tab inside the New Scan page. Placeholder for now — the
teammate building active/dynamic scanning (Selenium-driven payload
testing, etc.) builds this out the same way static_scan_tab.py is
built: Card, LabeledInput, make_checkbox, primary_button, Banner.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.widgets import Card, section_header


class DynamicScanTab(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        root.addWidget(section_header("Dynamic Scan"))
        card = Card()
        card.add(QLabel("Dynamic/active scan configuration not built yet."))
        root.addWidget(card)
        root.addStretch()
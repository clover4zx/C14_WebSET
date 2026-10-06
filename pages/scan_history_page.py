"""
pages/scan_history_page.py
Shown when the "Scan History" sidebar button is clicked. Placeholder
for now — build the real history/list view here later.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class ScanHistoryPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Scan History")
        subtitle = QLabel("Past scans and their results")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
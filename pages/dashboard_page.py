"""
pages/dashboard_page.py
The page shown when the "Dashboard" sidebar button is clicked. This is
the same content that used to be hardcoded directly inside GUI.py.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Dashboard")
        welcome = QLabel("Security Overview of Your Web Applications")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(welcome)
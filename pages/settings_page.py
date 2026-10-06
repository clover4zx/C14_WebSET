"""
pages/settings_page.py
Shown when the "Settings" sidebar button is clicked. Placeholder for
now — build the real target-scope / config form here later.
"""

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Settings")
        subtitle = QLabel("Target scope, authentication, and scan configuration")

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
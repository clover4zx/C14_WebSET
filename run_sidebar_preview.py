"""
run_sidebar_preview.py
Standalone runner for developing the Sidebar in isolation. Shows the
sidebar next to a plain panel that just prints which key was clicked —
enough to verify look, feel, and the navigation_requested signal work,
without needing the real main window skeleton.

Run:  python run_sidebar_preview.py
"""

import sys

from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QWidget

from app.sidebar import NavItem, Sidebar
from app.theme import STYLESHEET

# Each line below describes one button. Try changing a label or icon here
# and re-running this file to see the sidebar update.
NAV_ITEMS = [
    NavItem("dashboard", "Dashboard", "🏠"),
    NavItem("static_scan", "Static Scan", "🔎", badge="4"),
    NavItem("active_scan", "Active Scan", "⚡", enabled=False),
    NavItem("manual", "Manual Injection", "🧪", enabled=False),
    NavItem("cases", "Case Management", "🗂"),
    NavItem("reports", "Reports", "📄"),
    NavItem("settings", "Settings", "⚙"),
]


class PreviewWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebSET — Sidebar (standalone preview)")
        self.resize(900, 640)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(NAV_ITEMS)
        self.sidebar.navigation_requested.connect(self.on_navigate)
        layout.addWidget(self.sidebar)

        self.placeholder = QLabel("Click a sidebar item →")
        self.placeholder.setStyleSheet("font-size: 16px; color: #8b93a7; padding: 24px;")
        layout.addWidget(self.placeholder, stretch=1)

    def on_navigate(self, key: str):
        self.placeholder.setText(f"navigation_requested fired with key: '{key}'")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = PreviewWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

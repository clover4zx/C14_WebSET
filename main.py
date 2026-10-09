"""
main.py
Starts WebSET. Builds the window: sidebar on the left, one page at a
time on the right. Run this from the project's top folder:
    python main.py
"""

import sys

from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QStackedWidget,
    QWidget,
)

from app import theme
from app.sidebar import NavItem, Sidebar

# each sidebar button's page lives in its own file under pages/
from pages.dashboard_page import DashboardPage
from pages.new_scan_page import NewScanPage
from pages.scan_history_page import ScanHistoryPage
from pages.cases_page import CasesPage
from pages.reports_page import ReportsPage
from pages.settings_page import SettingsPage


# (key, sidebar label, page class)
# To add a page: create it in pages/, import it above, add one line here.
PAGES = [
    ("dashboard", "Dashboard", DashboardPage),
    ("new_scan", "New Scan", NewScanPage),
    ("scan_history", "Scan History", ScanHistoryPage),
    ("cases", "Cases", CasesPage),
    ("reports", "Reports", ReportsPage),
    ("settings", "Settings", SettingsPage),
]


class WebSETDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WebSET - Website Security Evaluation Tool")
        self.setMinimumSize(1200, 700)

        self.pages = {}        # key -> page object, e.g. self.pages["dashboard"]
        self._containers = {}  # key -> the scroll area wrapping that page

        # --- right-hand side: holds every page, only one visible at a time ---
        self.stack = QStackedWidget()
        for key, _label, page_class in PAGES:
            page = page_class()
            container = self._make_scrollable(page)
            self.stack.addWidget(container)
            self.pages[key] = page
            self._containers[key] = container

        # --- left-hand side: sidebar built from the same PAGES list ---
        self.sidebar = Sidebar([NavItem(key, label) for key, label, _ in PAGES])
        self.sidebar.navigation_requested.connect(self.show_page)

        # --- put them side by side ---
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)
        self.setCentralWidget(central_widget)

        self.show_page("dashboard")

    @staticmethod
    def _make_scrollable(page):
        """Wrap a page so it scrolls instead of squashing on small windows."""
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def show_page(self, key):
        page = self.pages[key]
        # pages with a refresh() method (e.g. Dashboard) reload their data when opened
        if hasattr(page, "refresh"):
            page.refresh()
        self.stack.setCurrentWidget(self._containers[key])
        self.sidebar.set_active(key)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.STYLESHEET)

    window = WebSETDashboard()
    window.show()

    sys.exit(app.exec())
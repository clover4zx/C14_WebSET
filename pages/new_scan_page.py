"""
pages/new_scan_page.py
Shown when the "New Scan" sidebar button is clicked. Just a tab
container — the actual content for each tab lives in its own file:
    - pages/tabs/static_scan_tab.py   (StaticScanTab)
    - pages/tabs/dynamic_scan_tab.py  (DynamicScanTab)
"""

from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.widgets import page_header
from pages.tabs.dynamic_scan_tab import DynamicScanTab
from pages.tabs.static_scan_tab import StaticScanTab


class NewScanPage(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 0)
        root.setSpacing(12)

        root.addWidget(page_header("New Scan", "Configure a static or dynamic scan"))

        tabs = QTabWidget()
        tabs.addTab(StaticScanTab(), "Static")
        tabs.addTab(DynamicScanTab(), "Dynamic")
        root.addWidget(tabs)
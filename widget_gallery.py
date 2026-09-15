"""
widget_gallery.py
Standalone preview of every common widget in app/widgets.py — run this on
its own to sanity-check styling before wiring up the full main menu.

Run:  python widget_gallery.py
"""

import sys

from PyQt5.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from app.theme import STYLESHEET
from app.widgets import (
    Banner,
    Card,
    ConfirmDialog,
    DataTable,
    LabeledCombo,
    LabeledInput,
    SearchBar,
    StatCard,
    danger_button,
    icon_button,
    page_header,
    primary_button,
    secondary_button,
    section_header,
    severity_pill,
    status_pill,
)


class GalleryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebSET — Common Widgets Gallery")
        self.resize(1000, 800)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        confirm_btn = primary_button("Run Confirm Dialog")
        confirm_btn.clicked.connect(self.show_confirm_demo)
        layout.addWidget(page_header(
            "Widget Gallery", "Every shared component, rendered in isolation",
            action=confirm_btn
        ))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(20)

        # Buttons
        body_layout.addWidget(section_header("Buttons"))
        btn_row = QHBoxLayout()
        btn_row.addWidget(primary_button("Primary"))
        btn_row.addWidget(secondary_button("Secondary"))
        btn_row.addWidget(danger_button("Danger"))
        btn_row.addWidget(icon_button("⟳", "Refresh"))
        btn_row.addStretch()
        body_layout.addLayout(btn_row)

        # Stat cards
        body_layout.addWidget(section_header("Stat Cards"))
        stat_row = QHBoxLayout()
        stat_row.addWidget(StatCard("Critical Findings", "3", "#e5484d"))
        stat_row.addWidget(StatCard("Pages Crawled", "47"))
        body_layout.addLayout(stat_row)

        # Pills
        body_layout.addWidget(section_header("Severity / Status Pills"))
        pill_row = QHBoxLayout()
        for s in ["Critical", "High", "Medium", "Low", "Info"]:
            pill_row.addWidget(severity_pill(s))
        for s in ["Open", "Confirmed", "Fixed"]:
            pill_row.addWidget(status_pill(s))
        pill_row.addStretch()
        body_layout.addLayout(pill_row)

        # Inputs
        body_layout.addWidget(section_header("Inputs"))
        input_card = Card()
        input_row = QHBoxLayout()
        input_row.addWidget(LabeledInput("Target URL", "https://example.com"))
        input_row.addWidget(LabeledCombo("Severity", ["Critical", "High", "Medium", "Low", "Info"]))
        input_wrap = QWidget()
        input_wrap.setLayout(input_row)
        input_card.add(input_wrap)
        input_card.add(SearchBar("Search findings..."))
        body_layout.addWidget(input_card)

        # Banners
        body_layout.addWidget(section_header("Banners"))
        body_layout.addWidget(Banner("Passive scan completed: 47 pages crawled.", "success"))
        body_layout.addWidget(Banner("2 requests timed out and were skipped.", "warning"))
        body_layout.addWidget(Banner("Active scan requires authorisation confirmation.", "danger"))

        # Table
        body_layout.addWidget(section_header("Data Table"))
        table = DataTable(["Vulnerability", "Location", "Severity", "Status"])
        table.set_rows([
            ("SQL Injection", "login.php?id=", severity_pill("Critical"), status_pill("Open")),
            ("Reflected XSS", "/search?q=", severity_pill("High"), status_pill("Confirmed")),
            ("Missing CSP Header", "/", severity_pill("Medium"), status_pill("Open")),
        ])
        body_layout.addWidget(table)

        layout.addWidget(body)

    def show_confirm_demo(self):
        ConfirmDialog.ask(
            "Confirm Authorisation",
            "I confirm I am authorised to run security tests against this target.",
            self,
        )


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = GalleryWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
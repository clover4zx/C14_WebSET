import sys

#features used
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame
)

#created main window - size, title, horizontal layout, sidebar (how to access other tabs)
class WebSETDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WebSET - Website Security Evaluation Tool")
        self.setMinimumSize(1200, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        logo = QLabel("WebSET")
        sidebar_layout.addWidget(logo)

        dashboard_button = QPushButton("Dashboard")
        new_scan_button = QPushButton("New Scan")
        history_button = QPushButton("Scan History")
        cases_button = QPushButton("Cases")
        reports_button = QPushButton("Reports")
        settings_button = QPushButton("Settings")

        sidebar_layout.addWidget(dashboard_button)
        sidebar_layout.addWidget(new_scan_button)
        sidebar_layout.addWidget(history_button)
        sidebar_layout.addWidget(cases_button)
        sidebar_layout.addWidget(reports_button)
        sidebar_layout.addWidget(settings_button)

        sidebar_layout.addStretch()

        main_layout.addWidget(sidebar)

        content_area = QWidget()
        content_layout = QVBoxLayout()
        content_area.setLayout(content_layout)

        title = QLabel("Dashboard")
        welcome = QLabel("Welcome to WebSET")

        content_layout.addWidget(title)
        content_layout.addWidget(welcome)

#adding summary cards - total scans, critical findings, open cases
        cards_layout = QHBoxLayout()

        total_scans_card = QFrame()
        total_scans_layout = QVBoxLayout()
        total_scans_card.setLayout(total_scans_layout)

        total_scans_title = QLabel("Total Scans")
        total_scans_number = QLabel("12")

        total_scans_layout.addWidget(total_scans_title)
        total_scans_layout.addWidget(total_scans_number)

        critical_card = QFrame()
        critical_layout = QVBoxLayout()
        critical_card.setLayout(critical_layout)

        critical_title = QLabel("Critical Findings")
        critical_number = QLabel("3")

        critical_layout.addWidget(critical_title)
        critical_layout.addWidget(critical_number)

        cases_card = QFrame()
        cases_layout = QVBoxLayout()
        cases_card.setLayout(cases_layout)

        cases_title = QLabel("Open Cases")
        cases_number = QLabel("5")

        cases_layout.addWidget(cases_title)
        cases_layout.addWidget(cases_number)

        cards_layout.addWidget(total_scans_card)
        cards_layout.addWidget(critical_card)
        cards_layout.addWidget(cases_card)

        content_layout.addLayout(cards_layout)

        content_layout.addStretch()

        main_layout.addWidget(content_area)

app = QApplication(sys.argv)

window = WebSETDashboard()
window.show()

sys.exit(app.exec())
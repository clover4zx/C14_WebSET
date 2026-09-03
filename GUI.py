import sys

#features used
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
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
        content_layout.addStretch()

        main_layout.addWidget(content_area)

app = QApplication(sys.argv)

window = WebSETDashboard()
window.show()

sys.exit(app.exec())
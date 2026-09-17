import sys

#features used
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,

    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,

    QPushButton,
)

from PyQt6.QtCore import (
    Qt,
)

#created main window, container
class WebSETDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WebSET - Website Security Evaluation Tool")
        self.setMinimumSize(1200, 700)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #summary area creation, seperating mainwindow into two (summary + dashboard)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        #sidebar creation
        sidebar = QWidget()

        ####CSS****
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #24133D;")

        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)

        main_layout.addWidget(sidebar, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        #######

        # logo placement
        logo = QLabel("WebSET")
        sidebar_layout.addWidget(logo)

        #nav buttons
        dashboard_button = QPushButton("Dashboard")
        new_scan_button = QPushButton("New Scan")
        history_button = QPushButton("Scan History")
        cases_button = QPushButton("Cases")
        reports_button = QPushButton("Reports")
        settings_button = QPushButton("Settings")

        #widgets
        sidebar_layout.addWidget(dashboard_button)
        sidebar_layout.addWidget(new_scan_button)
        sidebar_layout.addWidget(history_button)
        sidebar_layout.addWidget(cases_button)
        sidebar_layout.addWidget(reports_button)
        sidebar_layout.addWidget(settings_button)

        sidebar_layout.addStretch()

app = QApplication(sys.argv)
window = WebSETDashboard()
window.show()

sys.exit(app.exec())


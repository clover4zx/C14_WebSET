import sys
from pathlib import Path

#features used
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,

    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,

    QPushButton,

    QFrame,
)

from PyQt6.QtCore import Qt,

STYLESHEET_PATH = Path(__file__).parent / "styles.qss"

NAV_ITEMS = [
    "Dashboard",
    "New Scan",
    "Scan History",
    "Cases",
    "Reports",
    "Settings",
]

SUMMARY_CARDS = [

]
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

        ###Right-handside###########################
        content_area = QWidget()
        content_layout = QVBoxLayout()
        content_area.setLayout(content_layout)

        #CSSS
        content_layout.setContentsMargins(20, 20, 20, 0)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        main_layout.addWidget(content_area)

        #Heading
        title = QLabel("Dashboard")
        welcome = QLabel("Security Overview of Your Web Applictions")

        #CSSSS*****
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)

        welcome.setStyleSheet("""
            font-size: 16px;
        """)

        content_layout.addWidget(
            title,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        content_layout.addWidget(
            welcome,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        #Summary cards
        cards_layout = QHBoxLayout()

        #first
        total_scans_card = QFrame()

        #CSS Size
        total_scans_card.setFixedSize(200, 120)

        total_scans_card.setObjectName("total_scans_card")

        total_scans_layout = QVBoxLayout()
        total_scans_card.setLayout(total_scans_layout)

        # CSSS**
        total_scans_card.setStyleSheet("""
            #total_scans_card {
                border: 2px solid black;
                border-radius: 10px;
            }
        """)

        total_scans_title = QLabel("Total Scans")
        total_scans_number = QLabel("12")

        #CSS***
        total_scans_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_scans_number.setAlignment(Qt.AlignmentFlag.AlignCenter)

        total_scans_layout.addWidget(total_scans_title)
        total_scans_layout.addWidget(total_scans_number)

        cards_layout.addWidget(
            total_scans_card,
            alignment=Qt.AlignmentFlag.AlignLeft
        )

        content_layout.addLayout(cards_layout)








app = QApplication(sys.argv)
window = WebSETDashboard()
window.show()

sys.exit(app.exec())


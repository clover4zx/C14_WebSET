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


   QStackedWidget,
)


from PyQt6.QtCore import (
   Qt,
)


# each sidebar button's page lives in its own file under pages/
from pages.dashboard_page import DashboardPage
from pages.new_scan_page import NewScanPage
from pages.scan_history_page import ScanHistoryPage
from pages.cases_page import CasesPage
from pages.reports_page import ReportsPage
from pages.settings_page import SettingsPage




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
       # Holds every page; only one is visible at a time.
       self.stack = QStackedWidget()


       self.dashboard_page = DashboardPage()
       self.new_scan_page = NewScanPage()
       self.history_page = ScanHistoryPage()
       self.cases_page = CasesPage()
       self.reports_page = ReportsPage()
       self.settings_page = SettingsPage()


       self.stack.addWidget(self.dashboard_page)
       self.stack.addWidget(self.new_scan_page)
       self.stack.addWidget(self.history_page)
       self.stack.addWidget(self.cases_page)
       self.stack.addWidget(self.reports_page)
       self.stack.addWidget(self.settings_page)


       main_layout.addWidget(self.stack, 1)


       # Wire each button to show its matching page.
       dashboard_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.dashboard_page))
       new_scan_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.new_scan_page))
       history_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.history_page))
       cases_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.cases_page))
       reports_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.reports_page))
       settings_button.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))


       # Start on the Dashboard page.
       self.stack.setCurrentWidget(self.dashboard_page)




app = QApplication(sys.argv)
window = WebSETDashboard()
window.show()


sys.exit(app.exec())

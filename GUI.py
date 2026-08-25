import sys
from PyQt6.QtWidgets import QApplication, QLabel
app = QApplication(sys.argv)
label = QLabel("Hello WebSET!")
label.show()
app.exec()

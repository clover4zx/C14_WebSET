import sys

from PyQt6.QtWidgets import QApplication, QLabel

app= QApplication(sys.argv) #a list?
label = QLabel("Hello World")
label.show() #widget output
app.exec() #executes command
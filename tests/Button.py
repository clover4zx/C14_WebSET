import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import pyqtSlot

@pyqtSlot() #creates class for slot
def say_hello(): #defining function done by user
    print("Yay")

app = QApplication(sys.argv) #creates Qt application
button = QPushButton("Click me") #creating button
button.clicked.connect(say_hello) #connects button and application
button.show() #visible

app.exec() #main Qt loop
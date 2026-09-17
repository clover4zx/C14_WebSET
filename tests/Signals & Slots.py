import sys
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class Communicate(QObject):
    speak = pyqtSignal([int], [str])#2 signals - for int, strings)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.speak[int].connect(self.say_something)
        self.speak[str].connect(self.say_something)

    @pyqtSlot(int)
    @pyqtSlot(str) #these slots receives an int/str
    def say_something(self, arg):
        if isinstance(arg, int):
            print("This is a number:", arg)
        elif isinstance(arg, str):
            print("This is a string:", arg)

def say_hello():
    print("Yay")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    someone = Communicate()

    someone.speak[int].emit(10)
    someone.speak[str].emit("Hello everybody!")

    button = QPushButton("Click me")  # creating button
    button.clicked.connect(say_hello)  # connects button and application
    button.show()  # visible

    app.exec()  # main Qt loop

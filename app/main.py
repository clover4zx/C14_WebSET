"""
WebSET - Website Security Evaluation Tool
Entry point. Run this file (e.g. right-click > Run in PyCharm, or
`python main.py` from the project root).
"""

import sys

from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()